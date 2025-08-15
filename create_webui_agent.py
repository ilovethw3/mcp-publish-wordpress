#!/usr/bin/env python3
"""
Create Web UI System Agent
为Web UI创建系统内部使用的Agent配置
"""

import asyncio
import secrets
import sys
from datetime import datetime, timezone
from pathlib import Path

# Setup imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp_wordpress.services.config_service import config_service
from mcp_wordpress.core.database import get_session
from sqlalchemy import text

async def create_webui_agent():
    """创建Web UI系统Agent"""
    
    # 生成安全的API密钥
    api_key = f"webui_{secrets.token_urlsafe(32)}"
    
    agent_config = {
        "agent_id": "web-ui-internal",
        "name": "Web UI Internal Agent",
        "description": "Internal system agent for Web UI operations - DO NOT DELETE",
        "api_key": api_key,
        "status": "active",
        "rate_limit": {
            "requests_per_minute": 100,  # 高频率限制，因为Web UI可能有多个并发请求
            "requests_per_hour": 1000,
            "requests_per_day": 10000
        },
        "permissions": {
            "can_submit_articles": False,  # Web UI不提交文章，只审核
            "can_edit_own_articles": False,
            "can_delete_own_articles": False,
            "can_view_statistics": True,
            "can_approve_articles": True,  # 关键权限：可以审批文章
            "can_reject_articles": True,   # 关键权限：可以拒绝文章
            "allowed_categories": [],  # 无限制
            "allowed_tags": []         # 无限制
        },
        "notifications": {
            "on_approval": False,      # 系统Agent不需要通知
            "on_rejection": False,
            "on_publish_success": False,
            "on_publish_failure": False
        }
    }
    
    try:
        # 检查是否已存在
        existing_agent = None
        try:
            existing_agent = await config_service.get_agent("web-ui-internal")
            print("⚠️  Web UI系统Agent已存在")
            print(f"   ID: {existing_agent.id}")
            print(f"   名称: {existing_agent.name}")
            print(f"   状态: {existing_agent.status}")
            
            # 显示现有API密钥（部分）
            if existing_agent.api_key_hash:
                print(f"   API密钥: {existing_agent.api_key_hash[:10]}...")
            
            update_choice = input("是否更新现有Agent配置? (y/N): ")
            if update_choice.lower() != 'y':
                return existing_agent
                
        except Exception:
            # Agent不存在，继续创建
            pass
        
        if existing_agent:
            # 更新现有Agent
            updated_agent = await config_service.update_agent(
                agent_id="web-ui-internal",
                **agent_config
            )
            print("✅ Web UI系统Agent已更新")
            agent = updated_agent
        else:
            # 创建新Agent
            agent = await config_service.create_agent(**agent_config)
            print("✅ Web UI系统Agent已创建")
        
        print(f"   ID: {agent.id}")
        print(f"   名称: {agent.name}")
        print(f"   状态: {agent.status}")
        print(f"   API密钥: {api_key}")
        
        # 生成环境配置
        print("\n📝 请将以下配置添加到 web-ui/.env.local:")
        print(f"WEB_UI_AGENT_API_KEY={api_key}")
        
        # 验证Agent权限
        print(f"\n🔒 权限验证:")
        print(f"   可审批文章: {agent.permissions.get('can_approve_articles', False)}")
        print(f"   可拒绝文章: {agent.permissions.get('can_reject_articles', False)}")
        print(f"   可查看统计: {agent.permissions.get('can_view_statistics', False)}")
        
        return agent
        
    except Exception as e:
        print(f"❌ 创建Web UI系统Agent失败: {e}")
        import traceback
        traceback.print_exc()
        return None

async def verify_agent_access():
    """验证Agent访问权限"""
    try:
        # 测试数据库连接
        async with get_session() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM agents WHERE id = 'web-ui-internal'"))
            count = result.scalar()
            
            if count > 0:
                print("✅ 数据库验证：Web UI Agent存在")
                
                # 获取Agent详细信息
                result = await session.execute(text("""
                    SELECT id, name, status, rate_limit, permissions 
                    FROM agents 
                    WHERE id = 'web-ui-internal'
                """))
                agent_row = result.fetchone()
                
                if agent_row:
                    print(f"   ID: {agent_row.id}")
                    print(f"   名称: {agent_row.name}")
                    print(f"   状态: {agent_row.status}")
                    print(f"   权限: {agent_row.permissions}")
                
                return True
            else:
                print("❌ 数据库验证：Web UI Agent不存在")
                return False
                
    except Exception as e:
        print(f"❌ 数据库验证失败: {e}")
        return False

async def main():
    """主函数"""
    print("🚀 创建Web UI系统Agent...")
    print("=" * 50)
    
    # 创建Agent
    agent = await create_webui_agent()
    
    if agent:
        print("\n" + "=" * 50)
        print("🔍 验证Agent配置...")
        
        # 验证访问权限
        if await verify_agent_access():
            print("\n🎉 Web UI系统Agent配置完成！")
            print("\n下一步：")
            print("1. 将API密钥添加到 web-ui/.env.local")
            print("2. 重启Web UI服务")
            print("3. 测试文章审批功能")
        else:
            print("\n❌ Agent验证失败，请检查配置")
    else:
        print("\n❌ Web UI系统Agent创建失败")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())