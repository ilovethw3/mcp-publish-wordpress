# 架构文档：MCP WordPress Publisher v2.1

## 1. 概述

MCP WordPress Publisher v2.1 采用**双服务架构**设计，实现了 AI 代理和人类管理员的协同工作流程。该架构通过清晰的职责分离，确保了系统的可维护性、可扩展性和稳定性。

### 1.1 架构理念

**核心设计原则**：
- **职责分离**：MCP Server 专注 AI 代理服务，Web UI 专注人类管理
- **数据中心化**：共享 PostgreSQL 数据库确保数据一致性
- **协议标准化**：基于 MCP 协议的 AI 代理集成
- **技术栈分离**：后端 Python，前端 TypeScript，独立开发部署

**架构优势**：
- 🔄 **松耦合**：两个服务可独立开发、测试、部署
- 📈 **可扩展**：微服务架构便于水平扩展
- 🛡️ **高可用**：服务故障不会相互影响
- 🔧 **易维护**：技术栈分离降低维护复杂度

### 1.2 架构愿景图

```mermaid
graph TB
    subgraph "AI代理生态"
        A1[AI Writer Agent]
        A2[SEO Optimizer Agent]
        A3[Content Editor Agent]
        A4[Translation Agent]
    end
    
    subgraph "MCP Server (Python)"
        MCP[FastMCP Server]
        Tools[MCP Tools]
        Resources[MCP Resources]
        Auth[Bearer Token Auth]
    end
    
    subgraph "Web UI (Next.js)"
        UI[管理界面]
        API[API Routes]
        Proxy[MCP Proxy]
        DB_Direct[Direct DB Access]
    end
    
    subgraph "共享数据层"
        PG[(PostgreSQL)]
        Models[SQLModel]
    end
    
    subgraph "WordPress 站点群"
        WP1[技术博客]
        WP2[个人博客]
        WP3[作品集站]
    end
    
    A1 -.->|MCP Protocol| MCP
    A2 -.->|MCP Protocol| MCP
    A3 -.->|MCP Protocol| MCP
    A4 -.->|MCP Protocol| MCP
    
    MCP --> PG
    DB_Direct --> PG
    
    UI --> API
    API --> DB_Direct
    API --> Proxy
    Proxy -.->|HTTP| MCP
    
    MCP -.->|WordPress API| WP1
    MCP -.->|WordPress API| WP2
    MCP -.->|WordPress API| WP3
```

## 2. 整体架构设计

### 2.1 双服务架构概览

```mermaid
graph LR
    subgraph "服务边界"
        subgraph "MCP Server 进程"
            direction TB
            MCP_Main[FastMCP Server]
            MCP_Tools[Article Tools]
            MCP_Resources[Stats Resources]
            MCP_Auth[Auth Provider]
        end
        
        subgraph "Web UI 进程"
            direction TB
            NextJS[Next.js App]
            API_Routes[API Routes]
            UI_Components[UI Components]
            MCP_Client[MCP Client]
        end
    end
    
    subgraph "共享基础设施"
        Database[(PostgreSQL)]
        Models[SQLModel Schemas]
    end
    
    subgraph "外部集成"
        WordPress[WordPress Sites]
        AI_Agents[AI Agents]
    end
    
    MCP_Server --> Database
    Web_UI --> Database
    Web_UI -.->|HTTP Proxy| MCP_Server
    
    AI_Agents -.->|MCP Protocol| MCP_Server
    MCP_Server -.->|REST API| WordPress
```

### 2.2 架构层次结构

| 层级 | MCP Server | Web UI | 职责 |
|------|------------|---------|------|
| **表现层** | MCP Protocol | Next.js Pages | 用户交互界面 |
| **业务层** | Tools/Resources | API Routes | 业务逻辑处理 |
| **服务层** | FastMCP Core | MCP Client | 协议通信服务 |
| **数据层** | SQLModel ORM | Database Service | 数据持久化 |

## 3. 核心组件详解

### 3.1 MCP Server (后端服务)

**技术栈**: Python 3.13 + FastMCP + SQLModel + PostgreSQL

