#!/usr/bin/env python3
"""Direct tool testing without MCP protocol layer."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from mcp_wordpress.tools.articles import submit_article, list_articles
from mcp_wordpress.core.database import create_db_and_tables


async def test_direct_tools():
    """Test tools directly without MCP protocol."""
    print("🧪 Testing tools directly...")
    
    # Ensure DB tables exist
    create_db_and_tables()
    
    try:
        # Test list_articles directly
        print("\n🔍 Testing list_articles...")
        result = await list_articles()
        print(f"✅ list_articles result: {result}")
        
        # Test submit_article directly 
        print("\n📝 Testing submit_article...")
        result = await submit_article(
            title="Test Article Direct",
            content="This is a test article submitted directly",
            category="test"
        )
        print(f"✅ submit_article result: {result}")
        
        print("\n✅ All direct tool tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Direct tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    asyncio.run(test_direct_tools())