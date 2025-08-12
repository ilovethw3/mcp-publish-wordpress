"""
Site configuration management for MCP WordPress Publisher v2.1

This module manages WordPress site configuration loading from YAML files,
hot-reloading, and environment variable fallback.
"""

import asyncio
import os
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import yaml
import aiohttp

from mcp_wordpress.core.errors import ConfigurationError


logger = logging.getLogger(__name__)


@dataclass
class ConnectionPoolConfig:
    """Connection pool configuration"""
    max_connections: int = 5
    idle_timeout: int = 300


@dataclass
class SiteConfigData:
    """Site configuration data structure"""
    id: str
    name: str
    api_url: str
    username: str
    app_password: str
    default_category: str = ""
    default_tags: str = ""
    connection_pool: ConnectionPoolConfig = None
    health_check_interval: int = 60
    
    def __post_init__(self):
        if self.connection_pool is None:
            self.connection_pool = ConnectionPoolConfig()


@dataclass
class GlobalPublishingSettings:
    """Global publishing settings"""
    default_status: str = "publish"
    max_concurrent_publishes: int = 5
    retry_attempts: int = 3
    retry_delay: int = 30
    timeout: int = 120


class SiteConfigFileWatcher(FileSystemEventHandler):
    """站点配置文件监控器"""
    
    def __init__(self, config_manager: 'SiteConfigManager'):
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
            logger.info(f"检测到站点配置文件变更: {event.src_path}")
            asyncio.create_task(self.config_manager.reload_config())


