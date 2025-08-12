"""
End-to-end integration tests for MCP WordPress Publisher v2.1
Tests the complete workflow from article submission to WordPress publishing
"""
import asyncio
import pytest
import httpx
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch
import os

# Test configuration
TEST_CONFIG = {
    'mcp_server_url': os.getenv('TEST_MCP_SERVER_URL', 'http://localhost:8000'),
    'web_ui_url': os.getenv('TEST_WEB_UI_URL', 'http://localhost:3000'),
    'test_timeout': 60,
    'test_agent_api_key': 'test_agent_api_key_12345',
    'test_wordpress_site': 'test-site-001'
}

class TestE2EWorkflow:
    """End-to-end workflow tests"""
    
    @pytest.fixture
    async def http_client(self):
        """HTTP client for API requests"""
        async with httpx.AsyncClient(timeout=TEST_CONFIG['test_timeout']) as client:
            yield client
    
    @pytest.fixture
    async def test_article_data(self):
        """Sample article data for testing"""
        return {
            "title": f"Test Article {datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "content_markdown": """# Test Article

This is a test article for integration testing of the MCP WordPress Publisher v2.1 system.

## Features Being Tested

- Multi-agent article submission
- Content validation and processing
- Review and approval workflow  
- Multi-site WordPress publishing
- Real-time status updates

## Content

This article tests the complete workflow from submission to publication across multiple WordPress sites with different agent configurations.

Testing various markdown features:

### Lists
- Item 1
- Item 2
- Item 3

### Code
```python
def hello_world():
    return "Hello from MCP WordPress Publisher v2.1!"
```

### Links
Visit [our website](https://example.com) for more information.

End of test article.""",
            "category": "Test",
            "tags": "test,integration,mcp,v21"
        }
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_complete_article_workflow(self, http_client, test_article_data):
        """Test complete article submission to publication workflow"""
        
        # Step 1: Submit article via MCP Tools
        submit_response = await http_client.post(
            f"{TEST_CONFIG['mcp_server_url']}/tools/submit_article",
            headers={
                'Authorization': f"Bearer {TEST_CONFIG['test_agent_api_key']}",
                'Content-Type': 'application/json'
            },
            json=test_article_data
        )
        
        assert submit_response.status_code == 200
        submit_result = submit_response.json()
        assert 'article_id' in submit_result
        article_id = submit_result['article_id']
        
        # Step 2: Verify article appears in pending review status
        await asyncio.sleep(2)  # Allow for processing
        
        status_response = await http_client.get(
            f"{TEST_CONFIG['mcp_server_url']}/tools/get_article_status",
            headers={'Authorization': f"Bearer {TEST_CONFIG['test_agent_api_key']}"},
            params={'article_id': article_id}
        )
        
        assert status_response.status_code == 200
        status_result = status_response.json()
        assert status_result['status'] == 'pending_review'
        assert status_result['title'] == test_article_data['title']
        
        # Step 3: Approve article for publishing
        approve_response = await http_client.post(
            f"{TEST_CONFIG['mcp_server_url']}/tools/approve_article",
            headers={'Authorization': f"Bearer {TEST_CONFIG['test_agent_api_key']}"},
            json={
                'article_id': article_id,
                'reviewer_notes': 'Approved for integration testing'
            }
        )
        
        assert approve_response.status_code == 200
        
        # Step 4: Wait for publishing to complete
        max_wait_time = 30  # seconds
        wait_interval = 2   # seconds
        published = False
        
        for _ in range(max_wait_time // wait_interval):
            await asyncio.sleep(wait_interval)
            
            status_response = await http_client.get(
                f"{TEST_CONFIG['mcp_server_url']}/tools/get_article_status",
                headers={'Authorization': f"Bearer {TEST_CONFIG['test_agent_api_key']}"},
                params={'article_id': article_id}
            )
            
            if status_response.status_code == 200:
                status_result = status_response.json()
                if status_result['status'] == 'published':
                    published = True
                    assert 'wordpress_post_id' in status_result
                    assert 'permalink' in status_result
                    break
                elif status_result['status'] == 'publish_failed':
                    pytest.fail(f"Article publishing failed: {status_result.get('publish_error_message', 'Unknown error')}")
        
        assert published, "Article was not published within the expected time"
        
        # Step 5: Verify article appears in published articles list
        published_response = await http_client.get(
            f"{TEST_CONFIG['mcp_server_url']}/resources/published_articles",
            headers={'Authorization': f"Bearer {TEST_CONFIG['test_agent_api_key']}"}
        )
        
        assert published_response.status_code == 200
        published_articles = published_response.json()
        
        # Find our article in the published list
        our_article = None
        for article in published_articles.get('articles', []):
            if article['id'] == article_id:
                our_article = article
                break
        
        assert our_article is not None, "Published article not found in published articles list"
        assert our_article['status'] == 'published'
        assert our_article['wordpress_post_id'] is not None
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_multi_agent_submission(self, http_client):
        """Test multiple agents submitting articles simultaneously"""
        
        # Simulate multiple agents submitting articles
        agent_configs = [
            {'api_key': 'test_content_creator_key', 'category': 'Technology'},
            {'api_key': 'test_research_agent_key', 'category': 'Research'},
            {'api_key': 'test_news_agent_key', 'category': 'News'}
        ]
        
        submitted_articles = []
        
        # Submit articles from multiple agents
        for i, agent_config in enumerate(agent_configs):
            article_data = {
                "title": f"Multi-Agent Test Article {i+1} - {datetime.now().strftime('%H%M%S')}",
                "content_markdown": f"""# Multi-Agent Test Article {i+1}

This article is submitted by agent {i+1} for testing multi-agent functionality.

Category: {agent_config['category']}
Agent: Agent {i+1}
Timestamp: {datetime.now().isoformat()}

Content specific to agent {i+1} testing multi-agent submission capabilities.""",
                "category": agent_config['category'],
                "tags": f"multi-agent,test,agent-{i+1}"
            }
            
            submit_response = await http_client.post(
                f"{TEST_CONFIG['mcp_server_url']}/tools/submit_article",
                headers={
                    'Authorization': f"Bearer {agent_config['api_key']}",
                    'Content-Type': 'application/json'
                },
                json=article_data
            )
            
            assert submit_response.status_code == 200
            result = submit_response.json()
            submitted_articles.append({
                'article_id': result['article_id'],
                'agent_key': agent_config['api_key'],
                'title': article_data['title']
            })
        
        # Verify all articles were submitted successfully
        assert len(submitted_articles) == len(agent_configs)
        
        # Check that articles are properly attributed to different agents
        for article in submitted_articles:
            status_response = await http_client.get(
                f"{TEST_CONFIG['mcp_server_url']}/tools/get_article_status",
                headers={'Authorization': f"Bearer {article['agent_key']}"},
                params={'article_id': article['article_id']}
            )
            
            assert status_response.status_code == 200
            status_result = status_response.json()
            assert status_result['status'] == 'pending_review'
            assert status_result['title'] == article['title']
    
    @pytest.mark.integration 
    @pytest.mark.asyncio
    async def test_web_ui_integration(self, http_client):
        """Test Web UI integration with MCP server"""
        
        # Test Web UI health endpoint
        health_response = await http_client.get(f"{TEST_CONFIG['web_ui_url']}/api/health")
        assert health_response.status_code == 200
        
        # Test MCP server connection from Web UI
        connection_response = await http_client.get(
            f"{TEST_CONFIG['web_ui_url']}/api/mcp/connection-status"
        )
        assert connection_response.status_code == 200
        connection_data = connection_response.json()
        assert connection_data['connected'] is True
        
        # Test dashboard data endpoint
        dashboard_response = await http_client.get(
            f"{TEST_CONFIG['web_ui_url']}/api/mcp/dashboard"
        )
        assert dashboard_response.status_code == 200
        dashboard_data = dashboard_response.json()
        
        # Verify expected dashboard structure
        assert 'system_stats' in dashboard_data
        assert 'agents' in dashboard_data
        assert 'sites' in dashboard_data
        assert 'recent_articles' in dashboard_data
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, http_client):
        """Test error handling in various scenarios"""
        
        # Test 1: Invalid API key
        invalid_auth_response = await http_client.post(
            f"{TEST_CONFIG['mcp_server_url']}/tools/submit_article",
            headers={
                'Authorization': 'Bearer invalid_api_key',
                'Content-Type': 'application/json'
            },
            json={"title": "Test", "content_markdown": "Test content"}
        )
        assert invalid_auth_response.status_code == 401
        
        # Test 2: Malformed article data
        malformed_response = await http_client.post(
            f"{TEST_CONFIG['mcp_server_url']}/tools/submit_article",
            headers={
                'Authorization': f"Bearer {TEST_CONFIG['test_agent_api_key']}",
                'Content-Type': 'application/json'
            },
            json={"title": ""}  # Empty title should fail validation
        )
        assert malformed_response.status_code == 400
        
        # Test 3: Non-existent article ID
        nonexistent_response = await http_client.get(
            f"{TEST_CONFIG['mcp_server_url']}/tools/get_article_status",
            headers={'Authorization': f"Bearer {TEST_CONFIG['test_agent_api_key']}"},
            params={'article_id': 999999}
        )
        assert nonexistent_response.status_code == 404
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_real_time_updates(self, http_client):
        """Test real-time updates via Server-Sent Events"""
        
        # This test would normally use SSE client, but for simplicity 
        # we'll test the SSE endpoint availability
        sse_response = await http_client.get(
            f"{TEST_CONFIG['mcp_server_url']}/sse",
            headers={'Accept': 'text/event-stream'}
        )
        
        # SSE endpoint should be available (might timeout in test, but should connect)
        assert sse_response.status_code in [200, 408]  # 408 timeout is acceptable

class TestSystemIntegration:
    """System-level integration tests"""
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_database_connectivity(self, http_client):
        """Test database connectivity and basic operations"""
        
        # Test system health endpoint which checks database
        health_response = await http_client.get(
            f"{TEST_CONFIG['mcp_server_url']}/health"
        )
        assert health_response.status_code == 200
        health_data = health_response.json()
        assert health_data['status'] == 'healthy'
        assert 'database' in health_data['components']
        assert health_data['components']['database']['status'] == 'healthy'
    
    @pytest.mark.integration
    @pytest.mark.asyncio 
    async def test_multi_site_configuration(self, http_client):
        """Test multi-site configuration and availability"""
        
        # Get sites list
        sites_response = await http_client.get(
            f"{TEST_CONFIG['mcp_server_url']}/resources/sites",
            headers={'Authorization': f"Bearer {TEST_CONFIG['test_agent_api_key']}"}
        )
        
        assert sites_response.status_code == 200
        sites_data = sites_response.json()
        assert 'sites' in sites_data
        assert len(sites_data['sites']) > 0
        
        # Verify each site has required configuration
        for site in sites_data['sites']:
            assert 'id' in site
            assert 'name' in site
            assert 'wordpress_config' in site
            assert 'status' in site
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_agent_statistics(self, http_client):
        """Test agent statistics and monitoring"""
        
        # Get agent statistics
        stats_response = await http_client.get(
            f"{TEST_CONFIG['mcp_server_url']}/resources/agent_statistics",
            headers={'Authorization': f"Bearer {TEST_CONFIG['test_agent_api_key']}"}
        )
        
        assert stats_response.status_code == 200
        stats_data = stats_response.json()
        assert 'agents' in stats_data
        
        # Verify statistics structure
        for agent in stats_data['agents']:
            assert 'id' in agent
            assert 'statistics' in agent
            assert 'total_articles' in agent['statistics']
            assert 'published_articles' in agent['statistics']
            assert 'success_rate' in agent['statistics']

class TestPerformance:
    """Performance and load testing"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_concurrent_submissions(self, http_client):
        """Test system performance under concurrent load"""
        
        # Create multiple concurrent article submissions
        concurrent_requests = 10
        
        async def submit_article(index):
            article_data = {
                "title": f"Load Test Article {index} - {datetime.now().strftime('%H%M%S')}",
                "content_markdown": f"Load test content for article {index}",
                "category": "Test",
                "tags": f"load-test,article-{index}"
            }
            
            response = await http_client.post(
                f"{TEST_CONFIG['mcp_server_url']}/tools/submit_article",
                headers={
                    'Authorization': f"Bearer {TEST_CONFIG['test_agent_api_key']}",
                    'Content-Type': 'application/json'
                },
                json=article_data
            )
            return response
        
        # Submit articles concurrently
        tasks = [submit_article(i) for i in range(concurrent_requests)]
        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Verify all submissions succeeded
        successful_submissions = 0
        for response in responses:
            if not isinstance(response, Exception) and response.status_code == 200:
                successful_submissions += 1
        
        # At least 80% should succeed under load
        success_rate = successful_submissions / concurrent_requests
        assert success_rate >= 0.8, f"Success rate {success_rate} below threshold"

# Test configuration and setup
@pytest.fixture(scope="session", autouse=True)
async def setup_test_environment():
    """Setup test environment before running tests"""
    
    # Wait for services to be ready
    max_wait = 60  # seconds
    wait_interval = 5
    
    async with httpx.AsyncClient() as client:
        for _ in range(max_wait // wait_interval):
            try:
                # Check MCP server health
                health_response = await client.get(
                    f"{TEST_CONFIG['mcp_server_url']}/health",
                    timeout=10
                )
                if health_response.status_code == 200:
                    break
            except:
                pass
            
            await asyncio.sleep(wait_interval)
        else:
            pytest.fail("MCP server failed to start within expected time")
    
    yield
    
    # Cleanup after tests (if needed)
    pass

if __name__ == "__main__":
    # Run integration tests
    pytest.main([
        __file__,
        "-v",
        "--tb=short", 
        "-m", "integration"
    ])