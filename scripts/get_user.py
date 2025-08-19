#!/usr/bin/env python3
"""
Get user script for Next.js API routes
Returns single user by ID
"""

import sys
import json
import asyncio
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mcp_wordpress.services.user_service import user_service


async def get_user(user_id: int):
    """Get user by ID"""
    try:
        user = await user_service.get_user_by_id(user_id)
        
        if user:
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
                'user': user_dict
            }
        else:
            return {
                'success': False,
                'error': '用户不存在'
            }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    if len(sys.argv) != 2:
        print(json.dumps({
            'success': False,
            'error': '参数不足'
        }))
        sys.exit(1)
    
    user_id = int(sys.argv[1])
    
    result = asyncio.run(get_user(user_id))
    print(json.dumps(result))


if __name__ == '__main__':
    main()