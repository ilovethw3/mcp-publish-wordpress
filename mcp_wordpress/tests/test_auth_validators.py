"""
Tests for API key validators in MCP WordPress Publisher v2.1
"""

import pytest
from mcp_wordpress.auth.validators import AgentKeyValidator


class TestAgentKeyValidator:
    """Tests for AgentKeyValidator"""
    
    @pytest.fixture
    def validator(self):
        """AgentKeyValidator instance for testing"""
        return AgentKeyValidator()
    
    def test_hash_api_key(self, validator):
        """测试API密钥哈希"""
        key = "test-api-key-12345678901234567890"
        hashed = validator.hash_api_key(key)
        
        assert hashed is not None
        assert hashed != key  # 确保已哈希
        assert hashed.startswith('$2b$')  # bcrypt哈希格式
    
    def test_verify_api_key_valid(self, validator):
        """测试有效API密钥验证"""
        key = "test-api-key-12345678901234567890"
        hashed = validator.hash_api_key(key)
        
        assert validator.verify_api_key(key, hashed) is True
    
    def test_verify_api_key_invalid(self, validator):
        """测试无效API密钥验证"""
        key = "test-api-key-12345678901234567890"
        wrong_key = "wrong-api-key-12345678901234567890"
        hashed = validator.hash_api_key(key)
        
        assert validator.verify_api_key(wrong_key, hashed) is False
    
    def test_verify_api_key_corrupted_hash(self, validator):
        """测试损坏的哈希验证"""
        key = "test-api-key-12345678901234567890"
        corrupted_hash = "corrupted_hash_string"
        
        assert validator.verify_api_key(key, corrupted_hash) is False
    
    def test_is_key_strong_valid(self, validator):
        """测试强密钥验证"""
        strong_key = "sk-abcdef1234567890ABCDEF1234567890xyz"
        assert validator.is_key_strong(strong_key) is True
    
    def test_is_key_strong_too_short(self, validator):
        """测试过短的密钥"""
        short_key = "short_key"
        assert validator.is_key_strong(short_key) is False
    
    def test_is_key_strong_low_entropy(self, validator):
        """测试低熵值的密钥"""
        low_entropy_key = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"  # 32个a
        assert validator.is_key_strong(low_entropy_key) is False
    
    def test_secure_compare_equal(self, validator):
        """测试安全字符串比较 - 相等"""
        a = "test_string_123"
        b = "test_string_123"
        assert validator.secure_compare(a, b) is True
    
    def test_secure_compare_not_equal(self, validator):
        """测试安全字符串比较 - 不相等"""
        a = "test_string_123"
        b = "test_string_456"
        assert validator.secure_compare(a, b) is False
    
    def test_validate_key_format_valid(self, validator):
        """测试有效密钥格式验证"""
        valid_key = "sk-abcdef1234567890ABCDEF1234567890xyz"
        result = validator.validate_key_format(valid_key)
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert result["length"] >= 32
        assert result["entropy"] >= 0.5
        assert result["strength"] in ["medium", "strong"]
    
    def test_validate_key_format_too_short(self, validator):
        """测试过短密钥的格式验证"""
        short_key = "short_key"
        result = validator.validate_key_format(short_key)
        
        assert result["valid"] is False
        assert "密钥长度不足" in result["issues"][0]
        assert result["strength"] == "weak"
    
    def test_validate_key_format_low_entropy(self, validator):
        """测试低熵值密钥的格式验证"""
        low_entropy_key = "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"
        result = validator.validate_key_format(low_entropy_key)
        
        assert result["valid"] is False
        assert any("字符多样性不足" in issue for issue in result["issues"])
        assert result["entropy"] < 0.5
        assert result["strength"] == "weak"
    
    def test_validate_key_format_empty_key(self, validator):
        """测试空密钥的格式验证"""
        empty_key = ""
        result = validator.validate_key_format(empty_key)
        
        assert result["valid"] is False
        assert len(result["issues"]) > 0
        assert result["length"] == 0
        assert result["strength"] == "weak"
    
    def test_validate_key_format_strong_key(self, validator):
        """测试强密钥的格式验证"""
        strong_key = "sk-A1b2C3d4E5f6G7h8I9j0K1l2M3n4O5p6Q7r8S9t0U1v2W3x4Y5z6A7B8C9D0E1F2"
        result = validator.validate_key_format(strong_key)
        
        assert result["valid"] is True
        assert len(result["issues"]) == 0
        assert result["length"] >= 64
        assert result["entropy"] >= 0.7
        assert result["strength"] == "strong"