# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an MCP (Content Control Platform) - a WordPress publishing platform that receives AI-generated article drafts, provides human review capabilities, and publishes approved content to WordPress sites. The system consists of:

- **FastAPI Backend**: Handles article submission, review workflow, and WordPress publishing
- **Vue.js Frontend**: Dashboard for content reviewers to manage articles  
- **PostgreSQL Database**: Stores articles, users, and publication status
- **Docker Compose Deployment**: Containerized with Nginx reverse proxy

## Architecture

The system follows a three-tier architecture:
- **Frontend**: Vue.js SPA communicating via REST API
- **Backend**: FastAPI application with JWT authentication and WordPress integration
- **Database**: PostgreSQL with SQLModel for data modeling

Key workflow: External AI agents submit articles → Human reviewers approve/edit → Auto-publish to WordPress

## Development Commands

### Docker & Environment Setup
```bash
# Start development environment
docker-compose up -d

# Stop services
docker-compose down

# Rebuild services
docker-compose up --build
```

### Database Management
```bash
# Generate migration after model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check current migration status
alembic current
```

### Testing
```bash
# Run backend tests
pytest

# Run backend tests with coverage
pytest --cov=mcp

# Run frontend tests (when implemented)
npm test
```

## Project Structure

### Backend (`mcp/`)
```
mcp/
├── main.py             # FastAPI application entry point
├── api/v1/             # API routes
│   ├── articles.py     # Article management endpoints
│   └── auth.py         # Authentication endpoints
├── core/               # Core services
│   ├── config.py       # Environment configuration
│   ├── security.py     # JWT and password handling
│   └── wordpress_client.py # WordPress REST API client
├── models/             # SQLModel data models
│   ├── user.py         # User model
│   └── article.py      # Article model
└── db/                 # Database session management
    └── session.py
```

### Key Models
- **User**: Authentication (username, hashed_password, is_active)
- **Article**: Content workflow (title, content_markdown, content_html, status, tags, category, wordpress_post_id, wordpress_permalink, publish_error_message)

### Article Status Flow
`pending_review` → `publishing` → `published` | `publish_failed` | `rejected`

## API Authentication

- **JWT Authentication**: For frontend dashboard access
- **API Key Authentication**: For external AI agents submitting articles (X-API-Key header)

## Environment Variables

Required in `.env` file (see `.env.example`):
- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `AGENT_API_KEY`: API key for article submission
- `WORDPRESS_API_URL`: Target WordPress site API endpoint
- `WORDPRESS_USERNAME`: WordPress username
- `WORDPRESS_APP_PASSWORD`: WordPress application password
- `FRONTEND_CORS_ORIGINS`: Allowed origins for CORS

## WordPress Integration

The `WordPressClient` class handles:
- Tag and category ID resolution by name
- Post creation with proper field mapping
- Error handling for publication failures
- Permalink and post ID storage for traceability

## Testing Strategy

- **Backend**: Pytest with test database for integration tests, pytest-mock for WordPress API mocking
- **Frontend**: Component tests with Vitest/Jest, potential E2E testing with Cypress
- **Database**: Use test database with automatic rollback between tests

## Development Notes

- Use Alembic for all database schema changes
- CORS is configured for frontend development
- All API endpoints requiring authentication use JWT dependency injection
- WordPress publishing is asynchronous with status tracking
- Error messages from WordPress publishing failures are stored in database for user visibility

## Python Virtual Environment
```bash
# Activate virtual environment for local development
source venv_wordpress/bin/activate

# Install dependencies in virtual environment
pip install -r requirements.txt

# Install additional PostgreSQL driver if needed
pip install psycopg2-binary
```

## Deployment

### Initial Setup
```bash
# 1. Copy environment configuration
cp .env.example .env
# Edit .env with actual WordPress credentials

# 2. Start services
docker-compose up -d

# 3. Create admin user (requires virtual environment)
source venv_wordpress/bin/activate
python create_user.py admin your_password_here

# 4. Verify deployment
curl http://localhost/health
```

### Configuration Updates
After modifying `.env` file, restart FastAPI container:
```bash
docker-compose restart fastapi_app
```

### Common Troubleshooting

**psycopg2 Import Error**:
- Add `psycopg2-binary` to requirements.txt
- Rebuild container: `docker-compose up --build`

**WordPress 401 Unauthorized**:
- Verify WordPress application password format (contains spaces)
- Ensure WordPress user has admin privileges
- Test authentication manually: `curl -u username:password https://site.com/wp-json/wp/v2/users/me`

### Logs and Debugging
```bash
# View FastAPI application logs
docker-compose logs -f fastapi_app

# View all service logs
docker-compose logs

# Check container status
docker-compose ps
```

## API Usage Examples

### Authentication
```bash
# Login and get JWT token
curl -X POST "http://localhost/api/v1/auth/token" \
     -H "Content-Type: application/x-www-form-urlencoded" \
     -d "username=admin&password=your_password"

# Use token for authenticated requests
curl -X GET "http://localhost/api/v1/articles/" \
     -H "Authorization: Bearer YOUR_JWT_TOKEN"
```

### Article Management Workflow
```bash
# 1. Submit article (AI agent)
curl -X POST "http://localhost/api/v1/articles/submit" \
     -H "Content-Type: application/json" \
     -H "X-API-Key: your-agent-api-key" \
     -d '{"title":"Article Title","content_markdown":"# Content","tags":"tag1,tag2","category":"Category"}'

# 2. Review articles (human reviewer)
curl -X GET "http://localhost/api/v1/articles/?status=pending_review" \
     -H "Authorization: Bearer JWT_TOKEN"

# 3. Approve for publication
curl -X POST "http://localhost/api/v1/articles/{id}/approve" \
     -H "Authorization: Bearer JWT_TOKEN"

# 4. Check publication status (asynchronous)
curl -X GET "http://localhost/api/v1/articles/{id}" \
     -H "Authorization: Bearer JWT_TOKEN"
```

## WordPress Integration Details

The platform acts as a content pipeline, NOT a WordPress content manager:
- MCP database stores ALL submitted articles (pending, rejected, published)
- WordPress only receives APPROVED articles after human review
- `/api/v1/articles/` returns MCP platform articles, not WordPress posts
- WordPress articles accessible via WordPress REST API: `https://site.com/wp-json/wp/v2/posts`

### WordPress Publishing Process
1. Article approved → Status: `publishing`
2. Background task creates WordPress post
3. Success → Status: `published` + WordPress ID/permalink
4. Failure → Status: `publish_failed` + error message
5. Publishing is asynchronous - allow 5-10 seconds for completion

### WordPress Authentication Setup
1. WordPress admin → Users → Application Passwords
2. Generate new application password (format: "xxxx xxxx xxxx xxxx xxxx xxxx")
3. Configure in `.env`: `WORDPRESS_APP_PASSWORD="generated password with spaces"`
