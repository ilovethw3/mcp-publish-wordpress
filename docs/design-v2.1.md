# 设计文档：MCP WordPress发布服务器 v2.1

## 1. 概述

本设计文档基于已批准的需求文档v2.1，详细描述了MCP WordPress Publisher Server v2.1的架构设计。该版本在v2.0基础架构之上，新增了多代理API密钥认证、多WordPress站点支持和现代化Web管理界面，专门针对个人用户的多代理协作内容创作场景进行优化。

### 1.1 版本演进概述

**v2.0基础能力**：
- 符合MCP协议标准的WordPress发布服务器
- 支持stdio和SSE传输模式
- 基础的文章提交、审核和发布工作流
- 单一代理、单一WordPress站点架构

**v2.1核心增强**：
- **多代理认证系统**：支持5-10个AI代理并发连接和身份识别
- **多站点发布管理**：支持3-5个WordPress站点的统一管理
- **现代化Web界面**：基于Next.js的完整管理控制台
- **配置文件管理**：YAML格式的灵活配置和热重载
- **增强安全机制**：API密钥认证、审计日志和会话管理

### 1.2 目标架构愿景

```mermaid
graph TB
    subgraph "AI代理生态"
        A1[AI Writer]
        A2[SEO Optimizer] 
        A3[Content Editor]
        A4[Translation Bot]
        A5[...]
    end
    
    subgraph "MCP v2.1服务器"
        Auth[多代理认证系统]
        Router[多站点路由器]
        Core[MCP核心服务]
        WebUI[Web管理界面]
    end
    
    subgraph "WordPress站点群"
        WP1[技术博客]
        WP2[个人博客]
        WP3[作品集站]
        WP4[...]
    end
    
    A1 -.->|API Key Auth| Auth
    A2 -.->|API Key Auth| Auth
    A3 -.->|API Key Auth| Auth
    A4 -.->|API Key Auth| Auth
    A5 -.->|API Key Auth| Auth
    
    Auth --> Core
    Core --> Router
    Router --> WP1
    Router --> WP2
    Router --> WP3
    Router --> WP4
    
    WebUI -.->|管理界面| Core
```

## 2. 架构设计

### 2.1 整体系统架构

```mermaid
graph TD
    subgraph "前端层"
        UI[Next.js Web UI]
        UIComp[管理组件]
        UIReal[实时监控]
    end
    
    subgraph "MCP服务层"
        MCP[FastMCP Server v2.1]
        Auth[认证中间件]
        Tools[MCP Tools]
        Resources[MCP Resources]
        Prompts[MCP Prompts]
    end
    
    subgraph "业务逻辑层"
        AgentMgr[代理管理器]
        SiteMgr[站点管理器]
        ConfigMgr[配置管理器]
        PublishEngine[发布引擎]
    end
    
    subgraph "数据持久层"
        DB[(PostgreSQL)]
        ConfigFiles[YAML配置文件]
        Logs[审计日志]
    end
    
    subgraph "外部服务"
        WP1[WordPress Site 1]
        WP2[WordPress Site 2]
        WP3[WordPress Site 3]
    end
    
    UI --> MCP
    UIComp --> Tools
    UIReal --> Resources
    
    MCP --> Auth
    Auth --> Tools
    Auth --> Resources
    Auth --> Prompts
    
    Tools --> AgentMgr
    Tools --> SiteMgr
    Tools --> PublishEngine
    
    AgentMgr --> DB
    SiteMgr --> ConfigFiles
    ConfigMgr --> ConfigFiles
    PublishEngine --> WP1
    PublishEngine --> WP2
    PublishEngine --> WP3
    
    Auth --> Logs
```

### 2.2 认证架构设计

基于FastMCP BearerAuthProvider的认证系统：

```mermaid
sequenceDiagram
    participant Agent as AI代理
    participant Auth as 认证中间件
    participant MCP as MCP服务器
    participant DB as 数据库
    
    Agent->>+Auth: 连接请求 (Bearer Token)
    Auth->>+DB: 验证API密钥
    DB-->>-Auth: 密钥有效性
    
    alt 密钥有效
        Auth->>+MCP: 建立MCP连接
        MCP-->>-Auth: 连接成功
        Auth-->>-Agent: 认证成功
        
        Note over Agent,MCP: 正常MCP协议交互
        
        Agent->>+MCP: 调用Tools
        MCP->>Auth: 权限检查
        Auth->>DB: 记录审计日志
        MCP-->>-Agent: 工具执行结果
    else 密钥无效
        Auth->>DB: 记录失败尝试
        Auth-->>-Agent: 401 未授权
    end
```

### 2.3 多站点发布架构

```mermaid
graph LR
    subgraph "文章提交"
        Agent[AI代理]
        Article[文章内容]
        Target[目标站点]
    end
    
    subgraph "发布路由系统"
        Router[站点路由器]
        Config[sites.yml]
        Pool1[连接池1]
        Pool2[连接池2]  
        Pool3[连接池3]
    end
    
    subgraph "WordPress站点"
        WP1[技术博客<br/>api1.example.com]
        WP2[个人博客<br/>api2.example.com]
        WP3[作品集<br/>api3.example.com]
    end
    
    Agent --> Article
    Article --> Target
    Target --> Router
    
    Router --> Config
    Config --> Pool1
    Config --> Pool2
    Config --> Pool3
    
    Pool1 --> WP1
    Pool2 --> WP2
    Pool3 --> WP3
```

## 3. 核心组件设计

### 3.1 多代理认证系统

#### 3.1.1 FastMCP认证提供者集成

```python
from fastmcp.auth import BearerAuthProvider
from mcp_wordpress.auth.agents import AgentKeyValidator

class MultiAgentAuthProvider(BearerAuthProvider):
    def __init__(self, config: AgentConfig):
        self.agent_validator = AgentKeyValidator(config)
        
    async def validate_token(self, token: str) -> Optional[AccessToken]:
        """验证代理API密钥并返回访问令牌"""
        agent = await self.agent_validator.validate_key(token)
        if agent:
            return AccessToken(
                client_id=agent.id,
                scopes=["article:submit", "article:read"],
                metadata={"agent_name": agent.name, "role": agent.role}
            )
        return None
```

#### 3.1.2 配置文件管理

