#!/usr/bin/env python3
"""
测试Web UI完整工作流
验证从数据库初始化到文章审批的完整流程
"""

import asyncio
import sys
from pathlib import Path

# Setup imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp_wordpress.core.database import get_session
from mcp_wordpress.services.config_service import config_service
from mcp_wordpress.models.article import Article, ArticleStatus
from mcp_wordpress.models.agent import Agent
from sqlalchemy import text, select
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_webui_agent_exists():
    """测试Web UI系统Agent是否存在"""
    try:
        agent = await config_service.get_agent("web-ui-internal")
        logger.info(f"✅ Web UI系统Agent存在: {agent.name}")
        logger.info(f"   ID: {agent.id}")
        logger.info(f"   状态: {agent.status}")
        logger.info(f"   API密钥哈希: {agent.api_key_hash[:10]}...")
        logger.info(f"   权限: 审批={agent.permissions.get('can_approve_articles')}, 拒绝={agent.permissions.get('can_reject_articles')}")
        return True
    except Exception as e:
        logger.error(f"❌ Web UI系统Agent不存在: {e}")
        return False

async def test_sample_article_exists():
    """测试是否有待审核的文章"""
    try:
        async with get_session() as session:
            result = await session.execute(
                select(Article).where(Article.status == ArticleStatus.PENDING_REVIEW.value).limit(1)
            )
            article = result.scalars().first()
            
            if article:
                logger.info(f"✅ 找到待审核文章: {article.title}")
                logger.info(f"   ID: {article.id}")
                logger.info(f"   状态: {article.status}")
                logger.info(f"   创建时间: {article.created_at}")
                return article.id
            else:
                logger.warning("⚠️  没有找到待审核的文章")
                return None
    except Exception as e:
        logger.error(f"❌ 查询文章失败: {e}")
        return None

async def create_sample_article():
    """创建一个测试文章"""
    try:
        async with get_session() as session:
            article = Article(
                title="测试文章 - Web UI工作流验证",
                content_markdown="# 测试内容\n\n这是一个用于测试Web UI审批工作流的测试文章。\n\n包含以下内容：\n- 测试MCP工具调用\n- 测试WordPress发布\n- 测试认证流程",
                agent_id="test-agent",
                status=ArticleStatus.PENDING_REVIEW.value,
                tags="测试,Web UI,MCP",
                category="测试"
            )
            
            session.add(article)
            await session.commit()
            await session.refresh(article)
            
            logger.info(f"✅ 创建测试文章成功: {article.title}")
            logger.info(f"   ID: {article.id}")
            return article.id
            
    except Exception as e:
        logger.error(f"❌ 创建测试文章失败: {e}")
        return None

async def check_env_file():
    """检查Web UI环境文件配置"""
    env_file = Path("web-ui/.env.local")
    
    if not env_file.exists():
        logger.error("❌ Web UI环境文件不存在: web-ui/.env.local")
        return False
    
    content = env_file.read_text()
    
    if "WEB_UI_AGENT_API_KEY=" in content:
        # 提取API密钥前缀
        for line in content.split('\n'):
            if line.startswith('WEB_UI_AGENT_API_KEY='):
                api_key = line.split('=', 1)[1]
                logger.info(f"✅ Web UI环境文件包含API密钥: {api_key[:10]}...")
                return True
    
    logger.warning("⚠️  Web UI环境文件缺少 WEB_UI_AGENT_API_KEY")
    return False

async def main():
    """主测试函数"""
    logger.info("🚀 开始Web UI工作流测试...")
    logger.info("=" * 60)
    
    # 1. 检查Web UI Agent
    logger.info("1️⃣ 检查Web UI系统Agent...")
    if not await test_webui_agent_exists():
        logger.error("❌ 请先运行: python init_production_db.py")
        return
    
    # 2. 检查环境文件配置
    logger.info("\n2️⃣ 检查Web UI环境配置...")
    if not await check_env_file():
        logger.error("❌ 请先运行: python init_production_db.py")
        return
    
    # 3. 检查测试文章
    logger.info("\n3️⃣ 检查测试文章...")
    article_id = await test_sample_article_exists()
    
    if not article_id:
        logger.info("📝 创建测试文章...")
        article_id = await create_sample_article()
        
        if not article_id:
            logger.error("❌ 无法创建测试文章")
            return
    
    # 4. 总结和下一步
    logger.info("\n" + "=" * 60)
    logger.info("🎉 Web UI工作流准备完成!")
    logger.info("\n📋 测试清单:")
    logger.info("   ✅ Web UI系统Agent已创建")
    logger.info("   ✅ API密钥已配置到环境文件")
    logger.info(f"   ✅ 测试文章已准备 (ID: {article_id})")
    
    logger.info("\n🔄 下一步测试:")
    logger.info("   1. 启动MCP服务器: python -m mcp_wordpress.server")
    logger.info("   2. 启动Web UI: cd web-ui && npm run dev")
    logger.info("   3. 访问文章管理页面测试审批功能")
    logger.info(f"   4. 尝试审批文章ID {article_id}")
    
    logger.info("\n🔍 预期测试结果:")
    logger.info("   - Web UI启动时显示MCP连接正常")
    logger.info("   - 点击审批按钮触发WordPress发布")
    logger.info("   - 文章状态从'待审核'变为'已发布'")
    logger.info("   - 显示WordPress文章ID和链接")

if __name__ == "__main__":
    asyncio.run(main())