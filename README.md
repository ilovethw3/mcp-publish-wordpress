# MCP - Content Control Platform

A FastAPI-based content management system that receives AI-generated article drafts, provides human review capabilities, and publishes approved content to WordPress sites.

## Features

- **Article Submission**: API endpoint for external AI agents to submit articles
- **Human Review**: Dashboard for content reviewers to manage articles
- **WordPress Integration**: Automatic publishing to WordPress sites
- **JWT Authentication**: Secure access control for reviewers
- **Status Tracking**: Complete workflow from submission to publication

## Quick Start

### 1. Environment Setup

Copy the environment template and configure your settings:

```bash
cp .env.example .env
```

Edit `.env` with your configuration:
- Database connection string
- WordPress API credentials
- JWT secret key
- Agent API key

### 2. Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 3. Create Initial User

```bash
# Create an admin user
python create_user.py admin your_password_here
```

### 4. Access the API

- API Documentation: http://localhost/docs
- Health Check: http://localhost/health
- API Base URL: http://localhost/api/v1

## API Endpoints

### Authentication
- `POST /api/v1/auth/token` - Login and get JWT token
- `GET /api/v1/auth/me` - Get current user info

### Articles
- `POST /api/v1/articles/submit` - Submit article (requires Agent API key)
- `GET /api/v1/articles/` - List articles with search/filter
- `GET /api/v1/articles/{id}` - Get article details
- `PUT /api/v1/articles/{id}` - Update article
- `POST /api/v1/articles/{id}/approve` - Approve and publish
- `POST /api/v1/articles/{id}/reject` - Reject article
- `POST /api/v1/articles/{id}/retry` - Retry failed publication

## Development

### Local Development Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Set up database:
```bash
alembic upgrade head
```

3. Run development server:
```bash
uvicorn mcp.main:app --reload --host 0.0.0.0 --port 8000
```

### Database Migrations

```bash
# Generate migration after model changes
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Check current version
alembic current
```

### Testing

```bash
# Run tests
pytest

# Run with coverage
pytest --cov=mcp
```

## Project Structure

```
mcp-publish-wordpress/
├── mcp/                    # Main application package
│   ├── api/v1/            # API routes
│   ├── core/              # Core services (security, config, wordpress)
│   ├── models/            # SQLModel data models
│   ├── db/                # Database session management
│   └── main.py            # FastAPI application
├── alembic/               # Database migrations
├── docker-compose.yml     # Docker services
├── Dockerfile             # Application container
├── requirements.txt       # Python dependencies
└── create_user.py         # User creation script
```

## Configuration

Key environment variables:

- `DATABASE_URL`: PostgreSQL connection string
- `SECRET_KEY`: JWT signing key
- `AGENT_API_KEY`: API key for article submission
- `WORDPRESS_API_URL`: WordPress REST API endpoint
- `WORDPRESS_USERNAME`: WordPress username
- `WORDPRESS_APP_PASSWORD`: WordPress application password
- `FRONTEND_CORS_ORIGINS`: Allowed CORS origins for frontend

## WordPress Setup

1. Install Application Passwords plugin (WordPress 5.6+)
2. Create application password for your user
3. Configure WordPress API URL and credentials in `.env`

## License

MIT License