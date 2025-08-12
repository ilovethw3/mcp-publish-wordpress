"""MCP Resources for article data access."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlmodel import select, func
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
                    "content_preview": article.content_markdown[:200] + "..." if len(article.content_markdown) > 200 else article.content_markdown,
                    # v2.1新增字段
                    "submitting_agent": {
                        "id": article.submitting_agent_id,
                        "name": article.submitting_agent_name
                    } if article.submitting_agent_id else None,
                    "target_site": {
                        "id": article.target_site_id,
                        "name": article.target_site_name
                    } if article.target_site_id else None
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
                    "wordpress_permalink": article.wordpress_permalink,
                    # v2.1新增字段
                    "submitting_agent": {
                        "id": article.submitting_agent_id,
                        "name": article.submitting_agent_name
                    } if article.submitting_agent_id else None,
                    "target_site": {
                        "id": article.target_site_id,
                        "name": article.target_site_name
                    } if article.target_site_id else None,
                    "publishing_agent_id": article.publishing_agent_id
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
                    "reviewer_notes": article.reviewer_notes,
                    # v2.1新增字段
                    "submitting_agent": {
                        "id": article.submitting_agent_id,
                        "name": article.submitting_agent_name
                    } if article.submitting_agent_id else None,
                    "target_site": {
                        "id": article.target_site_id,
                        "name": article.target_site_name
                    } if article.target_site_id else None,
                    "publishing_agent_id": article.publishing_agent_id
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
                "publish_error_message": article.publish_error_message,
                # v2.1新增字段
                "submitting_agent": {
                    "id": article.submitting_agent_id,
                    "name": article.submitting_agent_name
                } if article.submitting_agent_id else None,
                "target_site": {
                    "id": article.target_site_id,
                    "name": article.target_site_name
                } if article.target_site_id else None,
                "publishing_agent_id": article.publishing_agent_id,
                "agent_metadata": json.loads(article.agent_metadata) if article.agent_metadata else None
            })
    # ========== v2.1新增多代理和多站点Resources ==========
    
    @mcp.resource("agent://list")
    async def get_agent_list() -> str:
        """Get list of all active agents with basic statistics."""
        async with get_session() as session:
            # 获取所有有文章提交记录的代理
            query = select(
                Article.submitting_agent_id,
                Article.submitting_agent_name,
                func.count(Article.id).label("total_articles"),
                func.count().filter(Article.status == ArticleStatus.PUBLISHED).label("published_articles"),
                func.max(Article.created_at).label("last_submission")
            ).where(
                Article.submitting_agent_id.isnot(None)
            ).group_by(
                Article.submitting_agent_id,
                Article.submitting_agent_name
            )
            
            result = await session.execute(query)
            agents_data = []
            
            for row in result.all():
                agent_id, agent_name, total_articles, published_articles, last_submission = row
                success_rate = (published_articles / total_articles * 100) if total_articles > 0 else 0
                
                agents_data.append({
                    "id": agent_id,
                    "name": agent_name,
                    "statistics": {
                        "total_articles": total_articles,
                        "published_articles": published_articles,
                        "success_rate": round(success_rate, 2),
                        "last_submission": last_submission.isoformat() if last_submission else None
                    }
                })
            
            return json.dumps({
                "agents": agents_data,
                "total_active_agents": len(agents_data),
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
    
    @mcp.resource("site://list")
    async def get_site_list() -> str:
        """Get list of all configured WordPress sites with statistics."""
        async with get_session() as session:
            # 获取所有有发布记录的站点
            query = select(
                Article.target_site_id,
                Article.target_site_name,
                func.count(Article.id).label("total_articles"),
                func.count().filter(Article.status == ArticleStatus.PUBLISHED).label("published_articles"),
                func.count().filter(Article.status == ArticleStatus.PUBLISH_FAILED).label("failed_articles"),
                func.max(Article.updated_at).filter(Article.status == ArticleStatus.PUBLISHED).label("last_publish")
            ).where(
                Article.target_site_id.isnot(None)
            ).group_by(
                Article.target_site_id,
                Article.target_site_name
            )
            
            result = await session.execute(query)
            sites_data = []
            
            for row in result.all():
                site_id, site_name, total_articles, published_articles, failed_articles, last_publish = row
                total_attempts = published_articles + failed_articles
                success_rate = (published_articles / total_attempts * 100) if total_attempts > 0 else 0
                
                # 计算健康状态
                if success_rate >= 90:
                    health_status = "healthy"
                elif success_rate >= 70:
                    health_status = "warning"
                else:
                    health_status = "error"
                
                sites_data.append({
                    "id": site_id,
                    "name": site_name,
                    "health_status": health_status,
                    "statistics": {
                        "total_articles": total_articles,
                        "published_articles": published_articles,
                        "failed_articles": failed_articles,
                        "success_rate": round(success_rate, 2),
                        "last_publish": last_publish.isoformat() if last_publish else None
                    }
                })
            
            return json.dumps({
                "sites": sites_data,
                "total_configured_sites": len(sites_data),
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
    
    @mcp.resource("agent://{agent_id}/articles")
    async def get_agent_articles(agent_id: str) -> str:
        """Get all articles from a specific agent."""
        async with get_session() as session:
            query = select(Article).where(
                Article.submitting_agent_id == agent_id
            ).order_by(Article.created_at.desc())
            
            result = await session.execute(query)
            articles = result.scalars().all()
            
            articles_data = []
            for article in articles:
                articles_data.append({
                    "id": article.id,
                    "title": article.title,
                    "status": article.status,
                    "tags": article.tags,
                    "category": article.category,
                    "created_at": article.created_at.isoformat(),
                    "updated_at": article.updated_at.isoformat(),
                    "target_site": {
                        "id": article.target_site_id,
                        "name": article.target_site_name
                    } if article.target_site_id else None,
                    "wordpress_post_id": article.wordpress_post_id,
                    "wordpress_permalink": article.wordpress_permalink
                })
            
            return json.dumps({
                "agent_id": agent_id,
                "articles": articles_data,
                "total_articles": len(articles_data),
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
    
    @mcp.resource("site://{site_id}/articles")
    async def get_site_articles(site_id: str) -> str:
        """Get all articles published to a specific site."""
        async with get_session() as session:
            query = select(Article).where(
                Article.target_site_id == site_id
            ).order_by(Article.updated_at.desc())
            
            result = await session.execute(query)
            articles = result.scalars().all()
            
            articles_data = []
            for article in articles:
                articles_data.append({
                    "id": article.id,
                    "title": article.title,
                    "status": article.status,
                    "tags": article.tags,
                    "category": article.category,
                    "created_at": article.created_at.isoformat(),
                    "updated_at": article.updated_at.isoformat(),
                    "submitting_agent": {
                        "id": article.submitting_agent_id,
                        "name": article.submitting_agent_name
                    } if article.submitting_agent_id else None,
                    "publishing_agent_id": article.publishing_agent_id,
                    "wordpress_post_id": article.wordpress_post_id,
                    "wordpress_permalink": article.wordpress_permalink,
                    "publish_error_message": article.publish_error_message
                })
            
            return json.dumps({
                "site_id": site_id,
                "articles": articles_data,
                "total_articles": len(articles_data),
                "last_updated": datetime.now(timezone.utc).isoformat()
            })
