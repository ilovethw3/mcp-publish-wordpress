# 设计文档：MCP WordPress发布服务器 v2.0

## 1. 概述

本设计文档基于已批准的需求文档v2.0，详细描述了符合Model Context Protocol (MCP) 标准的WordPress发布服务器架构。该系统使用MCP Python SDK实现，提供Tools、Resources和Prompts，支持stdio和SSE传输，完全符合JSON-RPC 2.0协议规范。

核心工作流：AI客户端通过MCP Tools提交文章 → 人工审核员批准 → 自动发布到WordPress

## 2. 架构设计

### 2.1 MCP协议架构

```mermaid
graph TD
    subgraph "MCP Client Environment"
        AI[AI Agent]
        Human[Human Reviewer Tool]
        CLI[CLI Client]
    end
    
    subgraph "MCP Server Process"
        MCP[MCP WordPress Server]
        Tools[MCP Tools Layer]
        Resources[MCP Resources Layer]
        Prompts[MCP Prompts Layer]
    end
    
    subgraph "Transport Layer"
        Stdio[Stdio Transport]
        SSE[SSE Transport]
    end
    
    subgraph "Backend Services"
        DB[(PostgreSQL Database)]
        WP[WordPress REST API]
    end
    
    AI <==> Stdio
    Human <==> SSE
    CLI <==> Stdio
    
    Stdio <==> MCP
    SSE <==> MCP
    
    MCP --> Tools
    MCP --> Resources  
    MCP --> Prompts
    
    Tools --> DB
    Tools --> WP
    Resources --> DB
```

### 2.2 MCP Server能力声明

```json
{
  "capabilities": {
    "tools": {
      "listChanged": true
    },
    "resources": {
      "subscribe": true,
      "listChanged": true
    },
    "prompts": {
      "listChanged": true
    },
    "logging": {}
  },
  "serverInfo": {
    "name": "wordpress-publisher",
    "version": "2.0.0",
    "description": "MCP server for WordPress content publishing workflow"
  }
}
```

## 3. 组件与接口

### 3.1 MCP Tools定义

#### 3.1.1 文章管理Tools

**submit_article**
```json
{
  "name": "submit_article",
  "description": "Submit a new article for review",
  "inputSchema": {
    "type": "object",
    "properties": {
      "title": {"type": "string", "maxLength": 200},
      "content_markdown": {"type": "string"},
      "tags": {"type": "string", "description": "Comma-separated tags"},
      "category": {"type": "string"}
    },
    "required": ["title", "content_markdown"]
  }
}
```

**approve_article**
```json
{
  "name": "approve_article", 
  "description": "Approve article and start WordPress publishing",
  "inputSchema": {
    "type": "object",
    "properties": {
      "article_id": {"type": "integer"},
      "reviewer_notes": {"type": "string"}
    },
    "required": ["article_id"]
  }
}
```

**reject_article**
```json
{
  "name": "reject_article",
  "description": "Reject article with reason",
  "inputSchema": {
    "type": "object", 
    "properties": {
      "article_id": {"type": "integer"},
      "rejection_reason": {"type": "string"}
    },
    "required": ["article_id", "rejection_reason"]
  }
}
```

**list_articles**
```json
{
  "name": "list_articles",
  "description": "List articles with filtering options",
  "inputSchema": {
    "type": "object",
    "properties": {
      "status": {"type": "string", "enum": ["pending_review", "publishing", "published", "rejected", "publish_failed"]},
      "search": {"type": "string"},
      "limit": {"type": "integer", "default": 50, "maximum": 100}
    }
  }
}
```

**get_article_status**
```json
{
  "name": "get_article_status",
  "description": "Get detailed article status and publishing information",
  "inputSchema": {
    "type": "object",
    "properties": {
      "article_id": {"type": "integer"}
    },
    "required": ["article_id"]
  }
}
```

### 3.2 MCP Resources定义

#### 3.2.1 文章数据Resources

- **article://pending** - 待审核文章列表
- **article://{id}** - 特定文章的完整数据
- **article://published** - 已发布文章列表
- **article://failed** - 发布失败的文章列表

