"""
Authentication middleware for MCP WordPress Publisher v2.1

This module implements FastMCP middleware for tool-level access control
and authentication event auditing.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastmcp.server.middleware import Middleware, MiddlewareContext, CallNext
from fastmcp.server.dependencies import get_access_token
from fastmcp.exceptions import ToolError
from fastmcp.tools.tool import ToolResult
import mcp.types as mt

from mcp_wordpress.core.errors import AuthenticationError, AuthorizationError
from mcp_wordpress.core.security import SecurityManager


logger = logging.getLogger(__name__)


class AuthenticationMiddleware(Middleware):
    """Authentication middleware for tool-level access control
    
    Implements FastMCP middleware pattern to enforce authentication
    and authorization for MCP tool calls.
    """
    
    def __init__(self):
        # 工具权限映射 - 定义每个工具需要的权限范围
        self.tool_permissions = {
            "submit_article": ["article:submit"],
            "list_articles": ["article:list"],
            "get_article_status": ["article:read"],
            "approve_article": ["article:approve"],
            "reject_article": ["article:reject"],
            "list_agents": ["agent:read"],
            "list_sites": ["site:read"],
            "get_agent_stats": ["agent:read"],
            "get_site_health": ["site:read"],
            # 测试工具权限
            "ping": [],  # 无需特殊权限
        }
    
    async def on_call_tool(
        self, 
        context: MiddlewareContext[mt.CallToolRequestParams],
        call_next: CallNext[mt.CallToolRequestParams, ToolResult]
    ) -> ToolResult:
        """工具调用前的权限检查
        
        Args:
            context: 中间件上下文，包含工具调用请求参数
            call_next: 调用下一个中间件或工具的函数
            
        Returns:
            ToolResult: 工具执行结果
            
        Raises:
            ToolError: 当权限不足或认证失败时
        """
        # 从上下文中提取工具名称和参数
        name = context.message.name
        arguments = context.message.arguments or {}
        
        # 开发模式检查 - 跳过认证
        from mcp_wordpress.core.config import settings
        if settings.development_mode:
            logger.warning(f"⚠️  开发模式：跳过工具 '{name}' 的认证检查")
            return await call_next(context)
        
        try:
            # 获取访问令牌
            access_token = get_access_token()
            if not access_token:
                await self._log_auth_failure(name, "未提供访问令牌")
                raise ToolError("认证失败: 未提供有效的访问令牌")
            
            # 安全管理器认证检查
            security_manager = SecurityManager.get_instance()
            # FastMCP 2.11.x: AccessToken没有metadata属性，使用client_id作为agent标识
            agent_name = access_token.client_id
            
            if not await security_manager.authenticate_request(access_token.client_id, agent_name or "unknown"):
                await self._log_auth_failure(name, "安全管理器拒绝请求", access_token.client_id)
                raise ToolError("请求被安全策略阻止（可能是速率限制）")
            
            # 检查工具权限要求
            required_scopes = self.tool_permissions.get(name, [])
            if required_scopes:
                missing_scopes = self._check_permissions(access_token, required_scopes)
                if missing_scopes:
                    await self._log_auth_failure(
                        name, 
                        f"权限不足，缺少范围: {missing_scopes}",
                        access_token.client_id
                    )
                    raise ToolError(f"权限不足: 需要权限范围 {missing_scopes}")
            
            # 记录成功的工具调用
            await self._log_tool_access(name, access_token.client_id, arguments)
            
            # 记录工具调用到安全管理器
            await security_manager.log_audit_event(
                agent_id=access_token.client_id,
                action=f"tool_call:{name}",
                resource=name,
                success=True,
                details={"arguments_count": len(arguments)}
            )
            
            # 权限检查通过，调用下一个中间件或工具
            return await call_next(context)
            
        except ToolError:
            # 重新抛出ToolError
            raise
        except Exception as e:
            # 处理其他异常
            logger.error(f"认证中间件处理错误: {e}")
            raise ToolError("内部认证错误")
    
    def _check_permissions(self, access_token, required_scopes: list) -> list:
        """检查访问令牌是否具有所需权限
        
        Args:
            access_token: 访问令牌
            required_scopes: 所需权限范围
            
        Returns:
            list: 缺失的权限范围
        """
        if not access_token.scopes:
            return required_scopes
        
        missing_scopes = []
        for scope in required_scopes:
            if scope not in access_token.scopes:
                missing_scopes.append(scope)
        
        return missing_scopes
    
    async def _log_auth_failure(
        self, 
        tool_name: str, 
        reason: str,
        agent_id: Optional[str] = None
    ) -> None:
        """记录认证失败事件
        
        Args:
            tool_name: 工具名称
            reason: 失败原因
            agent_id: 代理ID（如果可用）
        """
        log_message = f"工具 {tool_name} 认证失败: {reason}"
        if agent_id:
            log_message += f" (代理: {agent_id})"
        
        logger.warning(log_message)
        
        # 记录认证失败到安全管理器
        if SecurityManager.instance:
            await SecurityManager.instance.log_audit_event(
                agent_id=agent_id or "unknown",
                action="authentication_failure",
                resource=tool_name,
                success=False,
                details={"reason": reason}
            )
    
    async def _log_tool_access(
        self,
        tool_name: str,
        agent_id: str,
        arguments: Dict[str, Any]
    ) -> None:
        """记录成功的工具访问事件
        
        Args:
            tool_name: 工具名称
            agent_id: 代理ID
            arguments: 工具参数
        """
        # 过滤敏感信息
        safe_args = self._sanitize_arguments(arguments)
        
        logger.info(f"代理 {agent_id} 调用工具 {tool_name}")
        logger.debug(f"工具参数: {safe_args}")
        
        # 记录成功的工具访问到安全管理器
        if SecurityManager.instance:
            await SecurityManager.instance.log_audit_event(
                agent_id=agent_id,
                action="tool_access",
                resource=tool_name,
                success=True,
                details={"sanitized_args": safe_args}
            )
    
    def _sanitize_arguments(self, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """清理工具参数中的敏感信息
        
        Args:
            arguments: 原始参数
            
        Returns:
            Dict[str, Any]: 清理后的参数
        """
        sensitive_keys = ['api_key', 'password', 'token', 'secret']
        safe_args = {}
        
        for key, value in arguments.items():
            if any(sensitive in key.lower() for sensitive in sensitive_keys):
                safe_args[key] = "[REDACTED]"
            else:
                safe_args[key] = value
        
        return safe_args