"""权限检查器实现

专注于操作权限验证，包括基础权限、配额限制、工作时间、所有权和范围限制检查。
"""

from typing import List, Dict, Optional, Any
from dataclasses import dataclass
from datetime import datetime, time
import pytz
from sqlmodel import select, func
from mcp_wordpress.core.database import get_session
from mcp_wordpress.models.agent import Agent
from mcp_wordpress.models.article import Article
from mcp_wordpress.services.role_template_service import role_template_service
import logging

logger = logging.getLogger(__name__)


@dataclass
class PermissionCheckResult:
    """权限检查结果"""
    allowed: bool
    reason: Optional[str] = None
    remaining_quota: Optional[Dict[str, int]] = None


class PermissionChecker:
    """权限检查器 - 专注于操作权限，不做内容审查"""
    
    def __init__(self):
        self._agent_cache = {}
        self._cache_ttl = 300  # 5分钟缓存
    
    async def check_permission(
        self,
        agent_id: str,
        permission: str,
        check_ownership: bool = False,
        check_quota: bool = False,
        kwargs: Optional[Dict[str, Any]] = None
    ) -> bool:
        """检查单个权限"""
        
        try:
            # 1. 获取agent配置
            agent = await self._get_agent(agent_id)
            if not agent or agent.status != "active":
                logger.debug(f"Agent {agent_id} not found or inactive")
                return False
            
            # 2. 获取有效权限（包括角色模板权限）
            effective_permissions = await role_template_service.get_effective_permissions(agent_id)
            if not effective_permissions:
                logger.debug(f"No permissions found for agent {agent_id}")
                return False
            
            # 3. 检查基础权限
            if not effective_permissions.get(permission, False):
                logger.debug(f"Basic permission {permission} denied for agent {agent_id}")
                return False
            
            # 4. 检查配额限制（仅在需要时）
            if check_quota and not await self._check_quota_limits(agent, effective_permissions):
                logger.debug(f"Quota limits exceeded for agent {agent_id}")
                return False
            
            # 5. 检查工作时间限制
            if not await self._check_working_hours(effective_permissions):
                logger.debug(f"Working hours restriction for agent {agent_id}")
                return False
            
            # 6. 检查资源所有权
            if check_ownership and kwargs:
                if not await self._check_ownership(agent_id, kwargs):
                    logger.debug(f"Ownership check failed for agent {agent_id}")
                    return False
            
            # 7. 检查范围限制
            if not await self._check_scope_restrictions(effective_permissions, kwargs):
                logger.debug(f"Scope restrictions failed for agent {agent_id}")
                return False
            
            logger.debug(f"Permission {permission} granted for agent {agent_id}")
            return True
            
        except Exception as e:
            logger.error(f"Permission check error for agent {agent_id}, permission {permission}: {e}")
            return False
    
    async def check_permission_detailed(
        self,
        agent_id: str,
        permission: str,
        check_ownership: bool = False,
        check_quota: bool = False,
        kwargs: Optional[Dict[str, Any]] = None
    ) -> PermissionCheckResult:
        """详细权限检查，返回详细结果"""
        
        try:
            # 1. 获取agent配置
            agent = await self._get_agent(agent_id)
            if not agent:
                return PermissionCheckResult(False, f"Agent {agent_id} not found")
            
            if agent.status != "active":
                return PermissionCheckResult(False, f"Agent {agent_id} is {agent.status}")
            
            # 2. 获取有效权限
            effective_permissions = await role_template_service.get_effective_permissions(agent_id)
            if not effective_permissions:
                return PermissionCheckResult(False, "未配置权限")
            
            # 3. 检查基础权限
            if not effective_permissions.get(permission, False):
                return PermissionCheckResult(False, f"缺少权限: {permission}")
            
            # 4. 检查配额限制（仅在需要时）
            quota_check = None
            if check_quota:
                quota_check = await self._check_quota_limits_detailed(agent, effective_permissions)
                if not quota_check.allowed:
                    return quota_check
            
            # 5. 检查工作时间限制
            if not await self._check_working_hours(effective_permissions):
                return PermissionCheckResult(False, "不在允许的工作时间内")
            
            # 6. 检查资源所有权
            if check_ownership and kwargs:
                ownership_result = await self._check_ownership_detailed(agent_id, kwargs)
                if not ownership_result.allowed:
                    return ownership_result
            
            # 7. 检查范围限制
            scope_result = await self._check_scope_restrictions_detailed(effective_permissions, kwargs)
            if not scope_result.allowed:
                return scope_result
            
            return PermissionCheckResult(
                True, 
                "权限检查通过",
                quota_check.remaining_quota if quota_check else None
            )
            
        except Exception as e:
            logger.error(f"Detailed permission check error: {e}")
            return PermissionCheckResult(False, f"权限检查失败: {str(e)}")
    
    async def _get_agent(self, agent_id: str) -> Optional[Agent]:
        """获取agent配置（带缓存）"""
        try:
            # 检查缓存
            cache_key = f"agent_{agent_id}"
            cached_data = self._agent_cache.get(cache_key)
            if cached_data:
                agent, timestamp = cached_data
                if (datetime.utcnow() - timestamp).seconds < self._cache_ttl:
                    return agent
            
            # 从数据库获取
            async with get_session() as session:
                result = await session.execute(select(Agent).where(Agent.id == agent_id))
                agent = result.scalars().first()
                
                if agent:
                    # 缓存agent
                    self._agent_cache[cache_key] = (agent, datetime.utcnow())
                
                return agent
        except Exception as e:
            logger.error(f"Failed to get agent {agent_id}: {e}")
            return None
    
    async def _check_quota_limits(self, agent: Agent, permissions: Dict) -> bool:
        """检查配额限制"""
        try:
            quota_limits = permissions.get("quota_limits", {})
            if not quota_limits:
                return True
            
            # 检查日配额
            daily_limit = quota_limits.get("daily_articles", 0)
            if daily_limit > 0:
                daily_count = await self._get_daily_article_count(agent.id)
                if daily_count >= daily_limit:
                    return False
            
            # 检查月配额
            monthly_limit = quota_limits.get("monthly_articles", 0)
            if monthly_limit > 0:
                monthly_count = await self._get_monthly_article_count(agent.id)
                if monthly_count >= monthly_limit:
                    return False
            
            return True
        except Exception as e:
            logger.error(f"Quota check error for agent {agent.id}: {e}")
            return False
    
    async def _check_quota_limits_detailed(self, agent: Agent, permissions: Dict) -> PermissionCheckResult:
        """详细检查配额限制"""
        try:
            quota_limits = permissions.get("quota_limits", {})
            if not quota_limits:
                return PermissionCheckResult(True, "无配额限制", {})
            
            remaining_quota = {}
            
            # 检查日配额
            daily_limit = quota_limits.get("daily_articles", 0)
            if daily_limit > 0:
                daily_count = await self._get_daily_article_count(agent.id)
                remaining_daily = daily_limit - daily_count
                remaining_quota["daily"] = max(0, remaining_daily)
                
                if daily_count >= daily_limit:
                    return PermissionCheckResult(
                        False, 
                        f"日配额超限: {daily_count}/{daily_limit}",
                        remaining_quota
                    )
            
            # 检查月配额
            monthly_limit = quota_limits.get("monthly_articles", 0)
            if monthly_limit > 0:
                monthly_count = await self._get_monthly_article_count(agent.id)
                remaining_monthly = monthly_limit - monthly_count
                remaining_quota["monthly"] = max(0, remaining_monthly)
                
                if monthly_count >= monthly_limit:
                    return PermissionCheckResult(
                        False, 
                        f"月配额超限: {monthly_count}/{monthly_limit}",
                        remaining_quota
                    )
            
            return PermissionCheckResult(True, "配额检查通过", remaining_quota)
        except Exception as e:
            logger.error(f"Detailed quota check error for agent {agent.id}: {e}")
            return PermissionCheckResult(False, f"配额检查失败: {str(e)}")
    
    async def _check_working_hours(self, permissions: Dict) -> bool:
        """检查工作时间限制"""
        try:
            quota_limits = permissions.get("quota_limits", {})
            working_hours = quota_limits.get("working_hours", {})
            
            if not working_hours.get("enabled", False):
                return True
            
            timezone = pytz.timezone(working_hours.get("timezone", "UTC"))
            now = datetime.now(timezone)
            
            # 检查工作日
            working_days = working_hours.get("working_days", list(range(1, 8)))
            if now.weekday() + 1 not in working_days:
                return False
            
            # 检查工作时间
            start_time = time.fromisoformat(working_hours.get("start", "00:00"))
            end_time = time.fromisoformat(working_hours.get("end", "23:59"))
            current_time = now.time()
            
            return start_time <= current_time <= end_time
        except Exception as e:
            logger.error(f"Working hours check error: {e}")
            return True  # 发生错误时允许通过
    
    async def _check_ownership(self, agent_id: str, kwargs: Dict[str, Any]) -> bool:
        """检查资源所有权"""
        try:
            article_id = kwargs.get("article_id")
            if not article_id:
                return True  # 没有article_id，跳过所有权检查
            
            async with get_session() as session:
                result = await session.execute(
                    select(Article).where(Article.id == article_id)
                )
                article = result.scalars().first()
                
                if not article:
                    return False  # 文章不存在
                
                return article.submitting_agent_id == agent_id
        except Exception as e:
            logger.error(f"Ownership check error: {e}")
            return False
    
    async def _check_ownership_detailed(self, agent_id: str, kwargs: Dict[str, Any]) -> PermissionCheckResult:
        """详细检查资源所有权"""
        try:
            article_id = kwargs.get("article_id")
            if not article_id:
                return PermissionCheckResult(True, "无需检查所有权")
            
            async with get_session() as session:
                result = await session.execute(
                    select(Article).where(Article.id == article_id)
                )
                article = result.scalars().first()
                
                if not article:
                    return PermissionCheckResult(False, f"文章 {article_id} 不存在")
                
                if article.submitting_agent_id == agent_id:
                    return PermissionCheckResult(True, "所有权验证通过")
                else:
                    return PermissionCheckResult(
                        False, 
                        f"文章 {article_id} 属于 {article.submitting_agent_id}，您无权访问"
                    )
        except Exception as e:
            logger.error(f"Detailed ownership check error: {e}")
            return PermissionCheckResult(False, f"所有权检查失败: {str(e)}")
    
    async def _check_scope_restrictions(self, permissions: Dict, kwargs: Optional[Dict[str, Any]]) -> bool:
        """检查范围限制"""
        try:
            if not kwargs:
                return True
            
            # 检查分类限制
            category = kwargs.get("category")
            if category:
                allowed_categories = permissions.get("allowed_categories", [])
                if allowed_categories and category not in allowed_categories:
                    return False
            
            # 检查标签限制
            tags = kwargs.get("tags", "")
            if tags:
                allowed_tags = permissions.get("allowed_tags", [])
                if allowed_tags:
                    tag_list = [tag.strip() for tag in tags.split(',')]
                    if not all(tag in allowed_tags for tag in tag_list if tag):
                        return False
            
            return True
        except Exception as e:
            logger.error(f"Scope restrictions check error: {e}")
            return True  # 发生错误时允许通过
    
    async def _check_scope_restrictions_detailed(self, permissions: Dict, kwargs: Optional[Dict[str, Any]]) -> PermissionCheckResult:
        """详细检查范围限制"""
        try:
            if not kwargs:
                return PermissionCheckResult(True, "无需检查范围限制")
            
            # 检查分类限制
            category = kwargs.get("category")
            if category:
                allowed_categories = permissions.get("allowed_categories", [])
                if allowed_categories and category not in allowed_categories:
                    return PermissionCheckResult(
                        False, 
                        f"分类 '{category}' 不在允许列表中: {allowed_categories}"
                    )
            
            # 检查标签限制
            tags = kwargs.get("tags", "")
            if tags:
                allowed_tags = permissions.get("allowed_tags", [])
                if allowed_tags:
                    tag_list = [tag.strip() for tag in tags.split(',')]
                    forbidden_tags = [tag for tag in tag_list if tag and tag not in allowed_tags]
                    if forbidden_tags:
                        return PermissionCheckResult(
                            False, 
                            f"标签 {forbidden_tags} 不在允许列表中: {allowed_tags}"
                        )
            
            return PermissionCheckResult(True, "范围限制检查通过")
        except Exception as e:
            logger.error(f"Detailed scope restrictions check error: {e}")
            return PermissionCheckResult(False, f"范围检查失败: {str(e)}")
    
    async def _get_daily_article_count(self, agent_id: str) -> int:
        """获取今日文章数量"""
        try:
            today = datetime.now().date()
            async with get_session() as session:
                result = await session.execute(
                    select(func.count(Article.id)).where(
                        Article.submitting_agent_id == agent_id,
                        func.date(Article.created_at) == today
                    )
                )
                return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to get daily article count for {agent_id}: {e}")
            return 0
    
    async def _get_monthly_article_count(self, agent_id: str) -> int:
        """获取本月文章数量"""
        try:
            today = datetime.now()
            month_start = today.replace(day=1)
            async with get_session() as session:
                result = await session.execute(
                    select(func.count(Article.id)).where(
                        Article.submitting_agent_id == agent_id,
                        Article.created_at >= month_start
                    )
                )
                return result.scalar() or 0
        except Exception as e:
            logger.error(f"Failed to get monthly article count for {agent_id}: {e}")
            return 0
    
    def clear_cache(self):
        """清理权限检查器缓存"""
        self._agent_cache.clear()
        logger.info("Permission checker cache cleared")
    
    # 公开的检查方法供装饰器使用
    async def check_scope_restrictions(self, permissions: Dict, kwargs: Optional[Dict[str, Any]]) -> bool:
        """检查范围限制 - 公开方法"""
        return await self._check_scope_restrictions(permissions, kwargs)
    
    async def check_quota_limits_detailed(self, agent_id: str, permissions: Dict) -> PermissionCheckResult:
        """检查配额限制 - 公开方法"""
        agent = await self._get_agent(agent_id)
        return await self._check_quota_limits_detailed(agent, permissions)
    
    async def check_working_hours(self, permissions: Dict) -> bool:
        """检查工作时间限制 - 公开方法"""
        return await self._check_working_hours(permissions)


# 全局权限检查器实例
permission_checker = PermissionChecker()