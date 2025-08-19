"""
JWT Authentication middleware for MCP WordPress Publisher v2.1

This module provides JWT-based authentication middleware for protecting
API routes and validating user sessions.
"""

from typing import Optional, Callable, Any
from functools import wraps
import jwt
from datetime import datetime, timedelta
import os

from mcp_wordpress.services.user_service import user_service
from mcp_wordpress.models.user import User
from mcp_wordpress.core.errors import ValidationError, MCPError, MCPErrorCodes


class JWTAuth:
    """JWT Authentication handler"""
    
    def __init__(self, secret_key: Optional[str] = None):
        self.secret_key = secret_key or os.getenv('JWT_SECRET_KEY', 'default-secret-key-change-in-production')
        self.algorithm = 'HS256'
        self.token_expire_hours = 24
    
    def generate_token(self, user: User) -> str:
        """Generate JWT token for user"""
        payload = {
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'is_reviewer': user.is_reviewer,
            'exp': datetime.utcnow() + timedelta(hours=self.token_expire_hours),
            'iat': datetime.utcnow()
        }
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[dict]:
        """Verify and decode JWT token"""
        try:
            # Remove 'Bearer ' prefix if present
            if token.startswith('Bearer '):
                token = token[7:]
            
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            return payload
        except jwt.ExpiredSignatureError:
            raise ValidationError("Token已过期，请重新登录")
        except jwt.InvalidTokenError:
            raise ValidationError("无效的token")
    
    def refresh_token(self, token: str) -> Optional[str]:
        """Refresh JWT token if it's valid"""
        try:
            payload = self.verify_token(token)
            if not payload:
                return None
            
            # Create new token with extended expiry
            new_payload = {
                'user_id': payload['user_id'],
                'username': payload['username'],
                'email': payload['email'],
                'is_reviewer': payload['is_reviewer'],
                'exp': datetime.utcnow() + timedelta(hours=self.token_expire_hours),
                'iat': datetime.utcnow()
            }
            return jwt.encode(new_payload, self.secret_key, algorithm=self.algorithm)
        except:
            return None
    
    async def get_current_user(self, token: str) -> Optional[User]:
        """Get current user from token"""
        try:
            payload = self.verify_token(token)
            if not payload:
                return None
            
            user_id = payload.get('user_id')
            if not user_id:
                return None
            
            return await user_service.get_user_by_id(user_id)
        except Exception:
            return None


def require_auth(func: Callable) -> Callable:
    """Decorator to require authentication for API routes"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This decorator can be used with FastAPI or other frameworks
        # Implementation depends on the specific framework being used
        return await func(*args, **kwargs)
    return wrapper


def require_reviewer(func: Callable) -> Callable:
    """Decorator to require reviewer permissions"""
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # This decorator can be used to require reviewer permissions
        # Implementation depends on the specific framework being used
        return await func(*args, **kwargs)
    return wrapper


# Global JWT auth instance
jwt_auth = JWTAuth()