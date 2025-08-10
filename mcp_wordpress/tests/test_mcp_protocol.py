"""Tests for MCP protocol compliance and functionality."""

import pytest
import json
from unittest.mock import AsyncMock, patch, MagicMock

from mcp_wordpress.server import create_mcp_server
from mcp_wordpress.models.article import Article, ArticleStatus
from datetime import datetime, timezone


class TestMCPToolsRegistration:
    """Test MCP tools registration and functionality."""
    
    @pytest.mark.asyncio
    async def test_all_tools_registered(self):
        """Test that all expected tools are registered."""
        mcp = create_mcp_server()
        tools = await mcp.get_tools()
        
        expected_tools = [
            "submit_article",
            "list_articles", 
            "get_article_status",
            "approve_article",
            "reject_article"
        ]
        
        for tool_name in expected_tools:
            assert tool_name in tools, f"Tool '{tool_name}' not registered"
    
    @pytest.mark.asyncio
    async def test_tools_have_proper_signatures(self):
        """Test that tools have proper function signatures."""
        mcp = create_mcp_server()
        tools = await mcp.get_tools()
        
        # Test submit_article signature
        assert "submit_article" in tools
        submit_tool = tools["submit_article"]
        assert hasattr(submit_tool, 'name')
        assert hasattr(submit_tool, 'description')
        
        # Test list_articles signature
        assert "list_articles" in tools
        list_tool = tools["list_articles"]
        assert hasattr(list_tool, 'name')
        assert hasattr(list_tool, 'description')


class TestMCPResourcesAccess:
    """Test MCP resources access and data format."""
    
    @pytest.mark.asyncio
    async def test_all_resources_registered(self):
        """Test that all expected resources are registered."""
        mcp = create_mcp_server()
        resources = await mcp.get_resources()
        
        expected_resources = [
            "article://pending",
            "article://published", 
            "article://failed",  # Updated to match actual implementation
            "stats://summary",
            "stats://performance",
            "wordpress://config"
        ]
        
        for resource_uri in expected_resources:
            assert resource_uri in resources, f"Resource '{resource_uri}' not registered"
    
    @pytest.mark.asyncio
    async def test_article_resources_format(self):
        """Test article resources return proper JSON format."""
        mcp = create_mcp_server()
        resources = await mcp.get_resources()
        
        with patch('mcp_wordpress.resources.articles.get_session') as mock_session:
            mock_db_session = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db_session
            mock_result = AsyncMock()
            mock_scalars = AsyncMock()
            mock_scalars.all = lambda: []  # Not async
            mock_result.scalars = lambda: mock_scalars
            mock_db_session.execute = AsyncMock(return_value=mock_result)
            
            # Test pending articles resource
            resource = resources["article://pending"]
            result = await resource.read()
            
            # Should return valid JSON
            data = json.loads(result)
            assert "pending_articles" in data
            assert "updated_at" in data
            assert isinstance(data["pending_articles"], list)
    
    @pytest.mark.asyncio
    async def test_stats_resources_format(self):
        """Test stats resources return proper JSON format."""
        mcp = create_mcp_server()
        resources = await mcp.get_resources()
        
        with patch('mcp_wordpress.resources.stats.get_session') as mock_session:
            mock_db_session = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db_session
            mock_result = AsyncMock()
            mock_result.scalar = lambda: 5  # Not async  
            mock_scalars = AsyncMock()
            mock_scalars.all = lambda: []  # For article queries
            mock_result.scalars = lambda: mock_scalars
            mock_db_session.execute = AsyncMock(return_value=mock_result)
            
            # Test stats summary resource
            resource = resources["stats://summary"]
            result = await resource.read()
            
            # Should return valid JSON with expected fields
            data = json.loads(result)
            assert "total_articles" in data
            assert "articles_by_status" in data
            assert "last_updated" in data


class TestMCPPromptsGeneration:
    """Test MCP prompts registration and generation."""
    
    @pytest.mark.asyncio
    async def test_all_prompts_registered(self):
        """Test that all expected prompts are registered."""
        mcp = create_mcp_server()
        prompts = await mcp.get_prompts()
        
        expected_prompts = [
            "article_template",  # Updated to match actual implementation
            "review_checklist",
            "wordpress_formatting"
        ]
        
        for prompt_name in expected_prompts:
            assert prompt_name in prompts, f"Prompt '{prompt_name}' not registered"
    
    @pytest.mark.asyncio
    async def test_prompt_generation_format(self):
        """Test prompt generation returns proper format."""
        mcp = create_mcp_server()
        prompts = await mcp.get_prompts()
        
        # Test article template prompt
        prompt = prompts["article_template"]
        result = await prompt.render({
            "topic": "Python Testing",
            "target_audience": "developers"
        })
        
        # Should return valid prompt messages
        assert isinstance(result, list)
        assert len(result) > 0
        prompt_text = result[0].content.text
        assert isinstance(prompt_text, str)
        assert len(prompt_text) > 100  # Should be substantial content
        assert "Python Testing" in prompt_text  # Should include topic