#### 3.2.2 系统状态Resources

- **wordpress://config** - WordPress站点配置信息
- **stats://summary** - 系统统计数据（文章数量、状态分布等）
- **stats://performance** - 发布性能指标

### 3.3 MCP Prompts定义

#### 3.3.1 内容创建Prompts

**article_template**
```json
{
  "name": "article_template",
  "description": "Generate article template with best practices",
  "arguments": [
    {
      "name": "topic",
      "description": "Article topic or subject",
      "required": true
    },
    {
      "name": "target_audience", 
      "description": "Target audience for the article",
      "required": false
    }
  ]
}
```

**review_checklist**
```json
{
  "name": "review_checklist", 
  "description": "Generate review checklist for content quality",
  "arguments": [
    {
      "name": "content_type",
      "description": "Type of content being reviewed",
      "required": true
    }
  ]
}
```

## 4. 数据模型

### 4.1 数据库Schema

```python
class Article(SQLModel, table=True):
    __tablename__ = "articles"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    content_markdown: str
    content_html: Optional[str] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    status: ArticleStatus = Field(default=ArticleStatus.PENDING_REVIEW)
    
    # WordPress integration fields
    wordpress_post_id: Optional[int] = None
    wordpress_permalink: Optional[str] = None
    publish_error_message: Optional[str] = None
    
    # Timestamps
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
    
    # Review metadata
    reviewer_notes: Optional[str] = None
    rejection_reason: Optional[str] = None

class ArticleStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    PUBLISHING = "publishing" 
    PUBLISHED = "published"
    PUBLISH_FAILED = "publish_failed"
    REJECTED = "rejected"
```

### 4.2 MCP消息Schema

所有MCP消息遵循JSON-RPC 2.0格式：

```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "method": "tools/call",
  "params": {
    "name": "submit_article",
    "arguments": {
      "title": "Article Title",
      "content_markdown": "# Content"
    }
  }
}
```

## 5. 错误处理

### 5.1 MCP标准错误码

```python
class MCPErrorCodes:
    PARSE_ERROR = -32700      # JSON解析错误
    INVALID_REQUEST = -32600  # 无效的JSON-RPC请求
    METHOD_NOT_FOUND = -32601 # 方法不存在
    INVALID_PARAMS = -32602   # 无效参数
    INTERNAL_ERROR = -32603   # 内部错误
    
    # 应用特定错误码
    ARTICLE_NOT_FOUND = -40001
    INVALID_STATUS = -40002
    WORDPRESS_ERROR = -40003
    AUTH_FAILED = -40004
```

### 5.2 错误响应格式

```json
{
  "jsonrpc": "2.0",
  "id": "request-id",
  "error": {
    "code": -40001,
    "message": "Article not found",
    "data": {
      "article_id": 123,
      "details": "Article with ID 123 does not exist"
    }
  }
}
```

## 6. 测试策略

### 6.1 MCP协议测试

- **连接测试**: 验证stdio和SSE传输的连接建立
- **协议兼容性**: 确保JSON-RPC 2.0消息格式正确
- **能力协商**: 测试initialize/initialized握手流程

### 6.2 Tools测试

- **Tool发现**: 测试tools/list返回正确的schema
- **Tool执行**: 验证每个Tool的输入验证和输出格式
- **错误处理**: 测试各种错误场景的处理

### 6.3 Resources测试

- **Resource列表**: 测试resources/list返回
- **Resource读取**: 验证resources/read的内容和格式
- **订阅机制**: 测试Resource变更通知

### 6.4 集成测试

- **WordPress发布**: 端到端测试文章发布流程
- **状态同步**: 验证数据库与WordPress状态一致性
- **并发处理**: 测试多客户端同时操作

## 7. 部署架构

### 7.1 容器化部署

