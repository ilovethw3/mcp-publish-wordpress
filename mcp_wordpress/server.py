"""Main MCP WordPress server implementation."""

import asyncio
import sys
import logging
from datetime import datetime, timezone
from fastmcp import FastMCP
from starlette.requests import Request
from starlette.responses import JSONResponse
from sqlalchemy.sql import text

from mcp_wordpress.core.config import settings
from mcp_wordpress.core.database import create_db_and_tables, get_session
from mcp_wordpress.tools.articles import register_article_tools
from mcp_wordpress.tools.test_tools import register_test_tools
# Security tools moved to Web UI
from mcp_wordpress.resources.articles import register_article_resources
from mcp_wordpress.resources.stats import register_stats_resources
from mcp_wordpress.prompts.templates import register_content_prompts
from mcp_wordpress.core.security import SecurityManager
from mcp_wordpress.auth.middleware import AuthenticationMiddleware
from mcp_wordpress.auth.providers import MultiAgentAuthProvider, LegacyEnvironmentAuthProvider
from mcp_wordpress.core.errors import ConfigurationError
# Configuration API moved to Web UI


logger = logging.getLogger(__name__)


async def _create_auth_provider():
    """创建适当的认证提供者
    
    根据配置选择最合适的认证策略：
    1. 数据库中有代理配置 -> 使用 MultiAgentAuthProvider
    2. 环境变量AGENT_API_KEY存在 -> 使用LegacyEnvironmentAuthProvider
    3. 都不存在 -> 抛出配置错误
    
    Returns:
        认证提供者实例
    
    Raises:
        ConfigurationError: 当没有配置任何认证方式时
    """
    print("🔐 DEBUG: _create_auth_provider() 被调用")
    try:
        logger.info("开始创建认证提供者...")
        print("🔐 DEBUG: 开始创建认证提供者...")
        
        # 策略1: 开发模式检查 - 最高优先级
        if settings.development_mode:
            logger.warning("⚠️  开发模式：完全禁用认证（不推荐用于生产环境）")
            return None
        
        # 导入配置服务
        from mcp_wordpress.services.config_service import config_service
        
        # 策略2: 尝试使用数据库中的代理配置
        try:
            agents = await config_service.get_all_agents(active_only=True)
            print(f"🔐 DEBUG: 数据库中的活跃代理数量: {len(agents)}")
            logger.info(f"数据库中的活跃代理数量: {len(agents)}")
            
            if len(agents) > 0:
                logger.info("正在创建多代理认证提供者...")
                # 使用数据库认证提供者
                auth_provider = MultiAgentAuthProvider()
                logger.info("使用数据库多代理认证提供者 (支持Bearer Token)")
                return auth_provider
            else:
                logger.warning("数据库中没有找到活跃的代理")
        except Exception as e:
            logger.warning(f"数据库代理查询失败: {e}")
            import traceback
            logger.warning(f"错误详情: {traceback.format_exc()}")
        
        # 策略3: 回退到传统环境变量认证
        legacy_api_key = getattr(settings, 'agent_api_key', None)
        if legacy_api_key:
            auth_provider = LegacyEnvironmentAuthProvider(
                api_key=legacy_api_key,
                agent_id="legacy-agent"
            )
            logger.info("使用传统环境变量认证提供者")
            return auth_provider
        
        # 策略4: 生产环境安全策略 - 必须有认证配置
        logger.error(
            "❌ 生产环境安全要求：必须配置认证方式。\n"
            "请选择以下选项之一：\n"
            "1. 通过Web UI添加代理配置\n" 
            "2. 设置 AGENT_API_KEY 环境变量\n"
            "3. 启用开发模式 (DEVELOPMENT_MODE=true)"
        )
        raise ConfigurationError(
            "生产环境安全策略：未配置任何认证方式。MCP服务器拒绝启动以防止未授权访问。"
        )
        
    except ConfigurationError:
        raise
    except Exception as e:
        raise ConfigurationError(f"认证提供者初始化失败: {e}")


