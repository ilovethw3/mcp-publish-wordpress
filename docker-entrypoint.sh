#!/bin/bash
set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Logging function
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

# Wait for database to be ready
wait_for_db() {
    log "Waiting for database connection..."
    python -c "
import asyncio
import asyncpg
import os
import sys
from urllib.parse import urlparse

async def check_db():
    db_url = os.getenv('DATABASE_URL', '')
    if not db_url:
        print('DATABASE_URL not set')
        sys.exit(1)
    
    # Parse URL to get connection params
    parsed = urlparse(db_url.replace('postgresql+asyncpg://', 'postgresql://'))
    
    max_attempts = 30
    for attempt in range(max_attempts):
        try:
            conn = await asyncpg.connect(
                host=parsed.hostname or 'localhost',
                port=parsed.port or 5432,
                user=parsed.username,
                password=parsed.password,
                database=parsed.path.lstrip('/') if parsed.path else 'postgres'
            )
            await conn.close()
            print('Database is ready!')
            return
        except Exception as e:
            if attempt == max_attempts - 1:
                print(f'Failed to connect to database after {max_attempts} attempts: {e}')
                sys.exit(1)
            print(f'Attempt {attempt + 1}/{max_attempts}: Database not ready, waiting...')
            await asyncio.sleep(2)

asyncio.run(check_db())
"
}

# Wait for Redis to be ready
wait_for_redis() {
    if [ -n "$REDIS_URL" ]; then
        log "Waiting for Redis connection..."
        python -c "
import redis
import os
import sys
import time
from urllib.parse import urlparse

redis_url = os.getenv('REDIS_URL', '')
if not redis_url:
    print('Redis not configured, skipping...')
    sys.exit(0)

parsed = urlparse(redis_url)
max_attempts = 30

for attempt in range(max_attempts):
    try:
        r = redis.Redis.from_url(redis_url)
        r.ping()
        print('Redis is ready!')
        break
    except Exception as e:
        if attempt == max_attempts - 1:
            print(f'Failed to connect to Redis after {max_attempts} attempts: {e}')
            sys.exit(1)
        print(f'Attempt {attempt + 1}/{max_attempts}: Redis not ready, waiting...')
        time.sleep(2)
"
    fi
}

# Initialize configuration files from templates
init_config() {
    log "Initializing configuration files..."
    
    # Initialize agents.yml if not exists
    if [ ! -f "/app/config/agents.yml" ] && [ -f "/app/config/agents.yml.template" ]; then
        log "Creating agents.yml from template..."
        envsubst < /app/config/agents.yml.template > /app/config/agents.yml
    fi
    
    # Initialize sites.yml if not exists
    if [ ! -f "/app/config/sites.yml" ] && [ -f "/app/config/sites.yml.template" ]; then
        log "Creating sites.yml from template..."
        envsubst < /app/config/sites.yml.template > /app/config/sites.yml
    fi
}

# Run database migrations
run_migrations() {
    log "Running database migrations..."
    if ! alembic upgrade head; then
        error "Database migration failed"
        exit 1
    fi
    log "Database migrations completed successfully"
}

# Validate environment configuration
validate_config() {
    log "Validating configuration..."
    
    # Check required environment variables
    required_vars=(
        "DATABASE_URL"
        "SECRET_KEY"
        "JWT_SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    # Validate multi-agent configuration if enabled
    if [ "$MULTI_AGENT_MODE" = "true" ]; then
        if [ ! -f "/app/config/agents.yml" ]; then
            error "Multi-agent mode enabled but agents.yml not found"
            exit 1
        fi
    fi
    
    # Validate multi-site configuration if enabled
    if [ "$MULTI_SITE_MODE" = "true" ]; then
        if [ ! -f "/app/config/sites.yml" ]; then
            error "Multi-site mode enabled but sites.yml not found"
            exit 1
        fi
    fi
    
    log "Configuration validation passed"
}

# Create necessary directories
setup_directories() {
    log "Setting up directories..."
    mkdir -p /app/logs /app/uploads
    
    # Set proper permissions
    chmod 755 /app/logs /app/uploads
    
    log "Directories setup completed"
}

# Health check function
health_check() {
    log "Performing initial health check..."
    python -c "
import asyncio
from mcp_wordpress.core.database import get_session
from mcp_wordpress.core.config import settings

async def health_check():
    try:
        async with get_session() as session:
            # Test database connection
            from sqlalchemy import text
            await session.execute(text('SELECT 1'))
        print('Health check passed')
    except Exception as e:
        print(f'Health check failed: {e}')
        exit(1)

asyncio.run(health_check())
"
}

# Start the MCP server
start_server() {
    log "Starting MCP WordPress Publisher Server v2.1..."
    
    case "$1" in
        "development")
            exec python -m mcp_wordpress.server sse
            ;;
        "production")
            # Run FastMCP server directly in SSE mode for production
            exec python -m mcp_wordpress.server sse
            ;;
        "stdio")
            exec python -m mcp_wordpress.server stdio
            ;;
        "test")
            log "Running tests..."
            exec python -m pytest tests/ -v --cov=mcp_wordpress --cov-report=html --cov-report=term
            ;;
        *)
            error "Unknown command: $1"
            error "Available commands: development, production, stdio, test"
            exit 1
            ;;
    esac
}

# Main execution
main() {
    log "MCP WordPress Publisher Server v2.1 Docker Entrypoint"
    log "Command: ${1:-production}"
    
    # Setup
    setup_directories
    init_config
    validate_config
    
    # Wait for dependencies
    wait_for_db
    wait_for_redis
    
    # Database setup
    run_migrations
    
    # Final health check
    health_check
    
    # Start server
    start_server "${1:-production}"
}

# Handle signals for graceful shutdown
trap 'log "Received SIGTERM, shutting down gracefully..."; exit 0' SIGTERM
trap 'log "Received SIGINT, shutting down gracefully..."; exit 0' SIGINT

# Execute main function
main "$@"