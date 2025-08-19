"""User model for authentication."""

from datetime import datetime, timezone
from typing import Optional
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, DateTime
from sqlalchemy.sql import func


class User(SQLModel, table=True):
    """User database model."""
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(unique=True, max_length=50, description="Username")
    email: str = Field(unique=True, max_length=255, description="Email address")
    password_hash: str = Field(description="Hashed password")
    is_active: bool = Field(default=True, description="Whether user is active")
    is_reviewer: bool = Field(default=False, description="Whether user can review articles")
    last_login: Optional[datetime] = Field(
        default=None,
        description="Last login timestamp",
        sa_column=Column(DateTime(timezone=True), nullable=True)
    )
    
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