**agents.yml配置结构**：
```yaml
# agents.yml - 多代理配置
agents:
  - id: "ai-writer-001"
    name: "AI内容创作专家"
    api_key: "sk-aw-8f9e7d6c5b4a3210..."
    description: "专注于技术文章写作的AI代理"
    role: "content-creator"
    created_at: "2024-01-15T08:00:00Z"
    
  - id: "seo-optimizer-002"  
    name: "SEO优化专家"
    api_key: "sk-so-1a2b3c4d5e6f7890..."
    description: "负责SEO关键词优化和内容结构调整"
    role: "seo-optimizer"
    created_at: "2024-01-16T09:30:00Z"
    
  - id: "content-editor-003"
    name: "内容编辑审校"
    api_key: "sk-ce-f1e2d3c4b5a69708..."
    description: "进行语言润色和质量把控"
    role: "editor"
    created_at: "2024-01-17T14:20:00Z"

# 全局配置
global_settings:
  max_concurrent_agents: 10
  session_timeout: 1800  # 30分钟
  key_rotation_enabled: false
  audit_log_level: "info"
```

#### 3.1.3 动态配置加载

```python
class AgentConfigManager:
    def __init__(self, config_path: str = "config/agents.yml"):
        self.config_path = config_path
        self.agents: Dict[str, Agent] = {}
        self.file_watcher = None
        
    async def load_config(self) -> None:
        """加载代理配置文件"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = yaml.safe_load(f)
                
            self.agents = {}
            for agent_data in config_data.get('agents', []):
                agent = Agent(**agent_data)
                self.agents[agent.id] = agent
                
            logger.info(f"Loaded {len(self.agents)} agents from config")
            
        except Exception as e:
            logger.error(f"Failed to load agent config: {e}")
            raise ConfigurationError(f"Agent config loading failed: {e}")
    
    async def start_hot_reload(self) -> None:
        """启动配置文件热重载监控"""
        self.file_watcher = FileSystemWatcher(
            path=self.config_path,
            callback=self.reload_config
        )
        await self.file_watcher.start()
```

### 3.2 多站点发布系统

#### 3.2.1 站点配置管理

**sites.yml配置结构**：
```yaml
# sites.yml - 多站点配置
sites:
  - id: "tech-blog"
    name: "技术博客"
    api_url: "https://tech.example.com/wp-json/wp/v2"
    username: "publisher"
    app_password: "abcd efgh ijkl mnop"
    default_category: "技术分享"
    default_tags: ["编程", "技术"]
    connection_pool:
      max_connections: 5
      idle_timeout: 300
    health_check_interval: 60
    
  - id: "personal-blog"
    name: "个人博客" 
    api_url: "https://personal.example.com/wp-json/wp/v2"
    username: "author"
    app_password: "qrst uvwx yz12 3456"
    default_category: "生活感悟"
    connection_pool:
      max_connections: 3
      idle_timeout: 600
    health_check_interval: 120
    
  - id: "portfolio"
    name: "作品集网站"
    api_url: "https://portfolio.example.com/wp-json/wp/v2"
    username: "creator"
    app_password: "7890 abcd efgh ijkl"
    default_category: "项目展示"
    connection_pool:
      max_connections: 2
      idle_timeout: 900
    health_check_interval: 300

# 全局发布配置
publishing:
  default_status: "publish"
  max_concurrent_publishes: 5
  retry_attempts: 3
  retry_delay: 30
  timeout: 120
```

#### 3.2.2 站点路由器实现

```python
class MultiSitePublisher:
    def __init__(self, config: SiteConfig):
        self.sites: Dict[str, WordPressClient] = {}
        self.connection_pools: Dict[str, ConnectionPool] = {}
        self.health_monitors: Dict[str, HealthMonitor] = {}
        
    async def initialize_sites(self) -> None:
        """初始化所有WordPress站点连接"""
        for site_config in self.config.sites:
            # 创建WordPress客户端
            wp_client = WordPressClient(
                api_url=site_config.api_url,
                username=site_config.username,
                app_password=site_config.app_password
            )
            
            # 创建连接池
            pool = ConnectionPool(
                max_connections=site_config.connection_pool.max_connections,
                idle_timeout=site_config.connection_pool.idle_timeout
            )
            
            # 创建健康监控器
            monitor = HealthMonitor(
                site_id=site_config.id,
                check_interval=site_config.health_check_interval
            )
            
            self.sites[site_config.id] = wp_client
            self.connection_pools[site_config.id] = pool
            self.health_monitors[site_config.id] = monitor
            
            # 启动健康检查
            await monitor.start()
    
    async def publish_article(
        self, 
        article: Article, 
        target_site: str,
        agent_id: str
    ) -> PublishResult:
        """发布文章到指定站点"""
        
        if target_site not in self.sites:
            raise SiteNotFoundError(f"Site '{target_site}' not configured")
            
        wp_client = self.sites[target_site]
        
        try:
            # 更新文章状态
            article.status = ArticleStatus.PUBLISHING
            article.target_site = target_site
            article.publishing_agent = agent_id
            await self.update_article(article)
            
            # 执行WordPress发布
            result = await wp_client.create_post(
                title=article.title,
                content_markdown=article.content_markdown,
                tags=article.tags,
                category=article.category
            )
            
            # 更新发布结果
            article.status = ArticleStatus.PUBLISHED
            article.wordpress_post_id = result["id"]
            article.wordpress_permalink = result.get("link")
            await self.update_article(article)
            
            # 记录审计日志
            await self.audit_log.log_publish_success(
                article_id=article.id,
                agent_id=agent_id,
                target_site=target_site,
                wp_post_id=result["id"]
            )
            
            return PublishResult(
                success=True,
                article_id=article.id,
                wp_post_id=result["id"],
                wp_permalink=result.get("link"),
                target_site=target_site
            )
            
        except Exception as e:
            # 更新失败状态
            article.status = ArticleStatus.PUBLISH_FAILED
            article.publish_error_message = str(e)
            await self.update_article(article)
            
            # 记录审计日志
            await self.audit_log.log_publish_failure(
                article_id=article.id,
                agent_id=agent_id,
                target_site=target_site,
                error=str(e)
            )
            
            return PublishResult(
                success=False,
                article_id=article.id,
                error=str(e),
                target_site=target_site
            )
```

### 3.3 Web管理界面架构

#### 3.3.1 前端技术栈

```typescript
// 核心技术栈配置
const techStack = {
  framework: "Next.js 14+",
  language: "TypeScript",
  styling: "Tailwind CSS + Shadcn/ui",
  stateManagement: "Zustand + TanStack Query",
  realtime: "EventSource (SSE)",
  charts: "Recharts",
  tables: "TanStack Table",
  forms: "React Hook Form + Zod"
}
```

#### 3.3.2 界面组件架构

