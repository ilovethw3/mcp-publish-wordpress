from sqlmodel import SQLModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class ArticleStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    PUBLISH_FAILED = "publish_failed"
    REJECTED = "rejected"


class ArticleBase(SQLModel):
    title: str = Field(min_length=1, max_length=200, description="文章标题")
    content_markdown: str = Field(description="文章的Markdown内容")
    content_html: Optional[str] = Field(default=None, description="文章的HTML内容")
    tags: Optional[str] = Field(default=None, description="文章标签，逗号分隔")
    category: Optional[str] = Field(default=None, description="文章分类")


class ArticleCreate(ArticleBase):
    pass


class ArticleUpdate(SQLModel):
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    content_markdown: Optional[str] = Field(default=None)
    content_html: Optional[str] = Field(default=None)
    tags: Optional[str] = Field(default=None)
    category: Optional[str] = Field(default=None)
    status: Optional[ArticleStatus] = Field(default=None)


class Article(ArticleBase, table=True):
    __tablename__ = "articles"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="文章ID")
    status: ArticleStatus = Field(default=ArticleStatus.PENDING_REVIEW, description="文章状态")
    wordpress_post_id: Optional[int] = Field(default=None, description="WordPress文章ID")
    wordpress_permalink: Optional[str] = Field(default=None, description="WordPress永久链接")
    publish_error_message: Optional[str] = Field(default=None, description="发布失败错误信息")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")


class ArticleResponse(ArticleBase):
    id: int
    status: ArticleStatus
    wordpress_post_id: Optional[int]
    wordpress_permalink: Optional[str]
    publish_error_message: Optional[str]
    created_at: datetime
    updated_at: datetime


class ArticleList(SQLModel):
    id: int
    title: str
    status: ArticleStatus
    created_at: datetime
    updated_at: datetime