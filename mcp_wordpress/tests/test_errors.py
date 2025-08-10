"""Tests for MCP error handling utilities."""

import pytest
import json

from mcp_wordpress.core.errors import (
    MCPErrorCodes, create_mcp_error, create_mcp_success,
    MCPError, ArticleNotFoundError, InvalidStatusError,
    WordPressError, ValidationError
)


class TestMCPErrorCodes:
    """Test MCP error code constants."""
    
    def test_error_codes_defined(self):
        """Test all error codes are properly defined."""
        assert MCPErrorCodes.PARSE_ERROR == -32700
        assert MCPErrorCodes.INVALID_REQUEST == -32600
        assert MCPErrorCodes.METHOD_NOT_FOUND == -32601
        assert MCPErrorCodes.INVALID_PARAMS == -32602
        assert MCPErrorCodes.INTERNAL_ERROR == -32603
        
        # Application-specific codes
        assert MCPErrorCodes.ARTICLE_NOT_FOUND == -40001
        assert MCPErrorCodes.INVALID_STATUS == -40002
        assert MCPErrorCodes.WORDPRESS_ERROR == -40003
        assert MCPErrorCodes.AUTH_FAILED == -40004
        assert MCPErrorCodes.VALIDATION_ERROR == -40005


class TestErrorFormatting:
    """Test error response formatting functions."""
    
    def test_create_mcp_error_basic(self):
        """Test basic MCP error creation."""
        error_json = create_mcp_error(
            code=MCPErrorCodes.ARTICLE_NOT_FOUND,
            message="Article not found"
        )
        
        error_data = json.loads(error_json)
        assert "error" in error_data
        assert error_data["error"]["code"] == -40001
        assert error_data["error"]["message"] == "Article not found"
        assert "data" not in error_data["error"]
    
    def test_create_mcp_error_with_data(self):
        """Test MCP error creation with additional data."""
        error_json = create_mcp_error(
            code=MCPErrorCodes.VALIDATION_ERROR,
            message="Validation failed",
            data={"field": "title", "reason": "too long"}
        )
        
        error_data = json.loads(error_json)
        assert error_data["error"]["code"] == -40005
        assert error_data["error"]["message"] == "Validation failed"
        assert error_data["error"]["data"]["field"] == "title"
        assert error_data["error"]["data"]["reason"] == "too long"
    
    def test_create_mcp_success(self):
        """Test MCP success response creation."""
        success_json = create_mcp_success({
            "article_id": 123,
            "status": "published"
        })
        
        success_data = json.loads(success_json)
        assert success_data["article_id"] == 123
        assert success_data["status"] == "published"
        assert "error" not in success_data


class TestMCPExceptions:
    """Test custom MCP exception classes."""
    
    def test_base_mcp_error(self):
        """Test base MCPError class."""
        error = MCPError(
            code=MCPErrorCodes.INTERNAL_ERROR,
            message="Something went wrong",
            data={"context": "test"}
        )
        
        assert error.code == MCPErrorCodes.INTERNAL_ERROR
        assert error.message == "Something went wrong"
        assert error.data == {"context": "test"}
        
        # Test JSON conversion
        error_json = error.to_json()
        error_data = json.loads(error_json)
        assert error_data["error"]["code"] == -32603
        assert error_data["error"]["message"] == "Something went wrong"
        assert error_data["error"]["data"]["context"] == "test"
    
    def test_article_not_found_error(self):
        """Test ArticleNotFoundError."""
        error = ArticleNotFoundError(article_id=42)
        
        assert error.code == MCPErrorCodes.ARTICLE_NOT_FOUND
        assert "Article with ID 42 not found" in error.message
        assert error.data["article_id"] == 42
        
        # Test JSON format
        error_json = error.to_json()
        error_data = json.loads(error_json)
        assert error_data["error"]["code"] == -40001
        assert error_data["error"]["data"]["article_id"] == 42
    
    def test_invalid_status_error(self):
        """Test InvalidStatusError."""
        error = InvalidStatusError(
            current_status="published",
            required_status="pending_review"
        )
        
        assert error.code == MCPErrorCodes.INVALID_STATUS
        assert "pending_review" in error.message
        assert "published" in error.message
        assert error.data["current_status"] == "published"
        assert error.data["required_status"] == "pending_review"
    
    def test_wordpress_error(self):
        """Test WordPressError."""
        error = WordPressError(
            message="Connection failed",
            wp_error="HTTP 500"
        )
        
        assert error.code == MCPErrorCodes.WORDPRESS_ERROR
        assert "WordPress API error" in error.message
        assert "Connection failed" in error.message
        assert error.data["wordpress_error"] == "HTTP 500"
    
    def test_validation_error(self):
        """Test ValidationError."""
        error = ValidationError(
            field="title",
            message="cannot be empty"
        )
        
        assert error.code == MCPErrorCodes.VALIDATION_ERROR
        assert "title" in error.message
        assert "cannot be empty" in error.message
        assert error.data["field"] == "title"
        assert error.data["validation_error"] == "cannot be empty"


class TestErrorHandlingWorkflows:
    """Test error handling in typical workflows."""
    
    def test_chained_error_handling(self):
        """Test handling multiple error types in sequence."""
        errors = [
            ArticleNotFoundError(1),
            ValidationError("title", "too long"),
            WordPressError("API down", "500")
        ]
        
        for error in errors:
            error_json = error.to_json()
            error_data = json.loads(error_json)
            
            # All should follow JSON-RPC 2.0 format
            assert "error" in error_data
            assert "code" in error_data["error"]
            assert "message" in error_data["error"]
            assert isinstance(error_data["error"]["code"], int)
            assert isinstance(error_data["error"]["message"], str)
    
    @pytest.mark.unit
    def test_error_inheritance(self):
        """Test error class inheritance structure."""
        # All custom errors should inherit from MCPError
        assert issubclass(ArticleNotFoundError, MCPError)
        assert issubclass(InvalidStatusError, MCPError)
        assert issubclass(WordPressError, MCPError)
        assert issubclass(ValidationError, MCPError)
        
        # MCPError should inherit from Exception
        assert issubclass(MCPError, Exception)