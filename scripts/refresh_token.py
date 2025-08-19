#!/usr/bin/env python3
"""
Token refresh script for Next.js API routes
Refreshes JWT token and returns new token
"""

import sys
import json
import asyncio
import os

# Add the project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from mcp_wordpress.auth.jwt_auth import jwt_auth


async def refresh_token(token: str):
    """Refresh JWT token"""
    try:
        new_token = jwt_auth.refresh_token(token)
        
        if new_token:
            return {
                'success': True,
                'token': new_token
            }
        else:
            return {
                'success': False,
                'error': 'Token无效或已过期'
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
    
    token = sys.argv[1]
    
    result = asyncio.run(refresh_token(token))
    print(json.dumps(result))


if __name__ == '__main__':
    main()