```yaml
# docker-compose.yml
services:
  mcp-server:
    build: .
    environment:
      - MCP_TRANSPORT=stdio  # 或 sse
      - DATABASE_URL=postgresql://user:pass@postgres:5432/mcpdb
      - WORDPRESS_API_URL=https://site.com/wp-json/wp/v2
    depends_on:
      - postgres
      
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: mcpdb
      POSTGRES_USER: mcpuser  
      POSTGRES_PASSWORD: mcppass
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### 7.2 传输配置

**Stdio模式（开发/本地）**:
```bash
python -m mcp_wordpress_server
```

**SSE模式（生产/Web）**:
```bash
python -m mcp_wordpress_server --transport=sse --port=8000
```

## 8. 安全考虑

### 8.1 MCP安全最佳实践

1. **Tool安全**: 所有Tools需要适当的权限验证
2. **Resource访问控制**: 敏感Resources需要认证
3. **输入验证**: 严格验证所有Tool参数
4. **输出清理**: 防止敏感信息泄露

### 8.2 WordPress集成安全

1. **凭据管理**: 使用应用程序密码而非用户密码
2. **HTTPS通信**: 强制使用HTTPS与WordPress通信
3. **错误处理**: 避免在错误消息中暴露敏感信息

## 9. 性能考虑

### 9.1 并发处理

- **异步操作**: 所有Tool和Resource处理使用async/await
- **连接池**: PostgreSQL连接池管理
- **后台任务**: WordPress发布使用后台任务队列

### 9.2 缓存策略

- **Resource缓存**: 缓存频繁访问的Resources
- **WordPress元数据**: 缓存分类和标签信息
- **状态更新**: 使用事件驱动更新缓存

## 10. 监控与日志

### 10.1 MCP协议监控

- **消息统计**: 跟踪JSON-RPC消息数量和类型
- **Tool使用**: 监控各Tool的调用频率和成功率
- **连接状态**: 跟踪客户端连接和断开

### 10.2 业务指标

- **文章流转**: 监控文章从提交到发布的时间
- **审核效率**: 跟踪人工审核的处理时间
- **发布成功率**: WordPress发布成功/失败比率

## 11. 扩展性设计

### 11.1 插件架构

```python
class MCPWordPressServer(FastMCP):
    def __init__(self):
        super().__init__("wordpress-publisher")
        self.load_plugins()
    
    def load_plugins(self):
        # 动态加载Tools、Resources、Prompts
        for plugin in discover_plugins():
            plugin.register(self)
```

### 11.2 多站点支持

- **站点配置**: 支持多个WordPress站点配置
- **路由策略**: 根据文章类别路由到不同站点
- **权限隔离**: 不同审核员管理不同站点

## 12. 开发指南

### 12.1 目录结构

```
mcp-wordpress-server/
├── mcp_wordpress/
│   ├── __init__.py
│   ├── server.py          # 主MCP服务器实现
│   ├── tools/             # MCP Tools实现
│   │   ├── __init__.py
│   │   ├── articles.py    # 文章管理Tools
│   │   └── wordpress.py   # WordPress集成Tools
│   ├── resources/         # MCP Resources实现
│   │   ├── __init__.py
│   │   ├── articles.py    # 文章数据Resources
│   │   └── stats.py       # 统计Resources
│   ├── prompts/           # MCP Prompts实现
│   │   ├── __init__.py
│   │   └── templates.py   # 内容模板Prompts
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── article.py
│   │   └── user.py
│   ├── core/              # 核心服务
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── wordpress.py
│   │   └── security.py
│   └── tests/             # 测试套件
├── alembic/               # 数据库迁移
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
├── pyproject.toml
└── README.md
```

### 12.2 MCP Server主实现

```python
from mcp.server.fastmcp import FastMCP
from mcp_wordpress.tools.articles import register_article_tools
from mcp_wordpress.resources.articles import register_article_resources
from mcp_wordpress.prompts.templates import register_content_prompts

# 创建MCP服务器实例
mcp = FastMCP(
    name="wordpress-publisher",
    version="2.0.0",
    description="MCP server for WordPress content publishing"
)

# 注册功能模块
register_article_tools(mcp)
register_article_resources(mcp) 
register_content_prompts(mcp)

# 启动服务器
if __name__ == "__main__":
    import sys
    transport = sys.argv[1] if len(sys.argv) > 1 else "stdio"
    mcp.run(transport=transport)
