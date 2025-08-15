# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server for WordPress content publishing that enables AI agents to submit articles for human review and automatic WordPress publishing. The system consists of two main services: an MCP server for AI agent interactions and a Next.js Web UI for human management.

**Current Version**: v2.1 with multi-agent authentication, multi-site support, and database-backed configuration.

## Key Commands

### Virtual Environment
```bash
# Always activate the virtual environment first
source venv_mcp_publish_wordpress/bin/activate
```

### MCP Server Development
```bash
# Start MCP server in stdio mode (for direct AI client integration)
python -m mcp_wordpress.server

# Start MCP server in SSE mode (for web/HTTP integration)
python -m mcp_wordpress.server sse
```

### Web UI Development
```bash
cd web-ui

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Type checking and linting
npm run type-check
npm run lint
```

### Testing
```bash
# Run complete test suite
python run_tests.py

# Run specific test categories
pytest mcp_wordpress/tests/ -m unit
pytest mcp_wordpress/tests/ -m integration

# Run individual test files
pytest mcp_wordpress/tests/test_mcp_protocol.py -v

# Test MCP server connectivity
python test_sse_client.py
python test_connection.py
```

### Database Management
```bash
# Create migration after model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Initialize production database (handles all scenarios)
python init_production_db.py --help

# Database initialization options:
python init_production_db.py                # Safe initialization
python init_production_db.py --force-clean  # Complete rebuild (handles missing DB)
python init_production_db.py --clean-data   # Clear data, keep schema
```

### Docker Operations
```bash
# Development with local database
docker-compose up postgres redis

# Full production deployment
./deploy.sh -e production -b up

# Development with monitoring
./deploy.sh -e development --monitoring up
```

## Architecture Overview

### Core Design Principle
The system follows a **dual-service architecture** with clear separation of concerns:

- **MCP Server**: Handles AI agent interactions via MCP protocol (Tools, Resources, Prompts)
- **Web UI**: Provides human management interface with direct database access

### Current Architecture Status
✅ **Clean Separation Achieved**: Configuration management has been moved to Web UI. The MCP server now focuses solely on MCP protocol implementation while Web UI handles human management interface.

### Intended Clean Architecture
```
AI Agents ↔ MCP Server (FastMCP) ↔ Database ↔ Web UI (Next.js) ↔ Humans
                                     ↕
                               Shared Models
```

### Core Components

**MCP Server** (`mcp_wordpress/`):
- `server.py` - Main FastMCP server with stdio/SSE transport
- `tools/articles.py` - Article submission, approval, publishing tools
- `resources/articles.py` - Article data and statistics resources  
- `prompts/templates.py` - Content generation templates
- `auth/providers.py` - Multi-agent Bearer Token authentication

**Web UI** (`web-ui/src/`):
- `app/` - Next.js 14 App Router pages
- `app/api/` - API routes for configuration management
- `components/` - UI components for agents, sites, articles
- `hooks/` - Data fetching and state management

**Shared Infrastructure**:
- `models/` - SQLModel definitions (Agent, Site, Article)
- `services/config_service.py` - Database operations service
- `core/database.py` - Database connection and session management

## Critical Architecture Patterns

### Database Session Pattern
```python
# ALWAYS use this pattern for database operations
async with get_session() as session:
    # Use session.execute() for queries (NOT session.exec())
    result = await session.execute(select(Article))
    articles = result.scalars().all()  # Use .scalars() for ORM objects
    count = result.scalar()  # Use .scalar() for aggregate functions
```

### MCP Tool Registration Pattern
```python
def register_article_tools(mcp: FastMCP):
    @mcp.tool()
    async def submit_article(title: str, content: str, category: str = None):
        try:
            # Business logic here
            return create_mcp_success({"article_id": article.id})
        except ValidationError as e:
            return e.to_json()
```

### FastMCP Server Creation Pattern
```python
async def create_mcp_server() -> FastMCP:
    mcp = FastMCP(name=settings.mcp_server_name, version="2.1.0", auth=auth_provider)
    register_article_tools(mcp)      # Core article management
    register_article_resources(mcp)  # Data access
    register_content_prompts(mcp)    # AI templates
    return mcp
```

### Web UI Database Integration Pattern
```typescript
// Direct database access in API routes (NOT proxying to MCP server)
import { config_service } from '@/lib/database';

export async function POST(request: NextRequest) {
    const body = await request.json();
    const agent = await config_service.create_agent(body);
    return NextResponse.json({ success: true, data: agent });
}
```

## Database & Models

### Model Structure
- **Agent**: Multi-agent authentication with rate limiting and permissions
- **Site**: Multi-WordPress site configuration with publishing rules
- **Article**: Content workflow with status tracking and multi-site targeting

