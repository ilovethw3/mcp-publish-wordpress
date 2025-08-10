"""Article model and status definitions."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func


class ArticleStatus(str, Enum):
    """Article status enumeration."""
    PENDING_REVIEW = "pending_review"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    PUBLISH_FAILED = "publish_failed"
    REJECTED = "rejected"


class Article(SQLModel, table=True):
    """Article database model."""
    __tablename__ = "articles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200, description="Article title")
    content_markdown: str = Field(description="Article content in Markdown format")
    content_html: Optional[str] = Field(default=None, description="Article content in HTML format")
    tags: Optional[str] = Field(default=None, description="Comma-separated tags")
    category: Optional[str] = Field(default=None, description="Article category")
    status: ArticleStatus = Field(default=ArticleStatus.PENDING_REVIEW, description="Article status")
    
    # WordPress integration fields
    wordpress_post_id: Optional[int] = Field(default=None, description="WordPress post ID")
    wordpress_permalink: Optional[str] = Field(default=None, description="WordPress post permalink")
    publish_error_message: Optional[str] = Field(default=None, description="Error message if publishing failed")
    
    # Timestamps
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Creation timestamp",
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc), 
        description="Last update timestamp",
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    
    # Review metadata
    reviewer_notes: Optional[str] = Field(default=None, description="Notes from reviewer")
    rejection_reason: Optional[str] = Field(default=None, description="Reason for rejection")