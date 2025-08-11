# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server for WordPress content publishing. The system enables AI agents to submit articles for human review and automatic WordPress publishing through a complete async workflow.

**Current Version**: v2.1 featuring multi-agent API key authentication, multi-WordPress site support, and a Next.js web management interface for personal use scenarios.

## Key Commands

### Virtual Environment
```bash
# Always activate the virtual environment first
source venv_mcp_publish_wordpress/bin/activate
```

### Development Server
```bash
# Start MCP server in stdio mode (for development/testing)
python -m mcp_wordpress.server

# Start MCP server in SSE mode (for web/HTTP integration)
python -m mcp_wordpress.server sse
```

### Web UI Development
```bash
# Navigate to web UI directory
cd web-ui

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Type checking
npm run type-check

# Linting
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

# Test MCP server functionality
python test_sse_client.py         # Full interface test
python test_connection.py         # Connection test
```

### Database Management
```bash
# Create migration after model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Create user account for testing
python create_user.py
```

### Docker Operations
```bash
# Development with local database
docker-compose up postgres redis

# Full production deployment with web UI
./deploy.sh -e production -b up

# SSE deployment only
docker-compose up mcp-server postgres redis

# Development with monitoring
./deploy.sh -e development --monitoring up
```

## Architecture Overview

### V2.1 Multi-Tier Architecture
The system consists of three main tiers:
- **Backend MCP Server**: FastMCP-based server with multi-agent/multi-site support
- **Web Management Interface**: Next.js 14 application for configuration and monitoring
- **Supporting Services**: PostgreSQL, Redis, monitoring (Prometheus/Grafana)

### MCP Protocol Implementation
The server implements the complete MCP specification with three primary components:
- **Tools**: Interactive functions AI can invoke (article management, approval workflows, multi-agent operations)
- **Resources**: Read-only data endpoints (article feeds, statistics, agent/site configuration)
- **Prompts**: Template generation for content creation and review

### Core Architecture Patterns

**FastMCP Server Registration Pattern:**
```python
# In mcp_wordpress/server.py
def create_mcp_server() -> FastMCP:
    mcp = FastMCP(name=settings.mcp_server_name, version="2.1.0")
    register_article_tools(mcp)      # Article management tools
    register_agent_tools(mcp)        # Multi-agent management
    register_site_tools(mcp)         # Multi-site management
    register_article_resources(mcp)  # Data resources
    register_content_prompts(mcp)    # Content templates
    return mcp
```

**Multi-Agent Authentication Pattern:**
```python
# In mcp_wordpress/auth/providers.py
class MultiAgentAuthProvider(BearerAuthProvider):
    async def validate_token(self, token: str) -> Optional[AccessToken]:
        agent_id = self.config_manager.validate_api_key(token)
        if agent_id:
            return AccessToken(subject=agent_id, scopes=["article:submit"])
```

**Async Database Session Pattern:**
```python
# Always use this pattern for database operations
async with get_session() as session:
    # Use session.execute() for queries (not session.exec())
    result = await session.execute(select(Article))
    articles = result.scalars().all()  # Use .scalars() for ORM objects
    # Use result.scalar() for aggregate functions
    count = result.scalar()
```

**MCP Error Handling Pattern:**
```python
# All tools must return JSON strings and handle errors
try:
    # Business logic here
    return create_mcp_success({"result": data})
except (ValidationError, ArticleNotFoundError) as e:
    return e.to_json()  # Custom exceptions with MCP format
except Exception as e:
    error = MCPError(MCPErrorCodes.INTERNAL_ERROR, str(e))
    return error.to_json()
```

**Web UI Configuration Management Pattern:**
```typescript
// In web-ui/src/hooks/useConfigManagement.ts
export function useAgentConfig() {
    const { data, mutate } = useSWR('/api/config/agents');
    const createAgent = useCallback(async (agentData) => {
        const response = await fetch('/api/config/agents', {
            method: 'POST',
            body: JSON.stringify(agentData)
        });
        mutate(); // Refresh data
    });
}
```

