"""Configuration management for MCP WordPress server."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    # MCP Server Configuration
    mcp_server_name: str = "wordpress-publisher"
    mcp_transport: Literal["stdio", "sse"] = "stdio"
    mcp_port: int = 8000
    mcp_sse_path: str = Field(default="/sse", description="SSE endpoint path (without trailing slash to avoid redirects)")
    
    # Database Configuration
    database_url: str = Field(..., description="PostgreSQL database URL")
    
    # WordPress Integration
    wordpress_api_url: str = Field(..., description="WordPress REST API base URL")
    wordpress_username: str = Field(..., description="WordPress username")
    wordpress_app_password: str = Field(..., description="WordPress application password")
    
    # Security Configuration
    secret_key: str = Field(..., description="Secret key for JWT tokens")
    agent_api_key: str = Field(..., description="API key for AI agent authentication")
    
    # Optional Configuration
    debug: bool = False
    log_level: str = "INFO"
    
    model_config = {
        "env_file": ".env", 
        "env_file_encoding": "utf-8"
    }


settings = Settings()