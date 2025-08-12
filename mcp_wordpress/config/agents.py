"""
Agent configuration management for MCP WordPress Publisher v2.1

This module manages agent configuration loading from YAML files,
hot-reloading, and environment variable fallback.
"""

import asyncio
import os
import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import yaml

from mcp_wordpress.core.errors import ConfigurationError
from mcp_wordpress.models.agent import Agent
from mcp_wordpress.auth.validators import AgentKeyValidator


logger = logging.getLogger(__name__)


@dataclass
class AgentConfigData:
    """Agent configuration data structure"""
    id: str
    name: str
    api_key: str
    description: str = ""
    role: str = "content-creator"
    created_at: Optional[datetime] = None


@dataclass
class GlobalAgentSettings:
    """Global agent settings"""
    max_concurrent_agents: int = 10
    session_timeout: int = 1800  # 30分钟
    key_rotation_enabled: bool = False
    audit_log_level: str = "info"


class ConfigFileWatcher(FileSystemEventHandler):
    """文件系统监控器用于配置热重载"""
    
    def __init__(self, config_manager: 'AgentConfigManager'):
        self.config_manager = config_manager
        self.last_modified = 0
        
    def on_modified(self, event):
        """文件修改事件处理"""
        if event.is_directory:
            return
            
        # 防止重复触发
        current_time = datetime.now().timestamp()
        if current_time - self.last_modified < 1.0:
            return
        self.last_modified = current_time
        
        if event.src_path == str(self.config_manager.config_path):
            logger.info(f"Detected config file change: {event.src_path}")
            asyncio.create_task(self.config_manager.reload_config())


class AgentConfigManager:
    """代理配置管理器
    
    负责加载、验证和热重载代理配置文件
    """
    
    def __init__(self, config_path: str = "config/agents.yml"):
        self.config_path = Path(config_path)
        self.agents: Dict[str, AgentConfigData] = {}
        self.global_settings = GlobalAgentSettings()
        self.validator = AgentKeyValidator()
        self.file_watcher: Optional[Observer] = None
        self.last_loaded: Optional[datetime] = None
        
    async def load_config(self) -> None:
        """加载代理配置文件"""
        try:
            # 检查配置文件是否存在
            if not self.config_path.exists():
                await self._try_environment_fallback()
                return
                
            # 读取YAML配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                
            if not config_data:
                raise ConfigurationError("配置文件为空")
                
            # 清空现有配置
            self.agents.clear()
            
            # 加载全局设置
            if 'global_settings' in config_data:
                self._load_global_settings(config_data['global_settings'])
            
            # 加载代理配置
            agents_config = config_data.get('agents', [])
            if not agents_config:
                logger.warning("配置文件中未找到代理定义")
                return
                
            for agent_data in agents_config:
                agent_config = await self._validate_agent_config(agent_data)
                self.agents[agent_config.id] = agent_config
                
            self.last_loaded = datetime.now(timezone.utc)
            logger.info(f"成功加载 {len(self.agents)} 个代理配置")
            
        except yaml.YAMLError as e:
            error_msg = f"YAML配置文件解析失败: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        except Exception as e:
            error_msg = f"配置文件加载失败: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
    
    async def reload_config(self) -> None:
        """重新加载配置文件"""
        try:
            old_agent_count = len(self.agents)
            await self.load_config()
            new_agent_count = len(self.agents)
            
            logger.info(f"配置重载完成: {old_agent_count} -> {new_agent_count} 个代理")
            
        except Exception as e:
            logger.error(f"配置重载失败: {e}")
            # 重载失败时保持现有配置
    
    async def start_hot_reload(self) -> None:
        """启动配置文件热重载监控"""
        if self.file_watcher:
            return
            
        self.file_watcher = Observer()
        event_handler = ConfigFileWatcher(self)
        
        # 监控配置文件目录
        watch_dir = self.config_path.parent
        self.file_watcher.schedule(event_handler, str(watch_dir), recursive=False)
        self.file_watcher.start()
        
        logger.info(f"启动配置文件热重载监控: {watch_dir}")
    
    def stop_hot_reload(self) -> None:
        """停止配置文件热重载监控"""
        if self.file_watcher:
            self.file_watcher.stop()
            self.file_watcher.join()
            self.file_watcher = None
            logger.info("配置文件热重载监控已停止")
    
    def get_agent(self, agent_id: str) -> Optional[AgentConfigData]:
        """获取代理配置"""
        return self.agents.get(agent_id)
    
    def get_all_agents(self) -> List[AgentConfigData]:
        """获取所有代理配置"""
        return list(self.agents.values())
    
    def validate_api_key(self, api_key: str) -> Optional[str]:
        """验证API密钥并返回代理ID"""
        for agent_id, agent_config in self.agents.items():
            if self.validator.secure_compare(api_key, agent_config.api_key):
                return agent_id
        return None
    
    async def _try_environment_fallback(self) -> None:
        """尝试从环境变量回退配置"""
        agent_api_key = os.getenv('AGENT_API_KEY')
        if agent_api_key:
            # 创建默认代理配置
            default_agent = AgentConfigData(
                id="default-agent",
                name="默认代理",
                api_key=agent_api_key,
                description="从环境变量创建的默认代理",
                role="content-creator",
                created_at=datetime.now(timezone.utc)
            )
            
            # 验证密钥强度
            await self._validate_agent_config(default_agent.__dict__)
            self.agents[default_agent.id] = default_agent
            
            logger.info("使用环境变量AGENT_API_KEY创建默认代理配置")
        else:
            raise ConfigurationError(
                f"配置文件不存在: {self.config_path}，且未设置环境变量AGENT_API_KEY"
            )
    
    def _load_global_settings(self, settings_data: Dict[str, Any]) -> None:
        """加载全局设置"""
        self.global_settings = GlobalAgentSettings(
            max_concurrent_agents=settings_data.get('max_concurrent_agents', 10),
            session_timeout=settings_data.get('session_timeout', 1800),
            key_rotation_enabled=settings_data.get('key_rotation_enabled', False),
            audit_log_level=settings_data.get('audit_log_level', 'info')
        )
    
    async def _validate_agent_config(self, agent_data: Dict[str, Any]) -> AgentConfigData:
        """验证代理配置"""
        # 检查必需字段
        required_fields = ['id', 'name', 'api_key']
        for field in required_fields:
            if field not in agent_data or not agent_data[field]:
                raise ConfigurationError(f"代理配置缺少必需字段: {field}")
        
        # 验证API密钥强度
        api_key = agent_data['api_key']
        key_validation = self.validator.validate_key_format(api_key)
        if not key_validation['valid']:
            issues = ', '.join(key_validation['issues'])
            raise ConfigurationError(f"代理 {agent_data['id']} 的API密钥不符合要求: {issues}")
        
        # 检查密钥唯一性
        for existing_agent in self.agents.values():
            if existing_agent.api_key == api_key:
                raise ConfigurationError(
                    f"代理 {agent_data['id']} 的API密钥与 {existing_agent.id} 重复"
                )
        
        # 创建配置对象
        return AgentConfigData(
            id=agent_data['id'],
            name=agent_data['name'],
            api_key=api_key,
            description=agent_data.get('description', ''),
            role=agent_data.get('role', 'content-creator'),
            created_at=datetime.fromisoformat(agent_data['created_at']) 
                      if 'created_at' in agent_data 
                      else datetime.now(timezone.utc)
        )