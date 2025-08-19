"""
User Service for MCP WordPress Publisher v2.1

This module provides user management functionality including authentication,
password hashing, and user CRUD operations.
"""

from datetime import datetime, timezone
from typing import Dict, List, Optional, Any, Tuple
from sqlmodel import select, and_
from sqlalchemy.exc import IntegrityError
import bcrypt
import jwt
import secrets
from datetime import timedelta

from mcp_wordpress.core.database import get_session
from mcp_wordpress.models.user import User
from mcp_wordpress.core.errors import (
    ValidationError,
    MCPError,
    MCPErrorCodes
)


class UserService:
    """Service for managing user operations"""
    
    def __init__(self, jwt_secret: str = None):
        self.jwt_secret = jwt_secret or secrets.token_urlsafe(32)
        self.jwt_algorithm = 'HS256'
        self.token_expire_hours = 24
    
    @staticmethod
    def _hash_password(password: str) -> str:
        """Hash password using bcrypt"""
        salt = bcrypt.gensalt()
        return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
    
    @staticmethod
    def _verify_password(password: str, password_hash: str) -> bool:
        """Verify password against hash"""
        return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
    
    def _generate_jwt_token(self, user: User) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'is_reviewer': user.is_reviewer,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expire_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.jwt_secret, algorithm=self.jwt_algorithm)
    
    def _verify_jwt_token(self, token: str) -> Optional[Dict]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            return None
        except jwt.InvalidTokenError:
            return None
    
    async def create_user(
        self,
        username: str,
        email: str,
        password: str,
        is_reviewer: bool = False
    ) -> User:
        """Create a new user"""
        if len(password) < 8:
            raise ValidationError("password", "密码长度至少为8位")
        
        if not username or len(username) < 3:
            raise ValidationError("username", "用户名长度至少为3位")
        
        if not email or '@' not in email:
            raise ValidationError("email", "请输入有效的邮箱地址")
        
        password_hash = self._hash_password(password)
        
        user = User(
            username=username,
            email=email,
            password_hash=password_hash,
            is_reviewer=is_reviewer,
            is_active=True
        )
        
        try:
            async with get_session() as session:
                session.add(user)
                await session.commit()
                await session.refresh(user)
                return user
        except IntegrityError:
            raise ValidationError("username", "用户名或邮箱已存在")
    
    async def authenticate_user(self, username: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        """Authenticate user and return user object with JWT token"""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(
                    and_(
                        User.username == username,
                        User.is_active == True
                    )
                )
            )
            user = result.scalar_one_or_none()
            
            if not user or not self._verify_password(password, user.password_hash):
                return None, None
            
            # Update last login
            user.last_login = datetime.now(timezone.utc)
            user.updated_at = datetime.now(timezone.utc)
            await session.commit()
            
            # Generate JWT token
            token = self._generate_jwt_token(user)
            
            return user, token
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
    
    async def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.username == username)
            )
            return result.scalar_one_or_none()
    
    async def get_current_user_from_token(self, token: str) -> Optional[User]:
        """Get current user from JWT token"""
        payload = self._verify_jwt_token(token)
        if not payload:
            return None
        
        user_id = payload.get('user_id')
        if not user_id:
            return None
        
        return await self.get_user_by_id(user_id)
    
    async def get_all_users(
        self,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        is_active: Optional[bool] = None
    ) -> List[User]:
        """Get all users with optional filtering"""
        async with get_session() as session:
            query = select(User)
            
            if search:
                search_term = f"%{search}%"
                query = query.where(
                    User.username.ilike(search_term) |
                    User.email.ilike(search_term)
                )
            
            if is_active is not None:
                query = query.where(User.is_active == is_active)
            
            query = query.offset(skip).limit(limit).order_by(User.created_at.desc())
            
            result = await session.execute(query)
            return result.scalars().all()
    
    async def update_user(
        self,
        user_id: int,
        username: Optional[str] = None,
        email: Optional[str] = None,
        is_reviewer: Optional[bool] = None,
        is_active: Optional[bool] = None
    ) -> User:
        """Update user information"""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValidationError("user", "用户不存在")
            
            if username is not None:
                if len(username) < 3:
                    raise ValidationError("username", "用户名长度至少为3位")
                user.username = username
            
            if email is not None:
                if not email or '@' not in email:
                    raise ValidationError("email", "请输入有效的邮箱地址")
                user.email = email
            
            if is_reviewer is not None:
                user.is_reviewer = is_reviewer
            
            if is_active is not None:
                user.is_active = is_active
            
            user.updated_at = datetime.now(timezone.utc)
            
            try:
                await session.commit()
                await session.refresh(user)
                return user
            except IntegrityError:
                raise ValidationError("username", "用户名或邮箱已存在")
    
    async def change_password(self, user_id: int, new_password: str) -> bool:
        """Change user password"""
        if len(new_password) < 8:
            raise ValidationError("password", "密码长度至少为8位")
        
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValidationError("user", "用户不存在")
            
            user.password_hash = self._hash_password(new_password)
            user.updated_at = datetime.now(timezone.utc)
            
            await session.commit()
            return True
    
    async def delete_user(self, user_id: int) -> bool:
        """Soft delete user (mark as inactive and modify unique fields)"""
        async with get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                raise ValidationError("user", "用户不存在")
            
            # 防止重复删除
            if not user.is_active:
                raise ValidationError("user", "用户已被删除")
            
            # 软删除：标记为非活跃并修改唯一字段以避免约束冲突
            current_time = datetime.now(timezone.utc)
            timestamp = int(current_time.timestamp())
            
            user.is_active = False
            user.username = f"{user.username}_deleted_{timestamp}"
            user.email = f"{user.email}_deleted_{timestamp}"
            user.updated_at = current_time
            
            await session.commit()
            return True
    
    async def get_user_count(self, is_active: Optional[bool] = None) -> int:
        """Get total user count"""
        async with get_session() as session:
            query = select(User.id)
            
            if is_active is not None:
                query = query.where(User.is_active == is_active)
            
            result = await session.execute(query)
            users = result.scalars().all()
            return len(users)


# Global user service instance
user_service = UserService()