"""
Multi-site publishing engine for MCP WordPress Publisher v2.1

This module implements the core multi-site publishing functionality,
including site routing, connection pooling, and publish failure isolation.
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, Optional, Any
from dataclasses import dataclass
import aiohttp
import json

from mcp_wordpress.config.sites import SiteConfigManager, SiteConfigData
from mcp_wordpress.core.wordpress import WordPressClient
from mcp_wordpress.models.article import Article, ArticleStatus
from mcp_wordpress.core.database import get_session
from mcp_wordpress.core.errors import SiteNotFoundError, PublishingError


logger = logging.getLogger(__name__)


@dataclass
class PublishResult:
    """发布结果数据结构"""
    success: bool
    article_id: int
    target_site: str
    wp_post_id: Optional[int] = None
    wp_permalink: Optional[str] = None
    error: Optional[str] = None
    publish_time: Optional[datetime] = None


@dataclass
class ConnectionPoolStats:
    """连接池统计信息"""
    active_connections: int
    idle_connections: int
    total_requests: int
    failed_requests: int


class HealthMonitor:
    """站点健康监控器"""
    
    def __init__(self, site_id: str, check_interval: int = 60):
        self.site_id = site_id
        self.check_interval = check_interval
        self.is_running = False
        self._task: Optional[asyncio.Task] = None
        self.last_check: Optional[datetime] = None
        self.last_status = "unknown"
        
    async def start(self) -> None:
        """启动健康监控"""
        if self.is_running:
            return
            
        self.is_running = True
        self._task = asyncio.create_task(self._monitor_loop())
        logger.info(f"启动站点健康监控: {self.site_id}")
        
    async def stop(self) -> None:
        """停止健康监控"""
        if not self.is_running:
            return
            
        self.is_running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            
        logger.info(f"停止站点健康监控: {self.site_id}")
        
    async def check_health(self, site_config: SiteConfigData) -> str:
        """执行健康检查"""
        try:
            auth = aiohttp.BasicAuth(site_config.username, site_config.app_password)
            timeout = aiohttp.ClientTimeout(total=10)
            
            async with aiohttp.ClientSession(auth=auth, timeout=timeout) as session:
                async with session.get(f"{site_config.api_url}/users/me") as response:
                    if response.status == 200:
                        self.last_status = "healthy"
                    elif response.status == 401:
                        self.last_status = "auth_error"
                    else:
                        self.last_status = "error"
                        
        except asyncio.TimeoutError:
            self.last_status = "timeout"
        except Exception as e:
            logger.error(f"站点健康检查失败 {self.site_id}: {e}")
            self.last_status = "error"
            
        self.last_check = datetime.now(timezone.utc)
        return self.last_status
        
    async def _monitor_loop(self) -> None:
        """监控循环"""
        # 这里需要从配置管理器获取站点配置
        # 简化实现，实际使用时需要注入配置管理器
        while self.is_running:
            try:
                await asyncio.sleep(self.check_interval)
                # await self.check_health(site_config)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"健康监控循环错误 {self.site_id}: {e}")


class WordPressConnectionPool:
    """WordPress连接池管理器"""
    
    def __init__(self, site_config: SiteConfigData):
        self.site_id = site_config.id
        self.max_connections = site_config.connection_pool.max_connections
        self.idle_timeout = site_config.connection_pool.idle_timeout
        
        # 连接池统计
        self.stats = ConnectionPoolStats(
            active_connections=0,
            idle_connections=0,
            total_requests=0,
            failed_requests=0
        )
        
        # 使用aiohttp的连接器
        self.connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            limit_per_host=self.max_connections,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True
        )
        
        self.timeout = aiohttp.ClientTimeout(
            total=120,      # 总超时
            connect=30,     # 连接超时
            sock_read=60    # 读取超时
        )
        
        self.auth = aiohttp.BasicAuth(site_config.username, site_config.app_password)
        self.session: Optional[aiohttp.ClientSession] = None
        
    async def get_session(self) -> aiohttp.ClientSession:
        """获取HTTP会话"""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                connector=self.connector,
                timeout=self.timeout,
                auth=self.auth
            )
        return self.session
        
    async def cleanup(self) -> None:
        """清理连接池"""
        if self.session:
            await self.session.close()
        await self.connector.close()


class MultiSitePublisher:
    """多站点发布引擎
    
    负责管理多个WordPress站点的发布操作，包括站点路由、
    连接池管理和发布状态跟踪。
    """
    
    def __init__(self, site_config_manager: SiteConfigManager):
        self.site_config_manager = site_config_manager
        self.wp_clients: Dict[str, WordPressClient] = {}
        self.connection_pools: Dict[str, WordPressConnectionPool] = {}
        self.health_monitors: Dict[str, HealthMonitor] = {}
        self.is_initialized = False
        
    async def initialize(self) -> None:
        """初始化所有站点连接"""
        if self.is_initialized:
            return
            
        logger.info("初始化多站点发布引擎")
        
        sites = self.site_config_manager.get_all_sites()
        for site_config in sites:
            await self._setup_site(site_config)
            
        self.is_initialized = True
        logger.info(f"多站点发布引擎初始化完成，管理 {len(sites)} 个站点")
        
    async def cleanup(self) -> None:
        """清理所有连接和监控器"""
        logger.info("清理多站点发布引擎")
        
        # 停止健康监控
        for monitor in self.health_monitors.values():
            await monitor.stop()
            
        # 清理连接池
        for pool in self.connection_pools.values():
            await pool.cleanup()
            
        self.wp_clients.clear()
        self.connection_pools.clear()
        self.health_monitors.clear()
        self.is_initialized = False
        
    async def publish_article(
        self,
        article_id: int,
        target_site: str,
        agent_id: str
    ) -> PublishResult:
        """发布文章到指定站点
        
        Args:
            article_id: 文章ID
            target_site: 目标站点ID
            agent_id: 执行发布的代理ID
            
        Returns:
            PublishResult: 发布结果
        """
        if not self.is_initialized:
            await self.initialize()
            
        # 验证目标站点
        if target_site not in self.wp_clients:
            raise SiteNotFoundError(f"站点 '{target_site}' 未配置")
            
        # 获取文章数据
        async with get_session() as session:
            result = await session.execute(
                "SELECT * FROM articles WHERE id = :article_id",
                {"article_id": article_id}
            )
            article_data = result.first()
            
            if not article_data:
                raise PublishingError(f"文章不存在: {article_id}")
                
        try:
            # 更新文章状态为发布中
            await self._update_article_status(
                article_id, 
                ArticleStatus.PUBLISHING,
                target_site=target_site,
                publishing_agent=agent_id
            )
            
            # 执行WordPress发布
            wp_client = self.wp_clients[target_site]
            publish_result = await wp_client.create_post(
                title=article_data.title,
                content_markdown=article_data.content_markdown,
                tags=article_data.tags,
                category=article_data.category
            )
            
            # 更新发布成功状态
            await self._update_article_status(
                article_id,
                ArticleStatus.PUBLISHED,
                wp_post_id=publish_result.get("id"),
                wp_permalink=publish_result.get("link")
            )
            
            # 记录成功结果
            result = PublishResult(
                success=True,
                article_id=article_id,
                target_site=target_site,
                wp_post_id=publish_result.get("id"),
                wp_permalink=publish_result.get("link"),
                publish_time=datetime.now(timezone.utc)
            )
            
            logger.info(f"文章发布成功: {article_id} -> {target_site} (WP ID: {result.wp_post_id})")
            return result
            
        except Exception as e:
            # 更新发布失败状态
            await self._update_article_status(
                article_id,
                ArticleStatus.PUBLISH_FAILED,
                error_message=str(e)
            )
            
            # 记录失败结果
            result = PublishResult(
                success=False,
                article_id=article_id,
                target_site=target_site,
                error=str(e),
                publish_time=datetime.now(timezone.utc)
            )
            
            logger.error(f"文章发布失败: {article_id} -> {target_site}: {e}")
            return result
            
    async def get_site_health(self, site_id: str) -> Dict[str, Any]:
        """获取站点健康状态"""
        if site_id not in self.health_monitors:
            return {"status": "unknown", "message": "站点未配置"}
            
        monitor = self.health_monitors[site_id]
        pool = self.connection_pools.get(site_id)
        
        return {
            "site_id": site_id,
            "status": monitor.last_status,
            "last_check": monitor.last_check.isoformat() if monitor.last_check else None,
            "connection_pool": {
                "active_connections": pool.stats.active_connections if pool else 0,
                "idle_connections": pool.stats.idle_connections if pool else 0,
                "total_requests": pool.stats.total_requests if pool else 0,
                "failed_requests": pool.stats.failed_requests if pool else 0
            } if pool else None
        }
        
    async def _setup_site(self, site_config: SiteConfigData) -> None:
        """设置单个站点"""
        site_id = site_config.id
        
        # 创建WordPress客户端
        wp_client = WordPressClient(
            api_url=site_config.api_url,
            username=site_config.username,
            app_password=site_config.app_password
        )
        
        # 创建连接池
        connection_pool = WordPressConnectionPool(site_config)
        
        # 创建健康监控器
        health_monitor = HealthMonitor(
            site_id=site_id,
            check_interval=site_config.health_check_interval
        )
        
        self.wp_clients[site_id] = wp_client
        self.connection_pools[site_id] = connection_pool
        self.health_monitors[site_id] = health_monitor
        
        # 启动健康监控
        await health_monitor.start()
        
        logger.info(f"设置站点完成: {site_id} ({site_config.name})")
        
    async def _update_article_status(
        self,
        article_id: int,
        status: ArticleStatus,
        target_site: Optional[str] = None,
        publishing_agent: Optional[str] = None,
        wp_post_id: Optional[int] = None,
        wp_permalink: Optional[str] = None,
        error_message: Optional[str] = None
    ) -> None:
        """更新文章状态"""
        async with get_session() as session:
            update_data = {
                "status": status,
                "updated_at": datetime.now(timezone.utc)
            }
            
            if target_site:
                update_data["target_site_id"] = target_site
                # 获取站点名称
                site_config = self.site_config_manager.get_site(target_site)
                if site_config:
                    update_data["target_site_name"] = site_config.name
                    
            if publishing_agent:
                update_data["publishing_agent_id"] = publishing_agent
                
            if wp_post_id:
                update_data["wordpress_post_id"] = wp_post_id
                
            if wp_permalink:
                update_data["wordpress_permalink"] = wp_permalink
                
            if error_message:
                update_data["publish_error_message"] = error_message
                
            # 构建SQL更新语句
            set_clauses = [f"{key} = :{key}" for key in update_data.keys()]
            sql = f"UPDATE articles SET {', '.join(set_clauses)} WHERE id = :article_id"
            
            update_data["article_id"] = article_id
            await session.execute(sql, update_data)
            await session.commit()