#### 目录结构
```
mcp_wordpress/
├── server.py                 # FastMCP 服务器入口
├── tools/
│   └── articles.py           # 文章管理工具
├── resources/
│   ├── articles.py           # 文章数据资源
│   └── stats.py              # 统计资源
├── auth/
│   └── providers.py          # 多代理认证
├── core/
│   ├── config.py             # 配置管理
│   ├── database.py           # 数据库会话
│   └── wordpress.py          # WordPress客户端
└── models/                   # 数据模型
    ├── agent.py
    ├── site.py
    └── article.py
```

#### 核心功能模块

**1. MCP Tools (工具层)**
```python
# 文章管理工具示例
@mcp.tool()
async def submit_article(title: str, content_markdown: str, 
                        target_site: str = "") -> str:
    """AI 代理提交文章"""
    async with get_session() as session:
        article = Article(
            title=title,
            content_markdown=content_markdown,
            status=ArticleStatus.PENDING_REVIEW,
            target_site_id=target_site
        )
        session.add(article)
        await session.commit()
        return create_mcp_success({"article_id": article.id})
```

**2. MCP Resources (资源层)**
```python
# 统计资源示例
@mcp.resource("stats://summary")
async def get_stats_summary() -> str:
    """获取系统统计摘要"""
    async with get_session() as session:
        stats = await calculate_article_stats(session)
        return json.dumps(stats)
```

**3. 认证系统**
```python
# 多代理Bearer Token认证
class BearerTokenProvider:
    async def validate_token(self, token: str) -> bool:
        async with get_session() as session:
            agent = await get_agent_by_token(session, token)
            return agent is not None and agent.is_active
```

### 3.2 Web UI (前端服务)

**技术栈**: Next.js 14 + TypeScript + Tailwind CSS + Headless UI

#### 目录结构
```
web-ui/src/
├── app/
│   ├── agents/               # 代理管理页面
│   ├── articles/             # 文章管理页面
│   ├── sites/                # 站点管理页面
│   └── api/                  # API 路由
│       ├── config/           # 配置管理API
│       └── mcp-proxy/        # MCP代理API
├── components/
│   ├── config/               # 配置表单组件
│   ├── layout/               # 布局组件
│   └── ui/                   # 基础UI组件
├── lib/
│   ├── database/             # 数据库服务
│   ├── api.ts                # API客户端
│   └── mcp-client.ts         # MCP客户端
└── types/
    └── index.ts              # TypeScript类型定义
```

#### 核心功能模块

**1. 直接数据库访问**
```typescript
// 配置管理 - 直接访问数据库
export async function createAgent(data: AgentFormData): Promise<Agent> {
  const query = `
    INSERT INTO agents (name, description, api_key_hash, permissions) 
    VALUES ($1, $2, $3, $4) RETURNING *
  `;
  const result = await db.query(query, [name, description, hash, permissions]);
  return result.rows[0];
}
```

**2. MCP 代理调用**
```typescript
// 文章操作 - 代理到MCP服务器
export async function approveArticle(id: number): Promise<MCPResult> {
  const mcpClient = getMCPClient({ apiKey: process.env.WEB_UI_AGENT_API_KEY });
  return await mcpClient.approveArticle(id, reviewerNotes);
}
```

**3. 混合数据获取**
```typescript
// 文章列表页面
const ArticlesPage = () => {
  // 直接数据库查询获取列表
  const { articles, loading } = useArticles({
    status: selectedStatus,
    search: searchTerm
  });
  
  // MCP代理调用处理操作
  const handleApprove = async (id: number) => {
    await apiClient.mcpApproveArticle(id);
  };
};
```

### 3.3 数据库层 (共享数据)

**技术栈**: PostgreSQL 14+ + SQLModel + Alembic

#### 数据模型设计

**1. Agent 模型 (代理管理)**
```python
class Agent(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    api_key_hash: str
    status: str = "active"
    rate_limit: dict = Field(sa_column=Column(JSON))
    permissions: dict = Field(sa_column=Column(JSON))
    total_articles_submitted: int = 0
```

**2. Site 模型 (站点管理)**
```python
class Site(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    wordpress_config: dict = Field(sa_column=Column(JSON))
    publishing_rules: dict = Field(sa_column=Column(JSON))
    is_active: bool = True
```

