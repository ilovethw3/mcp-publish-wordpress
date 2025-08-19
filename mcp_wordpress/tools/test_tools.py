"""Simple test tools for debugging MCP issues."""

from datetime import datetime, timezone
from fastmcp import FastMCP


def register_test_tools(mcp: FastMCP):
    """Register simple test tools."""
    
    @mcp.tool()
    async def test_ping():
        """Simple ping test."""
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
    
