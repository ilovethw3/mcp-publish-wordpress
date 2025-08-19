"""
API Key utilities for MCP WordPress Publisher v2.1

This module provides API key utilities including validation, 
masking, and security helpers.
"""

import hmac
from typing import Dict, Any


def create_masked_api_key(api_key: str) -> str:
    """创建掩码显示的API密钥，显示前后8位
    
    Args:
        api_key: 原始API密钥
        
    Returns:
        str: 掩码后的密钥显示
    """
    if len(api_key) <= 16:
        # 如果密钥太短，只显示前几位
        return f"{api_key[:4]}{'*' * (len(api_key) - 4)}"
    
    # 显示前8位和后8位，中间用*替代
    middle_length = len(api_key) - 16
    return f"{api_key[:8]}{'*' * middle_length}{api_key[-8:]}"


def secure_compare(a: str, b: str) -> bool:
    """安全的字符串比较，防护时序攻击
    
    Args:
        a: 第一个字符串
        b: 第二个字符串
        
    Returns:
        bool: 字符串是否相等
    """
    return hmac.compare_digest(a.encode('utf-8'), b.encode('utf-8'))


def validate_key_format(key: str, min_length: int = 32, required_entropy: float = 0.5) -> Dict[str, Any]:
    """验证密钥格式并返回详细信息
    
    Args:
        key: 要验证的密钥
        min_length: 最小长度要求
        required_entropy: 最小熵值要求
        
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
    if len(key) < min_length:
        result["valid"] = False
        result["issues"].append(f"密钥长度不足，至少需要{min_length}字符")
    
    # 计算熵值
    if key:
        unique_chars = len(set(key))
        result["entropy"] = unique_chars / len(key)
        
        if result["entropy"] < required_entropy:
            result["valid"] = False
            result["issues"].append(f"密钥字符多样性不足，要求熵值至少{required_entropy}")
    
    # 确定强度等级
    if len(key) >= 64 and result["entropy"] >= 0.7:
        result["strength"] = "strong"
    elif len(key) >= 32 and result["entropy"] >= 0.5:
        result["strength"] = "medium"
    else:
        result["strength"] = "weak"
    
    return result