**3. Article 模型 (文章管理)**
```python
class Article(SQLModel, table=True):
    id: Optional[int] = Field(primary_key=True)
    title: str
    content_markdown: str
    status: ArticleStatus
    submitting_agent_id: Optional[str]
    target_site_id: Optional[str]
    wordpress_post_id: Optional[int]
```

## 4. 数据访问模式

### 4.1 双重数据访问设计

系统采用**混合数据访问模式**，根据场景选择最适合的访问方式：

```mermaid
graph TB
    subgraph "Web UI 数据访问"
        WUI[Web UI Pages]
        Direct[Direct DB Access]
        Proxy[MCP Proxy API]
    end
    
    subgraph "MCP Server 数据访问"
        MCP[MCP Tools]
        ORM[SQLModel ORM]
    end
    
    subgraph "数据库"
        PG[(PostgreSQL)]
    end
    
    WUI --> Direct
    WUI --> Proxy
    Proxy -.-> MCP
    Direct --> PG
    MCP --> ORM
    ORM --> PG
    
    style Direct fill:#e1f5fe
    style Proxy fill:#fff3e0
    style ORM fill:#e8f5e8
```

#### 4.2 数据访问决策矩阵

| 操作类型 | 访问方式 | 原因 | 示例 |
|----------|----------|------|------|
| **配置管理** | Direct DB | 高性能，实时性 | 代理/站点 CRUD |
| **数据查询** | Direct DB | 复杂查询，聚合 | 文章列表，统计 |
| **业务操作** | MCP Proxy | 复用业务逻辑 | 文章审批，发布 |
| **AI交互** | MCP Direct | 协议标准化 | AI代理提交文章 |

### 4.3 数据访问代码示例

**Direct DB Access (Web UI)**
```typescript
// 获取文章列表 - 高性能查询
export async function getArticles(filters: ArticleFilters): Promise<Article[]> {
  const conditions = [];
  const params = [];
  
  if (filters.status) {
    conditions.push(`status = $${params.length + 1}`);
    params.push(filters.status);
  }
  
  if (filters.search) {
    conditions.push(`title ILIKE $${params.length + 1}`);
    params.push(`%${filters.search}%`);
  }
  
  const query = `
    SELECT * FROM articles 
    ${conditions.length > 0 ? 'WHERE ' + conditions.join(' AND ') : ''}
    ORDER BY updated_at DESC
    LIMIT 50
  `;
  
  const result = await db.query(query, params);
  return result.rows;
}
```

**MCP ORM Access (MCP Server)**
```python
# 文章提交 - 业务逻辑处理
@mcp.tool()
async def submit_article(title: str, content_markdown: str) -> str:
    try:
        # 输入验证
        if len(title) > 200:
            raise ValidationError("title", "Title too long")
        
        # 获取提交代理信息
        access_token = get_access_token()
        agent_id = access_token.client_id if access_token else None
        
        # 数据库操作
        async with get_session() as session:
            article = Article(
                title=title.strip(),
                content_markdown=content_markdown,
                status=ArticleStatus.PENDING_REVIEW,
                submitting_agent_id=agent_id
            )
            
            session.add(article)
            await session.commit()
            await session.refresh(article)
            
            return create_mcp_success({
                "article_id": article.id,
                "status": article.status
            })
    except Exception as e:
        return MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e)).to_json()
```

## 5. 通信协议和 API

### 5.1 通信协议概览

```mermaid
sequenceDiagram
    participant AI as AI Agent
    participant MCP as MCP Server
    participant WEB as Web UI
    participant DB as Database
    participant WP as WordPress
    
    Note over AI,WP: 文章发布完整流程
    
    AI->>+MCP: MCP submit_article(title, content)
    MCP->>+DB: INSERT article (status: pending_review)
    DB-->>-MCP: article_id
    MCP-->>-AI: Success: {article_id: 123}
    
    Note over WEB,DB: 人类管理员操作
    
    WEB->>+DB: SELECT articles WHERE status='pending_review'
    DB-->>-WEB: articles_list
    
    WEB->>+MCP: HTTP POST /mcp-proxy/approve-article
    MCP->>+WP: WordPress API: create_post()
    WP-->>-MCP: {post_id: 456, link: "..."}
    MCP->>+DB: UPDATE article SET status='published'
    DB-->>-MCP: OK
    MCP-->>-WEB: Success: {wordpress_post_id: 456}
```

