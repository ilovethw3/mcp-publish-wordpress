"""MCP Tools for article management."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from sqlmodel import select
from fastmcp import FastMCP
from fastmcp.server.dependencies import get_access_token
import bleach

from mcp_wordpress.core.database import get_session
from mcp_wordpress.core.wordpress import WordPressClient
from mcp_wordpress.core.errors import (
    ArticleNotFoundError, InvalidStatusError, WordPressError, 
    ValidationError, create_mcp_success, MCPError, MCPErrorCodes
)
from mcp_wordpress.models.article import Article, ArticleStatus
from mcp_wordpress.models.site import Site
from mcp_wordpress.auth.permissions import require_permission, require_any_permission, require_edit_permission, require_submit_permission
from mcp_wordpress.services.role_template_service import role_template_service


async def get_site_config(session, site_id: str = None) -> dict:
    """Get WordPress configuration from database site.
    
    Args:
        session: Database session
        site_id: Site ID, if None uses first active site
        
    Returns:
        Dictionary with api_url, username, app_password
        
    Raises:
        ValueError: If no site found or site not configured
    """
    if site_id:
        # Get specific site
        result = await session.execute(select(Site).where(Site.id == site_id))
        site = result.scalars().first()
        
        if not site:
            raise ValueError(f"Site not found: {site_id}")
    else:
        # Get first active site as default
        result = await session.execute(
            select(Site).where(Site.status == "active").order_by(Site.created_at)
        )
        site = result.scalars().first()
        
        if not site:
            raise ValueError("No active WordPress sites configured. Please add a site through Web UI.")
    
    if not site.is_active:
        raise ValueError(f"Site {site.id} is not active")
    
    wp_config = site.wordpress_config
    if not wp_config or not wp_config.get("api_url") or not wp_config.get("username") or not wp_config.get("app_password"):
        raise ValueError(f"Site {site.id} WordPress configuration is incomplete")
    
    return {
        "api_url": wp_config["api_url"],
        "username": wp_config["username"], 
        "app_password": wp_config["app_password"]
    }


def register_article_tools(mcp: FastMCP):
    """Register all article management tools with the MCP server."""
    
    @mcp.tool()
    async def ping():
        """Simple ping test."""
        return {"status": "ok", "message": "MCP server is working"}
    
    @mcp.tool(
        description="Submit a new article for review with multi-agent support"
    )
    @require_submit_permission()
    async def submit_article(
        title: str,
        content_markdown: str,
        tags: str = "",
        category: str = "",
        agent_metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Submit a new article for review with v2.1 multi-agent support.
        
        Site selection will be done during approval/publishing phase.
        
        Args:
            title: Article title (max 200 characters)
            content_markdown: Article content in Markdown format
            tags: Comma-separated tags (optional)
            category: Article category (optional)
            agent_metadata: Additional metadata from submitting agent (optional)
            
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
            
            # Get submitting agent information from access token
            access_token = get_access_token()
            agent_id = access_token.client_id if access_token else None
            agent_name = getattr(access_token, 'metadata', {}).get("agent_name") if access_token else None
            
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
                    status=ArticleStatus.PENDING_REVIEW.value,
                    # v2.1新增字段
                    submitting_agent_id=agent_id,
                    submitting_agent_name=agent_name,
                    target_site_id=None,  # 站点选择将在审批时进行
                    agent_metadata=json.dumps(agent_metadata) if agent_metadata else None
                )
                
                session.add(article)
                await session.commit()
                await session.refresh(article)
                
                return create_mcp_success({
                    "article_id": article.id,
                    "status": article.status,
                    "submitting_agent": {
                        "id": article.submitting_agent_id,
                        "name": article.submitting_agent_name
                    } if article.submitting_agent_id else None,
                    "message": "Article submitted successfully for review. Site selection will be done during approval."
                })
        except (ValidationError, ArticleNotFoundError, InvalidStatusError) as e:
            return e.to_json()
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool()
    @require_permission("can_view_statistics")
    async def list_articles(
        status: str = "",
        search: str = "", 
        limit: int = 50,
        agent_id: str = "",
        target_site: str = ""
    ) -> str:
        """List articles with multi-dimensional filtering options.
        
        Args:
            status: Filter by status (pending_review, publishing, published, rejected, publish_failed)
            search: Search in title and content
            limit: Maximum number of articles to return (max 100)
            agent_id: Filter by submitting agent ID
            target_site: Filter by target site
            
        Returns:
            JSON string with list of articles including agent and site information
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
                
                # Apply agent filter (v2.1 new feature)
                if agent_id:
                    query = query.where(Article.submitting_agent_id == agent_id)
                
                # Apply site filter (v2.1 new feature)
                if target_site:
                    query = query.where(Article.target_site_id == target_site)
                
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
                    article_data = {
                        "id": article.id,
                        "title": article.title,
                        "status": article.status,
                        "tags": article.tags,
                        "category": article.category,
                        "created_at": article.created_at.isoformat(),
                        "updated_at": article.updated_at.isoformat(),
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
                    }
                    articles_data.append(article_data)
                
                return create_mcp_success({
                    "articles": articles_data,
                    "total": len(articles_data),
                    "filtered_by": {
                        "status": status,
                        "search": search,
                        "limit": limit,
                        "agent_id": agent_id,
                        "target_site": target_site
                    }
                })
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool(
        description="Get detailed article status and publishing information"
    )
    @require_permission("can_view_statistics")
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
                    "content_markdown": article.content_markdown,
                    "content_html": article.content_html,
                    "status": article.status,
                    "tags": article.tags,
                    "category": article.category,
                    "created_at": article.created_at.isoformat(),
                    "updated_at": article.updated_at.isoformat(),
                    "reviewer_notes": article.reviewer_notes,
                    "rejection_reason": article.rejection_reason,
                    "wordpress_post_id": article.wordpress_post_id,
                    "wordpress_permalink": article.wordpress_permalink,
                    "publish_error_message": article.publish_error_message,
                    # v2.1多代理支持字段
                    "submitting_agent": {
                        "id": article.submitting_agent_id,
                        "name": article.submitting_agent_name
                    } if article.submitting_agent_id else None,
                    "agent_metadata": article.agent_metadata,
                    "publishing_agent_id": article.publishing_agent_id,
                    # v2.1多站点支持字段
                    "target_site": {
                        "id": article.target_site_id,
                        "name": article.target_site_name
                    } if article.target_site_id else None
                })
        except (ArticleNotFoundError, InvalidStatusError) as e:
            return e.to_json()
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool(
        description="Approve article without publishing (审批通过，但不发布)"
    )
    @require_permission("can_approve_articles")
    async def approve_article(
        article_id: int,
        reviewer_notes: str = ""
    ) -> str:
        """Approve article without publishing to WordPress.
        
        Args:
            article_id: ID of the article to approve
            reviewer_notes: Optional notes from the reviewer
            
        Returns:
            JSON string with approval status
        """
        try:
            # Get approving agent information from access token
            access_token = get_access_token()
            approving_agent_id = access_token.client_id if access_token else None
            approving_agent_name = getattr(access_token, 'metadata', {}).get("agent_name") if access_token else None
            
            async with get_session() as session:
                result = await session.execute(select(Article).where(Article.id == article_id))
                article = result.scalars().first()
                
                if not article:
                    raise ArticleNotFoundError(article_id)
                
                if article.status != ArticleStatus.PENDING_REVIEW.value:
                    raise InvalidStatusError(article.status, ArticleStatus.PENDING_REVIEW.value)
                
                # Update article status to approved (不发布)
                article.status = ArticleStatus.APPROVED.value
                article.reviewer_notes = reviewer_notes
                article.updated_at = datetime.now(timezone.utc)
                
                # 记录审批者信息
                if approving_agent_id:
                    article.publishing_agent_id = approving_agent_id
                
                session.add(article)
                await session.commit()
                
                return create_mcp_success({
                    "article_id": article.id,
                    "status": article.status,
                    "reviewer_notes": reviewer_notes,
                    "approving_agent": {
                        "id": approving_agent_id,
                        "name": approving_agent_name
                    } if approving_agent_id else None,
                    "message": "Article approved successfully. Ready for publishing."
                })
        except (ArticleNotFoundError, InvalidStatusError) as e:
            return e.to_json()
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool(
        description="Publish approved article to specified WordPress site"
    )
    @require_permission("can_publish_articles")
    async def publish_article(
        article_id: int,
        target_site_id: str,
        notes: str = ""
    ) -> str:
        """Publish approved article to specified WordPress site.
        
        可以发布approved状态的文章，或重试发布publish_failed状态的文章。
        
        Args:
            article_id: ID of the article to publish
            target_site_id: ID of the WordPress site to publish to
            notes: Optional notes for publishing/retry
            
        Returns:
            JSON string with publishing result
        """
        try:
            # Get publishing agent information from access token
            access_token = get_access_token()
            publishing_agent_id = access_token.client_id if access_token else None
            publishing_agent_name = getattr(access_token, 'metadata', {}).get("agent_name") if access_token else None
            
            async with get_session() as session:
                result = await session.execute(select(Article).where(Article.id == article_id))
                article = result.scalars().first()
                
                if not article:
                    raise ArticleNotFoundError(article_id)
                
                # 只允许approved或publish_failed状态的文章发布
                if article.status not in [ArticleStatus.APPROVED.value, ArticleStatus.PUBLISH_FAILED.value]:
                    raise InvalidStatusError(article.status, f"{ArticleStatus.APPROVED.value} or {ArticleStatus.PUBLISH_FAILED.value}")
                
                # Get site information first to validate it exists
                site_result = await session.execute(select(Site).where(Site.id == target_site_id))
                target_site = site_result.scalars().first()
                
                if not target_site:
                    raise ValueError(f"Site not found: {target_site_id}")
                
                # Update article status to publishing and set target site
                article.status = ArticleStatus.PUBLISHING.value
                article.target_site_id = target_site_id
                article.target_site_name = target_site.name
                article.updated_at = datetime.now(timezone.utc)
                
                # 清除之前的发布错误信息
                article.publish_error_message = None
                
                # 记录发布者信息和备注
                if publishing_agent_id:
                    article.publishing_agent_id = publishing_agent_id
                if notes:
                    # 如果有审核备注，追加发布备注
                    if article.reviewer_notes:
                        article.reviewer_notes += f"\n\n发布备注: {notes}"
                    else:
                        article.reviewer_notes = f"发布备注: {notes}"
                
                session.add(article)
                await session.commit()
                
                # Attempt WordPress publishing
                try:
                    # Get WordPress configuration from database using the specified site
                    site_config = await get_site_config(session, target_site_id)
                    
                    wp_client = WordPressClient(
                        api_url=site_config["api_url"],
                        username=site_config["username"],
                        app_password=site_config["app_password"]
                    )
                    wp_result = await wp_client.create_post(
                        title=article.title,
                        content_markdown=article.content_markdown,
                        tags=article.tags,
                        category=article.category
                    )
                    
                    # Update article with WordPress info
                    article.status = ArticleStatus.PUBLISHED.value
                    article.wordpress_post_id = wp_result["id"]
                    article.wordpress_permalink = wp_result.get("link")
                    article.updated_at = datetime.now(timezone.utc)
                    
                    session.add(article)
                    await session.commit()
                    
                    return create_mcp_success({
                        "article_id": article.id,
                        "status": "published",
                        "wordpress_post_id": wp_result["id"],
                        "wordpress_permalink": wp_result.get("link"),
                        "target_site": {
                            "id": target_site_id,
                            "name": target_site.name
                        },
                        "publishing_agent": {
                            "id": publishing_agent_id,
                            "name": publishing_agent_name
                        } if publishing_agent_id else None,
                        "message": "Article published successfully to WordPress"
                    })
                    
                except Exception as e:
                    # Update article status to failed
                    article.status = ArticleStatus.PUBLISH_FAILED.value
                    article.publish_error_message = str(e)
                    article.updated_at = datetime.now(timezone.utc)
                    
                    session.add(article)
                    await session.commit()
                    
                    return create_mcp_success({
                        "article_id": article.id,
                        "status": "publish_failed",
                        "error": str(e),
                        "target_site": {
                            "id": target_site_id,
                            "name": target_site.name
                        },
                        "message": "WordPress publishing failed. You can retry later."
                    })
        except (ArticleNotFoundError, InvalidStatusError) as e:
            return e.to_json()
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool(
        description="Edit article content and metadata"
    )
    @require_edit_permission()
    async def edit_article(
        article_id: int,
        title: str = None,
        content_markdown: str = None,
        tags: str = None,
        category: str = None
    ) -> str:
        """Edit article content and metadata.
        
        允许修改pending_review或approved状态的文章。
        
        Args:
            article_id: ID of the article to edit
            title: New title (optional)
            content_markdown: New content in Markdown format (optional)
            tags: New tags (optional)
            category: New category (optional)
            
        Returns:
            JSON string with edit result
        """
        try:
            # Get editing agent information from access token
            access_token = get_access_token()
            editing_agent_id = access_token.client_id if access_token else None
            editing_agent_name = getattr(access_token, 'metadata', {}).get("agent_name") if access_token else None
            
            async with get_session() as session:
                result = await session.execute(select(Article).where(Article.id == article_id))
                article = result.scalars().first()
                
                if not article:
                    raise ArticleNotFoundError(article_id)
                
                # 只允许编辑pending_review或approved状态的文章
                if article.status not in [ArticleStatus.PENDING_REVIEW.value, ArticleStatus.APPROVED.value]:
                    raise InvalidStatusError(article.status, f"{ArticleStatus.PENDING_REVIEW.value} or {ArticleStatus.APPROVED.value}")
                
                # 权限检查已由装饰器完成（包括所有权和内容限制检查）
                
                # 记录修改前的值用于历史记录
                changes = {}
                
                # 更新字段（如果提供了新值）
                if title is not None and title.strip():
                    if len(title) > 200:
                        raise ValidationError("title", "Title cannot exceed 200 characters")
                    if article.title != title.strip():
                        changes["title"] = {"from": article.title, "to": title.strip()}
                        article.title = title.strip()
                
                if content_markdown is not None and content_markdown.strip():
                    # 清理内容
                    clean_content = bleach.clean(
                        content_markdown,
                        tags=['h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'p', 'br', 'strong', 'em', 'ul', 'ol', 'li', 'a', 'code', 'pre'],
                        attributes={'a': ['href', 'title']}
                    )
                    if article.content_markdown != clean_content:
                        changes["content_markdown"] = {"from": "原内容", "to": "新内容"}  # 不记录全文，太长
                        article.content_markdown = clean_content
                
                if tags is not None:
                    new_tags = tags.strip() if tags else None
                    if article.tags != new_tags:
                        changes["tags"] = {"from": article.tags, "to": new_tags}
                        article.tags = new_tags
                
                if category is not None:
                    new_category = category.strip() if category else None
                    if article.category != new_category:
                        changes["category"] = {"from": article.category, "to": new_category}
                        article.category = new_category
                
                # 如果没有任何变更
                if not changes:
                    return create_mcp_success({
                        "article_id": article.id,
                        "status": article.status,
                        "message": "No changes were made to the article."
                    })
                
                # 更新时间戳
                article.updated_at = datetime.now(timezone.utc)
                
                # 记录修改历史（简化版本，实际应该有专门的修改历史表）
                if article.reviewer_notes:
                    article.reviewer_notes += f"\n\n修改记录 ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} by {editing_agent_name or editing_agent_id or 'Unknown'}): {len(changes)}个字段被修改"
                else:
                    article.reviewer_notes = f"修改记录 ({datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M:%S')} by {editing_agent_name or editing_agent_id or 'Unknown'}): {len(changes)}个字段被修改"
                
                session.add(article)
                await session.commit()
                await session.refresh(article)
                
                return create_mcp_success({
                    "article_id": article.id,
                    "status": article.status,
                    "changes": changes,
                    "editing_agent": {
                        "id": editing_agent_id,
                        "name": editing_agent_name
                    } if editing_agent_id else None,
                    "message": f"Article updated successfully. {len(changes)} fields modified."
                })
        except (ArticleNotFoundError, InvalidStatusError, ValidationError) as e:
            return e.to_json()
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool(
        description="Reject article with reason"
    )
    @require_permission("can_approve_articles")
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
                
                if article.status != ArticleStatus.PENDING_REVIEW.value:
                    raise InvalidStatusError(article.status, ArticleStatus.PENDING_REVIEW.value)
                
                # Update article status to rejected
                article.status = ArticleStatus.REJECTED.value
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
    
    # ========== v2.1新增管理类MCP Tools ==========
    
    @mcp.tool(
        description="List all configured AI agents and their status"
    )
    @require_permission("can_view_statistics")
    async def list_agents(include_inactive: bool = False) -> str:
        """List all configured AI agents and their status.
        
        Args:
            include_inactive: Include inactive agents in results
            
        Returns:
            JSON string with list of agents and their information
        """
        try:
            from sqlalchemy import func
            async with get_session() as session:
                query = select(Article.submitting_agent_id, Article.submitting_agent_name).distinct()
                if not include_inactive:
                    # 只显示有活动的代理（最近有提交文章的）
                    query = query.where(Article.submitting_agent_id.isnot(None))
                
                result = await session.execute(query)
                agents_data = []
                
                for agent_id, agent_name in result.all():
                    if agent_id:
                        # 获取代理统计信息
                        stats_query = select(
                            func.count(Article.id).label('total_articles'),
                            func.count().filter(Article.status == ArticleStatus.PUBLISHED.value).label('published_articles'),
                            func.max(Article.created_at).label('last_submission')
                        ).where(Article.submitting_agent_id == agent_id)
                        
                        stats_result = await session.execute(stats_query)
                        stats = stats_result.first()
                        
                        agents_data.append({
                            "id": agent_id,
                            "name": agent_name,
                            "status": "active",  # 简化状态，实际应从配置管理器获取
                            "statistics": {
                                "total_articles": stats[0] if stats else 0,
                                "published_articles": stats[1] if stats else 0,
                                "last_submission": stats[2].isoformat() if stats and stats[2] else None
                            }
                        })
                
                return create_mcp_success({
                    "agents": agents_data,
                    "total": len(agents_data),
                    "include_inactive": include_inactive
                })
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool(
        description="List all configured WordPress sites and their health status"
    )
    @require_permission("can_view_statistics")
    async def list_sites(include_inactive: bool = False) -> str:
        """List all configured WordPress sites and their health status.
        
        Args:
            include_inactive: Include inactive sites in results
            
        Returns:
            JSON string with list of sites and their information
        """
        try:
            from sqlalchemy import func
            async with get_session() as session:
                query = select(Article.target_site_id, Article.target_site_name).distinct()
                if not include_inactive:
                    query = query.where(Article.target_site_id.isnot(None))
                
                result = await session.execute(query)
                sites_data = []
                
                for site_id, site_name in result.all():
                    if site_id:
                        # 获取站点统计信息
                        stats_query = select(
                            func.count(Article.id).label('total_articles'),
                            func.count().filter(Article.status == ArticleStatus.PUBLISHED.value).label('published_articles'),
                            func.max(Article.updated_at).filter(Article.status == ArticleStatus.PUBLISHED.value).label('last_publish')
                        ).where(Article.target_site_id == site_id)
                        
                        stats_result = await session.execute(stats_query)
                        stats = stats_result.first()
                        
                        sites_data.append({
                            "id": site_id,
                            "name": site_name,
                            "health_status": "unknown",  # 实际应从站点配置管理器获取
                            "statistics": {
                                "total_articles": stats[0] if stats else 0,
                                "published_articles": stats[1] if stats else 0,
                                "last_publish": stats[2].isoformat() if stats and stats[2] else None
                            }
                        })
                
                return create_mcp_success({
                    "sites": sites_data,
                    "total": len(sites_data),
                    "include_inactive": include_inactive
                })
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool(
        description="Get statistics for a specific agent"
    )
    @require_permission("can_view_statistics")
    async def get_agent_stats(agent_id: str) -> str:
        """Get detailed statistics for a specific agent.
        
        Args:
            agent_id: ID of the agent to get stats for
            
        Returns:
            JSON string with detailed agent statistics
        """
        try:
            from sqlalchemy import func
            async with get_session() as session:
                # 基础统计
                base_stats_query = select(
                    func.count(Article.id).label('total_submitted'),
                    func.count().filter(Article.status == ArticleStatus.PUBLISHED.value).label('total_published'),
                    func.count().filter(Article.status == ArticleStatus.REJECTED.value).label('total_rejected'),
                    func.count().filter(Article.status == ArticleStatus.PENDING_REVIEW.value).label('pending_review'),
                    func.min(Article.created_at).label('first_submission'),
                    func.max(Article.created_at).label('last_submission')
                ).where(Article.submitting_agent_id == agent_id)
                
                base_result = await session.execute(base_stats_query)
                base_stats = base_result.first()
                
                if not base_stats or base_stats[0] == 0:
                    raise ArticleNotFoundError(f"No articles found for agent: {agent_id}")
                
                # 获取代理名称
                name_query = select(Article.submitting_agent_name).where(
                    Article.submitting_agent_id == agent_id
                ).limit(1)
                name_result = await session.execute(name_query)
                agent_name = name_result.scalars().first()
                
                total_submitted = base_stats[0]
                success_rate = (base_stats[1] / total_submitted * 100) if total_submitted > 0 else 0
                
                return create_mcp_success({
                    "agent_id": agent_id,
                    "agent_name": agent_name,
                    "statistics": {
                        "total_submitted": total_submitted,
                        "total_published": base_stats[1],
                        "total_rejected": base_stats[2],
                        "pending_review": base_stats[3],
                        "success_rate": round(success_rate, 2),
                        "first_submission": base_stats[4].isoformat() if base_stats[4] else None,
                        "last_submission": base_stats[5].isoformat() if base_stats[5] else None
                    }
                })
        except ArticleNotFoundError as e:
            return e.to_json()
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()
    
    @mcp.tool(
        description="Get health status and metrics for a WordPress site"
    )
    @require_permission("can_view_statistics")
    async def get_site_health(site_id: str) -> str:
        """Get health status and metrics for a WordPress site.
        
        Args:
            site_id: ID of the site to check
            
        Returns:
            JSON string with site health status and metrics
        """
        try:
            from sqlalchemy import func
            async with get_session() as session:
                # 获取站点统计信息
                stats_query = select(
                    func.count(Article.id).label('total_articles'),
                    func.count().filter(Article.status == ArticleStatus.PUBLISHED).label('published_articles'),
                    func.count().filter(Article.status == ArticleStatus.PUBLISH_FAILED.value).label('failed_articles'),
                    func.max(Article.updated_at).filter(Article.status == ArticleStatus.PUBLISHED.value).label('last_successful_publish'),
                    func.max(Article.updated_at).filter(Article.status == ArticleStatus.PUBLISH_FAILED.value).label('last_failed_publish')
                ).where(Article.target_site_id == site_id)
                
                stats_result = await session.execute(stats_query)
                stats = stats_result.first()
                
                if not stats or stats[0] == 0:
                    return create_mcp_success({
                        "site_id": site_id,
                        "health_status": "unknown",
                        "message": "No publishing history found for this site"
                    })
                
                # 计算健康状态
                total_attempts = stats[1] + stats[2]  # published + failed
                success_rate = (stats[1] / total_attempts * 100) if total_attempts > 0 else 0
                
                if success_rate >= 90:
                    health_status = "healthy"
                elif success_rate >= 70:
                    health_status = "warning"
                else:
                    health_status = "error"
                
                # 获取站点名称
                name_query = select(Article.target_site_name).where(
                    Article.target_site_id == site_id
                ).limit(1)
                name_result = await session.execute(name_query)
                site_name = name_result.scalars().first()
                
                return create_mcp_success({
                    "site_id": site_id,
                    "site_name": site_name,
                    "health_status": health_status,
                    "metrics": {
                        "total_articles": stats[0],
                        "published_articles": stats[1],
                        "failed_articles": stats[2],
                        "success_rate": round(success_rate, 2),
                        "last_successful_publish": stats[3].isoformat() if stats[3] else None,
                        "last_failed_publish": stats[4].isoformat() if stats[4] else None
                    }
                })
        except Exception as e:
            error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
            return error.to_json()