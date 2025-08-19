#!/usr/bin/env python3
"""
Update user script for Next.js API routes
Updates user information
"""

import sys
import json
import asyncio
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mcp_wordpress.services.user_service import user_service


async def update_user(user_id: int, update_data: dict):
    """Update user"""
    try:
        user = await user_service.update_user(
            user_id=user_id,
            username=update_data.get('username'),
            email=update_data.get('email'),
            is_reviewer=update_data.get('is_reviewer'),
            is_active=update_data.get('is_active')
        )
        
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
    
    user_id = int(sys.argv[1])
    update_data = json.loads(sys.argv[2])
    
    result = asyncio.run(update_user(user_id, update_data))
    print(json.dumps(result))


if __name__ == '__main__':
    main()