### 5.2 MCP 协议接口

**Tools (工具)**
```json
{
  "tools": [
    {
      "name": "submit_article",
      "description": "Submit article for review",
      "inputSchema": {
        "type": "object",
        "properties": {
          "title": {"type": "string", "maxLength": 200},
          "content_markdown": {"type": "string"},
          "target_site": {"type": "string"}
        }
      }
    },
    {
      "name": "approve_article",
      "description": "Approve and publish article",
      "inputSchema": {
        "type": "object",
        "properties": {
          "article_id": {"type": "integer"},
          "reviewer_notes": {"type": "string"}
        }
      }
    },
    {
      "name": "retry_publish_article",
      "description": "Retry publishing failed article",
      "inputSchema": {
        "type": "object",
        "properties": {
          "article_id": {"type": "integer"},
          "reviewer_notes": {"type": "string"}
        }
      }
    }
  ]
}
```

**Resources (资源)**
```json
{
  "resources": [
    {
      "uri": "wordpress://config",
      "name": "WordPress Configuration",
      "description": "Get WordPress sites configuration"
    },
    {
      "uri": "stats://summary",
      "name": "System Statistics",
      "description": "Get system statistics summary"
    },
    {
      "uri": "stats://agents",
      "name": "Agent Statistics", 
      "description": "Get agent activity statistics"
    }
  ]
}
```

### 5.3 Web UI REST API

**配置管理 API**
```typescript
// Agents API
GET    /api/config/agents          // 获取代理列表
POST   /api/config/agents          // 创建代理
PUT    /api/config/agents/:id      // 更新代理
DELETE /api/config/agents/:id      // 删除代理

// Sites API  
GET    /api/config/sites           // 获取站点列表
POST   /api/config/sites           // 创建站点
PUT    /api/config/sites/:id       // 更新站点
DELETE /api/config/sites/:id       // 删除站点
POST   /api/config/sites/test-connection // 测试连接

// Articles API (直接数据库查询)
GET    /api/articles               // 获取文章列表
GET    /api/articles/stats         // 获取文章统计
```

**MCP 代理 API**
```typescript
// MCP Proxy APIs (转发到MCP服务器)
POST   /api/mcp-proxy/approve-article     // 审批文章
POST   /api/mcp-proxy/reject-article      // 拒绝文章  
POST   /api/mcp-proxy/retry-publish-article // 重试发布
```

## 6. 工作流程示例

### 6.1 文章发布工作流

```mermaid
sequenceDiagram
    participant AI as AI Writer Agent
    participant MCP as MCP Server
    participant DB as PostgreSQL
    participant WEB as Web UI Admin
    participant WP as WordPress Site
    
    Note over AI,WP: 完整文章发布工作流
    
    rect rgb(240, 248, 255)
        Note right of AI: 1. AI代理提交文章
        AI->>+MCP: submit_article(title, content, target_site)
        MCP->>MCP: Bearer Token 认证
        MCP->>MCP: 内容清理和验证
        MCP->>+DB: INSERT INTO articles (status='pending_review')
        DB-->>-MCP: article_id
        MCP-->>-AI: {success: true, article_id: 123}
    end
    
    rect rgb(255, 248, 240)
        Note right of WEB: 2. 人类管理员审核
        WEB->>+DB: SELECT * FROM articles WHERE status='pending_review'
        DB-->>-WEB: pending_articles[]
        WEB->>WEB: 人工审核内容
        WEB->>+MCP: POST /api/mcp-proxy/approve-article
        MCP->>+DB: SELECT * FROM sites WHERE id=target_site_id
        DB-->>-MCP: site_config
    end
    
    rect rgb(248, 255, 248) 
        Note right of MCP: 3. 自动WordPress发布
        MCP->>+WP: WordPress REST API: create_post()
        WP-->>-MCP: {id: 456, link: "https://blog.com/post"}
        MCP->>+DB: UPDATE articles SET status='published', wordpress_post_id=456
        DB-->>-MCP: OK
        MCP-->>-WEB: {success: true, wordpress_post_id: 456}
    end
```

