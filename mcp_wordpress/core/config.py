"""Configuration management for MCP WordPress Publisher v2.1."""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Literal, Optional


class Settings(BaseSettings):
    """Application settings loaded from environment variables for v2.1 multi-agent/multi-site architecture."""
    
    # MCP Server Configuration
    mcp_server_name: str = "MCP WordPress Publisher v2.1"
    mcp_transport: Literal["stdio", "sse"] = "sse"
    mcp_port: int = 8000
    mcp_sse_path: str = Field(default="/sse", description="SSE endpoint path (without trailing slash to avoid redirects)")
    
    # Database Configuration
    database_url: str = Field(..., description="PostgreSQL database URL")
    
    # Redis Configuration (Optional for caching and sessions)
    redis_url: Optional[str] = Field(None, description="Redis URL for caching and session management")
    
    # Security Configuration
    secret_key: str = Field(..., description="Secret key for JWT tokens and encryption")
    jwt_secret_key: str = Field(..., description="JWT secret key for authentication tokens")
    encryption_key: Optional[str] = Field(None, description="Encryption key for sensitive data")
    
    # Multi-Agent Configuration
    multi_agent_mode: bool = Field(default=True, description="Enable multi-agent support")
    agent_config_path: str = Field(default="/app/config/agents.yml", description="Path to agents configuration file")
    
    # Multi-Site Configuration  
    multi_site_mode: bool = Field(default=True, description="Enable multi-site support")
    site_config_path: str = Field(default="/app/config/sites.yml", description="Path to sites configuration file")
    
    # Legacy WordPress Configuration (Optional for backward compatibility)
    wordpress_api_url: Optional[str] = Field(None, description="Legacy: WordPress REST API base URL")
    wordpress_username: Optional[str] = Field(None, description="Legacy: WordPress username")
    wordpress_app_password: Optional[str] = Field(None, description="Legacy: WordPress application password")
    agent_api_key: Optional[str] = Field(None, description="Legacy: Single agent API key")
    
    # Logging and Monitoring Configuration
    debug: bool = False
    log_level: str = "INFO"
    enable_audit_logging: bool = Field(default=True, description="Enable audit logging")
    enable_metrics: bool = Field(default=True, description="Enable metrics collection")
    
    # Rate Limiting and Security Features
    enable_rate_limiting: bool = Field(default=True, description="Enable rate limiting")
    enable_api_versioning: bool = Field(default=True, description="Enable API versioning")
    
    model_config = {
        "env_file": ".env", 
        "env_file_encoding": "utf-8"
    }


settings = Settings()