"""Main MCP WordPress server implementation."""

import asyncio
import sys
from fastmcp import FastMCP

from mcp_wordpress.core.config import settings
from mcp_wordpress.core.database import create_db_and_tables
from mcp_wordpress.tools.articles import register_article_tools
from mcp_wordpress.tools.test_tools import register_test_tools
from mcp_wordpress.resources.articles import register_article_resources
from mcp_wordpress.resources.stats import register_stats_resources
from mcp_wordpress.prompts.templates import register_content_prompts


def create_mcp_server() -> FastMCP:
    """Create and configure the MCP server instance."""
    
    # Initialize FastMCP server
    mcp = FastMCP(
        name=settings.mcp_server_name,
        version="2.0.0"
    )
    
    # Register all functionality modules
    register_test_tools(mcp)  # Add test tools first for debugging
    register_article_tools(mcp)
    register_article_resources(mcp)
    register_stats_resources(mcp)
    register_content_prompts(mcp)
    
    return mcp


async def main():
    """Main server entry point."""
    
    # Create MCP server first
    mcp = create_mcp_server()
    
    # Create database tables if they don't exist (after MCP initialization)
    create_db_and_tables()
    
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


if __name__ == "__main__":
    asyncio.run(main())