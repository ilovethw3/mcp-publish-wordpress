"""角色模板管理服务

该服务提供角色模板的CRUD操作、角色应用到Agent、有效权限计算等功能。
"""

from typing import Dict, List, Optional
from sqlmodel import select
from mcp_wordpress.core.database import get_session
from mcp_wordpress.models.role_templates import RoleTemplate, RoleTemplateHistory, SYSTEM_ROLE_TEMPLATES
from mcp_wordpress.models.agent import Agent
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)


class RoleTemplateService:
    """角色模板管理服务"""
    
    def __init__(self):
        self._agent_cache = {}
        self._role_cache = {}
    
    async def initialize_system_roles(self):
        """系统启动时初始化预定义角色"""
        try:
            async with get_session() as session:
                for role_id, config in SYSTEM_ROLE_TEMPLATES.items():
                    # 检查角色是否已存在
                    existing_result = await session.execute(
                        select(RoleTemplate).where(RoleTemplate.id == role_id)
                    )
                    role = existing_result.scalars().first()
                    
                    if role:
                        # 更新系统角色（保持最新）
                        role.name = config["name"]
                        role.description = config["description"]
                        role.permissions = config["permissions"]
                        role.quota_limits = config.get("quota_limits", {})
                        role.updated_at = datetime.utcnow()
                        logger.info(f"Updated system role: {role_id}")
                    else:
                        # 创建新的系统角色
                        now = datetime.utcnow()
                        role = RoleTemplate(
                            id=role_id,
                            name=config["name"],
                            description=config["description"],
                            permissions=config["permissions"],
                            quota_limits=config.get("quota_limits", {}),
                            is_system_role=True,
                            is_active=True,
                            created_at=now,
                            updated_at=now
                        )
                        session.add(role)
                        logger.info(f"Created system role: {role_id}")
                    
                    # 缓存角色
                    self._role_cache[role_id] = role
                
                await session.commit()
                logger.info("System roles initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize system roles: {e}")
            raise
    
    
    async def get_effective_permissions(self, agent_id: str) -> Dict:
        """获取agent的有效权限（角色权限+个性化覆盖）"""
        try:
            # 每次都从数据库获取最新权限，确保实时生效
            async with get_session() as session:
                agent_result = await session.execute(
                    select(Agent).where(Agent.id == agent_id)
                )
                agent = agent_result.scalars().first()
                if not agent:
                    return {}
            
            # 如果没有角色模板，直接返回agent权限
            if not agent.role_template_id:
                return agent.permissions
            
            # 获取角色模板权限
            role_permissions = await self._get_role_permissions(agent.role_template_id)
            if not role_permissions:
                return agent.permissions
            
            # 合并权限：角色权限 + 个性化覆盖
            effective_permissions = {**role_permissions}
            if agent.permissions_override:
                effective_permissions.update(agent.permissions_override)
            
            return effective_permissions
        except Exception as e:
            logger.error(f"Failed to get effective permissions for agent {agent_id}: {e}")
            return {}
    
    async def _get_role_permissions(self, role_id: str) -> Dict:
        """获取角色模板权限（带缓存）"""
        try:
            # 尝试从缓存获取
            if role_id in self._role_cache:
                role = self._role_cache[role_id]
                return role.permissions
            
            # 从数据库获取
            async with get_session() as session:
                role_result = await session.execute(
                    select(RoleTemplate).where(
                        RoleTemplate.id == role_id,
                        RoleTemplate.is_active == True
                    )
                )
                role = role_result.scalars().first()
                if role:
                    # 缓存角色
                    self._role_cache[role_id] = role
                    return role.permissions
                
                return {}
        except Exception as e:
            logger.error(f"Failed to get role permissions for {role_id}: {e}")
            return {}
    
    
    def clear_cache(self):
        """清理所有缓存"""
        self._agent_cache.clear()
        self._role_cache.clear()
        logger.info("Role template service cache cleared")


# 全局服务实例
role_template_service = RoleTemplateService()