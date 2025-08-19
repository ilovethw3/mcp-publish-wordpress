#!/usr/bin/env python3
"""
Delete user script for Next.js API routes
Soft deletes user (marks as inactive)
"""

import sys
import json
import asyncio
import os
import logging

# Disable all logging output to stdout to keep clean JSON response
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


async def delete_user(user_id: int):
    """Delete user (soft delete)"""
    try:
        success = await user_service.delete_user(user_id)
        
        if success:
            return {
                'success': True,
                'message': '用户已删除'
            }
        else:
            return {
                'success': False,
                'error': '删除用户失败'
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
    
    result = asyncio.run(delete_user(user_id))
    print(json.dumps(result))


if __name__ == '__main__':
    main()