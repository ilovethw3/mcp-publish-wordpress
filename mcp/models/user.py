from sqlmodel import SQLModel, Field
from typing import Optional
from datetime import datetime


class UserBase(SQLModel):
    username: str = Field(
        index=True, 
        unique=True, 
        min_length=3, 
        max_length=50,
        description="用户名，用于登录认证"
    )
    is_active: bool = Field(default=True, description="用户是否激活")


class UserCreate(UserBase):
    password: str = Field(min_length=8, description="用户密码，至少8位")


class UserUpdate(SQLModel):
    username: Optional[str] = Field(default=None, min_length=3, max_length=50)
    password: Optional[str] = Field(default=None, min_length=8)
    is_active: Optional[bool] = Field(default=None)


class User(UserBase, table=True):
    __tablename__ = "users"
    
    id: Optional[int] = Field(default=None, primary_key=True, description="用户ID")
    hashed_password: str = Field(description="哈希后的密码")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="更新时间")


class UserResponse(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime