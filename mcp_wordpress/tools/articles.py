"""MCP Tools for article management."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List
from sqlmodel import select
from fastmcp import FastMCP
import bleach

from mcp_wordpress.core.database import get_session
from mcp_wordpress.core.wordpress import WordPressClient
from mcp_wordpress.core.errors import (
    ArticleNotFoundError, InvalidStatusError, WordPressError, 
    ValidationError, create_mcp_success, MCPError, MCPErrorCodes
)
from mcp_wordpress.models.article import Article, ArticleStatus


def register_article_tools(mcp: FastMCP):
    """Register all article management tools with the MCP server."""
    
    @mcp.tool()
    async def ping():
        """Simple ping test."""
        return {"status": "ok", "message": "MCP server is working"}
    
    @mcp.tool(
        description="Submit a new article for review"
    )
    async def submit_article(
        title: str,
        content_markdown: str,
        tags: str = "",
        category: str = ""
    ) -> str:
        """Submit a new article for review.
        
        Args:
            title: Article title (max 200 characters)
            content_markdown: Article content in Markdown format
            tags: Comma-separated tags (optional)
            category: Article category (optional)
            
        Returns:
            JSON string with article_id and status
        """
        try:
            # Input validation
            if len(title) > 200:
                raise ValidationError("title", "Title cannot exceed 200 characters")
            if len(title.strip()) == 0:
                raise ValidationError("title", "Title cannot be empty")
            if len(content_markdown.strip()) == 0:
                raise ValidationError("content_markdown", "Content cannot be empty")
            
            # Sanitize content for XSS protection
            clean_content = bleach.clean(
                content_markdown,
                tags=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'code', 'pre'],
                attributes={'a': ['href', 'title']}
            )
            
            async with get_session() as session:
                article = Article(
                    title=title.strip(),
                    content_markdown=clean_content,
                    tags=tags.strip() if tags else None,
                    category=category.strip() if category else None,
                    status=ArticleStatus.PENDING_REVIEW
                )
                
                session.add(article)
                await session.commit()
                await session.refresh(article)
                
                return create_mcp_success({
                    "article_id": article.id,
                    "status": article.status,
                    "message": "Article submitted successfully for review"
                })
        except (ValidationError, ArticleNotFoundError, InvalidStatusError) as e:
            return e.to_json()
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool()
    async def list_articles(
        status: str = "",
        search: str = "", 
        limit: int = 50
    ) -> str:
        """List articles with filtering options.
        
        Args:
            status: Filter by status (pending_review, publishing, published, rejected, publish_failed)
            search: Search in title and content
            limit: Maximum number of articles to return (max 100)
            
        Returns:
            JSON string with list of articles
        """
        try:
            # Validate limit
            if limit > 100:
                limit = 100
            
            async with get_session() as session:
                query = select(Article)
                
                # Apply status filter
                if status and status in [s.value for s in ArticleStatus]:
                    query = query.where(Article.status == status)
                
                # Apply search filter
                if search:
                    query = query.where(
                        Article.title.contains(search) | 
                        Article.content_markdown.contains(search)
                    )
                
                # Apply limit and order
                query = query.order_by(Article.updated_at.desc()).limit(limit)
                
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
                        "wordpress_post_id": article.wordpress_post_id,
                        "wordpress_permalink": article.wordpress_permalink
                    })
                
                return create_mcp_success({
                    "articles": articles_data,
                    "total": len(articles_data),
                    "filtered_by": {
                        "status": status,
                        "search": search,
                        "limit": limit
                    }
                })
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool(
        description="Get detailed article status and publishing information"
    )
    async def get_article_status(article_id: int) -> str:
        """Get detailed article status and publishing information.
        
        Args:
            article_id: ID of the article to check
            
        Returns:
            JSON string with detailed article information
        """
        try:
            async with get_session() as session:
                result = await session.execute(select(Article).where(Article.id == article_id))
                article = result.scalars().first()
                
                if not article:
                    raise ArticleNotFoundError(article_id)
                
                return create_mcp_success({
                    "article_id": article.id,
                    "title": article.title,
                    "status": article.status,
                    "tags": article.tags,
                    "category": article.category,
                    "created_at": article.created_at.isoformat(),
                    "updated_at": article.updated_at.isoformat(),
                    "reviewer_notes": article.reviewer_notes,
                    "rejection_reason": article.rejection_reason,
                    "wordpress_post_id": article.wordpress_post_id,
                    "wordpress_permalink": article.wordpress_permalink,
                    "publish_error_message": article.publish_error_message
                })
        except (ArticleNotFoundError, InvalidStatusError) as e:
            return e.to_json()
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool(
        description="Approve article and start WordPress publishing"
    )
    async def approve_article(
        article_id: int,
        reviewer_notes: str = ""
    ) -> str:
        """Approve article and start WordPress publishing.
        
        Args:
            article_id: ID of the article to approve
            reviewer_notes: Optional notes from the reviewer
            
        Returns:
            JSON string with approval status and WordPress publishing result
        """
        try:
            async with get_session() as session:
                result = await session.execute(select(Article).where(Article.id == article_id))
                article = result.scalars().first()
                
                if not article:
                    raise ArticleNotFoundError(article_id)
                
                if article.status != ArticleStatus.PENDING_REVIEW:
                    raise InvalidStatusError(article.status, ArticleStatus.PENDING_REVIEW)
                
                # Update article status to publishing
                article.status = ArticleStatus.PUBLISHING
                article.reviewer_notes = reviewer_notes
                article.updated_at = datetime.now(timezone.utc)
                
                session.add(article)
                await session.commit()
                
                # Attempt WordPress publishing
                try:
                    wp_client = WordPressClient()
                    wp_result = await wp_client.create_post(
                        title=article.title,
                        content_markdown=article.content_markdown,
                        tags=article.tags,
                        category=article.category
                    )
                    
                    # Update article with WordPress info
                    article.status = ArticleStatus.PUBLISHED
                    article.wordpress_post_id = wp_result["id"]
                    article.wordpress_permalink = wp_result.get("link")
                    article.updated_at = datetime.now(timezone.utc)
                    
                    session.add(article)
                    await session.commit()
                    
                    return json.dumps({
                        "article_id": article.id,
                        "status": "published",
                        "wordpress_post_id": wp_result["id"],
                        "wordpress_permalink": wp_result.get("link"),
                        "message": "Article approved and published successfully"
                    })
                    
                except Exception as e:
                    # Update article status to failed
                    article.status = ArticleStatus.PUBLISH_FAILED
                    article.publish_error_message = str(e)
                    article.updated_at = datetime.now(timezone.utc)
                    
                    session.add(article)
                    await session.commit()
                    
                    return json.dumps({
                        "article_id": article.id,
                        "status": "publish_failed",
                        "error": str(e),
                        "message": "Article approved but WordPress publishing failed"
                    })
        except (ArticleNotFoundError, InvalidStatusError) as e:
            return e.to_json()
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool(
        description="Reject article with reason"
    )
    async def reject_article(
        article_id: int,
        rejection_reason: str
    ) -> str:
        """Reject article with reason.
        
        Args:
            article_id: ID of the article to reject
            rejection_reason: Reason for rejection
            
        Returns:
            JSON string with rejection status
        """
        try:
            async with get_session() as session:
                result = await session.execute(select(Article).where(Article.id == article_id))
                article = result.scalars().first()
                
                if not article:
                    raise ArticleNotFoundError(article_id)
                
                if article.status != ArticleStatus.PENDING_REVIEW:
                    raise InvalidStatusError(article.status, ArticleStatus.PENDING_REVIEW)
                
                # Update article status to rejected
                article.status = ArticleStatus.REJECTED
                article.rejection_reason = rejection_reason
                article.updated_at = datetime.now(timezone.utc)
                
                session.add(article)
                await session.commit()
                
                return json.dumps({
                    "article_id": article.id,
                    "status": "rejected",
                    "rejection_reason": rejection_reason,
                    "message": "Article rejected successfully"
                })
        except (ArticleNotFoundError, InvalidStatusError) as e:
            return e.to_json()
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()