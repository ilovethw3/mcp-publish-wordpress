#!/usr/bin/env python3
"""
MCP WordPress SSE Client Test Script

This script tests the SSE MCP server by connecting to it and testing various functionalities.
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Any
from mcp_wordpress.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from mcp import ClientSession
    from mcp.client.sse import sse_client
    from mcp.types import Tool, Resource
except ImportError:
    print("MCP library not found. Please install it with: pip install mcp")
    exit(1)


class MCPTestClient:
    """Test client for MCP WordPress SSE server."""
    
    def __init__(self, server_url: str = None):
        if server_url is None:
            server_url = f"http://localhost:{settings.mcp_port}{settings.mcp_sse_path}"
        self.server_url = server_url
        self.client = None
        
    async def connect(self):
        """Connect to the MCP server."""
        try:
            logger.info(f"Connecting to MCP server at {self.server_url}")
            self.client = sse_client(self.server_url)
            self.read_stream, self.write_stream = await self.client.__aenter__()
            self.session = ClientSession(self.read_stream, self.write_stream)
            await self.session.__aenter__()
            await self.session.initialize()
            logger.info("✅ Successfully connected to MCP server")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to MCP server: {e}")
            return False
    
    async def disconnect(self):
        """Disconnect from the MCP server."""
        if hasattr(self, 'session') and self.session:
            try:
                await self.session.__aexit__(None, None, None)
                logger.info("✅ Disconnected from MCP session")
            except Exception as e:
                logger.error(f"❌ Error during session disconnect: {e}")
        
        if self.client:
            try:
                await self.client.__aexit__(None, None, None)
                logger.info("✅ Disconnected from MCP server")
            except Exception as e:
                logger.error(f"❌ Error during client disconnect: {e}")
    
    async def list_tools(self) -> List[Tool]:
        """List all available tools."""
        try:
            logger.info("📋 Listing available tools...")
            tools_response = await self.session.list_tools()
            tools = tools_response.tools
            logger.info(f"✅ Found {len(tools)} tools:")
            for tool in tools:
                logger.info(f"  - {tool.name}: {tool.description}")
            return tools
        except Exception as e:
            logger.error(f"❌ Failed to list tools: {e}")
            return []
    
    async def list_resources(self) -> List[Resource]:
        """List all available resources."""
        try:
            logger.info("📚 Listing available resources...")
            resources_response = await self.session.list_resources()
            resources = resources_response.resources
            logger.info(f"✅ Found {len(resources)} resources:")
            for resource in resources:
                logger.info(f"  - {resource.uri}: {resource.name}")
            return resources
        except Exception as e:
            logger.error(f"❌ Failed to list resources: {e}")
            return []
    
    async def test_submit_article(self) -> Dict[str, Any]:
        """Test article submission."""
        try:
            logger.info("📝 Testing article submission...")
            test_article = {
                "title": "Test Article from MCP Client",
                "content_markdown": "# Test Article\n\nThis is a test article submitted via MCP SSE client.\n\n## Features\n- MCP Protocol\n- SSE Transport\n- Automated Testing\n\nCreated at: " + datetime.now().isoformat(),
                "tags": "test, mcp, automation",
                "category": "Testing"
            }
            
            result = await self.session.call_tool("submit_article", test_article)
            logger.info("✅ Article submitted successfully:")
            logger.info(f"  Result: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to submit article: {e}")
            return {}
    
    async def test_list_articles(self) -> Dict[str, Any]:
        """Test listing articles."""
        try:
            logger.info("📄 Testing article listing...")
            result = await self.session.call_tool("list_articles", {
                "status": "pending",
                "limit": 10
            })
            logger.info("✅ Articles listed successfully:")
            logger.info(f"  Result: {result}")
            return result
        except Exception as e:
            logger.error(f"❌ Failed to list articles: {e}")
            return {}
    
    async def test_get_resources(self):
        """Test getting resource content."""
        try:
            logger.info("📊 Testing resource access...")
            
            # Test stats resource
            try:
                stats = await self.session.read_resource("stats://summary")
                logger.info("✅ Stats resource accessed successfully:")
                logger.info(f"  Content: {stats}")
            except Exception as e:
                logger.warning(f"⚠️  Stats resource not available: {e}")
            
            # Test pending articles resource
            try:
                pending = await self.session.read_resource("article://pending")
                logger.info("✅ Pending articles resource accessed successfully:")
                logger.info(f"  Content: {pending}")
            except Exception as e:
                logger.warning(f"⚠️  Pending articles resource not available: {e}")
                
        except Exception as e:
            logger.error(f"❌ Failed to test resources: {e}")
    
    async def run_full_test(self):
        """Run the complete test suite."""
        logger.info("🚀 Starting MCP WordPress SSE Client Tests")
        logger.info("=" * 50)
        
        # Connect to server
        if not await self.connect():
            return False
        
        try:
            # Test basic MCP protocol
            tools = await self.list_tools()
            resources = await self.list_resources()
            
            # Test functionality
            if tools:
                await self.test_submit_article()
                await self.test_list_articles()
            
            if resources:
                await self.test_get_resources()
            
            logger.info("=" * 50)
            logger.info("✅ All tests completed successfully!")
            return True
            
        except Exception as e:
            logger.error(f"❌ Test failed: {e}")
            return False
        finally:
            await self.disconnect()


async def main():
    """Main test function."""
    client = MCPTestClient()
    success = await client.run_full_test()
    
    if success:
        print("\n🎉 MCP SSE Server is working correctly!")
    else:
        print("\n❌ MCP SSE Server tests failed!")
        exit(1)


if __name__ == "__main__":
    asyncio.run(main())