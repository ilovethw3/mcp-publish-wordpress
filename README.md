# MCP WordPress Publisher Server v2.0

A [Model Context Protocol (MCP)](https://modelcontextprotocol.io) server for AI-driven WordPress content publishing workflow. This server provides Tools, Resources, and Prompts that enable AI clients to submit articles, manage review processes, and automatically publish content to WordPress sites.

## Features

- **MCP Protocol Compliant**: Full JSON-RPC 2.0 and MCP specification support
- **Multiple Transport**: Support for stdio and Server-Sent Events (SSE)
- **Article Management**: Submit, review, approve/reject articles via MCP Tools
- **WordPress Integration**: Automatic publishing to WordPress via REST API
- **Real-time Resources**: Access article data and system stats via MCP Resources
- **Content Templates**: AI-powered prompts for content creation
- **Async Architecture**: High-performance async/await implementation
- **Docker Ready**: Complete containerized deployment setup

## Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd mcp-publish-wordpress

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env
# Edit .env with your WordPress credentials
```

### 2. Database Setup

```bash
# Initialize Alembic (first time only)
alembic init alembic

# Create database migration
alembic revision --autogenerate -m "Initial migration"

# Apply migrations
alembic upgrade head
```

### 3. Create User Account

```bash
python create_user.py
```

### 4. Start the MCP Server

**Stdio Mode (for development):**
```bash
python -m mcp_wordpress.server
```

**SSE Mode (for web integration):**
```bash
python -m mcp_wordpress.server sse
```

## Docker Deployment

### Development Setup
```bash
docker-compose up postgres
python -m mcp_wordpress.server
```

### Production Setup (SSE)
```bash
docker-compose --profile sse up
```

### Stdio Mode
```bash
docker-compose up mcp-server
```

## MCP Client Usage

### Connecting via MCP Client

**Stdio Transport:**
```python
from mcp import StdioClient

async with StdioClient(
    command="python",
    args=["-m", "mcp_wordpress.server"]
) as client:
    # Use MCP client to interact with server
    tools = await client.list_tools()
    print(f"Available tools: {[tool.name for tool in tools]}")
```

**SSE Transport:**
```python
from mcp import SSEClient

# Default SSE path is /sse (configurable via MCP_SSE_PATH)
async with SSEClient("http://localhost:8000/sse") as client:
    # Use MCP client to interact with server
    resources = await client.list_resources()
    print(f"Available resources: {[resource.uri for resource in resources]}")
```

## Available MCP Tools

### Article Management
- `submit_article` - Submit new article for review
- `list_articles` - List articles with filtering
- `get_article_status` - Get detailed article status
- `approve_article` - Approve and publish article
- `reject_article` - Reject article with reason

### Example Tool Usage
```python
# Submit an article
result = await client.call_tool("submit_article", {
    "title": "My Great Article",
    "content_markdown": "# Introduction\nThis is my article content...",
    "tags": "wordpress, mcp, ai",
    "category": "Technology"
})

# List pending articles
articles = await client.call_tool("list_articles", {
    "status": "pending_review",
    "limit": 10
})

# Approve an article
approval = await client.call_tool("approve_article", {
    "article_id": 1,
    "reviewer_notes": "Looks great, ready to publish!"
})
```

## Available MCP Resources

### Article Data
- `article://pending` - List of articles pending review
- `article://published` - List of published articles  
- `article://failed` - List of failed publications
- `article://{id}` - Complete article data by ID

### System Status
- `wordpress://config` - WordPress configuration and connection status
- `stats://summary` - Article count statistics by status
- `stats://performance` - Publishing performance metrics

### Example Resource Usage
```python
# Get pending articles
pending = await client.read_resource("article://pending")
print(pending.contents[0].text)

# Get article details
article = await client.read_resource("article://123")
print(article.contents[0].text)

# Get system stats
stats = await client.read_resource("stats://summary")
print(stats.contents[0].text)
```

## Available MCP Prompts

### Content Creation
- `article_template` - Generate article template with best practices
- `review_checklist` - Generate review checklist for content quality
- `wordpress_formatting` - WordPress formatting guide and best practices

### Example Prompt Usage
```python
# Get article template
template = await client.get_prompt("article_template", {
    "topic": "AI and Machine Learning",
    "target_audience": "developers"
})
print(template.messages[0].content.text)

# Get review checklist
checklist = await client.get_prompt("review_checklist", {
    "content_type": "tutorial"
})
print(checklist.messages[0].content.text)
```

## Configuration

### Environment Variables

```bash
# MCP Server Configuration
MCP_SERVER_NAME=wordpress-publisher
MCP_TRANSPORT=stdio  # or sse
MCP_PORT=8000
MCP_SSE_PATH=/sse  # SSE endpoint path (without trailing slash to avoid redirects)

# Database Configuration  
DATABASE_URL=postgresql://user:pass@localhost:5432/mcpdb

# WordPress Integration
WORDPRESS_API_URL=https://your-site.com/wp-json/wp/v2
WORDPRESS_USERNAME=your-username
WORDPRESS_APP_PASSWORD=your-app-password

# Security Configuration
SECRET_KEY=your-secret-key
AGENT_API_KEY=your-agent-api-key

# Optional Configuration
DEBUG=false
LOG_LEVEL=INFO
```

### WordPress Setup

1. **Create Application Password:**
   - Go to WordPress Admin → Users → Your Profile
   - Scroll to "Application Passwords"
   - Create new application password for MCP server

2. **Enable REST API:**
   - Ensure WordPress REST API is enabled
   - Test API access: `https://your-site.com/wp-json/wp/v2/posts`

## Testing

```bash
# Run all tests
python run_tests.py

# Run specific test category
pytest mcp_wordpress/tests/ -m unit
pytest mcp_wordpress/tests/ -m integration

# Run with coverage
pytest mcp_wordpress/tests/ --cov=mcp_wordpress
```

## Development

### Project Structure
```
mcp-publish-wordpress/
├── mcp_wordpress/           # Main package
│   ├── tools/              # MCP Tools implementation
│   ├── resources/          # MCP Resources implementation  
│   ├── prompts/           # MCP Prompts implementation
│   ├── models/            # Database models
│   ├── core/              # Core services (config, database, wordpress)
│   └── tests/             # Test suite
├── alembic/               # Database migrations
├── docs/                  # Project documentation
├── docker-compose.yml     # Docker deployment
├── Dockerfile            # Container configuration
└── requirements.txt      # Python dependencies
```

### Adding New Tools

```python
# In mcp_wordpress/tools/your_module.py
from fastmcp import FastMCP

def register_your_tools(mcp: FastMCP):
    @mcp.tool()
    async def your_tool(param: str) -> str:
        """Your tool description."""
        # Implementation here
        return "result"

# In mcp_wordpress/server.py
from mcp_wordpress.tools.your_module import register_your_tools

def create_mcp_server():
    mcp = FastMCP(...)
    register_your_tools(mcp)  # Add this line
    return mcp
```

## Troubleshooting

### Common Issues

1. **Database Connection Failed**
   - Verify DATABASE_URL is correct
   - Ensure PostgreSQL is running
   - Check network connectivity

2. **WordPress API Errors**
   - Verify WORDPRESS_API_URL is correct
   - Check application password is valid
   - Ensure WordPress REST API is enabled

3. **MCP Client Connection Issues**
   - Verify transport mode (stdio vs sse)
   - Check port availability for SSE mode
   - Ensure MCP client is compatible

### Logs and Debugging

```bash
# Enable debug mode
export DEBUG=true

# Check application logs
docker-compose logs mcp-server

# Test WordPress connection
python -c "
from mcp_wordpress.core.wordpress import WordPressClient
import asyncio
async def test():
    client = WordPressClient()
    result = await client.test_connection()
    print(f'WordPress connection: {result}')
asyncio.run(test())
"
```

## API Reference

For detailed API documentation including all Tools, Resources, and Prompts schemas, see the [Design Document](docs/design.md).

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

## License

This project is licensed under the MIT License.