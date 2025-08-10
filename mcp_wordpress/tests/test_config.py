"""Tests for configuration management."""

import pytest
import os
from unittest.mock import patch

from mcp_wordpress.core.config import Settings
from pydantic import ValidationError


class TestSettings:
    """Test Settings configuration loading and validation."""
    
    def test_settings_with_env_vars(self):
        """Test settings loading from environment variables."""
        env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/testdb",
            "WORDPRESS_API_URL": "https://test.com/wp-json/wp/v2",
            "WORDPRESS_USERNAME": "testuser",
            "WORDPRESS_APP_PASSWORD": "testpass",
            "SECRET_KEY": "test_secret_key",
            "AGENT_API_KEY": "test_agent_key"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            assert settings.database_url == "postgresql://test:test@localhost:5432/testdb"
            assert settings.wordpress_api_url == "https://test.com/wp-json/wp/v2"
            assert settings.wordpress_username == "testuser"
            assert settings.wordpress_app_password == "testpass"
            assert settings.secret_key == "test_secret_key"
            assert settings.agent_api_key == "test_agent_key"
    
    def test_settings_with_optional_defaults(self):
        """Test settings with optional field defaults."""
        required_env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/testdb",
            "WORDPRESS_API_URL": "https://test.com/wp-json/wp/v2", 
            "WORDPRESS_USERNAME": "testuser",
            "WORDPRESS_APP_PASSWORD": "testpass",
            "SECRET_KEY": "test_secret_key",
            "AGENT_API_KEY": "test_agent_key"
        }
        
        with patch.dict(os.environ, required_env_vars, clear=True):
            settings = Settings()
            
            # Test defaults
            assert settings.mcp_server_name == "wordpress-publisher"
            assert settings.mcp_transport == "stdio"
            assert settings.mcp_port == 8000
            assert settings.debug is False
            assert settings.log_level == "INFO"
    
    def test_settings_missing_required_fields(self):
        """Test settings validation with missing required fields."""
        with patch.dict(os.environ, {}, clear=True):
            with pytest.raises(ValidationError):  # Specific ValidationError from pydantic
                # Create Settings without .env file loading
                Settings(_env_file=None)
    
    def test_settings_mcp_transport_validation(self):
        """Test MCP transport type validation."""
        env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/testdb",
            "WORDPRESS_API_URL": "https://test.com/wp-json/wp/v2",
            "WORDPRESS_USERNAME": "testuser", 
            "WORDPRESS_APP_PASSWORD": "testpass",
            "SECRET_KEY": "test_secret_key",
            "AGENT_API_KEY": "test_agent_key",
            "MCP_TRANSPORT": "sse"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            assert settings.mcp_transport == "sse"
        
        # Test invalid transport type
        env_vars["MCP_TRANSPORT"] = "invalid"
        with patch.dict(os.environ, env_vars):
            with pytest.raises(Exception):  # ValidationError
                Settings()
    
    def test_settings_debug_mode(self):
        """Test debug mode configuration."""
        env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/testdb",
            "WORDPRESS_API_URL": "https://test.com/wp-json/wp/v2",
            "WORDPRESS_USERNAME": "testuser",
            "WORDPRESS_APP_PASSWORD": "testpass", 
            "SECRET_KEY": "test_secret_key",
            "AGENT_API_KEY": "test_agent_key",
            "DEBUG": "true"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            assert settings.debug is True
    
    @pytest.mark.unit
    def test_database_url_parsing(self):
        """Test database URL format validation."""
        env_vars = {
            "DATABASE_URL": "postgresql://user:pass@host:5432/db",
            "WORDPRESS_API_URL": "https://test.com/wp-json/wp/v2",
            "WORDPRESS_USERNAME": "testuser",
            "WORDPRESS_APP_PASSWORD": "testpass",
            "SECRET_KEY": "test_secret_key", 
            "AGENT_API_KEY": "test_agent_key"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            # Basic URL validation
            assert "postgresql://" in settings.database_url
            assert "@" in settings.database_url
            assert ":" in settings.database_url
    
    @pytest.mark.unit  
    def test_wordpress_api_url_validation(self):
        """Test WordPress API URL format validation."""
        env_vars = {
            "DATABASE_URL": "postgresql://test:test@localhost:5432/testdb",
            "WORDPRESS_API_URL": "https://example.com/wp-json/wp/v2",
            "WORDPRESS_USERNAME": "testuser",
            "WORDPRESS_APP_PASSWORD": "testpass",
            "SECRET_KEY": "test_secret_key",
            "AGENT_API_KEY": "test_agent_key"
        }
        
        with patch.dict(os.environ, env_vars):
            settings = Settings()
            
            # Should end with wp-json/wp/v2
            assert settings.wordpress_api_url.endswith("/wp-json/wp/v2")
            assert settings.wordpress_api_url.startswith("https://")