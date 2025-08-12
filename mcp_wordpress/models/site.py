"""
Site model for MCP WordPress Publisher v2.1

This module defines the Site data model for multi-site WordPress
publishing management.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime, func


class Site(SQLModel, table=True):
    """Site model for multi-site WordPress publishing
    
    Represents a WordPress site that can receive published content
    from the MCP system.
    """
    __tablename__ = "sites"
    
    id: str = Field(primary_key=True, max_length=50)
    name: str = Field(max_length=100)
    api_url: str = Field(max_length=255)
    username: str = Field(max_length=100)
    # 注意：不存储明文密码，通过配置文件管理
    
    # 站点配置
    default_category: Optional[str] = Field(default=None, max_length=100)
    default_tags: Optional[str] = Field(default=None, max_length=500)
    
    # 状态信息
    is_active: bool = Field(default=True)
    last_health_check: Optional[datetime] = None
    health_status: str = Field(default="unknown")  # healthy, warning, error
    total_posts_published: int = Field(default=0)
    
    # 连接配置（存储在数据库中的配置选项）
    connection_timeout: int = Field(default=120)
    max_retries: int = Field(default=3)
    
    # 时间戳 - 使用timezone-aware默认值
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    
    def __str__(self) -> str:
        return f"Site(id={self.id}, name={self.name}, status={self.health_status})"
    
    def is_healthy(self) -> bool:
        """检查站点是否健康"""
        return self.health_status == "healthy" and self.is_active