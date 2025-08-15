#!/usr/bin/env python3
"""
生产环境数据库初始化脚本
确保部署时有干净的数据库环境
"""

import asyncio
import logging
import sys
import os
import secrets
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlparse
import asyncpg

# Setup imports
sys.path.insert(0, str(Path(__file__).parent))

from mcp_wordpress.core.database import get_session
from mcp_wordpress.core.config import settings
from mcp_wordpress.services.config_service import config_service
from sqlalchemy import text

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def parse_database_url(database_url: str):
    """解析数据库URL，分离服务器信息和数据库名"""
    # 移除 +asyncpg 后缀以便解析
    clean_url = database_url.replace('+asyncpg', '')
    parsed = urlparse(clean_url)
    
    # 构建服务器连接URL（连接到postgres默认数据库）
    server_url = f"{parsed.scheme}://{parsed.username}:{parsed.password}@{parsed.hostname}:{parsed.port}/postgres"
    
    # 获取目标数据库名
    database_name = parsed.path.lstrip('/')
    
    return server_url, database_name


async def check_database_exists(database_name: str) -> bool:
    """检查数据库是否存在"""
    try:
        server_url, _ = parse_database_url(settings.database_url)
        conn = await asyncpg.connect(server_url)
        
        try:
            result = await conn.fetchval(
                "SELECT 1 FROM pg_database WHERE datname = $1", 
                database_name
            )
            return result is not None
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"❌ 检查数据库存在性失败: {e}")
        return False


async def create_database(database_name: str) -> bool:
    """创建数据库"""
    try:
        server_url, _ = parse_database_url(settings.database_url)
        conn = await asyncpg.connect(server_url)
        
        try:
            logger.info(f"🏗️ 创建数据库: {database_name}")
            
            # 创建数据库
            await conn.execute(f'''
                CREATE DATABASE "{database_name}"
                WITH 
                    ENCODING = 'UTF8'
                    LC_COLLATE = 'en_US.utf8'
                    LC_CTYPE = 'en_US.utf8'
                    TEMPLATE = template0
            ''')
            
            logger.info(f"✅ 数据库 {database_name} 创建成功")
            return True
            
        finally:
            await conn.close()
            
    except Exception as e:
        logger.error(f"❌ 创建数据库失败: {e}")
        return False