```

## 13. WordPress集成设计

### 13.1 WordPress客户端架构

```python
class WordPressClient:
    def __init__(self, api_url: str, username: str, app_password: str):
        self.api_url = api_url
        self.auth = (username, app_password)
        self.session = requests.Session()
    
    async def create_post(self, title: str, content: str, **kwargs) -> dict:
        """创建WordPress文章"""
        
    async def get_categories(self) -> dict:
        """获取分类列表"""
        
    async def get_tags(self) -> dict:
        """获取标签列表"""
```

### 13.2 异步发布流程

1. **状态更新**: 文章状态设为`publishing`
2. **内容准备**: Markdown转HTML，解析标签和分类
3. **WordPress API调用**: 创建文章
4. **结果处理**: 更新状态和WordPress ID
5. **错误处理**: 记录失败原因

## 14. 配置管理

### 14.1 环境变量配置

```python
class Settings(BaseSettings):
    # MCP服务器配置
    mcp_server_name: str = "wordpress-publisher"
    mcp_transport: str = "stdio"  # stdio or sse
    mcp_port: int = 8000
    
    # 数据库配置
    database_url: str
    
    # WordPress集成
    wordpress_api_url: str
    wordpress_username: str
    wordpress_app_password: str
    
    # 安全配置
    secret_key: str
    agent_api_key: str
    
    class Config:
        env_file = ".env"
```

### 14.2 传输层配置

```python
def create_transport(transport_type: str, **kwargs):
    if transport_type == "stdio":
        return stdio_server()
    elif transport_type == "sse":
        return sse_server(port=kwargs.get("port", 8000))
    else:
        raise ValueError(f"Unsupported transport: {transport_type}")
```

## 15. 实现优先级

### 15.1 第一阶段：核心MCP功能
1. MCP服务器基础架构
2. 基本Tools实现（submit_article, list_articles）
3. 核心Resources（article://pending, article://{id}）
4. Stdio传输支持

### 15.2 第二阶段：WordPress集成
1. WordPress客户端实现
2. 发布相关Tools（approve_article, reject_article）
3. 异步发布流程
4. 错误处理和重试机制

### 15.3 第三阶段：高级功能
1. SSE传输支持
2. 完整Prompts实现
3. 统计Resources
4. 性能优化

## 16. 测试架构

### 16.1 MCP协议测试

```python
# 测试MCP客户端连接
async def test_mcp_connection():
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # 测试能力协商
            tools = await session.list_tools()
            assert len(tools.tools) > 0
            
            resources = await session.list_resources()
            assert len(resources.resources) > 0
```

### 16.2 Tools功能测试

```python
async def test_submit_article_tool():
    result = await session.call_tool("submit_article", {
        "title": "Test Article",
        "content_markdown": "# Test Content"
    })
    
    assert result.isError == False
    content = result.content[0]
    assert "article_id" in content.text
```

## 17. 部署策略

### 17.1 开发环境

```bash
# 本地开发 - stdio传输
python -m mcp_wordpress_server

# 与MCP客户端测试
mcp connect --stdio "python -m mcp_wordpress_server"
```

### 17.2 生产环境

```bash
# SSE传输，通过Docker部署
docker-compose up -d

# 健康检查
curl http://localhost:8000/health
```

## 18. 迁移策略

### 18.1 从REST API到MCP的迁移

1. **双协议支持期**: 同时支持REST API和MCP协议
2. **客户端迁移**: 逐步将客户端切换到MCP
3. **API废弃**: 在确认所有客户端迁移后移除REST API

### 18.2 数据兼容性

- 现有数据库结构保持不变
- 添加MCP相关的元数据字段
- 保持与现有WordPress集成的兼容性

## 19. 总结

本设计提供了完整的MCP标准WordPress发布服务器架构，确保：

- ✅ **协议兼容**: 完全符合MCP协议规范
- ✅ **功能完整**: 覆盖所有需求的Tools、Resources、Prompts
- ✅ **扩展性**: 支持多种传输方式和插件架构
- ✅ **安全性**: 实现适当的认证和权限控制
- ✅ **可维护性**: 清晰的模块划分和测试策略

该设计为后续的编码实施提供了详细的技术蓝图。