class TestMCPErrorHandling:
    """Test MCP protocol error handling."""
    
    @pytest.mark.asyncio
    async def test_tool_error_propagation(self):
        """Test that tool errors are properly formatted."""
        mcp = create_mcp_server()
        tools = await mcp.get_tools()
        
        with patch('mcp_wordpress.tools.articles.get_session') as mock_session:
            mock_db_session = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db_session
            mock_result = AsyncMock()
            mock_scalars = AsyncMock()
            mock_scalars.first = lambda: None  # Article not found, not async
            mock_result.scalars = lambda: mock_scalars
            mock_db_session.execute = AsyncMock(return_value=mock_result)
            
            # Test article not found error
            tool = tools["get_article_status"]
            result = await tool.fn(article_id=999)
            
            # Should return JSON-RPC 2.0 error format
            error_data = json.loads(result)
            assert "error" in error_data
            assert error_data["error"]["code"] == -40001
            assert "not found" in error_data["error"]["message"]
    
    @pytest.mark.asyncio
    async def test_validation_error_handling(self):
        """Test input validation error handling.""" 
        mcp = create_mcp_server()
        tools = await mcp.get_tools()
        
        with patch('mcp_wordpress.tools.articles.get_session') as mock_session:
            mock_db_session = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db_session
            mock_db_session.execute = AsyncMock()
            
            # Test title too long validation
            tool = tools["submit_article"]
            result = await tool.fn(
                title="x" * 300,  # Too long title
                content_markdown="# Test Content"
            )
            
            # Should return validation error
            error_data = json.loads(result)
            assert "error" in error_data
            assert error_data["error"]["code"] == -40005
            assert "title" in error_data["error"]["message"]


class TestMCPProtocolCompliance:
    """Test overall MCP protocol compliance."""
    
    def test_server_metadata(self):
        """Test server provides proper metadata."""
        mcp = create_mcp_server()
        
        # Required metadata
        assert hasattr(mcp, 'name')
        assert hasattr(mcp, 'version')
        assert hasattr(mcp, 'get_tools')
        assert hasattr(mcp, 'get_resources')
        assert hasattr(mcp, 'get_prompts')
        
        # Metadata values
        assert isinstance(mcp.name, str)
        assert isinstance(mcp.version, str)
        assert len(mcp.name) > 0
        assert len(mcp.version) > 0
    
    @pytest.mark.asyncio
    async def test_tools_interface_compliance(self):
        """Test tools follow MCP interface requirements."""
        mcp = create_mcp_server()
        tools = await mcp.get_tools()
        
        for tool_name, tool_obj in tools.items():
            # All tools should have required attributes
            assert hasattr(tool_obj, 'name'), f"Tool '{tool_name}' missing name attribute"
            assert hasattr(tool_obj, 'description'), f"Tool '{tool_name}' missing description attribute"
            
            # Tools should have valid descriptions
            assert tool_obj.description is not None, f"Tool '{tool_name}' has empty description"
            assert len(tool_obj.description) > 0, f"Tool '{tool_name}' has empty description"
    
    @pytest.mark.asyncio
    async def test_resources_interface_compliance(self):
        """Test resources follow MCP interface requirements."""
        mcp = create_mcp_server()
        resources = await mcp.get_resources()
        
        for resource_uri, resource_obj in resources.items():
            # All resources should have required attributes
            assert hasattr(resource_obj, 'uri'), f"Resource '{resource_uri}' missing uri attribute"
            assert hasattr(resource_obj, 'name'), f"Resource '{resource_uri}' missing name attribute"
            
            # Resource URIs should follow expected format
            assert "://" in resource_uri, f"Resource '{resource_uri}' invalid URI format"
    
    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_full_mcp_workflow(self):
        """Test complete MCP workflow integration."""
        mcp = create_mcp_server()
        tools = await mcp.get_tools()
        
        with patch('mcp_wordpress.tools.articles.get_session') as mock_session:
            mock_db_session = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock article creation
            mock_article = Article(
                id=1,
                title="Integration Test Article",
                content_markdown="# Integration Test Content",
                status=ArticleStatus.PENDING_REVIEW,
                created_at=datetime.now(timezone.utc),
                updated_at=datetime.now(timezone.utc)
            )
            mock_db_session.refresh = AsyncMock()
            mock_db_session.execute = AsyncMock()
            mock_db_session.add = MagicMock()  # Not async
            mock_db_session.commit = AsyncMock()
            
            # 1. Submit article
            submit_tool = tools["submit_article"]
            submit_result = await submit_tool.fn(
                title="Integration Test Article",
                content_markdown="# Integration Test Content"
            )
            
            submit_data = json.loads(submit_result)
            assert "article_id" in submit_data
            
            # 2. List articles
            mock_result = AsyncMock()
            mock_scalars = AsyncMock()
            mock_scalars.all = lambda: [mock_article]  # Not async
            mock_result.scalars = lambda: mock_scalars
            mock_db_session.execute = AsyncMock(return_value=mock_result)
            
            list_tool = tools["list_articles"]
            list_result = await list_tool.fn()
            
            list_data = json.loads(list_result)
            assert "articles" in list_data
            assert "total" in list_data