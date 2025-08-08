import pytest
import asyncio
import os
from typing import Generator
from unittest.mock import Mock
from sqlmodel import Session, create_engine, SQLModel
from pathlib import Path

# 设置测试环境变量（在导入应用模块之前）
def setup_test_env():
    """设置测试环境变量"""
    test_env_file = Path(__file__).parent.parent.parent / ".env.test"
    if test_env_file.exists():
        # 读取测试环境文件
        with open(test_env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
    else:
        # 如果没有测试环境文件，设置默认值
        os.environ.update({
            'DATABASE_URL': 'sqlite:///./test.db',
            'SECRET_KEY': 'test-jwt-secret-key-for-testing-only',
            'AGENT_API_KEY': 'test-agent-api-key',
            'WORDPRESS_API_URL': 'http://mock-wordpress.test/wp-json/wp/v2',
            'WORDPRESS_USERNAME': 'test_user',
            'WORDPRESS_APP_PASSWORD': 'test_pass',
            'APP_NAME': 'MCP Test Environment',
            'DEBUG': 'true'
        })

# 在导入应用模块前设置环境变量
setup_test_env()

# 现在可以安全地导入应用模块
from fastapi.testclient import TestClient
from mcp.main import app
from mcp.db.session import get_session
from mcp.core.config import settings

# 测试数据库引擎
TEST_DATABASE_URL = "sqlite:///./test.db"
test_engine = create_engine(TEST_DATABASE_URL, echo=False)

@pytest.fixture(scope="session")
def event_loop():
    """创建异步测试事件循环"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """创建测试数据库会话"""
    SQLModel.metadata.create_all(test_engine)
    with Session(test_engine) as session:
        yield session
        session.rollback()
    SQLModel.metadata.drop_all(test_engine)

@pytest.fixture(scope="function")
def client(db_session: Session) -> TestClient:
    """创建测试客户端"""
    app.dependency_overrides[get_session] = lambda: db_session
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def mock_wordpress_client():
    """模拟WordPress客户端"""
    mock = Mock()
    mock.create_post.return_value = {
        'success': True,
        'post_id': 123,
        'permalink': 'https://example.com/test-post'
    }
    mock.get_categories.return_value = {'Tech': 1, 'News': 2}
    mock.get_tags.return_value = {'AI': 1, 'Python': 2}
    mock.resolve_tag_ids.return_value = [1, 2]
    mock.resolve_category_id.return_value = 1
    return mock

@pytest.fixture
def sample_user_data():
    """示例用户数据"""
    return {
        "username": "testuser",
        "password": "testpass123",
        "is_active": True
    }

@pytest.fixture
def sample_article_data():
    """示例文章数据"""
    return {
        "title": "测试文章标题",
        "content_markdown": "# 测试内容\n这是一篇测试文章。",
        "tags": "AI,Python,测试",
        "category": "技术"
    }

@pytest.fixture
def auth_token(db_session):
    """创建认证令牌用于测试"""
    from mcp.models.user import User
    from mcp.core.security import get_password_hash, create_access_token
    
    # 创建测试用户
    user = User(
        username="testauth",
        hashed_password=get_password_hash("testpass"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    
    # 创建令牌
    return create_access_token({"sub": "testauth"})

@pytest.fixture
def auth_headers(auth_token):
    """认证请求头"""
    return {"Authorization": f"Bearer {auth_token}"}