### 6.2 配置管理工作流

```mermaid
flowchart TD
    Start([管理员登录Web UI]) --> Config{配置类型}
    
    Config -->|代理管理| Agent[代理配置流程]
    Config -->|站点管理| Site[站点配置流程]
    
    Agent --> A1[填写代理信息]
    A1 --> A2[生成API密钥]  
    A2 --> A3[设置权限和限制]
    A3 --> A4[保存到数据库]
    A4 --> A5[更新MCP认证缓存]
    
    Site --> S1[填写WordPress信息]
    S1 --> S2[测试连接]
    S2 --> S3{连接成功?}
    S3 -->|否| S1
    S3 -->|是| S4[设置发布规则]
    S4 --> S5[保存站点配置]
    S5 --> S6[MCP工具自动加载新配置]
    
    A5 --> Done([配置完成])
    S6 --> Done
    
    style Agent fill:#e3f2fd
    style Site fill:#f3e5f5
    style Done fill:#e8f5e8
```

## 7. 部署架构

### 7.1 生产环境部署

```mermaid
graph TB
    subgraph "负载均衡层"
        LB[Nginx Load Balancer]
    end
    
    subgraph "应用服务器 Node 1"
        MCP1[MCP Server :8000]
        WEB1[Web UI :3000] 
    end
    
    subgraph "应用服务器 Node 2"  
        MCP2[MCP Server :8001]
        WEB2[Web UI :3001]
    end
    
    subgraph "数据库集群"
        PG_Master[(PostgreSQL Master)]
        PG_Slave[(PostgreSQL Replica)]
    end
    
    subgraph "缓存层"
        Redis[(Redis Cache)]
    end
    
    subgraph "外部服务"
        WP1[WordPress Site 1]
        WP2[WordPress Site 2]
        WP3[WordPress Site 3]
    end
    
    LB --> WEB1
    LB --> WEB2
    
    WEB1 -.->|MCP Proxy| MCP1
    WEB2 -.->|MCP Proxy| MCP2
    
    MCP1 --> PG_Master
    MCP2 --> PG_Master
    WEB1 --> PG_Master
    WEB2 --> PG_Slave
    
    MCP1 --> Redis
    MCP2 --> Redis
    
    MCP1 -.-> WP1
    MCP1 -.-> WP2  
    MCP1 -.-> WP3
    MCP2 -.-> WP1
    MCP2 -.-> WP2
    MCP2 -.-> WP3
```

### 7.2 Docker 容器化部署

**docker-compose.yml 结构**
```yaml
version: '3.8'
services:
  mcp-server:
    build: ./Dockerfile.mcp-server
    ports: ["8000:8000"]
    environment:
      - MCP_TRANSPORT=sse
      - DATABASE_URL=postgresql://...
    depends_on: [postgres, redis]
    
  web-ui:
    build: ./web-ui/Dockerfile.web-ui  
    ports: ["3000:3000"]
    environment:
      - NEXT_PUBLIC_MCP_SERVER_URL=http://mcp-server:8000
      - WEB_UI_AGENT_API_KEY=${WEB_UI_AGENT_API_KEY}
    depends_on: [mcp-server]
    
  postgres:
    image: postgres:14
    environment:
      - POSTGRES_DB=mcpdb_v21
    volumes: ["postgres_data:/var/lib/postgresql/data"]
    
  redis:
    image: redis:7-alpine
    volumes: ["redis_data:/data"]
```

### 7.3 环境配置

**生产环境变量**
```bash
# 数据库配置 (两个服务共享)
DATABASE_URL=postgresql+asyncpg://mcpuser:secure_pass@postgres:5432/mcpdb_v21
REDIS_URL=redis://redis:6379/0

# MCP Server 配置
MCP_TRANSPORT=sse
MCP_PORT=8000
MCP_SSE_PATH=/sse
SECRET_KEY=production_secret_key_32_chars

# Web UI 配置  
NEXT_PUBLIC_MCP_SERVER_URL=https://mcp.yourdomain.com
WEB_UI_AGENT_API_KEY=webui_production_api_key_here

# 安全配置
JWT_SECRET_KEY=jwt_production_secret_key
ENABLE_RATE_LIMITING=true
ENABLE_AUDIT_LOGGING=true
```