```typescript
// 主要界面组件定义
interface WebUIComponents {
  // 多代理监控面板
  agentDashboard: {
    agentStatusGrid: AgentStatusCard[]
    realtimeActivity: ActivityFeedItem[]
    agentMetrics: PerformanceChart[]
    connectionManager: ConnectionControlPanel
  }
  
  // 多站点管理面板
  siteManagement: {
    siteOverview: SiteStatusCard[]
    publishingQueue: QueuedPublishItem[]
    healthMonitoring: HealthCheckPanel[]
    connectionPools: PoolStatusDisplay[]
  }
  
  // 内容审核工作台
  contentReview: {
    articleGrid: ArticleCard[]
    previewPane: MarkdownRenderer
    metadataPanel: ArticleMetaDisplay
    batchActions: BulkOperationControls
    collaborationView: AgentContributionTracker
  }
  
  // 系统配置管理
  configManagement: {
    agentConfig: YAMLEditor
    siteConfig: YAMLEditor
    systemSettings: SettingsForm
    configValidation: ValidationResults
    hotReload: ReloadTrigger
  }
  
  // 实时监控仪表盘
  monitoringDashboard: {
    systemMetrics: MetricDisplayGrid
    eventStream: RealTimeEventFeed
    performanceCharts: ChartContainer[]
    alertManager: AlertNotificationPanel
  }
}
```

#### 3.3.3 实时数据同步

```typescript
// 实时状态同步Hook
const useRealtimeAgentStatus = () => {
  const [agents, setAgents] = useAgentStore()
  
  useEffect(() => {
    const eventSource = new EventSource('/api/v2.1/realtime/agents')
    
    eventSource.addEventListener('agent_status_change', (event) => {
      const { agentId, status, metadata } = JSON.parse(event.data)
      
      setAgents(prev => prev.map(agent => 
        agent.id === agentId 
          ? { 
              ...agent, 
              status, 
              lastSeen: new Date(),
              ...metadata 
            }
          : agent
      ))
    })
    
    eventSource.addEventListener('agent_connected', (event) => {
      const agentData = JSON.parse(event.data)
      toast.success(`代理 ${agentData.name} 已连接`)
    })
    
    eventSource.addEventListener('agent_disconnected', (event) => {
      const agentData = JSON.parse(event.data)
      toast.info(`代理 ${agentData.name} 已断开连接`)
    })
    
    return () => eventSource.close()
  }, [setAgents])
  
  return agents
}

// 多站点发布状态追踪Hook
const useMultiSitePublishing = () => {
  const [publishingQueue, setQueue] = useState<PublishingQueueItem[]>([])
  
  useEffect(() => {
    const eventSource = new EventSource('/api/v2.1/realtime/publishing')
    
    eventSource.addEventListener('publish_started', (event) => {
      const item = JSON.parse(event.data)
      setQueue(prev => [...prev, item])
    })
    
    eventSource.addEventListener('publish_progress', (event) => {
      const { articleId, progress } = JSON.parse(event.data)
      setQueue(prev => prev.map(item =>
        item.articleId === articleId 
          ? { ...item, progress }
          : item
      ))
    })
    
    eventSource.addEventListener('publish_completed', (event) => {
      const { articleId, result } = JSON.parse(event.data)
      setQueue(prev => prev.filter(item => item.articleId !== articleId))
      
      if (result.success) {
        toast.success(`文章发布成功：${result.wp_permalink}`)
      } else {
        toast.error(`文章发布失败：${result.error}`)
      }
    })
    
    return () => eventSource.close()
  }, [])
  
  return { publishingQueue }
}
```

## 4. 数据模型扩展

### 4.1 扩展的Article模型

```python
class Article(SQLModel, table=True):
    __tablename__ = "articles"
    
    # 现有字段（保持不变）
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str = Field(max_length=200)
    content_markdown: str
    content_html: Optional[str] = None
    tags: Optional[str] = None
    category: Optional[str] = None
    status: ArticleStatus = Field(default=ArticleStatus.PENDING_REVIEW)
    
    # WordPress集成字段（保持不变）
    wordpress_post_id: Optional[int] = None
    wordpress_permalink: Optional[str] = None
    publish_error_message: Optional[str] = None
    
    # v2.1新增：多代理支持字段
    submitting_agent_id: Optional[str] = Field(
        default=None,
        description="提交文章的AI代理ID"
    )
    submitting_agent_name: Optional[str] = Field(
        default=None,
        description="提交代理的显示名称"
    )
    agent_metadata: Optional[str] = Field(
        default=None,
        description="代理相关元数据（JSON格式）"
    )
    
    # v2.1新增：多站点支持字段
    target_site_id: Optional[str] = Field(
        default=None,
        description="目标发布站点ID"
    )
    target_site_name: Optional[str] = Field(
        default=None,
        description="目标站点显示名称"
    )
    publishing_agent_id: Optional[str] = Field(
        default=None,
        description="执行发布操作的代理ID"
    )
    
    # 时间戳（使用timezone-aware默认值）
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="创建时间",
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="更新时间", 
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    
    # 审核元数据（保持不变）
    reviewer_notes: Optional[str] = None
    rejection_reason: Optional[str] = None


class ArticleStatus(str, Enum):
    PENDING_REVIEW = "pending_review"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    PUBLISH_FAILED = "publish_failed"
    REJECTED = "rejected"
```

### 4.2 新增Agent模型

```python
class Agent(SQLModel, table=True):
    __tablename__ = "agents"
    
    id: str = Field(primary_key=True, max_length=50)
    name: str = Field(max_length=100)
    description: Optional[str] = Field(default=None, max_length=500)
    role: str = Field(max_length=50)  # content-creator, seo-optimizer, editor等
    api_key_hash: str = Field(max_length=255)  # 存储API密钥的哈希值
    
    # 状态信息
    is_active: bool = Field(default=True)
    last_seen: Optional[datetime] = None
    total_articles_submitted: int = Field(default=0)
    
    # 时间戳
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )


class Site(SQLModel, table=True):
    __tablename__ = "sites"
    
    id: str = Field(primary_key=True, max_length=50)
    name: str = Field(max_length=100)
    api_url: str = Field(max_length=255)
    username: str = Field(max_length=100)
    # 注意：不存储明文密码，通过配置文件管理
    
    # 站点配置
    default_category: Optional[str] = Field(default=None, max_length=100)
    default_tags: Optional[str] = Field(default=None, max_length=500)
    
    # 状态信息
    is_active: bool = Field(default=True)
    last_health_check: Optional[datetime] = None
    health_status: str = Field(default="unknown")  # healthy, warning, error
    total_posts_published: int = Field(default=0)
    
    # 时间戳
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
    updated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
```

### 4.3 审计日志模型

