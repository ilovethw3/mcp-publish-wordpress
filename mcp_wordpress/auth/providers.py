"""
FastMCP Authentication Providers for MCP WordPress Publisher v2.1

This module implements FastMCP-compatible authentication providers
for multi-agent API key authentication.
"""

import logging
from typing import Optional, List
from fastmcp.auth import BearerAuthProvider, AccessToken

from mcp_wordpress.config.agents import AgentConfigManager
from mcp_wordpress.auth.validators import AgentKeyValidator
from mcp_wordpress.core.errors import AuthenticationError


logger = logging.getLogger(__name__)


class MultiAgentAuthProvider(BearerAuthProvider):
    """Multi-agent authentication provider
    
    Integrates with FastMCP's BearerAuthProvider to provide API key
    authentication for multiple AI agents.
    """
    
    def __init__(self, config_manager: AgentConfigManager):
        self.config_manager = config_manager
        self.validator = AgentKeyValidator()
        
    async def validate_token(self, token: str) -> Optional[AccessToken]:
        """验证代理API密钥并返回访问令牌
        
        Args:
            token: API密钥令牌
            
        Returns:
            AccessToken: 如果验证成功返回访问令牌，否则返回None
        """
        try:
            # 查找匹配的代理
            agent_id = self.config_manager.validate_api_key(token)
            if not agent_id:
                logger.warning("收到无效的API密钥尝试")
                return None
            
            # 获取代理配置
            agent_config = self.config_manager.get_agent(agent_id)
            if not agent_config:
                logger.error(f"代理配置不存在: {agent_id}")
                return None
            
            # 创建访问令牌
            access_token = AccessToken(
                client_id=agent_config.id,
                scopes=self._get_agent_scopes(agent_config.role),
                metadata={
                    "agent_name": agent_config.name,
                    "role": agent_config.role,
                    "description": agent_config.description
                }
            )
            
            logger.info(f"代理认证成功: {agent_config.name} ({agent_config.id})")
            return access_token
            
        except Exception as e:
            logger.error(f"认证过程发生错误: {e}")
            return None
    
    def _get_agent_scopes(self, role: str) -> List[str]:
        """根据代理角色获取权限范围
        
        Args:
            role: 代理角色
            
        Returns:
            List[str]: 权限范围列表
        """
        # v2.1采用简化权限模型 - 所有代理具有相同的基础权限
        base_scopes = [
            "article:submit",
            "article:read",
            "article:list",
            "agent:read",
            "site:read"
        ]
        
        # 特殊角色可能有额外权限
        if role == "reviewer" or role == "admin":
            base_scopes.extend([
                "article:review",
                "article:approve",
                "article:reject"
            ])
        
        return base_scopes


class LegacyEnvironmentAuthProvider(BearerAuthProvider):
    """Legacy environment variable authentication provider
    
    Provides backward compatibility for single-agent setups using
    the AGENT_API_KEY environment variable.
    """
    
    def __init__(self, api_key: str, agent_id: str = "legacy-agent"):
        self.api_key = api_key
        self.agent_id = agent_id
        self.validator = AgentKeyValidator()
        
    async def validate_token(self, token: str) -> Optional[AccessToken]:
        """验证传统环境变量API密钥
        
        Args:
            token: API密钥令牌
            
        Returns:
            AccessToken: 如果验证成功返回访问令牌，否则返回None
        """
        if not self.validator.secure_compare(token, self.api_key):
            return None
        
        return AccessToken(
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