### Key Backend Modules
- `mcp_wordpress/server.py` - Main MCP server with transport handling (stdio/SSE)
- `mcp_wordpress/tools/articles.py` - Article management tools with async database operations
- `mcp_wordpress/tools/agents.py` - Multi-agent management tools
- `mcp_wordpress/tools/sites.py` - Multi-site management tools
- `mcp_wordpress/auth/` - Multi-agent authentication system
- `mcp_wordpress/config/` - Agent and site configuration managers
- `mcp_wordpress/core/multi_site_publisher.py` - Multi-site publishing engine
- `mcp_wordpress/models/` - SQLModel with timezone handling and v2.1 extensions

### Key Frontend Modules
- `web-ui/src/app/` - Next.js 14 App Router pages
- `web-ui/src/components/` - Reusable UI components
- `web-ui/src/hooks/` - Custom hooks for data fetching and configuration management
- `web-ui/src/app/api/` - Next.js API Routes for configuration management
- `web-ui/src/types/` - TypeScript type definitions

## Database & ORM Critical Notes

### AsyncSession Usage
- **NEVER use `session.exec()`** - Use `session.execute()` instead
- **Always use `.scalars()`** for ORM object queries: `result.scalars().all()`, `result.scalars().first()`
- **Use `.scalar()`** for aggregate functions: `result.scalar()` 
- **DateTime handling**: Models use `datetime.now(timezone.utc)` defaults - don't override in tools

### Model Timezone Handling
```python
# Article model uses timezone-aware defaults
created_at: datetime = Field(
    default_factory=lambda: datetime.now(timezone.utc),
    sa_column=Column(DateTime(timezone=True), server_default=func.now())
)
# Don't manually set timestamps in tools - let model defaults handle it
```

### V2.1 Model Extensions
```python
# Article model v2.1 additions
agent_id: Optional[str] = Field(default=None, description="Submitting agent identifier")
target_site: Optional[str] = Field(default=None, description="Target WordPress site")

# New Site model for multi-site support
class Site(SQLModel, table=True):
    id: str = Field(primary_key=True)
    name: str
    wordpress_config: dict  # WordPress API configuration
    publishing_rules: dict  # Site-specific publishing rules
```

## Testing Architecture

### Test Categories (pytest markers)
- `@pytest.mark.unit` - Unit tests with mocked dependencies
- `@pytest.mark.integration` - Integration tests with real MCP protocol
- `@pytest.mark.slow` - Performance/load tests

### Mock Database Pattern for Tests
```python
# Always use this pattern when mocking database in tests
mock_result = AsyncMock()
mock_scalars = AsyncMock()
mock_scalars.all = lambda: mock_data  # Not async
mock_scalars.first = lambda: mock_item  # Not async
mock_result.scalars = lambda: mock_scalars
mock_result.scalar = lambda: 5  # For count queries
mock_db_session.execute = AsyncMock(return_value=mock_result)
```

## Configuration Management

### YAML Configuration Files
V2.1 uses YAML files for multi-agent and multi-site configuration:
- `config/agents.yml` - Agent definitions with API keys and permissions
- `config/sites.yml` - WordPress site configurations and publishing rules

### Web UI Configuration API Pattern
```typescript
// Configuration API Routes pattern
// web-ui/src/app/api/config/agents/route.ts
export async function POST(request: NextRequest) {
    const body = await request.json();
    // Validate agent data
    const errors = validateAgent(body);
    if (errors.length > 0) {
        return NextResponse.json({ success: false, errors });
    }
    // Update YAML file and return success
}
```

### Dynamic Configuration Management
The web UI provides full CRUD operations for agents and sites:
- **Empty defaults**: Configuration files start empty, managed via web interface
- **Real-time updates**: Changes immediately reflected in both UI and MCP server
- **Validation**: Comprehensive form validation and error handling
- **Testing integration**: Connection testing for WordPress sites during configuration

## MCP Transport Configuration