```python
class AuditLog(SQLModel, table=True):
    __tablename__ = "audit_logs"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    
    # 事件信息
    event_type: str = Field(max_length=50)  # agent_auth, article_submit, article_publish等
    event_category: str = Field(max_length=30)  # auth, content, system
    severity: str = Field(max_length=20)  # info, warning, error
    
    # 关联信息
    agent_id: Optional[str] = Field(default=None, max_length=50)
    article_id: Optional[int] = None
    site_id: Optional[str] = Field(default=None, max_length=50)
    
    # 事件详情
    message: str = Field(max_length=1000)
    metadata: Optional[str] = Field(default=None)  # JSON格式的附加信息
    
    # 网络信息
    ip_address: Optional[str] = Field(default=None, max_length=45)
    user_agent: Optional[str] = Field(default=None, max_length=500)
    
    # 时间戳
    timestamp: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        sa_column=Column(DateTime(timezone=True), server_default=func.now())
    )
```

## 5. 扩展的MCP接口定义

### 5.1 v2.1增强Tools

#### 5.1.1 多代理增强的Tools

**submit_article** (增强版)
```json
{
  "name": "submit_article",
  "description": "Submit a new article for review with multi-agent and multi-site support",
  "inputSchema": {
    "type": "object",
    "properties": {
      "title": {"type": "string", "maxLength": 200},
      "content_markdown": {"type": "string"},
      "tags": {"type": "string", "description": "Comma-separated tags"},
      "category": {"type": "string"},
      "target_site": {
        "type": "string", 
        "description": "Target WordPress site ID for publishing"
      },
      "agent_metadata": {
        "type": "object",
        "description": "Additional metadata from submitting agent"
      }
    },
    "required": ["title", "content_markdown"]
  }
}
```

**list_articles** (增强版)
```json
{
  "name": "list_articles", 
  "description": "List articles with multi-agent and multi-site filtering",
  "inputSchema": {
    "type": "object",
    "properties": {
      "status": {"type": "string", "enum": ["pending_review", "publishing", "published", "rejected", "publish_failed"]},
      "agent_id": {"type": "string", "description": "Filter by submitting agent"},
      "target_site": {"type": "string", "description": "Filter by target site"},
      "search": {"type": "string"},
      "limit": {"type": "integer", "default": 50, "maximum": 100}
    }
  }
}
```

#### 5.1.2 新增管理Tools

**list_agents**
```json
{
  "name": "list_agents",
  "description": "List all configured AI agents and their status",
  "inputSchema": {
    "type": "object", 
    "properties": {
      "include_inactive": {"type": "boolean", "default": false}
    }
  }
}
```

**list_sites**
```json
{
  "name": "list_sites",
  "description": "List all configured WordPress sites and their health status",
  "inputSchema": {
    "type": "object",
    "properties": {
      "include_inactive": {"type": "boolean", "default": false}
    }
  }
}
```

**get_agent_stats**
```json
{
  "name": "get_agent_stats",
  "description": "Get statistics for a specific agent",
  "inputSchema": {
    "type": "object",
    "properties": {
      "agent_id": {"type": "string"}
    },
    "required": ["agent_id"]
  }
}
```

**get_site_health**
```json
{
  "name": "get_site_health",
  "description": "Get health status and metrics for a WordPress site",
  "inputSchema": {
    "type": "object",
    "properties": {
      "site_id": {"type": "string"}
    },
    "required": ["site_id"]
  }
}
```

### 5.2 v2.1增强Resources

#### 5.2.1 代理相关Resources
- **agent://list** - 所有代理状态列表
- **agent://{id}** - 特定代理详细信息
- **agent://{id}/articles** - 特定代理提交的文章列表
- **agent://{id}/stats** - 特定代理的统计信息

#### 5.2.2 站点相关Resources
- **site://list** - 所有站点状态列表
- **site://{id}** - 特定站点详细信息
- **site://{id}/articles** - 特定站点的文章列表
- **site://{id}/health** - 特定站点的健康状态

#### 5.2.3 系统监控Resources
- **system://metrics** - 系统性能指标
- **system://events** - 系统事件流
- **audit://logs** - 审计日志（分页）
- **config://agents** - 代理配置状态
- **config://sites** - 站点配置状态

### 5.3 v2.1增强Prompts

#### 5.3.1 多代理协作Prompts

**multi_agent_workflow**
```json
{
  "name": "multi_agent_workflow",
  "description": "Generate workflow template for multi-agent content collaboration",
  "arguments": [
    {
      "name": "content_type",
      "description": "Type of content to be created",
      "required": true
    },
    {
      "name": "agent_roles",
      "description": "Roles of participating agents",
      "required": true  
    },
    {
      "name": "target_sites",
      "description": "Target publishing sites",
      "required": false
    }
  ]
}
```

**agent_specialization_guide**
```json
{
  "name": "agent_specialization_guide", 
  "description": "Generate role-specific guidelines for AI agents",
  "arguments": [
    {
      "name": "agent_role",
      "description": "Role of the agent (content-creator, seo-optimizer, editor)",
      "required": true
    },
    {
      "name": "content_domain", 
      "description": "Content domain or industry focus",
      "required": false
    }
  ]
}
```

## 6. 错误处理和安全强化

### 6.1 认证错误处理

```python
class AuthenticationError(MCPError):
    def __init__(self, message: str, agent_id: str = None):
        super().__init__(
            code=MCPErrorCodes.AUTH_FAILED,
            message=message,
            data={"agent_id": agent_id, "timestamp": datetime.utcnow().isoformat()}
        )

class AgentNotFoundError(MCPError):
    def __init__(self, agent_id: str):
        super().__init__(
            code=MCPErrorCodes.AGENT_NOT_FOUND,
            message=f"Agent '{agent_id}' not found or inactive",
            data={"agent_id": agent_id}
        )

class SiteNotFoundError(MCPError):
    def __init__(self, site_id: str):
        super().__init__(
            code=MCPErrorCodes.SITE_NOT_FOUND,
            message=f"Site '{site_id}' not configured or inactive", 
            data={"site_id": site_id}
        )

class ConfigurationError(MCPError):
    def __init__(self, message: str, config_file: str = None):
        super().__init__(
            code=MCPErrorCodes.CONFIG_ERROR,
            message=message,
            data={"config_file": config_file}
        )
```

### 6.2 安全强化措施

#### 6.2.1 API密钥安全
```python
class SecureKeyManager:
    @staticmethod
    def hash_api_key(key: str) -> str:
        """使用bcrypt安全哈希API密钥"""
        return bcrypt.hashpw(key.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    @staticmethod
    def verify_api_key(key: str, hashed: str) -> bool:
        """验证API密钥"""
        try:
            return bcrypt.checkpw(key.encode('utf-8'), hashed.encode('utf-8'))
        except Exception:
            return False
    
    @staticmethod
    def is_key_strong(key: str) -> bool:
        """检查API密钥强度"""
        if len(key) < 32:
            return False
        
        # 检查熵值
        import secrets
        entropy = len(set(key)) / len(key)
        return entropy > 0.5  # 要求足够的字符多样性
```

