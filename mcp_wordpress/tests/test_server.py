"""Tests for MCP server functionality."""

import pytest
import json
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch, MagicMock

from mcp_wordpress.server import create_mcp_server
from mcp_wordpress.models.article import Article, ArticleStatus


class TestMCPServer:
    """Test MCP server creation and basic functionality."""
    
    @pytest.mark.asyncio
    async def test_create_mcp_server(self):
        """Test MCP server creation."""
        mcp = create_mcp_server()
        assert mcp.name == "wordpress-publisher"
        assert mcp.version == "2.0.0"
        
        # Verify tools are registered using correct API
        tools = await mcp.get_tools()
        assert isinstance(tools, dict)
        assert len(tools) > 0
    
    @pytest.mark.asyncio
    async def test_submit_article_tool(self):
        """Test submit_article tool functionality."""
        mcp = create_mcp_server()
        
        with patch('mcp_wordpress.tools.articles.get_session') as mock_session:
            mock_db_session = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock the article creation
            mock_article = Article(
                id=1,
                title="Test Article",
                content_markdown="# Test Content",
                status=ArticleStatus.PENDING_REVIEW
            )
            mock_db_session.refresh = AsyncMock(side_effect=lambda article: setattr(article, 'id', 1))
            mock_db_session.add = MagicMock()  # Not async
            mock_db_session.commit = AsyncMock()
            
            # Call the tool using correct API
            tools = await mcp.get_tools()
            submit_tool = tools["submit_article"]
            result = await submit_tool.fn(
                title="Test Article",
                content_markdown="# Test Content"
            )
            
            # Verify result (updated for new success format)
            result_data = json.loads(result)
            assert "article_id" in result_data
            assert result_data["status"] == "pending_review"
            assert "message" in result_data
    
    @pytest.mark.asyncio
    async def test_list_articles_tool(self):
        """Test list_articles tool functionality."""
        mcp = create_mcp_server()
        
        with patch('mcp_wordpress.tools.articles.get_session') as mock_session:
            mock_db_session = AsyncMock()
            mock_session.return_value.__aenter__.return_value = mock_db_session
            
            # Mock articles data
            mock_articles = [
                Article(
                    id=1,
                    title="Article 1",
                    content_markdown="Content 1",
                    status=ArticleStatus.PENDING_REVIEW,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                ),
                Article(
                    id=2,
                    title="Article 2", 
                    content_markdown="Content 2",
                    status=ArticleStatus.PUBLISHED,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            ]
            
            mock_result = AsyncMock()
            mock_scalars = AsyncMock()
            mock_scalars.all = lambda: mock_articles  # Not async
            mock_result.scalars = lambda: mock_scalars
            mock_db_session.execute = AsyncMock(return_value=mock_result)
            
            # Call the tool using correct API
            tools = await mcp.get_tools()
            list_tool = tools["list_articles"]
            result = await list_tool.fn()
            
            # Verify result
            result_data = json.loads(result)
            assert "articles" in result_data
            assert len(result_data["articles"]) == 2
            assert result_data["total"] == 2