### Critical ORM Usage
- **NEVER use `session.exec()`** - Use `session.execute()` instead
- **Always use `.scalars().all()`** for object queries and `.scalar()` for aggregates
- **Timezone handling**: Models use UTC defaults - don't override in tools
- **Database Initialization**: Use `python init_production_db.py --force-clean` for complete rebuilds

### V2.1 Multi-Agent Extensions
```python
# Agent model supports full configuration in JSON fields
class Agent(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    rate_limit: dict = Field(sa_column=Column(JSON))
    permissions: dict = Field(sa_column=Column(JSON))
    notifications: dict = Field(sa_column=Column(JSON))
```

## Testing Strategy

### Test Categories
- `@pytest.mark.unit` - Unit tests with mocked dependencies
- `@pytest.mark.integration` - Full MCP protocol integration tests
- `@pytest.mark.slow` - Performance and load tests

### Mock Database Pattern
```python
# Standard pattern for mocking async database operations
mock_result = AsyncMock()
mock_scalars = AsyncMock()
mock_scalars.all = lambda: mock_data  # Synchronous lambda
mock_result.scalars = lambda: mock_scalars
mock_db_session.execute = AsyncMock(return_value=mock_result)
```

## Environment Configuration

### Required Backend Variables
```bash
# Database and Cache
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mcpdb_v21
REDIS_URL=redis://localhost:6379/0

# MCP Server
MCP_TRANSPORT=sse  # or stdio
MCP_PORT=8000
MCP_SSE_PATH=/sse

# Note: Multi-agent and multi-site features are now database-driven
# No longer require MULTI_AGENT_MODE or MULTI_SITE_MODE environment variables
```

### Web UI Variables
```bash
# Next.js Configuration (web-ui/.env.local)
NEXT_PUBLIC_MCP_SERVER_URL=http://localhost:8000
NEXT_PUBLIC_MCP_SSE_PATH=/sse

# Auto-generated during database initialization
WEB_UI_AGENT_API_KEY=webui_[generated_key]
```

## WordPress Integration

### Authentication Requirements
1. WordPress Application Password (not regular password)
2. REST API enabled at `/wp-json/wp/v2/`
3. User with `publish_posts` capability
4. HTTPS recommended for production

### Multi-Site Pattern
```python
# Multi-site publishing with error handling
site_config = self.site_manager.get_site(site_id)
wp_client = WordPressClient(site_config.wordpress_config)
try:
    result = await wp_client.create_post(title, content, tags, category)
except Exception as e:
    article.publish_error_message = str(e)
    article.status = ArticleStatus.PUBLISH_FAILED
```

## Development Patterns

### Adding New MCP Tools
1. Create async function with proper type hints
2. Use `@mcp.tool()` decorator with clear description
3. Implement input validation and error handling
4. Use async database session pattern
5. Return JSON strings via `create_mcp_success()` or `.to_json()`

### Adding Web UI Features
1. Create API routes in `web-ui/src/app/api/` with direct database access
2. Use TypeScript throughout with proper type definitions
3. Implement SWR for data fetching with cache management
4. Follow Tailwind CSS utility-first styling

### Database Model Changes
1. Update SQLModel definitions in `mcp_wordpress/models/`
2. Create Alembic migration: `alembic revision --autogenerate -m "Description"`
3. Apply migration: `alembic upgrade head`
4. Update both MCP server and Web UI to use new schema
5. For major schema changes, use `python init_production_db.py --force-clean` to rebuild

## Common Issues & Solutions

### Database Session Errors
- `'AsyncSession' object has no attribute 'exec'` → Use `.execute()` instead
- `'coroutine' object has no attribute 'all'` → Use `.scalars().all()` pattern
- Timezone errors → Don't manually set timestamps, use model defaults
- Database doesn't exist → Use `python init_production_db.py --force-clean`
- Schema out of sync → Run `alembic upgrade head` or use `--force-clean` for major changes

### MCP Protocol Issues
- Tools returning `None` → Ensure JSON string returns, not objects
- SSE connection failures → Check server uses `run_sse_async()` with correct path
- Authentication failures → Verify Bearer Token format and database agent records

### Web UI Development Issues
- API route failures → Check Next.js API route structure and error handling
- TypeScript errors → Run `npm run type-check` for detailed diagnostics
- Configuration not updating → Ensure database operations complete successfully

### WordPress Integration Issues
- Connection failures → Test with `python test_connection.py`
- Authentication errors → Verify Application Password format (spaces, not hyphens)
- Publishing failures → Check user permissions and REST API availability