#### 6.2.2 会话管理
```python
class SessionManager:
    def __init__(self):
        self.active_sessions: Dict[str, AgentSession] = {}
        self.session_timeout = 1800  # 30分钟
        
    async def create_session(self, agent: Agent) -> str:
        """创建代理会话"""
        session_id = secrets.token_urlsafe(32)
        session = AgentSession(
            session_id=session_id,
            agent_id=agent.id,
            created_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        self.active_sessions[session_id] = session
        
        # 记录会话创建
        await audit_log.log_session_created(agent.id, session_id)
        
        return session_id
    
    async def validate_session(self, session_id: str, agent_id: str) -> bool:
        """验证会话有效性"""
        session = self.active_sessions.get(session_id)
        if not session:
            return False
            
        if session.agent_id != agent_id:
            return False
            
        # 检查会话是否过期
        if datetime.utcnow() - session.last_activity > timedelta(seconds=self.session_timeout):
            await self.terminate_session(session_id)
            return False
            
        # 更新活动时间
        session.last_activity = datetime.utcnow()
        return True
```

#### 6.2.3 限流和保护

```python
class RateLimiter:
    def __init__(self):
        self.connection_attempts: Dict[str, List[datetime]] = {}
        self.blocked_ips: Dict[str, datetime] = {}
        
    async def check_connection_limit(self, ip_address: str) -> bool:
        """检查连接限制"""
        now = datetime.utcnow()
        window = timedelta(minutes=5)
        max_attempts = 10
        
        # 清理过期记录
        if ip_address in self.connection_attempts:
            self.connection_attempts[ip_address] = [
                attempt for attempt in self.connection_attempts[ip_address] 
                if now - attempt < window
            ]
        
        # 检查是否被阻止
        if ip_address in self.blocked_ips:
            if now - self.blocked_ips[ip_address] < timedelta(hours=1):
                return False
            else:
                del self.blocked_ips[ip_address]
        
        # 记录尝试
        if ip_address not in self.connection_attempts:
            self.connection_attempts[ip_address] = []
        
        self.connection_attempts[ip_address].append(now)
        
        # 检查是否超过限制
        if len(self.connection_attempts[ip_address]) > max_attempts:
            self.blocked_ips[ip_address] = now
            await audit_log.log_ip_blocked(ip_address)
            return False
            
        return True
```

## 7. 测试策略

### 7.1 单元测试策略

#### 7.1.1 认证系统测试
```python
class TestMultiAgentAuth(unittest.TestCase):
    async def test_valid_agent_authentication(self):
        """测试有效代理认证"""
        auth_provider = MultiAgentAuthProvider(test_config)
        token = await auth_provider.validate_token("valid-api-key")
        
        self.assertIsNotNone(token)
        self.assertEqual(token.client_id, "test-agent-001")
        self.assertIn("article:submit", token.scopes)
    
    async def test_invalid_agent_authentication(self):
        """测试无效代理认证"""
        auth_provider = MultiAgentAuthProvider(test_config)
        token = await auth_provider.validate_token("invalid-key")
        
        self.assertIsNone(token)
    
    async def test_config_hot_reload(self):
        """测试配置热重载"""
        config_manager = AgentConfigManager("test_agents.yml")
        await config_manager.load_config()
        
        initial_count = len(config_manager.agents)
        
        # 修改配置文件
        self.modify_test_config()
        await config_manager.reload_config()
        
        self.assertNotEqual(len(config_manager.agents), initial_count)
```

#### 7.1.2 多站点发布测试
```python
class TestMultiSitePublishing(unittest.TestCase):
    async def test_site_routing(self):
        """测试站点路由"""
        publisher = MultiSitePublisher(test_site_config)
        await publisher.initialize_sites()
        
        # 测试文章路由到正确站点
        article = self.create_test_article(target_site="tech-blog")
        result = await publisher.publish_article(article, "tech-blog", "test-agent")
        
        self.assertTrue(result.success)
        self.assertEqual(result.target_site, "tech-blog")
    
    async def test_site_health_monitoring(self):
        """测试站点健康监控"""
        monitor = HealthMonitor("test-site")
        
        with mock.patch.object(monitor, 'check_site_health', return_value=False):
            status = await monitor.get_health_status()
            self.assertEqual(status, "error")
    
    async def test_connection_pool_management(self):
        """测试连接池管理"""
        pool = ConnectionPool(max_connections=5)
        
        # 测试连接获取和释放
        connections = []
        for i in range(5):
            conn = await pool.get_connection()
            connections.append(conn)
        
        self.assertEqual(len(pool.active_connections), 5)
        
        # 释放连接
        for conn in connections:
            await pool.return_connection(conn)
        
        self.assertEqual(len(pool.idle_connections), 5)
```

### 7.2 集成测试策略

#### 7.2.1 端到端工作流测试
```python
class TestE2EWorkflow(unittest.TestCase):
    async def test_multi_agent_article_workflow(self):
        """测试多代理文章工作流"""
        # 1. AI-Writer代理提交文章
        writer_client = MCPClient(auth_token="writer-api-key")
        submit_result = await writer_client.call_tool("submit_article", {
            "title": "测试文章",
            "content_markdown": "# 测试内容",
            "target_site": "tech-blog"
        })
        
        article_id = submit_result["article_id"]
        
        # 2. SEO-Optimizer代理查看文章
        seo_client = MCPClient(auth_token="seo-api-key")
        article = await seo_client.read_resource(f"article://{article_id}")
        
        # 3. 人工审核批准
        review_client = MCPClient(auth_token="reviewer-api-key")
        approve_result = await review_client.call_tool("approve_article", {
            "article_id": article_id,
            "reviewer_notes": "内容质量良好，批准发布"
        })
        
        # 4. 验证发布结果
        self.assertTrue(approve_result["success"])
        self.assertIsNotNone(approve_result["wordpress_post_id"])
    
    async def test_multi_site_publishing_isolation(self):
        """测试多站点发布隔离"""
        # 提交到不同站点的文章
        articles = [
            {"title": "技术文章", "target_site": "tech-blog"},
            {"title": "生活感悟", "target_site": "personal-blog"},
            {"title": "项目展示", "target_site": "portfolio"}
        ]
        
        client = MCPClient(auth_token="test-api-key")
        
        for article_data in articles:
            result = await client.call_tool("submit_article", article_data)
            article_id = result["article_id"]
            
            # 批准发布
            await client.call_tool("approve_article", {"article_id": article_id})
            
            # 验证发布到正确站点
            article = await client.read_resource(f"article://{article_id}")
            self.assertEqual(article["target_site"], article_data["target_site"])
```

### 7.3 性能测试策略