### SSE Mode (Web/HTTP Integration)
- Server runs on configurable SSE path (default: `http://0.0.0.0:8000/sse`)
- Use `await mcp.run_sse_async(host="0.0.0.0", port=settings.mcp_port, path=settings.mcp_sse_path)`
- Client connects via `sse_client(f"http://localhost:{settings.mcp_port}{settings.mcp_sse_path}")`
- SSE path configured via `MCP_SSE_PATH` environment variable (default: `/sse`)

### Stdio Mode (Direct Integration) 
- Server runs via `await mcp.run_stdio_async()`
- Client connects via `stdio_client(server_params)` with command args

## WordPress Integration Requirements

### Authentication Setup
1. WordPress Application Password (not regular password)
2. REST API must be enabled at `/wp-json/wp/v2/`
3. User needs `publish_posts` capability
4. HTTPS recommended for production

### Multi-Site API Pattern
```python
# Multi-site WordPress client pattern
site_config = self.site_manager.get_site(site_id)
wp_client = WordPressClient(site_config.wordpress_config)
try:
    result = await wp_client.create_post(title, content_markdown, tags, category)
    # Returns {"id": post_id, "link": permalink}
except Exception as e:
    # Log error, update article status to PUBLISH_FAILED
    article.publish_error_message = str(e)
```

## Environment Configuration

### Required Backend Variables
```bash
# Database Configuration
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mcpdb_v21
REDIS_URL=redis://:password@localhost:6379/0

# MCP Server Configuration
MCP_TRANSPORT=sse  # or stdio
MCP_PORT=8000
MCP_SSE_PATH=/sse
MCP_SERVER_NAME="MCP WordPress Publisher v2.1"

# Security Configuration
SECRET_KEY=jwt-secret-key
JWT_SECRET_KEY=jwt-secret
ENCRYPTION_KEY=encryption-key

# Multi-Agent/Site Configuration
AGENT_CONFIG_PATH=/app/config/agents.yml
SITE_CONFIG_PATH=/app/config/sites.yml
MULTI_AGENT_MODE=true
MULTI_SITE_MODE=true

# Feature Flags
DEBUG=false
ENABLE_RATE_LIMITING=true
ENABLE_API_VERSIONING=true
ENABLE_AUDIT_LOGGING=true
ENABLE_METRICS=true
```

### Web UI Environment Variables
```bash
# Next.js Configuration
NEXT_PUBLIC_MCP_SERVER_URL=http://localhost:8000
NEXT_PUBLIC_MCP_SSE_PATH=/sse
NEXTAUTH_SECRET=your-nextauth-secret
NEXTAUTH_URL=http://localhost:3000

# Feature Flags
NEXT_PUBLIC_ENABLE_REALTIME=true
NEXT_PUBLIC_POLLING_INTERVAL=30000
```

## Development Patterns

### Adding New MCP Tools
1. Create async function with proper type hints
2. Use `@mcp.tool()` decorator with description
3. Implement comprehensive input validation
4. Use async database session pattern
5. Return JSON strings via `create_mcp_success()` or error `.to_json()`
6. Add corresponding unit tests with proper mocks

### Adding Web UI Components
1. Follow Next.js 14 App Router patterns
2. Use TypeScript for all components
3. Implement proper error boundaries and loading states
4. Use SWR for data fetching with proper cache management
5. Follow Tailwind CSS utility-first approach
6. Implement accessibility standards

### Adding Configuration API Routes
1. Create API route in `web-ui/src/app/api/` following REST conventions
2. Implement comprehensive input validation
3. Handle YAML file operations safely
4. Return consistent API response format
5. Include error handling and logging
6. Test with both valid and invalid inputs

## Performance & Security Notes

### Database Connection Pooling
- AsyncSession uses connection pooling (pool_size=20, max_overflow=30)
- Always use async context managers for sessions
- Implement proper connection cleanup in error cases

### Security Considerations
- Never log WordPress credentials or API keys
- All user inputs are validated and sanitized (using bleach for content)
- Database queries use parameterized statements (SQLModel handles this)
- Implement rate limiting for production deployments
- Multi-agent API key authentication with JWT tokens
- Configuration file encryption for sensitive data

