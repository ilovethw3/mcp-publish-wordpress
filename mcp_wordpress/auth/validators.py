"""
API Key validation utilities for MCP WordPress Publisher v2.1

This module provides secure API key validation and management functionality
with protection against timing attacks and proper key strength validation.
"""

import secrets
import hashlib
import hmac
from typing import Optional, Dict, Any
import bcrypt


class AgentKeyValidator:
    """Secure API key validator with timing attack protection"""
    
    def __init__(self):
        self.min_key_length = 32
        self.required_entropy = 0.5
    
    def hash_api_key(self, key: str) -> str:
        """使用bcrypt安全哈希API密钥
        
        Args:
            key: 原始API密钥
            
        Returns:
            str: 哈希后的密钥
        """
        return bcrypt.hashpw(key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    def verify_api_key(self, key: str, hashed: str) -> bool:
        """验证API密钥，防护时序攻击
        
        Args:
            key: 要验证的密钥
            hashed: 存储的哈希值
            
        Returns:
            bool: 密钥是否有效
        """
        try:
            return bcrypt.checkpw(key.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    def is_key_strong(self, key: str) -> bool:
        """检查API密钥强度
        
        Args:
            key: 要检查的密钥
            
        Returns:
            bool: 密钥是否满足强度要求
        """
        if len(key) < self.min_key_length:
            return False
        
        # 检查字符多样性（熵值）
        unique_chars = len(set(key))
        entropy = unique_chars / len(key)
        
        return entropy >= self.required_entropy
    
    def secure_compare(self, a: str, b: str) -> bool:
        """安全的字符串比较，防护时序攻击
        
        Args:
            a: 第一个字符串
            b: 第二个字符串
            
        Returns:
            bool: 字符串是否相等
        """
        return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))
    
    def validate_key_format(self, key: str) -> Dict[str, Any]:
        """验证密钥格式并返回详细信息
        
        Args:
            key: 要验证的密钥
            
        Returns:
            dict: 验证结果详情
        """
        result = {
            "valid": True,
            "issues": [],
            "length": len(key),
            "entropy": 0.0,
            "strength": "unknown"
        }
        
        # 检查长度
        if len(key) < self.min_key_length:
            result["valid"] = False
            result["issues"].append(f"密钥长度不足，至少需要{self.min_key_length}字符")
        
        # 计算熵值
        if key:
            unique_chars = len(set(key))
            result["entropy"] = unique_chars / len(key)
            
            if result["entropy"] < self.required_entropy:
                result["valid"] = False
                result["issues"].append(f"密钥字符多样性不足，要求熵值至少{self.required_entropy}")
        
        # 确定强度等级
        if len(key) >= 64 and result["entropy"] >= 0.7:
            result["strength"] = "strong"
        elif len(key) >= 32 and result["entropy"] >= 0.5:
            result["strength"] = "medium"
        else:
            result["strength"] = "weak"
        
        return result