class SiteConfigManager:
    """站点配置管理器
    
    负责加载、验证和热重载WordPress站点配置文件
    """
    
    def __init__(self, config_path: str = "config/sites.yml"):
        self.config_path = Path(config_path)
        self.sites: Dict[str, SiteConfigData] = {}
        self.global_settings = GlobalPublishingSettings()
        self.file_watcher: Optional[Observer] = None
        self.last_loaded: Optional[datetime] = None
        
    async def load_config(self) -> None:
        """加载站点配置文件"""
        try:
            # 检查配置文件是否存在
            if not self.config_path.exists():
                await self._try_environment_fallback()
                return
                
            # 读取YAML配置文件
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                
            if not config_data:
                raise ConfigurationError("站点配置文件为空")
                
            # 清空现有配置
            self.sites.clear()
            
            # 加载全局发布设置
            if 'publishing' in config_data:
                self._load_global_settings(config_data['publishing'])
            
            # 加载站点配置
            sites_config = config_data.get('sites', [])
            if not sites_config:
                logger.warning("配置文件中未找到站点定义")
                return
                
            for site_data in sites_config:
                site_config = await self._validate_site_config(site_data)
                self.sites[site_config.id] = site_config
                
            self.last_loaded = datetime.now(timezone.utc)
            logger.info(f"成功加载 {len(self.sites)} 个站点配置")
            
        except yaml.YAMLError as e:
            error_msg = f"YAML站点配置文件解析失败: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
        except Exception as e:
            error_msg = f"站点配置文件加载失败: {e}"
            logger.error(error_msg)
            raise ConfigurationError(error_msg)
    
    async def reload_config(self) -> None:
        """重新加载配置文件"""
        try:
            old_site_count = len(self.sites)
            await self.load_config()
            new_site_count = len(self.sites)
            
            logger.info(f"站点配置重载完成: {old_site_count} -> {new_site_count} 个站点")
            
        except Exception as e:
            logger.error(f"站点配置重载失败: {e}")
            # 重载失败时保持现有配置
    
    async def start_hot_reload(self) -> None:
        """启动配置文件热重载监控"""
        if self.file_watcher:
            return
            
        self.file_watcher = Observer()
        event_handler = SiteConfigFileWatcher(self)
        
        # 监控配置文件目录
        watch_dir = self.config_path.parent
        self.file_watcher.schedule(event_handler, str(watch_dir), recursive=False)
        self.file_watcher.start()
        
        logger.info(f"启动站点配置文件热重载监控: {watch_dir}")
    
    def stop_hot_reload(self) -> None:
        """停止配置文件热重载监控"""
        if self.file_watcher:
            self.file_watcher.stop()
            self.file_watcher.join()
            self.file_watcher = None
            logger.info("站点配置文件热重载监控已停止")
    
    def get_site(self, site_id: str) -> Optional[SiteConfigData]:
        """获取站点配置"""
        return self.sites.get(site_id)
    
    def get_all_sites(self) -> List[SiteConfigData]:
        """获取所有站点配置"""
        return list(self.sites.values())
    
    def get_active_sites(self) -> List[SiteConfigData]:
        """获取活跃站点配置"""
        # 在实际实现中，可以从数据库检查站点状态
        # 这里简化为返回所有配置的站点
        return self.get_all_sites()
    
    async def validate_site_connection(self, site_id: str) -> bool:
        """验证站点连接"""
        site_config = self.get_site(site_id)
        if not site_config:
            return False
            
        try:
            # 测试WordPress REST API连接
            auth = aiohttp.BasicAuth(site_config.username, site_config.app_password)
            timeout = aiohttp.ClientTimeout(total=30)
            
            async with aiohttp.ClientSession(auth=auth, timeout=timeout) as session:
                # 测试API可达性
                async with session.get(f"{site_config.api_url}/users/me") as response:
                    return response.status == 200
                    
        except Exception as e:
            logger.error(f"站点连接测试失败 {site_id}: {e}")
            return False
    
    async def _try_environment_fallback(self) -> None:
        """尝试从环境变量回退配置"""
        wordpress_api_url = os.getenv('WORDPRESS_API_URL')
        wordpress_username = os.getenv('WORDPRESS_USERNAME')
        wordpress_app_password = os.getenv('WORDPRESS_APP_PASSWORD')
        
        if all([wordpress_api_url, wordpress_username, wordpress_app_password]):
            # 创建默认站点配置
            default_site = SiteConfigData(
                id="default-site",
                name="默认WordPress站点",
                api_url=wordpress_api_url,
                username=wordpress_username,
                app_password=wordpress_app_password,
                default_category=os.getenv('WORDPRESS_DEFAULT_CATEGORY', ''),
                connection_pool=ConnectionPoolConfig()
            )
            
            # 验证站点配置
            await self._validate_site_config(default_site.__dict__)
            self.sites[default_site.id] = default_site
            
            logger.info("使用环境变量创建默认站点配置")
        else:
            raise ConfigurationError(
                f"站点配置文件不存在: {self.config_path}，且环境变量配置不完整"
            )
    
    def _load_global_settings(self, settings_data: Dict[str, Any]) -> None:
        """加载全局发布设置"""
        self.global_settings = GlobalPublishingSettings(
            default_status=settings_data.get('default_status', 'publish'),
            max_concurrent_publishes=settings_data.get('max_concurrent_publishes', 5),
            retry_attempts=settings_data.get('retry_attempts', 3),
            retry_delay=settings_data.get('retry_delay', 30),
            timeout=settings_data.get('timeout', 120)
        )
    
    async def _validate_site_config(self, site_data: Dict[str, Any]) -> SiteConfigData:
        """验证站点配置"""
        # 检查必需字段
        required_fields = ['id', 'name', 'api_url', 'username', 'app_password']
        for field in required_fields:
            if field not in site_data or not site_data[field]:
                raise ConfigurationError(f"站点配置缺少必需字段: {field}")
        
        # 验证API URL格式
        api_url = site_data['api_url']
        if not api_url.startswith(('http://', 'https://')):
            raise ConfigurationError(f"站点 {site_data['id']} 的API URL格式无效: {api_url}")
        
        # 检查站点ID唯一性
        if site_data['id'] in self.sites:
            raise ConfigurationError(f"站点ID重复: {site_data['id']}")
        
        # 构建连接池配置
        connection_pool_data = site_data.get('connection_pool', {})
        connection_pool = ConnectionPoolConfig(
            max_connections=connection_pool_data.get('max_connections', 5),
            idle_timeout=connection_pool_data.get('idle_timeout', 300)
        )
        
        # 创建配置对象
        return SiteConfigData(
            id=site_data['id'],
            name=site_data['name'],
            api_url=api_url,
            username=site_data['username'],
            app_password=site_data['app_password'],
            default_category=site_data.get('default_category', ''),
            default_tags=site_data.get('default_tags', ''),
            connection_pool=connection_pool,
            health_check_interval=site_data.get('health_check_interval', 60)
        )