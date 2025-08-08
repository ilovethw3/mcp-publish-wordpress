# MCP WordPress 发布平台测试套件

这个测试套件为MCP WordPress发布平台提供全面的测试覆盖，包括单元测试、集成测试和质量保证检查。

## 📁 测试结构

```
mcp/tests/
├── README.md                    # 本文件
├── conftest.py                  # 测试配置和fixtures
├── test_auth.py                # 认证系统测试
├── test_wordpress_client.py    # WordPress客户端测试
├── test_models.py              # 数据模型测试
├── test_api_integration.py     # API集成测试
└── test_quality_assurance.py   # 质量保证和性能测试
```

## 🧪 测试类型

### 单元测试 (`@pytest.mark.unit`)
- **认证系统**: 密码哈希、JWT令牌、用户认证
- **WordPress客户端**: API调用、错误处理、数据转换
- **数据模型**: 用户和文章模型的CRUD操作
- **安全功能**: 加密、验证、权限检查

### 集成测试 (`@pytest.mark.integration`)
- **API端点**: 完整的REST API功能测试
- **数据库集成**: 数据持久化和查询测试
- **业务流程**: 端到端工作流验证
- **外部服务**: WordPress集成测试

### 质量保证测试
- **代码质量**: 命名规范、文档覆盖
- **性能基准**: 响应时间、查询性能
- **安全验证**: SQL注入防护、认证绕过
- **错误处理**: 异常情况处理

## 🚀 运行测试

### 使用测试运行器（推荐）

```bash
# 检查测试依赖
python run_tests.py --check-deps

# 运行所有测试
python run_tests.py --all

# 运行单元测试
python run_tests.py --unit

# 运行集成测试
python run_tests.py --integration

# 运行覆盖率测试
python run_tests.py --coverage

# 运行特定测试文件
python run_tests.py --file test_auth.py

# 运行性能测试
python run_tests.py --performance

# 运行安全测试
python run_tests.py --security
```

### 直接使用pytest

```bash
# 运行所有测试
pytest mcp/tests/

# 运行单元测试
pytest mcp/tests/ -m unit

# 运行集成测试
pytest mcp/tests/ -m integration

# 运行特定测试文件
pytest mcp/tests/test_auth.py

# 运行特定测试函数
pytest mcp/tests/test_auth.py::TestSecurityFunctions::test_password_hashing

# 生成覆盖率报告
pytest mcp/tests/ --cov=mcp --cov-report=html

# 运行失败重试
pytest mcp/tests/ --lf

# 详细输出
pytest mcp/tests/ -v -s
```

## 📊 测试覆盖率

当前目标覆盖率：**80%+**

| 组件类别 | 目标覆盖率 | 重要程度 |
|----------|------------|----------|
| 核心业务逻辑 | 95% | 高 |
| API端点 | 90% | 高 |
| 数据模型 | 85% | 中 |
| 工具函数 | 90% | 中 |
| WordPress集成 | 80% | 中 |

### 查看覆盖率报告

```bash
# 生成HTML覆盖率报告
pytest --cov=mcp --cov-report=html

# 在浏览器中查看
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
```

## 🔧 测试配置

### pytest配置 (`pytest.ini`)

```ini
[tool:pytest]
testpaths = mcp/tests
addopts = --cov=mcp --cov-fail-under=80 -v
markers =
    unit: 单元测试
    integration: 集成测试
    slow: 慢速测试
    wordpress: WordPress相关测试
```

### 环境变量

测试环境需要以下环境变量：

```bash
# 测试数据库（使用SQLite）
DATABASE_URL=sqlite:///./test.db

# 测试JWT密钥
SECRET_KEY=test-jwt-secret-key-for-testing-only

# 测试API密钥
AGENT_API_KEY=test-agent-api-key

# 模拟WordPress配置
WORDPRESS_API_URL=http://mock-wordpress.test
WORDPRESS_USERNAME=test_user
WORDPRESS_APP_PASSWORD=test_pass
```

## 📝 编写新测试

### 测试文件命名规范

- 测试文件：`test_<module_name>.py`
- 测试类：`Test<ClassName>`
- 测试方法：`test_<description>`

### 示例测试函数

```python
@pytest.mark.unit
def test_user_creation(db_session):
    """测试用户创建功能"""
    user = User(username="testuser", hashed_password="hashed")
    db_session.add(user)
    db_session.commit()
    
    assert user.id is not None
    assert user.username == "testuser"

@pytest.mark.integration
def test_login_api(client):
    """测试登录API端点"""
    response = client.post("/api/v1/auth/token", data={
        "username": "testuser",
        "password": "testpass"
    })
    
    assert response.status_code == 200
    assert "access_token" in response.json()
```

### 使用Fixtures

```python
def test_with_authenticated_user(client, auth_headers):
    """使用认证用户的测试"""
    response = client.get("/api/v1/articles/", headers=auth_headers)
    assert response.status_code == 200

def test_with_mock_wordpress(mock_wordpress_client):
    """使用模拟WordPress客户端的测试"""
    result = mock_wordpress_client.create_post("标题", "内容")
    assert result['success'] is True
```

## 🎯 测试最佳实践

### 1. 测试独立性
- 每个测试都应该独立运行
- 使用fixtures设置测试数据
- 测试后清理资源

### 2. 描述性命名
```python
# 好的命名
def test_user_login_with_valid_credentials_returns_token():
    pass

# 不好的命名
def test_login():
    pass
```

### 3. 测试边界情况
```python
def test_article_title_validation():
    """测试文章标题验证"""
    # 正常情况
    assert validate_title("正常标题")
    
    # 边界情况
    assert not validate_title("")  # 空标题
    assert not validate_title("A" * 201)  # 超长标题
    assert not validate_title(None)  # None值
```

### 4. 使用适当的断言
```python
# 使用具体的断言
assert response.status_code == 200
assert len(articles) == 3
assert "error" in response.json()

# 避免模糊的断言
assert response  # 不够具体
assert articles  # 不够明确
```

## 🐛 调试测试

### 运行特定测试
```bash
# 运行失败的测试
pytest --lf

# 运行特定测试并停在第一个失败
pytest -x test_auth.py

# 详细输出调试信息
pytest -vvv -s test_auth.py::test_password_hashing

# 使用pdb调试器
pytest --pdb test_auth.py
```

### 常见问题

1. **数据库相关错误**
   - 确保测试数据库配置正确
   - 检查fixture是否正确清理数据

2. **异步测试问题**
   - 使用`@pytest.mark.asyncio`标记
   - 确保event_loop fixture正确配置

3. **Mock相关问题**
   - 确保mock的路径正确
   - 验证mock的返回值类型

## 📈 持续集成

### GitHub Actions配置

```yaml
name: 测试
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: 3.11
      - run: pip install -r requirements.txt
      - run: pytest --cov=mcp --cov-report=xml
      - uses: codecov/codecov-action@v3
```

## 🔍 测试报告

### 生成测试报告

```bash
# JUnit XML格式报告
pytest --junitxml=test_results.xml

# HTML报告
pytest --html=test_report.html

# 覆盖率徽章
coverage-badge -o coverage.svg
```

---

## 📞 支持

如果在运行测试时遇到问题：

1. 检查所有依赖是否已安装
2. 验证环境变量设置
3. 查看测试输出的具体错误信息
4. 参考本README或代码中的注释

测试是代码质量的重要保证，请在提交代码前运行相关测试！