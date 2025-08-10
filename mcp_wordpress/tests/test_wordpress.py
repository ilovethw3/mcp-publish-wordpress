"""Tests for WordPress integration."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import aiohttp

from mcp_wordpress.core.wordpress import WordPressClient


class TestWordPressClient:
    """Test WordPress REST API client."""
    
    @pytest.fixture
    def wp_client(self):
        """Create WordPress client for testing."""
        return WordPressClient(
            api_url="https://test.com/wp-json/wp/v2",
            username="testuser",
            app_password="testpass"
        )
    
    @pytest.mark.asyncio
    async def test_create_post_success(self, wp_client):
        """Test successful post creation."""
        mock_response_data = {
            "id": 123,
            "title": {"rendered": "Test Article"},
            "link": "https://test.com/test-article",
            "status": "publish"
        }
        
        with patch.object(wp_client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 201
            mock_response.json = AsyncMock(return_value=mock_response_data)
            
            # Create proper async context manager mock
            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_session.post = MagicMock(return_value=mock_context_manager)
            mock_get_session.return_value = mock_session
            
            result = await wp_client.create_post(
                title="Test Article",
                content_markdown="# Test Content"
            )
            
            assert result["id"] == 123
            assert result["link"] == "https://test.com/test-article"
    
    @pytest.mark.asyncio
    async def test_create_post_failure(self, wp_client):
        """Test post creation failure."""
        with patch.object(wp_client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 400
            mock_response.text = AsyncMock(return_value="Bad Request")
            
            # Create proper async context manager mock
            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_session.post = MagicMock(return_value=mock_context_manager)
            mock_get_session.return_value = mock_session
            
            with pytest.raises(Exception) as exc_info:
                await wp_client.create_post(
                    title="Test Article",
                    content_markdown="# Test Content"
                )
            
            assert "WordPress API error: 400" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_connection_test_success(self, wp_client):
        """Test successful connection test."""
        with patch.object(wp_client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 200
            
            # Create proper async context manager mock
            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = MagicMock(return_value=mock_context_manager)
            mock_get_session.return_value = mock_session
            
            result = await wp_client.test_connection()
            assert result is True
    
    @pytest.mark.asyncio
    async def test_connection_test_failure(self, wp_client):
        """Test failed connection test."""
        with patch.object(wp_client, '_get_session') as mock_get_session:
            mock_session = AsyncMock()
            mock_response = AsyncMock()
            mock_response.status = 401
            
            # Create proper async context manager mock
            mock_context_manager = MagicMock()
            mock_context_manager.__aenter__ = AsyncMock(return_value=mock_response)
            mock_context_manager.__aexit__ = AsyncMock(return_value=None)
            mock_session.get = MagicMock(return_value=mock_context_manager)
            mock_get_session.return_value = mock_session
            
            result = await wp_client.test_connection()
            assert result is False