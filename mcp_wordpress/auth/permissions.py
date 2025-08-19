"""权限检查装饰器和权限管理

提供基于角色模板的权限检查装饰器和权限验证功能。
"""

from functools import wraps
from typing import List, Optional, Callable, Any
from fastmcp.server.dependencies import get_access_token
from mcp_wordpress.core.errors import PermissionDeniedError
from mcp_wordpress.services.role_template_service import role_template_service
import logging

logger = logging.getLogger(__name__)

# 权限名称的中文映射
PERMISSION_LABELS = {
    "can_submit_articles": "提交文章",
    "can_edit_own_articles": "编辑自己的文章", 
    "can_edit_others_articles": "编辑他人文章",
    "can_approve_articles": "审批文章",
    "can_publish_articles": "发布文章",
    "can_view_statistics": "查看统计信息"
}

def get_permission_label(permission: str) -> str:
    """获取权限的中文标签"""
    return PERMISSION_LABELS.get(permission, permission)


def require_permission(
    permission: str,
    check_ownership: bool = False,
    check_quota: bool = False
) -> Callable:
    """权限检查装饰器
    
    Args:
        permission: 需要的权限名称 (如 'can_submit_articles')
        check_ownership: 是否检查资源所有权
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                # 获取当前用户访问令牌
                access_token = get_access_token()
                if not access_token:
                    raise PermissionDeniedError("未找到有效的访问令牌")
                
                # 执行权限检查
                from mcp_wordpress.auth.permission_checker import permission_checker
                has_permission = await permission_checker.check_permission(
                    agent_id=access_token.client_id,
                    permission=permission,
                    check_ownership=check_ownership,
                    check_quota=check_quota,
                    kwargs=kwargs
                )
                
                if not has_permission:
                    logger.warning(f"Permission denied for agent {access_token.client_id}: {permission}")
                    raise PermissionDeniedError(f"权限不足: 需要'{get_permission_label(permission)}'权限")
                
                # 执行原函数
                return await func(*args, **kwargs)
            except PermissionDeniedError:
                raise
            except Exception as e:
                logger.error(f"Permission check error for {permission}: {e}")
                raise PermissionDeniedError(f"权限检查失败: {str(e)}")
        return wrapper
    return decorator


def require_any_permission(permissions: List[str]) -> Callable:
    """多权限检查装饰器 - 满足任一权限即可"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                access_token = get_access_token()
                if not access_token:
                    raise PermissionDeniedError("未找到有效的访问令牌")
                
                from mcp_wordpress.auth.permission_checker import permission_checker
                
                # 检查是否有任一权限
                for permission in permissions:
                    try:
                        if await permission_checker.check_permission(
                            agent_id=access_token.client_id,
                            permission=permission,
                            check_quota=False,  # 默认不检查配额，除非明确需要
                            kwargs=kwargs
                        ):
                            logger.debug(f"Permission granted for agent {access_token.client_id}: {permission}")
                            return await func(*args, **kwargs)
                    except Exception as e:
                        logger.debug(f"Permission check failed for {permission}: {e}")
                        continue
                
                logger.warning(f"All permissions denied for agent {access_token.client_id}: {permissions}")
                permission_labels = [get_permission_label(p) for p in permissions]
                raise PermissionDeniedError(f"权限不足: 需要以下权限之一: {', '.join(permission_labels)}")
            except PermissionDeniedError:
                raise
            except Exception as e:
                logger.error(f"Permission check error for {permissions}: {e}")
                raise PermissionDeniedError(f"权限检查失败: {str(e)}")
        return wrapper
    return decorator