def update_env_file(file_path: str, key: str, value: str):
    """安全地更新环境文件中的特定键值对"""
    try:
        file_path_obj = Path(file_path)
        
        # 确保目录存在
        file_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # 读取现有内容
        lines = []
        if file_path_obj.exists():
            with open(file_path_obj, 'r', encoding='utf-8') as f:
                lines = f.readlines()
        
        # 检查是否已存在该键
        key_found = False
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{key}="):
                lines[i] = f"{key}={value}\n"
                key_found = True
                logger.info(f"📝 更新现有配置: {key}={value[:10]}...")
                break
        
        # 如果没找到，添加新行
        if not key_found:
            # 确保文件以换行符结尾
            if lines and not lines[-1].endswith('\n'):
                lines[-1] += '\n'
            lines.append(f"{key}={value}\n")
            logger.info(f"📝 添加新配置: {key}={value[:10]}...")
        
        # 写回文件
        with open(file_path_obj, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        
        logger.info(f"✅ 环境文件已更新: {file_path}")
        return True
        
    except Exception as e:
        logger.error(f"❌ 更新环境文件失败: {e}")
        return False


async def run_alembic_upgrade():
    """运行 Alembic 升级到最新版本"""
    try:
        logger.info("🔖 运行 Alembic 数据库迁移...")
        
        # 检查是否有 alembic 配置
        if not Path("alembic.ini").exists():
            logger.warning("⚠️ 未找到 alembic.ini，跳过数据库迁移")
            return False
            
        # 运行升级到最新版本
        result = subprocess.run(
            ["alembic", "upgrade", "head"], 
            capture_output=True, 
            text=True,
            check=True
        )
        
        # 验证升级是否成功
        current_result = subprocess.run(
            ["alembic", "current"], 
            capture_output=True, 
            text=True,
            check=True
        )
        
        logger.info("✅ Alembic 数据库迁移完成")
        logger.info(f"📍 当前版本: {current_result.stdout.strip()}")
        return True
        
    except subprocess.CalledProcessError as e:
        logger.error(f"❌ Alembic 迁移失败: {e}")
        if e.stderr:
            logger.error(f"错误详情: {e.stderr}")
        logger.error("请检查数据库连接和迁移文件")
        return False
    except FileNotFoundError:
        logger.error("❌ Alembic 未安装，无法进行数据库迁移")
        logger.error("请安装 alembic: pip install alembic")
        return False
    except Exception as e:
        logger.error(f"❌ Alembic 迁移过程发生错误: {e}")
        return False


async def check_database_state():
    """检查数据库状态"""
    try:
        async with get_session() as session:
            # 检查是否有任何表
            result = await session.execute(text(
                "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'public'"
            ))
            table_count = result.scalar()
            
            if table_count == 0:
                logger.info("✅ 数据库为空，可以安全初始化")
                return "empty"
            
            # 检查是否有业务数据
            tables_to_check = ['articles', 'agents', 'sites', 'users']
            has_data = False
            
            for table in tables_to_check:
                try:
                    result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                    count = result.scalar()
                    if count > 0:
                        logger.warning(f"⚠️  表 {table} 包含 {count} 条记录")
                        has_data = True
                except:
                    # 表不存在，正常情况
                    pass
            
            if has_data:
                return "has_data"
            else:
                logger.info("✅ 数据库表存在但无业务数据")
                return "clean_schema"
                
    except Exception as e:
        logger.error(f"❌ 检查数据库状态失败: {e}")
        return "error"


async def clean_database():
    """清理数据库（仅在明确要求时）"""
    logger.warning("🧹 开始清理数据库...")
    
    async with get_session() as session:
        try:
            # 删除业务数据（保留表结构）
            tables_to_clean = ['articles', 'agents', 'sites', 'users']
            
            for table in tables_to_clean:
                try:
                    await session.execute(text(f"DELETE FROM {table}"))
                    logger.info(f"✅ 清理表数据: {table}")
                except Exception as e:
                    logger.warning(f"⚠️  清理表 {table} 失败: {e}")
            
            await session.commit()
            logger.info("✅ 数据库数据清理完成")
            
        except Exception as e:
            logger.error(f"❌ 数据库清理失败: {e}")
            await session.rollback()
            raise


async def drop_all_tables():
    """完全删除所有表和相关对象（强制重建时使用）"""
    logger.warning("🗑️  开始删除所有数据库对象...")
    
    # 首先检查数据库是否存在
    _, database_name = parse_database_url(settings.database_url)
    
    # 先检查数据库是否存在
    db_exists = await check_database_exists(database_name)
    
    if not db_exists:
        logger.warning(f"⚠️  数据库 {database_name} 不存在")
        logger.info(f"🏗️ 创建新数据库: {database_name}")
        success = await create_database(database_name)
        if success:
            logger.info("✅ 数据库创建完成，可以继续初始化")
            return  # 成功创建，继续后续流程
        else:
            raise Exception("数据库创建失败")
    
    # 数据库存在，继续删除表和对象
    try:
        async with get_session() as session:
            # 删除所有业务表
            tables_to_drop = ['articles', 'agents', 'sites', 'users']
            
            for table in tables_to_drop:
                try:
                    await session.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                    logger.info(f"✅ 删除表: {table}")
                except Exception as e:
                    logger.warning(f"⚠️  删除表 {table} 失败: {e}")
            
            # 删除枚举类型
            try:
                await session.execute(text("DROP TYPE IF EXISTS articlestatus CASCADE"))
                logger.info("✅ 删除枚举类型: articlestatus")
            except Exception as e:
                logger.warning(f"⚠️  删除枚举类型失败: {e}")
            
            # 重置 Alembic 版本
            try:
                await session.execute(text("DELETE FROM alembic_version"))
                logger.info("✅ 重置 Alembic 版本跟踪")
            except Exception as e:
                logger.warning(f"⚠️  重置 Alembic 版本失败: {e}")
            
            await session.commit()
            logger.info("✅ 数据库对象删除完成")
            
    except Exception as e:
        logger.error(f"❌ 删除数据库对象失败: {e}")
        raise


async def init_production_schema():
    """初始化生产环境数据库schema"""
    logger.info("🔧 初始化数据库schema...")
    
    try:
        # 使用 Alembic 运行数据库迁移
        success = await run_alembic_upgrade()
        if not success:
            raise Exception("Alembic 数据库迁移失败")
        
        logger.info("✅ 数据库schema初始化完成")
        
    except Exception as e:
        logger.error(f"❌ Schema初始化失败: {e}")
        raise


async def create_essential_config():
    """创建必要的系统配置"""
    logger.info("⚙️ 创建必要的系统配置...")
    
    # 注意：站点配置现在通过 Web UI 界面管理，不再创建默认站点
    # 用户可以在 Web UI 中根据实际需要创建和配置 WordPress 站点
    
    logger.info("✅ 系统配置准备完成")
    logger.info("📝 站点配置将通过 Web UI 界面进行管理")
    
    return True


async def create_webui_agent():
    """创建Web UI系统Agent"""
    logger.info("⚙️ 创建Web UI系统Agent...")
    
    try:
        # 检查是否已存在
        try:
            existing_agent = await config_service.get_agent("web-ui-internal")
            logger.info("✅ Web UI系统Agent已存在，跳过创建")
            logger.info(f"⚠️  注意：无法获取现有Agent的API密钥，请检查 web-ui/.env.local 配置")
            return existing_agent.api_key_hash[:10] + "..."  # 返回部分API密钥用于日志
        except Exception:
            # Agent不存在，继续创建
            pass
        
        # 生成安全的API密钥
        api_key = f"webui_{secrets.token_urlsafe(32)}"
        
        agent_config = {
            "agent_id": "web-ui-internal",
            "name": "Web UI Internal Agent",
            "description": "Internal system agent for Web UI operations - DO NOT DELETE",
            "api_key": api_key,
            "status": "active",
            "rate_limit": {
                "requests_per_minute": 100,  # 高频率限制
                "requests_per_hour": 1000,
                "requests_per_day": 10000
            },
            "permissions": {
                "can_submit_articles": False,  # Web UI不提交文章
                "can_edit_own_articles": False,
                "can_delete_own_articles": False,
                "can_view_statistics": True,
                "can_approve_articles": True,  # 关键：审批权限
                "can_reject_articles": True,   # 关键：拒绝权限
                "allowed_categories": [],
                "allowed_tags": []
            },
            "notifications": {
                "on_approval": False,      # 系统Agent不需要通知
                "on_rejection": False,
                "on_publish_success": False,
                "on_publish_failure": False
            }
        }
        
        # 创建Agent
        agent = await config_service.create_agent(**agent_config)
        logger.info(f"✅ 创建Web UI系统Agent: {agent.name}")
        
        # 自动写入Web UI环境文件
        env_file_path = "web-ui/.env.local"
        logger.info("📝 正在更新 Web UI 环境配置...")
        
        if update_env_file(env_file_path, "WEB_UI_AGENT_API_KEY", api_key):
            logger.info(f"✅ 已自动写入 API 密钥到 {env_file_path}")
            logger.info(f"🔐 密钥前缀: {api_key[:10]}...")
        else:
            logger.error("❌ 自动写入失败，请手动添加以下配置到 web-ui/.env.local:")
            logger.error(f"   WEB_UI_AGENT_API_KEY={api_key}")
        
        return api_key
        
    except Exception as e:
        logger.error(f"❌ 创建Web UI系统Agent失败: {e}")
        return None


async def main():
    """主函数"""
    logger.info("🚀 生产环境数据库初始化开始...")
    logger.info(f"📍 数据库URL: {settings.database_url[:50]}...")
    
    # 检查环境变量
    if os.getenv("ENVIRONMENT") != "production":
        logger.warning("⚠️  未检测到生产环境变量 ENVIRONMENT=production")
        confirm = input("确认要在非生产环境运行此脚本吗? (y/N): ")
        if confirm.lower() != 'y':
            logger.info("❌ 用户取消操作")
            return
    
    try:
        # 1. 检查数据库状态
        db_state = await check_database_state()
        
        if db_state == "error":
            logger.error("❌ 无法连接到数据库，请检查配置")
            sys.exit(1)
        
        elif db_state == "has_data":
            logger.error("❌ 数据库包含业务数据，不能在生产环境自动清理")
            logger.error("   如需清理，请手动备份数据后运行: python init_production_db.py --force-clean")
            sys.exit(1)
        
        # 2. 初始化schema（如果需要）
        if db_state == "empty":
            await init_production_schema()
        
        # 3. 创建必要的系统配置
        config_created = await create_essential_config()
        
        # 4. 创建Web UI系统Agent
        webui_api_key = None
        if os.getenv("CREATE_WEBUI_AGENT", "true").lower() == "true":
            webui_api_key = await create_webui_agent()
        else:
            logger.info("⏭️  跳过Web UI系统Agent创建（CREATE_WEBUI_AGENT=false）")
        
        if config_created:
            logger.info("🎉 数据库初始化完成!")
            logger.info("📋 下一步操作:")
            logger.info("   1. 启动 MCP 服务器: python -m mcp_wordpress.server")
            logger.info("   2. 启动 Web UI: cd web-ui && npm run dev")
            logger.info("   3. 访问 Web UI 创建和配置 WordPress 站点")
            
            if webui_api_key:
                logger.info("✅ Web UI API 密钥已自动配置")
        else:
            logger.error("❌ 默认配置创建失败")
            sys.exit(1)
            
    except Exception as e:
        logger.error(f"❌ 初始化失败: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)


if __name__ == "__main__":
    # 显示帮助信息
    if "--help" in sys.argv or "-h" in sys.argv:
        print("""
生产环境数据库初始化脚本

用法:
    python init_production_db.py [选项]

选项:
    无参数           - 正常初始化（检查数据库状态，安全初始化）
    --force-clean   - 强制清理模式：完全删除所有表和对象，然后重新创建
    --clean-data    - 数据清理模式：清理所有表数据，但保留表结构
    --help, -h      - 显示此帮助信息

注意:
    --force-clean 会删除所有数据和表结构，请谨慎使用！
    --clean-data 只删除数据，保留表结构，适用于重置数据但保持schema的场景
        """)
        sys.exit(0)
    
    # 检查命令行参数
    if "--force-clean" in sys.argv:
        async def force_clean():
            logger.info("🧹 强制清理模式启动...")
            logger.info("⚠️  将完全删除所有表和对象，然后重新创建")
            await drop_all_tables()  # 完全删除表结构
            await init_production_schema()  # 通过 Alembic 重新创建
            await create_essential_config()
            await create_webui_agent()
            logger.info("🎉 强制清理和重建完成!")
            
        asyncio.run(force_clean())
    
    elif "--clean-data" in sys.argv:
        async def clean_data():
            logger.info("🧹 数据清理模式启动...")
            logger.info("⚠️  将清理所有表数据，但保留表结构")
            await clean_database()  # 只清理数据，保留表结构
            await create_essential_config()
            await create_webui_agent()
            logger.info("🎉 数据清理完成!")
            
        asyncio.run(clean_data())
    
    else:
        asyncio.run(main())