### Web UI Security
- Server-side validation for all configuration changes
- No sensitive data exposed to client-side JavaScript
- CSRF protection via Next.js built-in mechanisms
- Input sanitization for all form data

## Deployment Architecture

### Production Deployment
```bash
# Full production deployment with monitoring
./deploy.sh -e production -b -m --backup up

# Parameters:
# -e: environment (development, testing, production)
# -b: build images from scratch
# -m: enable monitoring (Prometheus/Grafana)
# --backup: create backup before deployment
```

### Service Architecture
- **mcp-server**: Main MCP server (FastMCP + Python)
- **web-ui**: Management interface (Next.js 14)
- **postgres**: Database with v2.1 schema
- **redis**: Session management and caching
- **prometheus**: Metrics collection
- **grafana**: Monitoring dashboards

### Health Checks and Monitoring
All services include comprehensive health checks and monitoring:
- HTTP health check endpoints
- Prometheus metrics integration
- Grafana dashboards for system observability
- Alert thresholds for failures and performance issues

## Common Development Issues

### Database Session Errors
- If seeing `'AsyncSession' object has no attribute 'exec'`: Use `.execute()` instead
- If seeing `'coroutine' object has no attribute 'all'`: Use `.scalars().all()` pattern
- If seeing timezone errors: Don't manually set timestamps, use model defaults

### MCP Protocol Errors  
- If tools return `None`: Ensure return JSON strings, not objects
- If SSE connection fails: Check server is using `run_sse_async()` not `run_http_async()`
- If stdio hangs: Verify client uses correct server command args

### Web UI Development Issues
- If API routes fail: Check CORS configuration and Next.js API route structure
- If configuration changes don't reflect: Ensure SWR cache invalidation
- If TypeScript errors: Check type definitions in `web-ui/src/types/`
- If build fails: Run `npm run type-check` to identify TypeScript issues

### WordPress API Issues
- Test connection independently: `python test_connection.py`
- Verify application password format (spaces, not hyphens)
- Check WordPress user permissions for post creation
- Ensure REST API is not disabled by security plugins
- For multi-site: Verify each site configuration independently

## Important Architectural Notes

### FastMCP Server Pattern
The server uses FastMCP's registration pattern extensively. All new functionality should follow:
1. Create module-specific registration functions (`register_*_tools`, `register_*_resources`)
2. Import and call registration functions in `create_mcp_server()` 
3. Use proper MCP decorators (`@mcp.tool()`, `@mcp.resource()`, `@mcp.prompt()`)
4. Return JSON strings from all MCP functions, never objects

### Multi-Agent Architecture Principles
- **Agent Equality**: All agents have same base permissions, roles handled at agent level
- **Configuration-Driven**: Use YAML files for complex multi-entity management
- **Backward Compatibility**: Support existing single-agent configurations
- **Failure Isolation**: Agent failures should not affect other agents

### Multi-Site Architecture Principles
- **Site Isolation**: Failure in one WordPress site should not affect others
- **Load Balancing**: Support priority-based and round-robin distribution
- **Health Monitoring**: Continuous monitoring of site availability and performance
- **Failover Support**: Automatic failover to alternative sites when configured

### Web UI Architecture Principles
- **Server-Side Configuration**: All configuration managed server-side via API routes
- **Real-Time Updates**: Changes reflected immediately across UI and backend
- **Progressive Enhancement**: Core functionality works without JavaScript
- **Component Reusability**: Shared components for consistent UX across pages

### Error Handling Philosophy
- Custom exceptions extend `MCPError` base class
- All exceptions must implement `.to_json()` for MCP compliance
- Use specific error codes: -40001 (not found), -32603 (internal error)
- Never expose sensitive data (passwords, API keys) in error messages
- Web UI provides user-friendly error messages with technical details in logs

### Testing Strategy
- Use pytest markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.slow`
- Mock database using the established AsyncMock pattern
- Integration tests should use real MCP protocol communication
- Test files in `mcp_wordpress/tests/` follow naming convention `test_*.py`
- Web UI testing focuses on API route functionality and component behavior