#### 7.3.1 并发代理连接测试
```python
class TestConcurrentAgents(unittest.TestCase):
    async def test_multiple_agent_connections(self):
        """测试多代理并发连接"""
        concurrent_agents = 10
        tasks = []
        
        for i in range(concurrent_agents):
            agent_client = MCPClient(auth_token=f"agent-{i:03d}-api-key")
            task = asyncio.create_task(self.simulate_agent_activity(agent_client))
            tasks.append(task)
        
        results = await asyncio.gather(*tasks)
        
        # 验证所有代理都成功完成操作
        self.assertEqual(len(results), concurrent_agents)
        self.assertTrue(all(result["success"] for result in results))
    
    async def simulate_agent_activity(self, client: MCPClient):
        """模拟代理活动"""
        # 提交文章
        submit_result = await client.call_tool("submit_article", {
            "title": f"文章来自{client.agent_id}",
            "content_markdown": "# 测试内容"
        })
        
        # 查询文章状态
        article_id = submit_result["article_id"]
        status_result = await client.call_tool("get_article_status", {
            "article_id": article_id
        })
        
        return {"success": True, "article_id": article_id}
```

### 7.4 安全测试策略

#### 7.4.1 认证安全测试
```python
class TestSecurityMeasures(unittest.TestCase):
    async def test_api_key_brute_force_protection(self):
        """测试API密钥暴力破解保护"""
        invalid_keys = [f"invalid-key-{i}" for i in range(20)]
        
        auth_provider = MultiAgentAuthProvider(test_config)
        
        # 尝试多次无效认证
        for key in invalid_keys:
            token = await auth_provider.validate_token(key)
            self.assertIsNone(token)
        
        # 验证IP被阻止
        rate_limiter = RateLimiter()
        is_allowed = await rate_limiter.check_connection_limit("127.0.0.1")
        self.assertFalse(is_allowed)
    
    async def test_session_timeout(self):
        """测试会话超时"""
        session_manager = SessionManager()
        agent = Agent(id="test-agent", name="Test Agent")
        
        session_id = await session_manager.create_session(agent)
        
        # 初始验证应该成功
        is_valid = await session_manager.validate_session(session_id, agent.id)
        self.assertTrue(is_valid)
        
        # 模拟会话超时
        session = session_manager.active_sessions[session_id]
        session.last_activity = datetime.utcnow() - timedelta(hours=1)
        
        # 超时后验证应该失败
        is_valid = await session_manager.validate_session(session_id, agent.id)
        self.assertFalse(is_valid)
```

## 8. 部署架构

### 8.1 容器化部署配置

#### 8.1.1 Docker Compose配置
```yaml
# docker-compose.yml (v2.1)
version: '3.8'

services:
  # MCP服务器 v2.1
  mcp-server:
    build:
      context: .
      dockerfile: Dockerfile.v2.1
    container_name: mcp-wordpress-v2.1
    environment:
      # MCP服务器配置
      - MCP_TRANSPORT=sse
      - MCP_PORT=8000
      - MCP_SSE_PATH=/sse
      
      # FastMCP认证配置
      - FASTMCP_SERVER_AUTH=bearer
      - FASTMCP_SERVER_AUTH_BEARER_TOKENS_FILE=/config/api_keys.txt
      
      # 数据库配置
      - DATABASE_URL=postgresql+asyncpg://mcpuser:mcppass@postgres:5432/mcpdb
      
      # 配置文件路径
      - AGENTS_CONFIG_PATH=/config/agents.yml
      - SITES_CONFIG_PATH=/config/sites.yml
      
      # 安全配置
      - SECRET_KEY=${SECRET_KEY}
      - DEBUG=false
      - LOG_LEVEL=INFO
    
    ports:
      - "8000:8000"
    
    volumes:
      - ./config:/config:ro
      - ./logs:/app/logs
      - agent_uploads:/app/uploads
    
    depends_on:
      - postgres
      - redis
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
    restart: unless-stopped
  
  # Web管理界面
  mcp-ui:
    build:
      context: ./ui
      dockerfile: Dockerfile
    container_name: mcp-ui-v2.1
    environment:
      - NODE_ENV=production
      - NEXT_PUBLIC_MCP_API_URL=http://mcp-server:8000
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - NEXTAUTH_URL=http://localhost:3000
    
    ports:
      - "3000:3000"
    
    depends_on:
      - mcp-server
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:3000/api/health"]
      interval: 30s
      timeout: 10s
      retries: 3
    
    restart: unless-stopped
  
  # PostgreSQL数据库
  postgres:
    image: postgres:15-alpine
    container_name: mcp-postgres-v2.1
    environment:
      - POSTGRES_DB=mcpdb
      - POSTGRES_USER=mcpuser
      - POSTGRES_PASSWORD=mcppass
      - POSTGRES_INITDB_ARGS=--auth-host=scram-sha-256
    
    ports:
      - "5432:5432"
    
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./database/init:/docker-entrypoint-initdb.d:ro
    
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U mcpuser -d mcpdb"]
      interval: 30s
      timeout: 10s
      retries: 3
    
    restart: unless-stopped
  
  # Redis缓存（用于会话管理和限流）
  redis:
    image: redis:7-alpine
    container_name: mcp-redis-v2.1
    command: redis-server --appendonly yes --requirepass ${REDIS_PASSWORD}
    
    ports:
      - "6379:6379"
    
    volumes:
      - redis_data:/data
    
    healthcheck:
      test: ["CMD", "redis-cli", "--raw", "incr", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3
    
    restart: unless-stopped

volumes:
  postgres_data:
  redis_data:
  agent_uploads:

networks:
  default:
    name: mcp-v2.1-network
```

#### 8.1.2 配置文件结构
```
config/
├── agents.yml                 # 代理配置
├── sites.yml                  # WordPress站点配置
├── api_keys.txt              # API密钥列表（用于FastMCP认证）
└── system.yml                # 系统全局配置
```

**api_keys.txt示例**：
```
# FastMCP认证密钥文件
# 格式: token:client_id:scopes
sk-aw-8f9e7d6c5b4a3210...:ai-writer-001:article:submit,article:read
sk-so-1a2b3c4d5e6f7890...:seo-optimizer-002:article:submit,article:read
sk-ce-f1e2d3c4b5a69708...:content-editor-003:article:submit,article:read,article:review
```

### 8.2 生产部署策略

