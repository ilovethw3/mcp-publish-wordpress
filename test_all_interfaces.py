#!/usr/bin/env python3
"""
测试 MCP WordPress 服务器的所有接口
"""

import asyncio
import json
from mcp import ClientSession, stdio_client
import subprocess
import sys
import os

async def test_submit_article(session):
    """测试提交文章接口"""
    print("🔍 测试 submit_article 工具...")
    try:
        result = await session.call_tool("submit_article", {
            "title": "测试文章 - MCP WordPress 接口测试",
            "content_markdown": """# MCP WordPress 接口测试

这是一篇用于测试 MCP WordPress 服务器接口功能的文章。

## 测试内容

- 文章提交功能
- 内容审核流程  
- WordPress 发布集成

## 技术特点

1. **MCP 协议支持**：完整实现了 Model Context Protocol
2. **异步处理**：使用 FastAPI 和异步数据库操作
3. **WordPress 集成**：通过 REST API 自动发布内容

这是一个测试文章，用于验证系统的各项功能是否正常工作。""",
            "tags": "测试,MCP,WordPress,接口",
            "category": "技术测试"
        })
        print(f"✅ submit_article 成功: {result}")
        response = json.loads(result.content[0].text)
        return response.get('article_id')
    except Exception as e:
        print(f"❌ submit_article 失败: {e}")
        return None

async def test_list_articles(session):
    """测试列出文章接口"""
    print("🔍 测试 list_articles 工具...")
    try:
        result = await session.call_tool("list_articles", {})
        print(f"✅ list_articles 成功: {result}")
        return True
    except Exception as e:
        print(f"❌ list_articles 失败: {e}")
        return False

async def test_get_article_status(session, article_id):
    """测试获取文章状态接口"""
    print(f"🔍 测试 get_article_status 工具 (article_id: {article_id})...")
    if not article_id:
        print("⚠️ 跳过 get_article_status 测试 (没有有效的 article_id)")
        return False
        
    try:
        result = await session.call_tool("get_article_status", {
            "article_id": article_id
        })
        print(f"✅ get_article_status 成功: {result}")
        return True
    except Exception as e:
        print(f"❌ get_article_status 失败: {e}")
        return False

async def test_approve_article(session, article_id):
    """测试批准文章接口"""
    print(f"🔍 测试 approve_article 工具 (article_id: {article_id})...")
    if not article_id:
        print("⚠️ 跳过 approve_article 测试 (没有有效的 article_id)")
        return False
        
    try:
        result = await session.call_tool("approve_article", {
            "article_id": article_id,
            "reviewer_notes": "自动化测试批准"
        })
        print(f"✅ approve_article 成功: {result}")
        return True
    except Exception as e:
        print(f"❌ approve_article 失败: {e}")
        return False

async def test_reject_article(session, article_id):
    """测试拒绝文章接口"""
    print(f"🔍 测试 reject_article 工具 (article_id: {article_id})...")
    if not article_id:
        print("⚠️ 跳过 reject_article 测试 (没有有效的 article_id)")
        return False
        
    try:
        # 为了测试拒绝功能，我们需要先创建另一篇文章
        submit_result = await session.call_tool("submit_article", {
            "title": "测试拒绝文章",
            "content_markdown": "这是用于测试拒绝功能的文章",
            "tags": "测试",
            "category": "测试"
        })
        
        if submit_result:
            reject_response = json.loads(submit_result.content[0].text)
            reject_article_id = reject_response.get('article_id')
            
            result = await session.call_tool("reject_article", {
                "article_id": reject_article_id,
                "rejection_reason": "自动化测试拒绝"
            })
            print(f"✅ reject_article 成功: {result}")
            return True
    except Exception as e:
        print(f"❌ reject_article 失败: {e}")
        return False

async def test_all_interfaces():
    """测试所有接口"""
    print("🚀 开始测试 MCP WordPress 服务器接口...")
    
    # 启动 MCP 服务器进程
    server_params = {
        "command": sys.executable,
        "args": ["-m", "mcp_wordpress.server"]
    }
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                
                print("📋 可用工具:")
                tools_result = await session.list_tools()
                if hasattr(tools_result, 'tools'):
                    for tool in tools_result.tools:
                        print(f"  - {tool.name}")
                else:
                    print("  无法获取工具列表")
                
                print("\n" + "="*50)
                print("开始接口测试")
                print("="*50)
                
                # 测试提交文章
                article_id = await test_submit_article(session)
                
                # 测试列出文章
                await test_list_articles(session)
                
                # 测试获取文章状态
                await test_get_article_status(session, article_id)
                
                # 测试批准文章 (注意：这会发布到 WordPress)
                await test_approve_article(session, article_id)
                
                # 测试拒绝文章
                await test_reject_article(session, article_id)
                
                print("\n" + "="*50)
                print("接口测试完成")
                print("="*50)
                
    except Exception as e:
        print(f"❌ MCP 客户端连接失败: {e}")

if __name__ == "__main__":
    asyncio.run(test_all_interfaces())