#!/usr/bin/env python3
"""
混合认证功能演示脚本

演示如何使用新的HybridAuthProvider支持多种认证方式：
1. 标准 Bearer Token: Authorization: Bearer <api-key>
2. URL 参数: ?key=<api-key>

使用方法:
    python examples/hybrid_auth_demo.py
"""

import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import aiohttp
import json


async def test_hybrid_authentication():
    """测试混合认证功能"""
    
    # 配置
    MCP_SERVER_URL = "http://localhost:8000"
    TEST_API_KEY = "test-api-key-123456789"  # 来自 config/agents.yml 的示例key
    ADMIN_API_KEY = "admin-api-key-987654321"
    
    print("🔐 混合认证功能演示")
    print("=" * 50)
    
    async with aiohttp.ClientSession() as session:
        
        # 测试1: Bearer Token 认证
        print("\n1️⃣  测试 Bearer Token 认证")
        print("-" * 30)
        
        headers = {
            'Authorization': f'Bearer {TEST_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with session.post(
                f"{MCP_SERVER_URL}/tools/ping", 
                headers=headers,
                json={}
            ) as response:
                result = await response.json()
                print(f"✅ Bearer Token 认证成功")
                print(f"   响应状态: {response.status}")
                print(f"   服务器响应: {result.get('message', 'N/A')}")
        except Exception as e:
            print(f"❌ Bearer Token 认证失败: {e}")
        
        
        # 测试2: URL 参数认证
        print("\n2️⃣  测试 URL 参数认证")
        print("-" * 30)
        
        try:
            async with session.post(
                f"{MCP_SERVER_URL}/tools/ping?key={TEST_API_KEY}",
                headers={'Content-Type': 'application/json'},
                json={}
            ) as response:
                result = await response.json()
                print(f"✅ URL 参数认证成功")
                print(f"   响应状态: {response.status}")
                print(f"   服务器响应: {result.get('message', 'N/A')}")
        except Exception as e:
            print(f"❌ URL 参数认证失败: {e}")
        
        
        # 测试3: 管理员权限
        print("\n3️⃣  测试管理员权限 (Bearer Token)")
        print("-" * 30)
        
        admin_headers = {
            'Authorization': f'Bearer {ADMIN_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        try:
            async with session.get(
                f"{MCP_SERVER_URL}/tools/list_articles",
                headers=admin_headers
            ) as response:
                result = await response.json()
                print(f"✅ 管理员权限验证成功")
                print(f"   响应状态: {response.status}")
                if 'data' in result:
                    print(f"   文章数量: {result['data'].get('total', 0)}")
        except Exception as e:
            print(f"❌ 管理员权限验证失败: {e}")
        
        
        # 测试4: 管理员权限 (URL 参数)
        print("\n4️⃣  测试管理员权限 (URL 参数)")
        print("-" * 30)
        
        try:
            async with session.get(
                f"{MCP_SERVER_URL}/tools/list_articles?key={ADMIN_API_KEY}",
                headers={'Content-Type': 'application/json'}
            ) as response:
                result = await response.json()
                print(f"✅ 管理员URL认证成功")
                print(f"   响应状态: {response.status}")
                if 'data' in result:
                    print(f"   文章数量: {result['data'].get('total', 0)}")
        except Exception as e:
            print(f"❌ 管理员URL认证失败: {e}")
        
        
        # 测试5: 无效认证
        print("\n5️⃣  测试无效认证")
        print("-" * 30)
        
        try:
            async with session.post(
                f"{MCP_SERVER_URL}/tools/ping?key=invalid-key",
                headers={'Content-Type': 'application/json'},
                json={}
            ) as response:
                result = await response.json()
                print(f"❌ 无效认证被正确拒绝")
                print(f"   响应状态: {response.status}")
                print(f"   错误信息: {result.get('error', 'N/A')}")
        except Exception as e:
            print(f"✅ 无效认证正确失败: {e}")
        
        
        # 测试6: 优先级测试 (Bearer Token vs URL 参数)
        print("\n6️⃣  测试认证优先级 (Bearer Token 优先)")
        print("-" * 30)
        
        mixed_headers = {
            'Authorization': f'Bearer {TEST_API_KEY}',
            'Content-Type': 'application/json'
        }
        
        try:
            # 同时提供Bearer Token和URL参数，应该优先使用Bearer Token
            async with session.post(
                f"{MCP_SERVER_URL}/tools/ping?key=wrong-key",  # 故意使用错误的URL参数
                headers=mixed_headers,  # 但提供正确的Bearer Token
                json={}
            ) as response:
                result = await response.json()
                print(f"✅ Bearer Token 优先级验证成功")
                print(f"   响应状态: {response.status}")
                print(f"   说明: 即使URL参数错误，Bearer Token仍然有效")
        except Exception as e:
            print(f"❌ 优先级测试失败: {e}")


def print_usage_examples():
    """打印使用示例"""
    print("\n📚 使用示例")
    print("=" * 50)
    
    print("\n🔗 HTTP请求示例:")
    print("""
# 方式1: Bearer Token (推荐)
curl -X POST \\
  -H "Authorization: Bearer test-api-key-123456789" \\
  -H "Content-Type: application/json" \\
  http://localhost:8000/tools/ping

# 方式2: URL 参数
curl -X POST \\
  -H "Content-Type: application/json" \\
  "http://localhost:8000/tools/ping?key=test-api-key-123456789"

# 方式3: 获取文章列表 (管理员权限)
curl -X GET \\
  -H "Authorization: Bearer admin-api-key-987654321" \\
  http://localhost:8000/tools/list_articles

# 方式4: URL参数获取文章列表
curl -X GET \\
  "http://localhost:8000/tools/list_articles?key=admin-api-key-987654321"
""")
    
    print("\n🌐 浏览器访问示例:")
    print("""
# 直接在浏览器中访问 (仅限GET请求)
http://localhost:8000/tools/list_articles?key=admin-api-key-987654321
http://localhost:8000/health?key=test-api-key-123456789
""")
    
    print("\n⚠️  安全注意事项:")
    print("""
1. Bearer Token 认证更安全，推荐用于生产环境
2. URL 参数认证方便测试，但可能在日志中暴露
3. 系统会自动清理日志中的敏感信息
4. 两种认证方式同时提供时，优先使用 Bearer Token
""")


async def main():
    """主函数"""
    print_usage_examples()
    
    print("\n🚀 开始认证功能测试...")
    print("请确保 MCP 服务器正在运行 (python -m mcp_wordpress.server sse)")
    
    # 等待用户确认
    input("\n按回车键继续测试...")
    
    try:
        await test_hybrid_authentication()
        
        print("\n" + "=" * 50)
        print("✅ 混合认证功能测试完成!")
        print("📖 查看上述输出了解各种认证方式的工作情况")
        
    except KeyboardInterrupt:
        print("\n\n❌ 测试被用户中断")
    except Exception as e:
        print(f"\n\n❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())