#### 8.2.1 环境配置管理
```bash
# .env.production
# 生产环境配置

# 基础服务配置
SECRET_KEY=your-super-secret-key-for-production-use
NEXTAUTH_SECRET=your-nextauth-secret-key

# Redis配置
REDIS_PASSWORD=secure-redis-password

# 数据库配置（外部托管）
DATABASE_URL=postgresql+asyncpg://user:pass@db.example.com:5432/mcpdb

# WordPress站点（通过配置文件管理）
# 不在环境变量中存储WordPress凭据

# 监控和日志
LOG_LEVEL=INFO
SENTRY_DSN=https://your-sentry-dsn
PROMETHEUS_ENABLED=true

# SSL和安全
SSL_CERT_PATH=/certs/fullchain.pem  
SSL_KEY_PATH=/certs/privkey.pem
FORCE_HTTPS=true
```

#### 8.2.2 负载均衡配置
```nginx
# nginx.conf - 反向代理配置
upstream mcp_servers {
    server mcp-server-1:8000;
    server mcp-server-2:8000;
    keepalive 32;
}

upstream ui_servers {
    server mcp-ui-1:3000;
    server mcp-ui-2:3000;
    keepalive 32;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/ssl/certs/fullchain.pem;
    ssl_certificate_key /etc/ssl/private/privkey.pem;

    # UI路由
    location / {
        proxy_pass http://ui_servers;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }

    # MCP API路由
    location /api/mcp/ {
        proxy_pass http://mcp_servers/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # SSE支持
        proxy_set_header Connection '';
        proxy_buffering off;
        proxy_cache off;
        proxy_read_timeout 86400;
    }

    # 健康检查
    location /health {
        proxy_pass http://mcp_servers/health;
        access_log off;
    }
}
```

### 8.3 监控和日志

#### 8.3.1 Prometheus监控配置
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'mcp-server'
    static_configs:
      - targets: ['mcp-server:8000']
    metrics_path: '/metrics'
    scrape_interval: 30s
    
  - job_name: 'mcp-ui'
    static_configs:
      - targets: ['mcp-ui:3000']
    metrics_path: '/api/metrics'
    scrape_interval: 30s

  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
    scrape_interval: 30s
    
  - job_name: 'nginx'
    static_configs:
      - targets: ['nginx-exporter:9113']
    scrape_interval: 30s
```

#### 8.3.2 Grafana仪表盘配置
```json
{
  "dashboard": {
    "title": "MCP WordPress Publisher v2.1",
    "panels": [
      {
        "title": "代理连接状态",
        "type": "stat",
        "targets": [
          {
            "expr": "mcp_active_agents_total",
            "legendFormat": "活跃代理数"
          }
        ]
      },
      {
        "title": "站点健康状态",
        "type": "table",
        "targets": [
          {
            "expr": "mcp_site_health_status",
            "legendFormat": "{{site_id}}"
          }
        ]
      },
      {
        "title": "文章发布吞吐量",
        "type": "graph",
        "targets": [
          {
            "expr": "rate(mcp_articles_published_total[5m])",
            "legendFormat": "文章/分钟"
          }
        ]
      },
      {
        "title": "API请求延迟",
        "type": "graph",
        "targets": [
          {
            "expr": "histogram_quantile(0.95, rate(mcp_request_duration_seconds_bucket[5m]))",
            "legendFormat": "95th percentile"
          }
        ]
      }
    ]
  }
}
```

## 9. 性能优化和可扩展性

### 9.1 数据库性能优化

#### 9.1.1 索引策略
```sql
-- 为v2.1新增字段创建索引
CREATE INDEX CONCURRENTLY idx_articles_submitting_agent 
ON articles(submitting_agent_id) 
WHERE submitting_agent_id IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_articles_target_site 
ON articles(target_site_id) 
WHERE target_site_id IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_articles_agent_status 
ON articles(submitting_agent_id, status) 
WHERE submitting_agent_id IS NOT NULL;

CREATE INDEX CONCURRENTLY idx_articles_site_status 
ON articles(target_site_id, status) 
WHERE target_site_id IS NOT NULL;

-- 审计日志索引
CREATE INDEX CONCURRENTLY idx_audit_logs_agent_timestamp 
ON audit_logs(agent_id, timestamp DESC);

CREATE INDEX CONCURRENTLY idx_audit_logs_event_type_timestamp 
ON audit_logs(event_type, timestamp DESC);

-- 复合索引用于常见查询
CREATE INDEX CONCURRENTLY idx_articles_status_updated_agent 
ON articles(status, updated_at DESC, submitting_agent_id);
```

#### 9.1.2 分区策略
```sql
-- 审计日志按月分区
CREATE TABLE audit_logs (
    id SERIAL,
    event_type VARCHAR(50),
    agent_id VARCHAR(50),
    timestamp TIMESTAMP WITH TIME ZONE,
    -- 其他字段...
) PARTITION BY RANGE (timestamp);

-- 创建分区表
CREATE TABLE audit_logs_2024_01 PARTITION OF audit_logs
FOR VALUES FROM ('2024-01-01') TO ('2024-02-01');

CREATE TABLE audit_logs_2024_02 PARTITION OF audit_logs  
FOR VALUES FROM ('2024-02-01') TO ('2024-03-01');

-- 自动分区管理
CREATE OR REPLACE FUNCTION create_monthly_partition(table_name text, start_date date)
RETURNS void AS $$
DECLARE
    partition_name text;
    end_date date;
BEGIN
    partition_name := table_name || '_' || to_char(start_date, 'YYYY_MM');
    end_date := start_date + interval '1 month';
    
    EXECUTE format('CREATE TABLE %I PARTITION OF %I 
                   FOR VALUES FROM (%L) TO (%L)',
                   partition_name, table_name, start_date, end_date);
END;
$$ LANGUAGE plpgsql;
```

### 9.2 缓存策略

#### 9.2.1 Redis缓存配置
```python
class CacheManager:
    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url, decode_responses=True)
        
    async def cache_agent_config(self, agent_id: str, config: dict, ttl: int = 3600):
        """缓存代理配置"""
        key = f"agent:config:{agent_id}"
        await self.redis.setex(key, ttl, json.dumps(config))
    
    async def cache_site_health(self, site_id: str, status: dict, ttl: int = 300):
        """缓存站点健康状态"""
        key = f"site:health:{site_id}"
        await self.redis.setex(key, ttl, json.dumps(status))
    
    async def cache_article_stats(self, agent_id: str, stats: dict, ttl: int = 600):
        """缓存代理文章统计"""
        key = f"agent:stats:{agent_id}"
        await self.redis.setex(key, ttl, json.dumps(stats))
    
    async def invalidate_cache_pattern(self, pattern: str):
        """批量删除缓存"""
        keys = await self.redis.keys(pattern)
        if keys:
            await self.redis.delete(*keys)
```

#### 9.2.2 应用层缓存
```python
from functools import wraps
import asyncio
from typing import Any, Callable

