"""Simple test tools for debugging MCP issues."""

import json
from datetime import datetime, timezone
from sqlmodel import select
from fastmcp import FastMCP

from mcp_wordpress.core.database import get_session
from mcp_wordpress.models.article import Article


def register_test_tools(mcp: FastMCP):
    """Register simple test tools."""
    
    @mcp.tool()
    async def test_ping():
        """Simple ping test."""
        return {"status": "ok", "timestamp": datetime.now(timezone.utc).isoformat()}
    
    @mcp.tool()
    async def test_list_articles():
        """List all articles (simplified version)."""
        try:
            async with get_session() as session:
                query = select(Article).order_by(Article.updated_at.desc()).limit(10)
                result = await session.exec(query)
                articles = result.all()
                
                articles_data = []
                for article in articles:
                    articles_data.append({
                        "id": article.id,
                        "title": article.title,
                        "status": article.status,
                        "created_at": article.created_at.isoformat()
                    })
                
                return {
                    "status": "success",
                    "articles": articles_data,
                    "total": len(articles_data)
                }
                
        except Exception as e:
            return {
                "status": "error", 
                "message": str(e)
            }