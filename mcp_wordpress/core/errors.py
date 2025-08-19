"""MCP standard error handling utilities."""

import json
from typing import Any, Dict, Optional


class MCPErrorCodes:
    """Standard MCP error codes following JSON-RPC 2.0 specification."""
    
    # JSON-RPC 2.0 standard errors
    PARSE_ERROR = -32700
    INVALID_REQUEST = -32600
    METHOD_NOT_FOUND = -32601
    INVALID_PARAMS = -32602
    INTERNAL_ERROR = -32603
    
    # Application-specific error codes
    ARTICLE_NOT_FOUND = -40001
    INVALID_STATUS = -40002
    WORDPRESS_ERROR = -40003
    AUTH_FAILED = -40004
    VALIDATION_ERROR = -40005


def create_mcp_error(
    code: int, 
    message: str, 
    data: Optional[Dict[str, Any]] = None
) -> str:
    """Create MCP standard error response in JSON-RPC 2.0 format.
    
    Args:
        code: Error code from MCPErrorCodes
        message: Human-readable error message
        data: Optional additional error data
        
    Returns:
        JSON string with error response
    """
    error_response = {
        "error": {
            "code": code,
            "message": message
        }
    }
    
    if data:
        error_response["error"]["data"] = data
        
    return json.dumps(error_response)


def create_mcp_success(data: Dict[str, Any]) -> str:
    """Create MCP standard success response.
    
    Args:
        data: Response data
        
    Returns:
        JSON string with success response
    """
    return json.dumps(data)


class MCPError(Exception):
    """Base exception for MCP-related errors."""
    
    def __init__(self, code: int, message: str, data: Optional[Dict[str, Any]] = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(message)
        
    def to_json(self) -> str:
        """Convert exception to MCP error JSON."""
        return create_mcp_error(self.code, self.message, self.data)


class ArticleNotFoundError(MCPError):
    """Article not found error."""
    
    def __init__(self, article_id: int):
        super().__init__(
            code=MCPErrorCodes.ARTICLE_NOT_FOUND,
            message=f"Article with ID {article_id} not found",
            data={"article_id": article_id}
        )


class InvalidStatusError(MCPError):
    """Invalid article status error."""
    
    def __init__(self, current_status: str, required_status: str):
        super().__init__(
            code=MCPErrorCodes.INVALID_STATUS,
            message=f"Article status must be '{required_status}' but is '{current_status}'",
            data={"current_status": current_status, "required_status": required_status}
        )


class WordPressError(MCPError):
    """WordPress API error."""
    
    def __init__(self, message: str, wp_error: str = None):
        super().__init__(
            code=MCPErrorCodes.WORDPRESS_ERROR,
            message=f"WordPress API error: {message}",
            data={"wordpress_error": wp_error} if wp_error else None
        )


class ValidationError(MCPError):
    """Input validation error."""
    
    def __init__(self, field: str, message: str):
        super().__init__(
            code=MCPErrorCodes.VALIDATION_ERROR,
            message=f"Validation error for field '{field}': {message}",
            data={"field": field, "validation_error": message}
        )


class ConfigurationError(MCPError):
    """Configuration error."""
    
    def __init__(self, message: str, config_file: str = None):
        super().__init__(
            code=MCPErrorCodes.INTERNAL_ERROR,
            message=f"Configuration error: {message}",
            data={"config_file": config_file} if config_file else None
        )


class AuthenticationError(MCPError):
    """Authentication error."""
    
    def __init__(self, message: str = "Authentication failed"):
        super().__init__(
            code=MCPErrorCodes.AUTH_FAILED,
            message=message
        )


class AuthorizationError(MCPError):
    """Authorization error."""
    
    def __init__(self, message: str = "Authorization failed", required_scope: str = None):
        super().__init__(
            code=MCPErrorCodes.AUTH_FAILED,
            message=message,
            data={"required_scope": required_scope} if required_scope else None
        )


class PermissionDeniedError(MCPError):
    """Permission denied error for role-based access control."""
    
    def __init__(self, message: str = "Permission denied", required_permission: str = None, agent_id: str = None):
        super().__init__(
            code=MCPErrorCodes.AUTH_FAILED,
            message=message,
            data={
                "required_permission": required_permission,
                "agent_id": agent_id
            } if required_permission or agent_id else None
        )


class AgentNotFoundError(MCPError):
    """Agent not found error."""
    
    def __init__(self, agent_id: str):
        super().__init__(
            code=MCPErrorCodes.INTERNAL_ERROR,
            message=f"Agent with ID '{agent_id}' not found",
            data={"agent_id": agent_id}
        )


class SiteNotFoundError(MCPError):
    """Site not found error."""
    
    def __init__(self, site_id: str):
        super().__init__(
            code=MCPErrorCodes.INTERNAL_ERROR,
            message=f"Site with ID '{site_id}' not found",
            data={"site_id": site_id}
        )


class PublishingError(MCPError):
    """Publishing error."""
    
    def __init__(self, message: str, site_id: str = None, article_id: int = None):
        super().__init__(
            code=MCPErrorCodes.WORDPRESS_ERROR,
            message=f"Publishing error: {message}",
            data={"site_id": site_id, "article_id": article_id}
        )