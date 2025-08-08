from fastapi import APIRouter, Depends, HTTPException, status, Query, BackgroundTasks
from sqlmodel import Session, select, or_, and_, desc
from typing import List, Optional
import markdown
from datetime import datetime

from mcp.core.security import get_current_user, verify_api_key
from mcp.db.session import get_session
from mcp.models.user import User
from mcp.models.article import (
    Article, ArticleCreate, ArticleUpdate, ArticleResponse, 
    ArticleList, ArticleStatus
)
from mcp.core.wordpress_client import WordPressClient

router = APIRouter(prefix="/articles", tags=["articles"])


def publish_to_wordpress(article_id: int, session: Session):
    """Background task to publish article to WordPress."""
    statement = select(Article).where(Article.id == article_id)
    article = session.exec(statement).first()
    
    if not article:
        return
    
    # Update status to publishing
    article.status = ArticleStatus.PUBLISHING
    article.updated_at = datetime.utcnow()
    session.add(article)
    session.commit()
    
    try:
        # Initialize WordPress client
        wp_client = WordPressClient()
        
        # Use HTML content if available, otherwise convert markdown
        content = article.content_html or markdown.markdown(article.content_markdown)
        
        # Publish to WordPress
        result = wp_client.create_post(
            title=article.title,
            content=content,
            tags=article.tags,
            category=article.category,
            status='publish'
        )
        
        if result['success']:
            # Update article with WordPress data
            article.status = ArticleStatus.PUBLISHED
            article.wordpress_post_id = result['post_id']
            article.wordpress_permalink = result['permalink']
            article.publish_error_message = None
        else:
            # Mark as failed
            article.status = ArticleStatus.PUBLISH_FAILED
            article.publish_error_message = result.get('error', 'Unknown error')
        
    except Exception as e:
        # Mark as failed
        article.status = ArticleStatus.PUBLISH_FAILED
        article.publish_error_message = str(e)
    
    article.updated_at = datetime.utcnow()
    session.add(article)
    session.commit()


@router.post("/submit", response_model=ArticleResponse)
async def submit_article(
    article: ArticleCreate,
    background_tasks: BackgroundTasks,
    session: Session = Depends(get_session),
    api_key_valid: bool = Depends(verify_api_key)
):
    """Submit article for review (for external AI agents)."""
    
    # Convert markdown to HTML if not provided
    html_content = article.content_html or markdown.markdown(article.content_markdown)
    
    # Create new article
    db_article = Article(
        title=article.title,
        content_markdown=article.content_markdown,
        content_html=html_content,
        tags=article.tags,
        category=article.category,
        status=ArticleStatus.PENDING_REVIEW
    )
    
    session.add(db_article)
    session.commit()
    session.refresh(db_article)
    
    return db_article


@router.get("/", response_model=List[ArticleList])
async def get_articles(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    search: Optional[str] = Query(None),
    status: Optional[ArticleStatus] = Query(None),
    sort_by: str = Query("created_at", regex="^(created_at|updated_at|title)$"),
    sort_order: str = Query("desc", regex="^(asc|desc)$"),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get articles list with search, filter and sorting."""
    
    # Build query
    statement = select(Article)
    
    # Apply filters
    if status:
        statement = statement.where(Article.status == status)
    
    if search:
        search_filter = or_(
            Article.title.icontains(search),
            Article.content_markdown.icontains(search),
            Article.tags.icontains(search) if Article.tags else False,
            Article.category.icontains(search) if Article.category else False
        )
        statement = statement.where(search_filter)
    
    # Apply sorting
    sort_column = getattr(Article, sort_by)
    if sort_order == "desc":
        statement = statement.order_by(desc(sort_column))
    else:
        statement = statement.order_by(sort_column)
    
    # Apply pagination
    statement = statement.offset(skip).limit(limit)
    
    articles = session.exec(statement).all()
    
    # Transform to response format
    return [
        ArticleList(
            id=article.id,
            title=article.title,
            status=article.status,
            created_at=article.created_at,
            updated_at=article.updated_at
        ) for article in articles
    ]


@router.get("/{article_id}", response_model=ArticleResponse)
async def get_article(
    article_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Get article by ID."""
    statement = select(Article).where(Article.id == article_id)
    article = session.exec(statement).first()
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    return article


@router.put("/{article_id}", response_model=ArticleResponse)
async def update_article(
    article_id: int,
    article_update: ArticleUpdate,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Update article."""
    statement = select(Article).where(Article.id == article_id)
    article = session.exec(statement).first()
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    # Update fields
    update_data = article_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        setattr(article, field, value)
    
    # If markdown was updated, regenerate HTML
    if 'content_markdown' in update_data:
        article.content_html = markdown.markdown(article.content_markdown)
    
    article.updated_at = datetime.utcnow()
    session.add(article)
    session.commit()
    session.refresh(article)
    
    return article


@router.delete("/{article_id}")
async def delete_article(
    article_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Delete article."""
    statement = select(Article).where(Article.id == article_id)
    article = session.exec(statement).first()
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    session.delete(article)
    session.commit()
    
    return {"message": "Article deleted successfully"}


@router.post("/{article_id}/approve")
async def approve_article(
    article_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Approve article and start publishing process."""
    statement = select(Article).where(Article.id == article_id)
    article = session.exec(statement).first()
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    if article.status != ArticleStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article is not in pending review status"
        )
    
    # Start publishing process in background
    background_tasks.add_task(publish_to_wordpress, article_id, session)
    
    return {"message": "Article approved and publishing started"}


@router.post("/{article_id}/reject")
async def reject_article(
    article_id: int,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Reject article."""
    statement = select(Article).where(Article.id == article_id)
    article = session.exec(statement).first()
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    if article.status != ArticleStatus.PENDING_REVIEW:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article is not in pending review status"
        )
    
    article.status = ArticleStatus.REJECTED
    article.updated_at = datetime.utcnow()
    session.add(article)
    session.commit()
    
    return {"message": "Article rejected"}


@router.post("/{article_id}/retry")
async def retry_publish(
    article_id: int,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    """Retry publishing failed article."""
    statement = select(Article).where(Article.id == article_id)
    article = session.exec(statement).first()
    
    if not article:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Article not found"
        )
    
    if article.status != ArticleStatus.PUBLISH_FAILED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Article is not in failed status"
        )
    
    # Start publishing process in background
    background_tasks.add_task(publish_to_wordpress, article_id, session)
    
    return {"message": "Article publishing retry started"}