def cache_result(ttl: int = 300, key_prefix: str = ""):
    """缓存函数结果的装饰器"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            cached_result = await cache_manager.get(cache_key)
            if cached_result:
                return json.loads(cached_result)
            
            # 执行函数并缓存结果
            result = await func(*args, **kwargs)
            await cache_manager.setex(cache_key, ttl, json.dumps(result, default=str))
            
            return result
        return wrapper
    return decorator

# 使用示例
class AgentStatsService:
    @cache_result(ttl=600, key_prefix="agent_stats")
    async def get_agent_article_count(self, agent_id: str) -> int:
        """获取代理文章数量（带缓存）"""
        async with get_session() as session:
            result = await session.execute(
                select(func.count(Article.id))
                .where(Article.submitting_agent_id == agent_id)
            )
            return result.scalar()
```

### 9.3 连接池优化

#### 9.3.1 数据库连接池配置
```python
# mcp_wordpress/core/database.py 扩展
class DatabaseManager:
    def __init__(self):
        self.async_engine = create_async_engine(
            settings.database_url,
            # v2.1优化的连接池配置
            pool_size=50,              # 增加基础连接池大小
            max_overflow=100,          # 增加溢出连接数
            pool_pre_ping=True,        # 连接前预检
            pool_recycle=3600,         # 连接回收时间
            pool_timeout=30,           # 获取连接超时
            
            # 新增配置
            pool_reset_on_return='commit',  # 返回时重置连接
            connect_args={
                "server_settings": {
                    "application_name": "mcp_wordpress_v2.1",
                    "jit": "off"  # 禁用JIT以减少延迟
                }
            }
        )
        
        # 创建异步会话工厂
        self.AsyncSessionLocal = sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False,
            autoflush=False,  # 禁用自动flush以提高性能
        )
```

#### 9.3.2 WordPress连接池管理
```python
class WordPressConnectionPool:
    def __init__(self, site_config: SiteConfig):
        self.site_id = site_config.id
        self.max_connections = site_config.connection_pool.max_connections
        self.idle_timeout = site_config.connection_pool.idle_timeout
        
        # 使用aiohttp的连接池
        self.connector = aiohttp.TCPConnector(
            limit=self.max_connections,
            limit_per_host=self.max_connections,
            ttl_dns_cache=300,
            use_dns_cache=True,
            keepalive_timeout=60,
            enable_cleanup_closed=True,
            # 优化SSL性能
            ssl=False if site_config.api_url.startswith('http://') else None
        )
        
        self.timeout = aiohttp.ClientTimeout(
            total=120,      # 总超时
            connect=30,     # 连接超时
            sock_read=60    # 读取超时
        )
        
        self.session = aiohttp.ClientSession(
            connector=self.connector,
            timeout=self.timeout,
            auth=aiohttp.BasicAuth(site_config.username, site_config.app_password)
        )
    
    async def cleanup(self):
        """清理连接池"""
        await self.session.close()
        await self.connector.close()
```

### 9.4 异步任务处理

#### 9.4.1 后台任务队列
```python
from celery import Celery
from mcp_wordpress.core.config import settings

# 创建Celery应用
celery_app = Celery(
    'mcp_wordpress',
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=['mcp_wordpress.tasks']
)

# Celery配置
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    
    # 任务路由
    task_routes={
        'mcp_wordpress.tasks.publish_article': {'queue': 'publishing'},
        'mcp_wordpress.tasks.health_check': {'queue': 'monitoring'},
        'mcp_wordpress.tasks.cleanup_old_logs': {'queue': 'maintenance'},
    },
    
    # 工作进程配置
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=1000,
)

# 发布任务
@celery_app.task(bind=True, max_retries=3)
def publish_article_task(self, article_id: int, target_site: str, agent_id: str):
    """异步发布文章任务"""
    try:
        # 执行发布逻辑
        result = asyncio.run(publish_article_async(article_id, target_site, agent_id))
        return result
    except Exception as exc:
        # 重试逻辑
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=60, exc=exc)
        else:
            # 标记文章为发布失败
            asyncio.run(mark_article_failed(article_id, str(exc)))
            raise

# 健康检查任务
@celery_app.task
def site_health_check_task(site_id: str):
    """站点健康检查任务"""
    return asyncio.run(check_site_health_async(site_id))

# 定期清理任务
@celery_app.task
def cleanup_old_logs_task():
    """清理旧日志任务"""
    return asyncio.run(cleanup_audit_logs_older_than(days=90))
```

#### 9.4.2 定时任务配置
```python
from celery.schedules import crontab

celery_app.conf.beat_schedule = {
    # 每分钟检查站点健康状态
    'health-check-all-sites': {
        'task': 'mcp_wordpress.tasks.health_check_all',
        'schedule': crontab(minute='*'),
    },
    
    # 每小时清理过期会话
    'cleanup-expired-sessions': {
        'task': 'mcp_wordpress.tasks.cleanup_expired_sessions',
        'schedule': crontab(minute=0),
    },
    
    # 每天清理旧审计日志
    'cleanup-old-audit-logs': {
        'task': 'mcp_wordpress.tasks.cleanup_old_logs',
        'schedule': crontab(hour=2, minute=0),
    },
    
    # 每周生成代理活动报告
    'generate-agent-reports': {
        'task': 'mcp_wordpress.tasks.generate_weekly_reports',
        'schedule': crontab(day_of_week=1, hour=6, minute=0),
    },
}
```

## 10. 总结

MCP WordPress Publisher Server v2.1设计在v2.0坚实基础上，实现了企业级的多代理协作和多站点发布能力。关键架构特性包括：

### 10.1 核心增强
- ✅ **多代理认证系统**：基于FastMCP BearerAuthProvider的安全认证
- ✅ **多站点发布管理**：支持3-5个WordPress站点的统一管理
- ✅ **现代化Web界面**：Next.js + TypeScript的完整管理控制台
- ✅ **配置文件管理**：YAML格式配置和热重载机制
- ✅ **增强安全机制**：API密钥认证、审计日志和会话管理

### 10.2 技术亮点
- **无历史包袱**：直接基于v2.0代码库升级，无兼容性约束
- **高性能架构**：异步处理、连接池、缓存策略全面优化
- **企业级安全**：认证、授权、审计、限流全面覆盖
- **完整监控**：Prometheus + Grafana的全面监控体系
- **容器化部署**：Docker + Nginx的生产级部署方案

### 10.3 可扩展性设计
- **插件架构**：模块化设计支持功能扩展
- **微服务就绪**：组件独立，便于服务拆分
- **云原生支持**：容器化、配置外部化、无状态设计
- **监控完备**：全面的性能指标和告警机制

该设计为v2.1的实施提供了完整的技术蓝图，确保系统既满足当前的多代理、多站点需求，又具备未来扩展的灵活性。