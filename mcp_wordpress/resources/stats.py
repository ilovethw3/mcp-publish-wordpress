"""MCP Resources for system statistics and WordPress configuration."""

import json
from datetime import datetime, timezone, timedelta
from sqlmodel import select, func
from fastmcp import FastMCP

from mcp_wordpress.core.database import get_session
from mcp_wordpress.core.wordpress import WordPressClient
from mcp_wordpress.core.config import settings
from mcp_wordpress.models.article import Article, ArticleStatus


def register_stats_resources(mcp: FastMCP):
    """Register all statistics and configuration resources with the MCP server."""
    
    @mcp.resource("wordpress://config")
    async def get_wordpress_config() -> str:
        """Get WordPress site configuration information."""
        wp_client = WordPressClient()
        
        try:
            # Test connection
            is_connected = await wp_client.test_connection()
            
            return json.dumps({
                "api_base": "/".join(settings.wordpress_api_url.split("/")[:-2]),  # 只暴露主域名
                "connection_status": "connected" if is_connected else "disconnected",
                "last_checked": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            return json.dumps({
                "api_base": "/".join(settings.wordpress_api_url.split("/")[:-2]),  # 只暴露主域名
                "connection_status": "error",
                "error_message": "Connection failed",  # 不暴露具体错误信息
                "last_checked": datetime.now(timezone.utc).isoformat()
            })
    
    @mcp.resource("stats://summary")
    async def get_stats_summary() -> str:
        """Get system statistics summary."""
        async with get_session() as session:
            # Count articles by status
            stats = {}
            for status in ArticleStatus:
                result = await session.execute(
                    select(func.count(Article.id)).where(Article.status == status)
                )
                stats[status.value] = result.scalar() or 0
            
            # Get total count
            total_result = await session.execute(select(func.count(Article.id)))
            total_count = total_result.scalar() or 0
            
            # Get recent activity (last 24 hours)
            yesterday = datetime.now(timezone.utc) - timedelta(days=1)
            recent_result = await session.execute(
                select(func.count(Article.id)).where(Article.created_at >= yesterday)
            )
            recent_count = recent_result.scalar() or 0
            
            return json.dumps({
                "total_articles": total_count,
                "articles_by_status": stats,
                "recent_submissions_24h": recent_count,
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
    
    @mcp.resource("stats://performance")
    async def get_performance_metrics() -> str:
        """Get system performance metrics."""
        async with get_session() as session:
            # Calculate average processing time for published articles
            published_articles = await session.execute(
                select(Article).where(Article.status == ArticleStatus.PUBLISHED)
            )
            articles = published_articles.scalars().all()
            
            if articles:
                processing_times = []
                for article in articles:
                    if article.created_at and article.updated_at:
                        processing_time = (article.updated_at - article.created_at).total_seconds()
                        processing_times.append(processing_time)
                
                avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
            else:
                avg_processing_time = 0
            
            # Calculate success rate
            total_attempted = await session.execute(
                select(func.count(Article.id)).where(
                    Article.status.in_([
                        ArticleStatus.PUBLISHED, 
                        ArticleStatus.PUBLISH_FAILED
                    ])
                )
            )
            total_attempted_count = total_attempted.scalar() or 0
            
            published_count = await session.execute(
                select(func.count(Article.id)).where(Article.status == ArticleStatus.PUBLISHED)
            )
            published_count_result = published_count.scalar() or 0
            
            success_rate = (published_count_result / total_attempted_count * 100) if total_attempted_count > 0 else 0
            
            return json.dumps({
                "avg_processing_time_seconds": round(avg_processing_time, 2),
                "success_rate_percent": round(success_rate, 2),
                "total_attempted_publications": total_attempted_count,
                "successful_publications": published_count_result,
                "last_calculated": datetime.now(timezone.utc).isoformat()
            })