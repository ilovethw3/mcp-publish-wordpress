# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Model Context Protocol) server for WordPress content publishing. The system enables AI agents to submit articles for human review and automatic WordPress publishing through a complete async workflow.

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
docker-compose up postgres

# Full SSE deployment
docker-compose --profile sse up --build

# Full stdio deployment  
docker-compose up --build
```

## Architecture Overview

### MCP Protocol Implementation
The server implements the complete MCP specification with three primary components:
- **Tools**: Interactive functions AI can invoke (article management, approval workflows)
- **Resources**: Read-only data endpoints (article feeds, statistics, configuration)
- **Prompts**: Template generation for content creation and review

### Core Architecture Patterns

**FastMCP Server Registration Pattern:**
```python
# In mcp_wordpress/server.py
def create_mcp_server() -> FastMCP:
    mcp = FastMCP(name=settings.mcp_server_name, version="2.0.0")
    register_article_tools(mcp)      # Tools registration
    register_article_resources(mcp)  # Resources registration  
    register_content_prompts(mcp)    # Prompts registration
    return mcp
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

### Key Modules
- `mcp_wordpress/server.py` - Main MCP server with transport handling (stdio/SSE)
- `mcp_wordpress/tools/articles.py` - All article management tools with async database operations
- `mcp_wordpress/resources/articles.py` - Article data resources (pending, published, failed)
- `mcp_wordpress/resources/stats.py` - System statistics and WordPress configuration
- `mcp_wordpress/core/wordpress.py` - WordPress REST API client with async HTTP
- `mcp_wordpress/core/database.py` - AsyncSession management and connection pooling
- `mcp_wordpress/models/article.py` - SQLModel with proper timezone handling

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

### API Error Handling
```python
# WordPress client pattern
wp_client = WordPressClient()
try:
    result = await wp_client.create_post(title, content_markdown, tags, category)
    # Returns {"id": post_id, "link": permalink}
except Exception as e:
    # Log error, update article status to PUBLISH_FAILED
    article.publish_error_message = str(e)
```

## Environment Configuration

### Required Variables
```bash
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/mcpdb  # Note: +asyncpg for async
WORDPRESS_API_URL=https://site.com/wp-json/wp/v2
WORDPRESS_USERNAME=username
WORDPRESS_APP_PASSWORD=xxxx xxxx xxxx xxxx  # Application password format
SECRET_KEY=jwt-secret-key
AGENT_API_KEY=api-key-for-agents
MCP_TRANSPORT=sse  # or stdio
MCP_PORT=8000
MCP_SSE_PATH=/sse  # SSE endpoint path (without trailing slash to avoid redirects)
```

## Development Patterns

### Adding New MCP Tools
1. Create async function with proper type hints
2. Use `@mcp.tool()` decorator with description
3. Implement comprehensive input validation
4. Use async database session pattern
5. Return JSON strings via `create_mcp_success()` or error `.to_json()`
6. Add corresponding unit tests with proper mocks

### Adding New MCP Resources  
1. Use `@mcp.resource("uri://path")` decorator
2. Return JSON strings with timestamp metadata
3. Handle both single items and collections
4. Add to registration function in module

### Error Handling Strategy
- Custom exception classes extend `MCPError` base class
- All exceptions implement `.to_json()` for MCP-compliant responses  
- Tools catch specific exceptions first, then general Exception
- Use proper JSON-RPC 2.0 error codes (-40001 for not found, -32603 for internal)

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

## Common Development Issues

### Database Session Errors
- If seeing `'AsyncSession' object has no attribute 'exec'`: Use `.execute()` instead
- If seeing `'coroutine' object has no attribute 'all'`: Use `.scalars().all()` pattern
- If seeing timezone errors: Don't manually set timestamps, use model defaults

### MCP Protocol Errors  
- If tools return `None`: Ensure return JSON strings, not objects
- If SSE connection fails: Check server is using `run_sse_async()` not `run_http_async()`
- If stdio hangs: Verify client uses correct server command args

### WordPress API Issues
- Test connection independently: `python test_connection.py`
- Verify application password format (spaces, not hyphens)
- Check WordPress user permissions for post creation
- Ensure REST API is not disabled by security plugins