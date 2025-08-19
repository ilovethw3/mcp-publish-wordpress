"""
Agent model for MCP WordPress Publisher v2.1

This module defines the Agent data model for multi-agent authentication
and management in the MCP WordPress publishing system.
"""

from datetime import datetime, timezone
from typing import Optional, List
from sqlmodel import SQLModel, Field, Column, DateTime, func, JSON


class Agent(SQLModel, table=True):
    """Agent model for multi-agent system
    
    Represents an AI agent that can connect to the MCP server
    and perform content operations.
    """
    __tablename__ = "agents"
    
    id: str = Field(primary_key=True, max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    api_key_hash: str = Field(max_length=255)  # 存储API密钥的哈希值
    api_key_display: str = Field(default="", max_length=100)  # 掩码显示的API密钥
    status: str = Field(default="active")  # active, inactive, locked
    
    # 速率限制配置
    rate_limit: dict = Field(default_factory=lambda: {
        "requests_per_minute": 10,
        "requests_per_hour": 100,
        "requests_per_day": 500
    }, sa_column=Column(JSON))
    
    # 权限配置
    permissions: dict = Field(default_factory=lambda: {
        "can_submit_articles": True,
        "can_edit_own_articles": True,
        "can_view_statistics": True,
        "can_approve_articles": False,
        "can_publish_articles": False,
        "can_edit_others_articles": False,
        "can_review_agents": [],
        "allowed_categories": [],
        "allowed_tags": []
    }, sa_column=Column(JSON))
    
    # 通知配置
    notifications: dict = Field(default_factory=lambda: {
        "on_approval": False,
        "on_rejection": True,
        "on_publish_success": True,
        "on_publish_failure": True
    }, sa_column=Column(JSON))
    
    # 角色模板关联 (v3.0新增)
    role_template_id: Optional[str] = Field(default=None, foreign_key="role_templates.id", max_length=50)
    permissions_override: dict = Field(default_factory=dict, sa_column=Column(JSON))
    
    # 统计信息
    total_articles_submitted: int = Field(default=0)
    total_articles_published: int = Field(default=0)
    total_articles_rejected: int = Field(default=0)
    last_seen: Optional[datetime] = None
    first_submission: Optional[datetime] = None
    last_submission: Optional[datetime] = None
    
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
        if self.total_articles_submitted == 0:
            return 0.0
        return (self.total_articles_published / self.total_articles_submitted) * 100
    
    @property
    def is_active(self) -> bool:
        """检查代理是否活跃"""
        return self.status == "active"
    
    def __str__(self) -> str:
        return f"Agent(id={self.id}, name={self.name}, status={self.status})"