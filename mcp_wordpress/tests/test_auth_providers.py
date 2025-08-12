"""
Tests for authentication providers in MCP WordPress Publisher v2.1
"""

import pytest
from unittest.mock import AsyncMock, Mock
from datetime import datetime, timezone

from mcp_wordpress.auth.providers import MultiAgentAuthProvider, LegacyEnvironmentAuthProvider
from mcp_wordpress.config.agents import AgentConfigManager, AgentConfigData


class TestMultiAgentAuthProvider:
    """Tests for MultiAgentAuthProvider"""
    
    @pytest.fixture
    def mock_config_manager(self):
        """Mock agent configuration manager"""
        manager = Mock(spec=AgentConfigManager)
        manager.validate_api_key = Mock()
        manager.get_agent = Mock()
        return manager
    
    @pytest.fixture
    def auth_provider(self, mock_config_manager):
        """MultiAgentAuthProvider instance for testing"""
        return MultiAgentAuthProvider(mock_config_manager)
    
    @pytest.fixture
    def sample_agent_config(self):
        """Sample agent configuration"""
        return AgentConfigData(
            id="test-agent-001",
            name="测试AI写手",
            api_key="sk-test-key-12345678901234567890123456789012",
            description="用于测试的AI代理",
            role="content-creator",
            created_at=datetime.now(timezone.utc)
        )
    
    @pytest.mark.asyncio
    async def test_valid_token_authentication(self, auth_provider, mock_config_manager, sample_agent_config):
        """测试有效令牌认证"""
        # 设置mock返回值
        mock_config_manager.validate_api_key.return_value = "test-agent-001"
        mock_config_manager.get_agent.return_value = sample_agent_config
        
        # 执行认证
        access_token = await auth_provider.validate_token("valid-api-key")
        
        # 验证结果
        assert access_token is not None
        assert access_token.client_id == "test-agent-001"
        assert "article:submit" in access_token.scopes
        assert access_token.metadata["agent_name"] == "测试AI写手"
        assert access_token.metadata["role"] == "content-creator"
        
        # 验证调用
        mock_config_manager.validate_api_key.assert_called_once_with("valid-api-key")
        mock_config_manager.get_agent.assert_called_once_with("test-agent-001")
    
    @pytest.mark.asyncio
    async def test_invalid_token_authentication(self, auth_provider, mock_config_manager):
        """测试无效令牌认证"""
        # 设置mock返回值
        mock_config_manager.validate_api_key.return_value = None
        
        # 执行认证
        access_token = await auth_provider.validate_token("invalid-api-key")
        
        # 验证结果
        assert access_token is None
        
        # 验证调用
        mock_config_manager.validate_api_key.assert_called_once_with("invalid-api-key")
        mock_config_manager.get_agent.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_agent_not_found(self, auth_provider, mock_config_manager):
        """测试代理不存在的情况"""
        # 设置mock返回值
        mock_config_manager.validate_api_key.return_value = "nonexistent-agent"
        mock_config_manager.get_agent.return_value = None
        
        # 执行认证
        access_token = await auth_provider.validate_token("some-api-key")
        
        # 验证结果
        assert access_token is None
        
        # 验证调用
        mock_config_manager.validate_api_key.assert_called_once_with("some-api-key")
        mock_config_manager.get_agent.assert_called_once_with("nonexistent-agent")
    
    def test_get_agent_scopes_content_creator(self, auth_provider):
        """测试内容创作者角色的权限范围"""
        scopes = auth_provider._get_agent_scopes("content-creator")
        
        expected_scopes = [
            "article:submit",
            "article:read",
            "article:list",
            "agent:read",
            "site:read"
        ]
        
        assert all(scope in scopes for scope in expected_scopes)
        assert "article:review" not in scopes
    
    def test_get_agent_scopes_reviewer(self, auth_provider):
        """测试审核者角色的权限范围"""
        scopes = auth_provider._get_agent_scopes("reviewer")
        
        expected_scopes = [
            "article:submit",
            "article:read",
            "article:list",
            "agent:read",
            "site:read",
            "article:review",
            "article:approve",
            "article:reject"
        ]
        
        assert all(scope in scopes for scope in expected_scopes)
    
    @pytest.mark.asyncio
    async def test_authentication_exception_handling(self, auth_provider, mock_config_manager):
        """测试认证过程中异常处理"""
        # 设置mock抛出异常
        mock_config_manager.validate_api_key.side_effect = Exception("数据库连接失败")
        
        # 执行认证
        access_token = await auth_provider.validate_token("test-key")
        
        # 验证结果
        assert access_token is None


class TestLegacyEnvironmentAuthProvider:
    """Tests for LegacyEnvironmentAuthProvider"""
    
    @pytest.fixture
    def auth_provider(self):
        """LegacyEnvironmentAuthProvider instance for testing"""
        return LegacyEnvironmentAuthProvider(
            api_key="legacy-api-key-12345678901234567890",
            agent_id="legacy-agent"
        )
    
    @pytest.mark.asyncio
    async def test_valid_legacy_token(self, auth_provider):
        """测试有效的传统令牌"""
        access_token = await auth_provider.validate_token("legacy-api-key-12345678901234567890")
        
        assert access_token is not None
        assert access_token.client_id == "legacy-agent"
        assert "article:submit" in access_token.scopes
        assert "article:review" in access_token.scopes  # 传统代理具有所有权限
        assert access_token.metadata["role"] == "legacy"
    
    @pytest.mark.asyncio
    async def test_invalid_legacy_token(self, auth_provider):
        """测试无效的传统令牌"""
        access_token = await auth_provider.validate_token("wrong-api-key")
        
        assert access_token is None
    
    @pytest.mark.asyncio
    async def test_empty_token(self, auth_provider):
        """测试空令牌"""
        access_token = await auth_provider.validate_token("")
        
        assert access_token is None