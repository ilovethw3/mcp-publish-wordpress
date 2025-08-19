"""
FastMCP Authentication Providers for MCP WordPress Publisher v2.1

This module implements FastMCP-compatible authentication providers
for multi-agent API key authentication.
"""

import logging
from typing import Optional, List
from fastmcp.server.auth import TokenVerifier
from fastmcp.server.dependencies import AccessToken
from starlette.requests import Request

from mcp_wordpress.services.config_service import config_service
from mcp_wordpress.auth.validators import secure_compare
from mcp_wordpress.core.errors import AuthenticationError


logger = logging.getLogger(__name__)


class DevelopmentModeAuthProvider(TokenVerifier):
    """开发模式认证提供者 - 允许所有请求"""
    
    def __init__(self):
        super().__init__(resource_server_url=None)
        self.logger = logging.getLogger(__name__)
    
    async def verify_token(self, request: Request) -> Optional[AccessToken]:
        """开发模式：创建虚拟访问令牌"""
        self.logger.warning("⚠️ 开发模式：使用虚拟访问令牌")
        
        # 无论请求是否有Authorization头，都返回虚拟令牌 (FastMCP 2.11.x 兼容格式)
        return AccessToken(
            token="dev-token",  # FastMCP 2.11.x 要求必须提供token参数
            client_id="dev-agent",
            scopes=["*"],  # 开发模式拥有所有权限
            metadata={
                "agent_name": "开发模式代理",
                "role": "development",
                "description": "开发模式虚拟代理"
            }
        )
    
    async def extract_token(self, request: Request) -> Optional[str]:
        """开发模式：总是返回虚拟令牌字符串"""
        return "dev-token"


class MultiAgentAuthProvider(TokenVerifier):
    """Multi-agent authentication provider
    
    Integrates with FastMCP's BearerAuthProvider to provide database-based
    API key authentication for multiple AI agents.
    """
    
    def __init__(self):
        super().__init__(resource_server_url=None)
        
    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """FastMCP 2.11.2 兼容性: verify_token 方法"""
        return await self.validate_token(token)
        
    async def validate_token(self, token: str) -> Optional[AccessToken]:
        """验证代理API密钥并返回访问令牌
        
        Args:
            token: API密钥令牌
            
        Returns:
            AccessToken: 如果验证成功返回访问令牌，否则返回None
        """
        try:
            print(f"🔐 DEBUG: MultiAgentAuthProvider.validate_token - 收到token: {token[:10] if token else 'None'}...")
            logger.debug(f"开始验证API密钥: {token[:10]}...")
            
            # 使用数据库服务查找匹配的代理
            agent_id = await config_service.validate_api_key(token)
            print(f"🔐 DEBUG: 密钥验证结果 - agent_id: {agent_id}")
            logger.debug(f"密钥验证结果 - agent_id: {agent_id}")
            
            if not agent_id:
                print("🔐 DEBUG: 收到无效的API密钥尝试")
                logger.warning("收到无效的API密钥尝试")
                return None
            
            # 获取代理配置
            try:
                agent = await config_service.get_agent(agent_id)
            except Exception as e:
                logger.error(f"获取代理配置失败: {e}")
                return None
            
            # 创建访问令牌 (FastMCP 2.11.x 兼容格式)
            access_token = AccessToken(
                token=token,  # FastMCP 2.11.x 要求必须提供token参数
                client_id=agent.id,
                scopes=self._get_agent_scopes(agent),
                metadata={
                    "agent_name": agent.name,
                    "agent_id": agent.id,
                    "role": "multi-agent",
                    "description": f"多代理认证: {agent.name}",
                    "permissions": agent.permissions
                }
            )
            
            logger.info(f"代理认证成功: {agent.name} ({agent.id})")
            return access_token
            
        except Exception as e:
            logger.error(f"认证过程发生错误: {e}")
            return None
    
    def _get_agent_scopes(self, agent) -> List[str]:
        """根据代理权限配置获取权限范围
        
        Args:
            agent: Agent 模型实例
            
        Returns:
            List[str]: 权限范围列表
        """
        # v2.1基于权限配置的动态范围
        scopes = []
        
        permissions = agent.permissions
        
        # 基础权限
        if permissions.get("can_submit_articles", False):
            scopes.append("article:submit")
        if permissions.get("can_edit_own_articles", False):
            scopes.append("article:edit")
        if permissions.get("can_delete_own_articles", False):
            scopes.append("article:delete")
        if permissions.get("can_view_statistics", False):
            scopes.append("article:statistics")
        
        # 审核权限
        if permissions.get("can_approve_articles", False):
            scopes.append("article:approve")
        if permissions.get("can_reject_articles", False):
            scopes.append("article:reject")
        
        # 通用读取权限
        scopes.extend([
            "article:read",
            "article:list", 
            "agent:read",
            "site:read"
        ])
        
        return scopes


class LegacyEnvironmentAuthProvider(TokenVerifier):
    """Legacy environment variable authentication provider
    
    Provides backward compatibility for single-agent setups using
    the AGENT_API_KEY environment variable.
    """
    
    def __init__(self, api_key: str, agent_id: str = "legacy-agent"):
        super().__init__(resource_server_url=None)
        self.api_key = api_key
        self.agent_id = agent_id
        
    async def verify_token(self, token: str) -> Optional[AccessToken]:
        """FastMCP 2.11.2 兼容性: verify_token 方法"""
        return await self.validate_token(token)
        
    async def validate_token(self, token: str) -> Optional[AccessToken]:
        """验证传统环境变量API密钥
        
        Args:
            token: API密钥令牌
            
        Returns:
            AccessToken: 如果验证成功返回访问令牌，否则返回None
        """
        if not secure_compare(token, self.api_key):
            return None
        
        return AccessToken(
            token=token,  # 原始令牌
            client_id=self.agent_id,
            scopes=[
                "article:submit",
                "article:read", 
                "article:list",
                "article:review",
                "article:approve",
                "article:reject",
                "agent:read",
                "site:read"
            ],
            metadata={
                "agent_name": "传统代理",
                "role": "legacy",
                "description": "从环境变量配置的传统代理"
            }
        )


