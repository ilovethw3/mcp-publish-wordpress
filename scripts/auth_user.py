#!/usr/bin/env python3
"""
Authentication script for Next.js API routes
Authenticates user and returns JSON response
"""

import sys
import json
import asyncio
import os
import logging

# Disable all logging output to stdout to keep clean JSON response
import logging
logging.getLogger().setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.engine').setLevel(logging.CRITICAL)
logging.getLogger('sqlalchemy.engine.Engine').setLevel(logging.CRITICAL)
logging.basicConfig(level=logging.CRITICAL)

# Suppress all possible logging outputs
import warnings
warnings.filterwarnings("ignore")

# Set all known loggers to CRITICAL
for logger_name in ['sqlalchemy', 'sqlalchemy.engine', 'sqlalchemy.pool', 'sqlalchemy.dialects']:
    logging.getLogger(logger_name).setLevel(logging.CRITICAL)

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mcp_wordpress.services.user_service import user_service
from mcp_wordpress.auth.jwt_auth import jwt_auth


async def authenticate_user(username: str, password: str):
    """Authenticate user and return result"""
    try:
        user, token = await user_service.authenticate_user(username, password)
        
        if user and token:
            # Convert user to dict
            user_dict = {
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_reviewer': user.is_reviewer,
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            }
            
            return {
                'success': True,
                'user': user_dict,
                'token': token
            }
        else:
            return {
                'success': False,
                'error': '用户名或密码错误'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    if len(sys.argv) != 3:
        print(json.dumps({
            'success': False,
            'error': '参数不足'
        }))
        sys.exit(1)
    
    username = sys.argv[1]
    password = sys.argv[2]
    
    result = asyncio.run(authenticate_user(username, password))
    print(json.dumps(result))


if __name__ == '__main__':
    main()