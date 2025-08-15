"""
Site model for MCP WordPress Publisher v2.1

This module defines the Site data model for multi-site WordPress
publishing management.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime, func, JSON


class Site(SQLModel, table=True):
    """Site model for multi-site WordPress publishing
    
    Represents a WordPress site that can receive published content
    from the MCP system.
    """
    __tablename__ = "sites"
    
    id: str = Field(primary_key=True, max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    status: str = Field(default="active")  # active, inactive
    health_status: str = Field(default="unknown")  # healthy, warning, error, unknown
    
    # WordPress配置
    wordpress_config: dict = Field(default_factory=lambda: {
        "api_url": "",
        "username": "",
        "app_password_hash": "",  # 存储加密的应用密码
        "default_status": "publish",
        "default_comment_status": "open",
        "default_ping_status": "open",
        "category_mapping": {},
        "tag_auto_create": True
    }, sa_column=Column(JSON))
    
    # 发布规则
    publishing_rules: dict = Field(default_factory=lambda: {
        "allowed_agents": [],
        "allowed_categories": [],
        "min_word_count": 100,
        "max_word_count": 5000,
        "require_featured_image": False,
        "auto_approve": False,
        "auto_publish_approved": True
    }, sa_column=Column(JSON))
    
    # 速率限制
    rate_limit: dict = Field(default_factory=lambda: {
        "max_posts_per_hour": 10,
        "max_posts_per_day": 50,
        "max_concurrent_publishes": 2
    }, sa_column=Column(JSON))
    
    # 通知配置
    notifications: dict = Field(default_factory=lambda: {
        "on_publish_success": True,
        "on_publish_failure": True,
        "on_connection_error": True
    }, sa_column=Column(JSON))
    
    # 统计信息
    total_posts_published: int = Field(default=0)
    total_posts_failed: int = Field(default=0)
    last_health_check: Optional[datetime] = None
    last_publish: Optional[datetime] = None
    
    # 连接配置
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
    
    @property
    def success_rate(self) -> float:
        """计算发布成功率"""
        total_attempts = self.total_posts_published + self.total_posts_failed
        if total_attempts == 0:
            return 0.0
        return (self.total_posts_published / total_attempts) * 100
    
    @property 
    def is_active(self) -> bool:
        """检查站点是否活跃"""
        return self.status == "active"
    
    def is_healthy(self) -> bool:
        """检查站点是否健康"""
        return self.health_status == "healthy" and self.is_active
    
    def __str__(self) -> str:
        return f"Site(id={self.id}, name={self.name}, status={self.health_status})"