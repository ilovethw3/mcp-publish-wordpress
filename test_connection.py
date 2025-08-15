#!/usr/bin/env python3
"""
Simple MCP SSE Connection Test

This script performs basic connectivity tests to ensure the SSE server is reachable
and responding to MCP protocol messages.
"""

import asyncio
import aiohttp
import logging
import os
from datetime import datetime
from mcp_wordpress.core.config import settings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Test configuration - Use Web UI agent key from environment
TEST_AGENT_KEY = os.getenv('WEB_UI_AGENT_API_KEY', os.getenv('TEST_AGENT_KEY', 'webui_vs6VPQa4qkopdwbBJZMjNRwIRwnYqBm2279yN0mRXec'))


async def test_http_connectivity(url: str = "http://localhost:8000") -> bool:
    """Test basic HTTP connectivity to the server."""
    try:
        logger.info(f"Testing HTTP connectivity to {url}")
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=5)) as response:
                logger.info(f"✅ HTTP connection successful - Status: {response.status}")
                return True
    except asyncio.TimeoutError:
        logger.error("❌ HTTP connection timeout")
        return False
    except aiohttp.ClientConnectorError as e:
        logger.error(f"❌ HTTP connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected HTTP error: {e}")
        return False


async def test_sse_endpoint(url: str = None) -> bool:
    """Test SSE endpoint availability."""
    if url is None:
        url = f"http://localhost:{settings.mcp_port}{settings.mcp_sse_path}"
    try:
        logger.info(f"Testing SSE endpoint: {url}")
        async with aiohttp.ClientSession() as session:
            headers = {
                'Accept': 'text/event-stream',
                'Cache-Control': 'no-cache',
                'Authorization': f'Bearer {TEST_AGENT_KEY}',
            }
            async with session.get(url, headers=headers, timeout=aiohttp.ClientTimeout(total=5)) as response:
                logger.info(f"✅ SSE endpoint accessible - Status: {response.status}")
                logger.info(f"Content-Type: {response.headers.get('Content-Type', 'Not set')}")
                return response.status == 200
    except asyncio.TimeoutError:
        logger.error("❌ SSE endpoint timeout")
        return False
    except aiohttp.ClientConnectorError as e:
        logger.error(f"❌ SSE endpoint connection failed: {e}")
        return False
    except Exception as e:
        logger.error(f"❌ Unexpected SSE error: {e}")
        return False


async def test_mcp_client_connection() -> bool:
    """Test MCP client connection capability."""
    try:
        logger.info("Testing MCP client connection...")
        from mcp import ClientSession
        from mcp.client.sse import sse_client
        
        logger.info("✅ MCP client libraries imported successfully")
        
        # Test actual connection with Bearer Token
        try:
            headers = {"Authorization": f"Bearer {TEST_AGENT_KEY}"}
            async with sse_client(f"http://localhost:{settings.mcp_port}{settings.mcp_sse_path}", headers=headers) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    await session.initialize()
                    logger.info("✅ MCP SSE client connected successfully")
                    
                    # Try to make a basic MCP call
                    tools_response = await session.list_tools()
                    tools = tools_response.tools
                    logger.info(f"✅ MCP protocol working - Found {len(tools)} tools")
                    return True
        except Exception as e:
            logger.error(f"❌ MCP protocol error: {e}")
            return False
            
    except ImportError:
        logger.error("❌ MCP library not installed. Run: pip install mcp")
        return False
    except Exception as e:
        logger.error(f"❌ MCP client test failed: {e}")
        return False


async def test_docker_services() -> bool:
    """Test if Docker services are running."""
    try:
        import subprocess
        logger.info("Checking Docker services status...")
        
        # Check if docker-compose services are running
        result = subprocess.run(
            ["docker-compose", "ps", "--services", "--filter", "status=running"],
            capture_output=True,
            text=True,
            cwd="/home/tian/claudecode/mcp-publish-wordpress"
        )
        
        if result.returncode == 0:
            running_services = result.stdout.strip().split('\n')
            logger.info(f"✅ Docker services running: {running_services}")
            
            # Check specifically for our services
            expected_services = ["postgres", "mcp-server-sse"]
            missing_services = []
            for service in expected_services:
                if not any(service in running for running in running_services):
                    missing_services.append(service)
            
            if missing_services:
                logger.warning(f"⚠️  Missing services: {missing_services}")
                return False
            else:
                logger.info("✅ All expected services are running")
                return True
        else:
            logger.error("❌ Failed to check Docker services")
            return False
            
    except FileNotFoundError:
        logger.error("❌ docker-compose not found")
        return False
    except Exception as e:
        logger.error(f"❌ Docker services check failed: {e}")
        return False


async def main():
    """Run all connection tests."""
    logger.info("🧪 Starting MCP SSE Connection Tests")
    logger.info("=" * 50)
    logger.info(f"🔑 Using test agent key: {TEST_AGENT_KEY[:20]}...")  # Only show first 20 chars for security
    
    tests = [
        ("Docker Services", test_docker_services()),
        ("HTTP Connectivity", test_http_connectivity()),
        ("SSE Endpoint", test_sse_endpoint()),
        ("MCP Client Connection", test_mcp_client_connection()),
    ]
    
    results = {}
    for test_name, test_coro in tests:
        logger.info(f"\n🔍 Running: {test_name}")
        try:
            result = await test_coro
            results[test_name] = result
            if result:
                logger.info(f"✅ {test_name}: PASSED")
            else:
                logger.error(f"❌ {test_name}: FAILED")
        except Exception as e:
            logger.error(f"❌ {test_name}: ERROR - {e}")
            results[test_name] = False
    
    # Summary
    logger.info("\n" + "=" * 50)
    logger.info("📊 Test Results Summary:")
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"  {test_name}: {status}")
    
    logger.info(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All connection tests passed! SSE server is ready for use.")
        return True
    else:
        print(f"\n❌ {total - passed} test(s) failed. Please check the logs above.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)