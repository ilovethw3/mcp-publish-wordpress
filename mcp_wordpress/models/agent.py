"""
Agent model for MCP WordPress Publisher v2.1

This module defines the Agent data model for multi-agent authentication
and management in the MCP WordPress publishing system.
"""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field, Column, DateTime, func


class Agent(SQLModel, table=True):
    """Agent model for multi-agent system
    
    Represents an AI agent that can connect to the MCP server
    and perform content operations.
    """
    __tablename__ = "agents"
    
    id: str = Field(primary_key=True, max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    role: str = Field(max_length=50)  # content-creator, seo-optimizer, editor等
    api_key_hash: str = Field(max_length=255)  # 存储API密钥的哈希值
    
    # 状态信息
    is_active: bool = Field(default=True)
    last_seen: Optional[datetime] = None
    total_articles_submitted: int = Field(default=0)
    
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
        return f"Agent(id={self.id}, name={self.name}, role={self.role})"