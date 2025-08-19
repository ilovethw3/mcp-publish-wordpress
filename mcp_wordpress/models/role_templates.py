"""角色模板数据库模型和预定义角色配置"""

from sqlmodel import SQLModel, Field, Column, JSON
from sqlalchemy import String
from datetime import datetime
from typing import Dict, List, Optional


class RoleTemplate(SQLModel, table=True):
    """角色模板表"""
    
    __tablename__ = "role_templates"
    
    # 内部自增主键，仅用于SQLAlchemy要求
    internal_id: Optional[int] = Field(primary_key=True, default=None)
    # 业务主键，允许重复（用于逻辑删除场景）
    id: str = Field(max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = None
    permissions: Dict = Field(sa_column=Column(JSON), default_factory=dict)
    quota_limits: Dict = Field(sa_column=Column(JSON), default_factory=dict)
    is_system_role: bool = Field(default=False)
    is_active: bool = Field(default=True)
    created_by: Optional[str] = Field(max_length=50, default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    deleted_at: Optional[datetime] = Field(default=None)


class RoleTemplateHistory(SQLModel, table=True):
    """角色模板变更历史表"""
    
    __tablename__ = "role_template_history"
    
    id: Optional[int] = Field(primary_key=True, default=None)
    role_template_id: str = Field(max_length=50)
    action: str = Field(max_length=20)  # 'created', 'updated', 'deleted'
    old_config: Optional[Dict] = Field(sa_column=Column(JSON), default=None)
    new_config: Optional[Dict] = Field(sa_column=Column(JSON), default=None)
    changed_by: Optional[str] = Field(max_length=50, default=None)
    created_at: datetime = Field(default_factory=datetime.utcnow)


# 系统预定义角色模板
SYSTEM_ROLE_TEMPLATES = {
    "content_creator": {
        "name": "内容创建者",
        "description": "专注于创建和编辑内容的基础角色",
        "permissions": {
            "can_submit_articles": True,
            "can_edit_own_articles": True,
            "can_view_statistics": True,
            "can_approve_articles": False,
            "can_publish_articles": False,
            "can_edit_others_articles": False,
            "can_review_agents": [],
            "allowed_categories": [],
            "allowed_tags": []
        },
        "quota_limits": {
            "daily_articles": 5,
            "monthly_articles": 100,
            "working_hours": {
                "enabled": False
            }
        }
    },
    
    "content_reviewer": {
        "name": "内容审核者", 
        "description": "负责审核和批准内容的角色",
        "permissions": {
            "can_submit_articles": False,
            "can_edit_own_articles": False,
            "can_view_statistics": True,
            "can_approve_articles": True,
            "can_publish_articles": False,
            "can_edit_others_articles": True,
            "can_review_agents": [],
            "allowed_categories": [],
            "allowed_tags": []
        },
        "quota_limits": {
            "daily_articles": 50,  # 可审核更多文章
            "monthly_articles": 1000,
            "working_hours": {
                "enabled": False
            }
        }
    },
    
    "content_publisher": {
        "name": "内容发布者",
        "description": "负责发布内容到WordPress站点",
        "permissions": {
            "can_submit_articles": False,
            "can_edit_own_articles": False,
            "can_view_statistics": True,
            "can_approve_articles": False,
            "can_publish_articles": True,
            "can_edit_others_articles": False,
            "can_review_agents": [],
            "allowed_categories": [],
            "allowed_tags": []
        },
        "quota_limits": {
            "daily_articles": 50,
            "monthly_articles": 1000,
            "working_hours": {
                "enabled": False
            }
        }
    },
    
    "content_manager": {
        "name": "内容管理者",
        "description": "具有完整内容管理权限的角色",
        "permissions": {
            "can_submit_articles": True,
            "can_edit_own_articles": True,
            "can_edit_others_articles": True,
            "can_approve_articles": True,
            "can_publish_articles": True,
            "can_view_statistics": True,
            "can_review_agents": [],
            "allowed_categories": [],
            "allowed_tags": []
        },
        "quota_limits": {
            "daily_articles": 0,    # 0表示无限制
            "monthly_articles": 0,
            "working_hours": {
                "enabled": False
            }
        }
    }
}