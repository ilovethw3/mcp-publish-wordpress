"""MCP Resources for article data access."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlmodel import select
from fastmcp import FastMCP

from mcp_wordpress.core.database import get_session
from mcp_wordpress.models.article import Article, ArticleStatus


def register_article_resources(mcp: FastMCP):
    """Register all article-related resources with the MCP server."""
    
    @mcp.resource("article://pending")
    async def get_pending_articles() -> str:
        """Get list of articles pending review."""
        async with get_session() as session:
            query = select(Article).where(Article.status == ArticleStatus.PENDING_REVIEW)
            result = await session.execute(query)
            articles = result.scalars().all()
            
            articles_data = []
            for article in articles:
                articles_data.append({
                    "id": article.id,
                    "title": article.title,
                    "tags": article.tags,
                    "category": article.category,
                    "created_at": article.created_at.isoformat(),
                    "content_preview": article.content_markdown[:200] + "..." if len(article.content_markdown) > 200 else article.content_markdown
                })
            
            return json.dumps({
                "pending_articles": articles_data,
                "count": len(articles_data),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
    
    @mcp.resource("article://published")
    async def get_published_articles() -> str:
        """Get list of published articles."""
        async with get_session() as session:
            query = select(Article).where(Article.status == ArticleStatus.PUBLISHED)
            result = await session.execute(query)
            articles = result.scalars().all()
            
            articles_data = []
            for article in articles:
                articles_data.append({
                    "id": article.id,
                    "title": article.title,
                    "tags": article.tags,
                    "category": article.category,
                    "created_at": article.created_at.isoformat(),
                    "wordpress_post_id": article.wordpress_post_id,
                    "wordpress_permalink": article.wordpress_permalink
                })
            
            return json.dumps({
                "published_articles": articles_data,
                "count": len(articles_data),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
    
    @mcp.resource("article://failed")
    async def get_failed_articles() -> str:
        """Get list of articles that failed to publish."""
        async with get_session() as session:
            query = select(Article).where(Article.status == ArticleStatus.PUBLISH_FAILED)
            result = await session.execute(query)
            articles = result.scalars().all()
            
            articles_data = []
            for article in articles:
                articles_data.append({
                    "id": article.id,
                    "title": article.title,
                    "tags": article.tags,
                    "category": article.category,
                    "created_at": article.created_at.isoformat(),
                    "publish_error_message": article.publish_error_message,
                    "reviewer_notes": article.reviewer_notes
                })
            
            return json.dumps({
                "failed_articles": articles_data,
                "count": len(articles_data),
                "updated_at": datetime.now(timezone.utc).isoformat()
            })
    
    @mcp.resource("article://{article_id}")
    async def get_article_detail(article_id: str) -> str:
        """Get complete article data by ID."""
        try:
            article_id_int = int(article_id)
        except ValueError:
            return json.dumps({"error": "Invalid article ID format"})
        
        async with get_session() as session:
            result = await session.execute(select(Article).where(Article.id == article_id_int))
            article = result.scalars().first()
            
            if not article:
                return json.dumps({
                    "error": "Article not found",
                    "article_id": article_id_int
                })
            
            return json.dumps({
                "id": article.id,
                "title": article.title,
                "content_markdown": article.content_markdown,
                "content_html": article.content_html,
                "tags": article.tags,
                "category": article.category,
                "status": article.status,
                "created_at": article.created_at.isoformat(),
                "updated_at": article.updated_at.isoformat(),
                "reviewer_notes": article.reviewer_notes,
                "rejection_reason": article.rejection_reason,
                "wordpress_post_id": article.wordpress_post_id,
                "wordpress_permalink": article.wordpress_permalink,
                "publish_error_message": article.publish_error_message
            })