## Database Initialization System

### Intelligent Initialization
The `init_production_db.py` script provides robust database management with automatic recovery:

```bash
# Safe initialization - checks state and initializes if needed
python init_production_db.py

# Complete rebuild - handles any scenario including missing database
python init_production_db.py --force-clean

# Data reset only - preserves schema
python init_production_db.py --clean-data
```

### Auto-Recovery Features
- **Missing Database**: Automatically creates database if it doesn't exist
- **Schema Conflicts**: Handles Alembic version mismatches
- **Environment Setup**: Auto-generates Web UI API keys and writes to `.env.local`
- **System Agents**: Creates required internal agents for Web UI operations

### Production Deployment Pattern
1. Run `python init_production_db.py --force-clean` for clean deployment
2. Alembic manages all schema changes automatically
3. Web UI Agent is created with proper permissions for article management
4. All environment files are updated automatically

## UI/UX Architecture

### Toast Notification System
The Web UI uses a global toast notification system for user feedback:

```typescript
// Global ToastProvider in app/layout.tsx provides toast functionality
import { useToastContext } from '@/contexts/ToastContext';

const { showSuccess, showError, showWarning, showInfo } = useToastContext();

// Enhanced success messages with action buttons
showSuccess(message, { 
  duration: 8000,
  action: {
    label: '查看文章',
    onClick: () => window.open(permalink, '_blank')
  }
});
```

**Key Features**:
- SSR-compatible with no-op fallback during build time
- Fixed positioning in top-right corner for consistent UX
- Support for action buttons (e.g., "View Article" links)
- Automatic duration management by message type
- Multi-line content support with proper formatting

### Site Selection Workflow Pattern
**v2.1 New Feature**: Site selection moved from article submission to approval phase:

```python
# Article submission (AI agents) - NO site specification required
submit_article(title, content, tags, category)  # target_site_id = null

# Article approval (humans) - REQUIRES site selection
approve_article(article_id, target_site_id, reviewer_notes)

# Retry publishing - CAN change target site
retry_publish_article(article_id, target_site_id, reviewer_notes)
```

**Web UI Implementation**:
- Approval dialog includes site selection dropdown
- Sites fetched from `/api/config/sites` (active sites only)
- Validation ensures site selection before approval
- Retry functionality allows switching to different sites

### React Component Patterns

**Modal Dialog Pattern**:
```typescript
// Standard modal structure for consistent UX
<div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
  <div className="bg-white p-6 rounded-lg max-w-md w-full mx-4">
    <h3 className="text-lg font-semibold mb-4">Dialog Title</h3>
    {/* Content with proper spacing and validation */}
    <div className="flex space-x-3 justify-end">
      <Button variant="outline" onClick={onCancel}>取消</Button>
      <Button variant="primary" onClick={onConfirm}>确认</Button>
    </div>
  </div>
</div>
```

**Data Fetching Pattern**:
```typescript
// Use SWR for cache management and real-time updates
const { articles, refresh } = useArticles({
  status: selectedStatus,
  search: searchTerm,
  agent_id: selectedAgent,
  limit: 50
});

// Direct database access in API routes (NOT MCP proxy)
export async function GET() {
  const sites = await getAllSites();
  return NextResponse.json({ success: true, data: { sites } });
}
```

## Critical Development Guidelines

### Article Status Workflow
```
pending_review → [Approval with Site Selection] → publishing → published
               ↘ [Rejection] → rejected
publishing → [Failure] → publish_failed → [Retry with Site Selection]
```

### Database Model Relationships
- **Articles**: `target_site_id` is null during submission, set during approval
- **Agents**: String IDs with JSON configuration for rate limits and permissions  
- **Sites**: String IDs with embedded WordPress configuration and publishing rules
- **Multi-site Support**: Articles can be retried to different sites if publishing fails

### Error Handling Patterns
```python
# MCP Tools must return JSON strings, never raise exceptions to clients
try:
    # Business logic
    return create_mcp_success(result_data)
except ValidationError as e:
    return e.to_json()  # Structured error response
except Exception as e:
    error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
    return error.to_json()
```

```typescript
// Web UI error handling with toast notifications
try {
  const result = await apiCall();
  if (result.success) {
    showSuccess('操作成功！');
  } else {
    throw new Error(result.error);
  }
} catch (error) {
  showError(`操作失败: ${error.message}`);
}
```

### TypeScript Integration Patterns
- **Strict typing**: All API responses use typed interfaces
- **SSR compatibility**: Components handle server/client rendering differences
- **Context providers**: Global state management for toasts, authentication
- **Hook patterns**: Custom hooks for data fetching, state management, and UI interactions