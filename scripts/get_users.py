#!/usr/bin/env python3
"""
Get users script for Next.js API routes
Returns list of users with pagination and filtering
"""

import sys
import json
import asyncio
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mcp_wordpress.services.user_service import user_service


async def get_users(skip: int, limit: int, search: str = None, is_active: str = None):
    """Get users with filtering"""
    try:
        is_active_bool = None
        if is_active is not None:
            is_active_bool = is_active.lower() == 'true'
        
        users = await user_service.get_all_users(
            skip=skip,
            limit=limit,
            search=search if search else None,
            is_active=is_active_bool
        )
        
        # Get total count
        total_count = await user_service.get_user_count(is_active=is_active_bool)
        
        # Convert users to dict
        users_dict = []
        for user in users:
            users_dict.append({
                'id': user.id,
                'username': user.username,
                'email': user.email,
                'is_reviewer': user.is_reviewer,
                'is_active': user.is_active,
                'last_login': user.last_login.isoformat() if user.last_login else None,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            })
        
        return {
            'success': True,
            'data': {
                'users': users_dict,
                'total': total_count,
                'skip': skip,
                'limit': limit
            }
        }
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def main():
    if len(sys.argv) < 4:
        print(json.dumps({
            'success': False,
            'error': '参数不足'
        }))
        sys.exit(1)
    
    skip = int(sys.argv[1])
    limit = int(sys.argv[2])
    search = sys.argv[3] if sys.argv[3] else None
    is_active = sys.argv[4] if len(sys.argv) > 4 else None
    
    result = asyncio.run(get_users(skip, limit, search, is_active))
    print(json.dumps(result))


if __name__ == '__main__':
    main()