async def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server instance."""
    
    # Initialize authentication provider
    auth_provider = await _create_auth_provider()
    
    # Initialize FastMCP server with authentication
    mcp = FastMCP(
        name=settings.mcp_server_name,
        version="2.1.0",
        auth=auth_provider
    )
    
    # Add health check endpoint
    @mcp.custom_route("/health", methods=["GET"])
    async def health_check(request: Request) -> JSONResponse:
        """System health check endpoint for Docker and monitoring."""
        health_data = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "server": {
                "name": settings.mcp_server_name,
                "version": "2.1.0",
                "transport": "sse"
            },
            "components": {}
        }
        
        # Check database connection
        try:
            async with get_session() as session:
                await session.execute(text("SELECT 1"))
            health_data["components"]["database"] = {"status": "healthy"}
        except Exception as e:
            health_data["components"]["database"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
            health_data["status"] = "unhealthy"
        
        # Check Redis connection (if configured)
        try:
            import redis.asyncio as redis
            redis_client = redis.from_url(settings.redis_url)
            await redis_client.ping()
            health_data["components"]["redis"] = {"status": "healthy"}
            await redis_client.close()
        except Exception as e:
            health_data["components"]["redis"] = {
                "status": "unhealthy", 
                "error": str(e)
            }
            # Redis is not critical, so don't mark overall status as unhealthy
        
        # Return appropriate status code
        status_code = 200 if health_data["status"] == "healthy" else 503
        return JSONResponse(health_data, status_code=status_code)
    
    # Add readiness check endpoint
    @mcp.custom_route("/health/ready", methods=["GET"])
    async def readiness_check(request: Request) -> JSONResponse:
        """Readiness check for Kubernetes-style deployments."""
        try:
            # Check if database is accessible
            async with get_session() as session:
                await session.execute(text("SELECT 1"))
            
            return JSONResponse({
                "status": "ready",
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            return JSONResponse({
                "status": "not_ready",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }, status_code=503)
    
    # Add liveness check endpoint
    @mcp.custom_route("/health/live", methods=["GET"])
    async def liveness_check(request: Request) -> JSONResponse:
        """Liveness check - server is running."""
        return JSONResponse({
            "status": "alive",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
    
    # Register all functionality modules
    register_test_tools(mcp)  # Add test tools first for debugging
    register_article_tools(mcp)
    # Security monitoring tools moved to Web UI for management interface
    register_article_resources(mcp)
    register_stats_resources(mcp)
    register_content_prompts(mcp)
    
    # Configuration management moved to Web UI for proper separation of concerns
    
    # Configure v2.1 authentication and security
    # 只有在非开发模式下才添加认证中间件
    if not settings.development_mode:
        auth_middleware = AuthenticationMiddleware()
        mcp.add_middleware(auth_middleware)
        logger.info("✅ 认证中间件已启用")
    else:
        logger.warning("⚠️  开发模式：跳过认证中间件")
    
    return mcp


async def main():
    """Main server entry point."""
    
    # Create MCP server first
    mcp = await create_mcp_server()
    
    # Create database tables if they don't exist (after MCP initialization)
    create_db_and_tables()
    
    # Initialize security manager for v2.1
    security_manager = SecurityManager.get_instance()
    await security_manager.initialize()
    
    try:
        # Determine transport method
        transport = settings.mcp_transport
        if len(sys.argv) > 1:
            if sys.argv[1] in ["stdio", "sse"]:
                transport = sys.argv[1]
        
        # Run server with specified transport
        if transport == "stdio":
            await mcp.run_stdio_async()
        elif transport == "sse":
            # Use SSE async method for SSE transport with custom path
            await mcp.run_sse_async(
                host="0.0.0.0", 
                port=settings.mcp_port,
                path=settings.mcp_sse_path
            )
        else:
            raise ValueError(f"Unsupported transport method: {transport}")
    finally:
        # Cleanup security manager on shutdown
        await security_manager.cleanup()


if __name__ == "__main__":
    asyncio.run(main())