def require_edit_permission() -> Callable:
    """文章编辑权限装饰器 - 自动处理所有权检查"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                access_token = get_access_token()
                if not access_token:
                    raise PermissionDeniedError("未找到有效的访问令牌")
                
                from mcp_wordpress.auth.permission_checker import permission_checker
                from mcp_wordpress.services.role_template_service import role_template_service
                
                agent_id = access_token.client_id
                
                # 获取有效权限
                effective_permissions = await role_template_service.get_effective_permissions(agent_id)
                
                # 检查编辑权限
                has_edit_own = effective_permissions.get("can_edit_own_articles", False)
                has_edit_others = effective_permissions.get("can_edit_others_articles", False)
                
                if not (has_edit_own or has_edit_others):
                    raise PermissionDeniedError("权限不足: 需要文章编辑权限")
                
                # 如果只有编辑自己文章的权限，需要检查所有权
                if has_edit_own and not has_edit_others:
                    if not await permission_checker.check_permission(
                        agent_id=agent_id,
                        permission="can_edit_own_articles",
                        check_ownership=True,
                        check_quota=False,  # 编辑操作不检查配额
                        kwargs=kwargs
                    ):
                        raise PermissionDeniedError("权限不足: 只能编辑自己提交的文章")
                
                # 检查内容限制（分类和标签）
                if not await permission_checker.check_scope_restrictions(effective_permissions, kwargs):
                    raise PermissionDeniedError("权限不足: 分类或标签不在允许范围内")
                
                logger.debug(f"Edit permission granted for agent {agent_id}")
                return await func(*args, **kwargs)
                
            except PermissionDeniedError:
                raise
            except Exception as e:
                logger.error(f"Edit permission check error: {e}")
                raise PermissionDeniedError(f"权限检查失败: {str(e)}")
        return wrapper
    return decorator


def require_submit_permission() -> Callable:
    """文章提交权限装饰器 - 自动处理内容限制和配额检查"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                access_token = get_access_token()
                if not access_token:
                    raise PermissionDeniedError("未找到有效的访问令牌")
                
                from mcp_wordpress.auth.permission_checker import permission_checker
                from mcp_wordpress.services.role_template_service import role_template_service
                
                agent_id = access_token.client_id
                
                # 获取有效权限
                effective_permissions = await role_template_service.get_effective_permissions(agent_id)
                
                # 检查提交权限
                if not effective_permissions.get("can_submit_articles", False):
                    raise PermissionDeniedError("权限不足: 需要文章提交权限")
                
                # 检查内容限制（分类和标签）
                if not await permission_checker.check_scope_restrictions(effective_permissions, kwargs):
                    raise PermissionDeniedError("权限不足: 分类或标签不在允许范围内")
                
                # 检查配额限制
                quota_result = await permission_checker.check_quota_limits_detailed(agent_id, effective_permissions)
                if not quota_result.allowed:
                    raise PermissionDeniedError(f"配额超限: {quota_result.reason}")
                
                # 检查工作时间限制
                if not await permission_checker.check_working_hours(effective_permissions):
                    raise PermissionDeniedError("权限不足: 当前不在允许的工作时间内")
                
                logger.debug(f"Submit permission granted for agent {agent_id}")
                return await func(*args, **kwargs)
                
            except PermissionDeniedError:
                raise
            except Exception as e:
                logger.error(f"Submit permission check error: {e}")
                raise PermissionDeniedError(f"权限检查失败: {str(e)}")
        return wrapper
    return decorator


def require_all_permissions(permissions: List[str]) -> Callable:
    """多权限检查装饰器 - 需要满足所有权限"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            try:
                access_token = get_access_token()
                if not access_token:
                    raise PermissionDeniedError("未找到有效的访问令牌")
                
                from mcp_wordpress.auth.permission_checker import permission_checker
                
                # 检查所有权限
                for permission in permissions:
                    if not await permission_checker.check_permission(
                        agent_id=access_token.client_id,
                        permission=permission,
                        check_quota=False,  # 默认不检查配额，除非明确需要
                        kwargs=kwargs
                    ):
                        logger.warning(f"Permission denied for agent {access_token.client_id}: {permission}")
                        raise PermissionDeniedError(f"权限不足: 缺少'{get_permission_label(permission)}'权限")
                
                logger.debug(f"All permissions granted for agent {access_token.client_id}: {permissions}")
                return await func(*args, **kwargs)
            except PermissionDeniedError:
                raise
            except Exception as e:
                logger.error(f"Permission check error for {permissions}: {e}")
                raise PermissionDeniedError(f"权限检查失败: {str(e)}")
        return wrapper
    return decorator


def check_permission_sync(agent_id: str, permission: str, **kwargs) -> bool:
    """同步权限检查 - 用于非异步场景"""
    import asyncio
    
    try:
        from mcp_wordpress.auth.permission_checker import permission_checker
        return asyncio.run(permission_checker.check_permission(
            agent_id=agent_id,
            permission=permission,
            kwargs=kwargs
        ))
    except Exception as e:
        logger.error(f"Sync permission check error for {permission}: {e}")
        return False


async def check_permission_async(agent_id: str, permission: str, **kwargs) -> bool:
    """异步权限检查 - 用于异步场景"""
    try:
        from mcp_wordpress.auth.permission_checker import permission_checker
        return await permission_checker.check_permission(
            agent_id=agent_id,
            permission=permission,
            kwargs=kwargs
        )
    except Exception as e:
        logger.error(f"Async permission check error for {permission}: {e}")
        return False


def get_current_agent_id() -> Optional[str]:
    """获取当前Agent ID"""
    try:
        access_token = get_access_token()
        return access_token.client_id if access_token else None
    except Exception:
        return None


async def get_current_agent_permissions() -> dict:
    """获取当前Agent的有效权限"""
    try:
        agent_id = get_current_agent_id()
        if not agent_id:
            return {}
        
        return await role_template_service.get_effective_permissions(agent_id)
    except Exception as e:
        logger.error(f"Failed to get current agent permissions: {e}")
        return {}