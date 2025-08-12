"""Main MCP WordPress server implementation."""

import asyncio
import sys
from fastmcp import FastMCP

from mcp_wordpress.core.config import settings
from mcp_wordpress.core.database import create_db_and_tables
from mcp_wordpress.tools.articles import register_article_tools
from mcp_wordpress.tools.test_tools import register_test_tools
from mcp_wordpress.tools.security import register_security_tools
from mcp_wordpress.resources.articles import register_article_resources
from mcp_wordpress.resources.stats import register_stats_resources
from mcp_wordpress.prompts.templates import register_content_prompts
from mcp_wordpress.core.security import SecurityManager
from mcp_wordpress.auth.middleware import AuthenticationMiddleware


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server instance."""
    
    # Initialize FastMCP server
    mcp = FastMCP(
        name=settings.mcp_server_name,
        version="2.1.0"
    )
    
    # Register all functionality modules
    register_test_tools(mcp)  # Add test tools first for debugging
    register_article_tools(mcp)
    register_security_tools(mcp)  # Security management tools
    register_article_resources(mcp)
    register_stats_resources(mcp)
    register_content_prompts(mcp)
    
    # Configure v2.1 authentication and security
    auth_middleware = AuthenticationMiddleware()
    mcp.add_middleware(auth_middleware)
    
    return mcp


async def main():
    """Main server entry point."""
    
    # Create MCP server first
    mcp = create_mcp_server()
    
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