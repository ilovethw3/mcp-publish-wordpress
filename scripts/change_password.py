#!/usr/bin/env python3
"""
Change password script for Next.js API routes
Changes user password
"""

import sys
import json
import asyncio
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mcp_wordpress.services.user_service import user_service


async def change_password(user_id: int, new_password: str):
    """Change user password"""
    try:
        success = await user_service.change_password(user_id, new_password)
        
        if success:
            return {
                'success': True,
                'message': '密码修改成功'
            }
        else:
            return {
                'success': False,
                'error': '密码修改失败'
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
    new_password = sys.argv[2]
    
    result = asyncio.run(change_password(user_id, new_password))
    print(json.dumps(result))


if __name__ == '__main__':
    main()