## 8. 技术栈总结

### 8.1 完整技术组件

| 层级 | 组件 | 版本 | 职责 |
|------|------|------|------|
| **前端** | Next.js | 14+ | React 全栈框架 |
| | TypeScript | 5+ | 类型安全开发 |
| | Tailwind CSS | 3+ | 响应式样式框架 |
| | Headless UI | 1+ | 无样式UI组件 |
| **后端** | Python | 3.13+ | MCP服务器运行时 |
| | FastMCP | 2.11+ | MCP协议服务器框架 |
| | SQLModel | 0.0.14+ | 数据库ORM |
| | Pydantic | 2+ | 数据验证和序列化 |
| **数据库** | PostgreSQL | 14+ | 主数据库 |
| | Alembic | 1+ | 数据库迁移管理 |
| | Redis | 7+ | 缓存和会话存储 |
| **部署** | Docker | 20+ | 容器化部署 |
| | Nginx | 1.20+ | 反向代理负载均衡 |
| **协议** | MCP Protocol | 1.0 | AI代理通信协议 |
| | JSON-RPC | 2.0 | 远程过程调用协议 |

### 8.2 依赖关系图

```mermaid
graph TD
    subgraph "前端依赖"
        NextJS[Next.js 14] --> React[React 18]
        NextJS --> TS[TypeScript 5]
        UI[Headless UI] --> React
        TW[Tailwind CSS] --> NextJS
    end
    
    subgraph "后端依赖"  
        FastMCP[FastMCP 2.11] --> Py[Python 3.13]
        SQLModel[SQLModel] --> Pydantic[Pydantic 2]
        SQLModel --> SA[SQLAlchemy 2]
        Alembic[Alembic] --> SA
    end
    
    subgraph "数据存储"
        PG[PostgreSQL 14]
        Redis[Redis 7]
    end
    
    subgraph "部署工具"
        Docker[Docker 20+]
        Compose[Docker Compose]
        Nginx[Nginx 1.20+]
    end
    
    FastMCP --> PG
    FastMCP --> Redis
    NextJS -.->|HTTP| FastMCP
    
    Docker --> FastMCP
    Docker --> NextJS
    Docker --> PG
    Nginx --> Docker
```

## 9. 总结和优势

### 9.1 架构优势总结

| 优势类别 | 具体优势 | 实现方式 |
|----------|----------|----------|
| **开发效率** | 前后端独立开发 | 技术栈分离，接口契约 |
| | 类型安全保证 | TypeScript + SQLModel |
| | 快速迭代部署 | Docker容器化 |
| **系统性能** | 数据访问优化 | 直接DB vs MCP代理混合 |
| | 并发处理能力 | 异步编程模式 |
| | 缓存策略优化 | Redis多级缓存 |
| **可扩展性** | 水平扩展支持 | 无状态服务设计 |
| | 多租户架构 | 多代理多站点支持 |
| | 插件化扩展 | MCP协议标准化 |
| **可维护性** | 清晰职责分离 | 双服务架构 |
| | 完善日志审计 | 结构化日志记录 |
| | 自动化测试 | 单元测试+集成测试 |

### 9.2 适用场景

**最适合的使用场景**：
- 🤖 **多AI代理协作**: 支持5-10个AI代理同时工作
- 📝 **内容创作流程**: 自动化内容审核发布工作流
- 🌐 **多站点管理**: 统一管理3-5个WordPress站点
- 👥 **混合团队协作**: AI代理+人类编辑的协同工作

**技术选型理由**：
- **双服务架构**: 满足AI自动化和人类管理的不同需求
- **MCP协议**: 标准化AI代理集成方式
- **PostgreSQL**: 支持JSON字段的关系型数据库
- **Next.js**: 现代化全栈Web开发框架

这个架构设计为AI代理和人类用户提供了一个高效、可靠、可扩展的协作平台，是现代AI辅助内容创作系统的最佳实践范例。