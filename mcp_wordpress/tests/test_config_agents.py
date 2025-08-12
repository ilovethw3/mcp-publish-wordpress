"""
Tests for agent configuration management in MCP WordPress Publisher v2.1
"""

import pytest
import tempfile
import os
from pathlib import Path
from unittest.mock import Mock, patch
from datetime import datetime, timezone
import yaml

from mcp_wordpress.config.agents import AgentConfigManager, AgentConfigData, GlobalAgentSettings
from mcp_wordpress.core.errors import ConfigurationError


class TestAgentConfigManager:
    """Tests for AgentConfigManager"""
    
    @pytest.fixture
    def sample_config_data(self):
        """Sample configuration data"""
        return {
            'agents': [
                {
                    'id': 'ai-writer-001',
                    'name': 'AI内容创作专家',
                    'api_key': 'sk-aw-8f9e7d6c5b4a3210fedcba0987654321',
                    'description': '专注于技术文章写作的AI代理',
                    'role': 'content-creator',
                    'created_at': '2024-01-15T08:00:00Z'
                },
                {
                    'id': 'seo-optimizer-002',
                    'name': 'SEO优化专家',
                    'api_key': 'sk-so-1a2b3c4d5e6f789012345678901234567890',
                    'description': '负责SEO关键词优化和内容结构调整',
                    'role': 'seo-optimizer',
                    'created_at': '2024-01-16T09:30:00Z'
                }
            ],
            'global_settings': {
                'max_concurrent_agents': 10,
                'session_timeout': 1800,
                'key_rotation_enabled': False,
                'audit_log_level': 'info'
            }
        }
    
    @pytest.fixture
    def temp_config_file(self, sample_config_data):
        """Create temporary config file"""
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
        yaml.dump(sample_config_data, temp_file, default_flow_style=False, allow_unicode=True)
        temp_file.close()
        
        yield temp_file.name
        
        # Cleanup
        os.unlink(temp_file.name)
    
    @pytest.fixture
    def config_manager(self, temp_config_file):
        """AgentConfigManager instance for testing"""
        return AgentConfigManager(temp_config_file)
    
    @pytest.mark.asyncio
    async def test_load_config_success(self, config_manager, sample_config_data):
        """测试成功加载配置"""
        await config_manager.load_config()
        
        assert len(config_manager.agents) == 2
        assert 'ai-writer-001' in config_manager.agents
        assert 'seo-optimizer-002' in config_manager.agents
        
        # 检查第一个代理配置
        agent1 = config_manager.agents['ai-writer-001']
        assert agent1.name == 'AI内容创作专家'
        assert agent1.role == 'content-creator'
        assert agent1.api_key == 'sk-aw-8f9e7d6c5b4a3210fedcba0987654321'
        
        # 检查全局设置
        assert config_manager.global_settings.max_concurrent_agents == 10
        assert config_manager.global_settings.session_timeout == 1800
        assert config_manager.last_loaded is not None
    
    @pytest.mark.asyncio
    async def test_load_config_file_not_found(self):
        """测试配置文件不存在的情况"""
        config_manager = AgentConfigManager("nonexistent.yml")
        
        # 不设置环境变量，应该抛出异常
        with pytest.raises(ConfigurationError) as exc_info:
            await config_manager.load_config()
        assert "配置文件不存在" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_load_config_environment_fallback(self):
        """测试环境变量回退"""
        config_manager = AgentConfigManager("nonexistent.yml")
        
        with patch.dict('os.environ', {'AGENT_API_KEY': 'env-api-key-123456789012345678901234567890'}):
            await config_manager.load_config()
            
            assert len(config_manager.agents) == 1
            assert 'default-agent' in config_manager.agents
            
            default_agent = config_manager.agents['default-agent']
            assert default_agent.name == '默认代理'
            assert default_agent.api_key == 'env-api-key-123456789012345678901234567890'
    
    @pytest.mark.asyncio
    async def test_load_config_invalid_yaml(self):
        """测试无效YAML配置"""
        # 创建无效YAML文件
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
        temp_file.write("invalid: yaml: content: [unclosed")
        temp_file.close()
        
        config_manager = AgentConfigManager(temp_file.name)
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                await config_manager.load_config()
            assert "YAML配置文件解析失败" in str(exc_info.value)
        finally:
            os.unlink(temp_file.name)
    
    @pytest.mark.asyncio
    async def test_validate_agent_config_missing_fields(self, config_manager):
        """测试缺少必需字段的代理配置"""
        invalid_agent = {'name': '测试代理'}  # 缺少id和api_key
        
        with pytest.raises(ConfigurationError) as exc_info:
            await config_manager._validate_agent_config(invalid_agent)
        assert "缺少必需字段" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_validate_agent_config_weak_key(self, config_manager):
        """测试弱API密钥"""
        weak_key_agent = {
            'id': 'test-agent',
            'name': '测试代理', 
            'api_key': 'weak_key'  # 太短且熵值低
        }
        
        with pytest.raises(ConfigurationError) as exc_info:
            await config_manager._validate_agent_config(weak_key_agent)
        assert "API密钥不符合要求" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_validate_api_key(self, config_manager):
        """测试API密钥验证"""
        await config_manager.load_config()
        
        # 有效密钥
        valid_agent_id = config_manager.validate_api_key('sk-aw-8f9e7d6c5b4a3210fedcba0987654321')
        assert valid_agent_id == 'ai-writer-001'
        
        # 无效密钥
        invalid_agent_id = config_manager.validate_api_key('invalid-key')
        assert invalid_agent_id is None
    
    def test_get_agent(self, config_manager):
        """测试获取代理配置"""
        # 先手动添加一个代理用于测试
        agent_config = AgentConfigData(
            id='test-agent',
            name='测试代理',
            api_key='test-key',
            role='content-creator'
        )
        config_manager.agents['test-agent'] = agent_config
        
        # 存在的代理
        result = config_manager.get_agent('test-agent')
        assert result is not None
        assert result.id == 'test-agent'
        
        # 不存在的代理
        result = config_manager.get_agent('nonexistent')
        assert result is None
    
    def test_get_all_agents(self, config_manager):
        """测试获取所有代理配置"""
        # 先手动添加代理用于测试
        agent1 = AgentConfigData(id='agent1', name='代理1', api_key='key1', role='creator')
        agent2 = AgentConfigData(id='agent2', name='代理2', api_key='key2', role='optimizer')
        
        config_manager.agents['agent1'] = agent1
        config_manager.agents['agent2'] = agent2
        
        all_agents = config_manager.get_all_agents()
        assert len(all_agents) == 2
        assert agent1 in all_agents
        assert agent2 in all_agents
    
    @pytest.mark.asyncio
    async def test_duplicate_api_keys(self):
        """测试重复API密钥检测"""
        duplicate_config = {
            'agents': [
                {
                    'id': 'agent1',
                    'name': '代理1',
                    'api_key': 'sk-same-key-12345678901234567890123456789012'
                },
                {
                    'id': 'agent2', 
                    'name': '代理2',
                    'api_key': 'sk-same-key-12345678901234567890123456789012'  # 重复密钥
                }
            ]
        }
        
        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yml', delete=False)
        yaml.dump(duplicate_config, temp_file, default_flow_style=False, allow_unicode=True)
        temp_file.close()
        
        config_manager = AgentConfigManager(temp_file.name)
        
        try:
            with pytest.raises(ConfigurationError) as exc_info:
                await config_manager.load_config()
            assert "API密钥" in str(exc_info.value) and "重复" in str(exc_info.value)
        finally:
            os.unlink(temp_file.name)
    
    @pytest.mark.asyncio
    async def test_reload_config(self, config_manager, temp_config_file):
        """测试配置重载"""
        # 初始加载
        await config_manager.load_config()
        initial_count = len(config_manager.agents)
        
        # 修改配置文件添加新代理
        new_config = {
            'agents': [
                {
                    'id': 'new-agent-003',
                    'name': '新增代理',
                    'api_key': 'sk-new-1234567890123456789012345678901234',
                    'role': 'editor'
                }
            ]
        }
        
        with open(temp_config_file, 'w', encoding='utf-8') as f:
            yaml.dump(new_config, f, default_flow_style=False, allow_unicode=True)
        
        # 重新加载配置
        await config_manager.reload_config()
        
        assert len(config_manager.agents) != initial_count
        assert 'new-agent-003' in config_manager.agents