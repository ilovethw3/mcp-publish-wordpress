#!/bin/bash
set -e

# MCP WordPress Publisher v2.1 Deployment Script
# This script handles deployment across different environments

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
NC='\033[0m' # No Color

# Default values
ENVIRONMENT="development"
COMPOSE_FILE="docker-compose.yml"
BUILD_IMAGES=false
PULL_IMAGES=false
RUN_MIGRATIONS=false
BACKUP_BEFORE_DEPLOY=false
VERBOSE=false

# Logging functions
log() {
    echo -e "${GREEN}[$(date +'%Y-%m-%d %H:%M:%S')] $1${NC}"
}

info() {
    echo -e "${BLUE}[$(date +'%Y-%m-%d %H:%M:%S')] INFO: $1${NC}"
}

warn() {
    echo -e "${YELLOW}[$(date +'%Y-%m-%d %H:%M:%S')] WARNING: $1${NC}"
}

error() {
    echo -e "${RED}[$(date +'%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}"
}

debug() {
    if [ "$VERBOSE" = true ]; then
        echo -e "${PURPLE}[$(date +'%Y-%m-%d %H:%M:%S')] DEBUG: $1${NC}"
    fi
}

# Help function
show_help() {
    cat << EOF
MCP WordPress Publisher v2.1 Deployment Script

Usage: $0 [OPTIONS] COMMAND

COMMANDS:
    up          Start the services
    down        Stop the services
    restart     Restart the services
    build       Build all images
    pull        Pull latest images
    logs        Show service logs
    status      Show service status
    backup      Create a backup
    restore     Restore from backup
    migrate     Run database migrations
    test        Run integration tests
    clean       Clean up unused resources

OPTIONS:
    -e, --env ENVIRONMENT       Set environment (development, staging, production)
    -f, --file FILE            Docker compose file to use
    -b, --build                Build images before starting
    -p, --pull                 Pull latest images before starting
    -m, --migrate              Run database migrations
    --backup                   Create backup before deployment
    -v, --verbose              Enable verbose output
    -h, --help                 Show this help message

EXAMPLES:
    # Start development environment
    $0 -e development up

    # Deploy to production with build and migrations
    $0 -e production -b -m --backup up

    # View logs for specific service
    $0 logs mcp-server

    # Clean restart with fresh images
    $0 -e production -p restart

EOF
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -e|--env)
                ENVIRONMENT="$2"
                shift 2
                ;;
            -f|--file)
                COMPOSE_FILE="$2"
                shift 2
                ;;
            -b|--build)
                BUILD_IMAGES=true
                shift
                ;;
            -p|--pull)
                PULL_IMAGES=true
                shift
                ;;
            -m|--migrate)
                RUN_MIGRATIONS=true
                shift
                ;;
            --backup)
                BACKUP_BEFORE_DEPLOY=true
                shift
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                COMMAND="$1"
                shift
                SERVICE_NAME="$1"
                shift || true
                break
                ;;
        esac
    done
}

# Validate environment
validate_environment() {
    debug "Validating environment: $ENVIRONMENT"
    
    case $ENVIRONMENT in
        development|staging|production|testing)
            info "Environment: $ENVIRONMENT"
            ;;
        *)
            error "Invalid environment: $ENVIRONMENT"
            error "Valid environments: development, staging, production, testing"
            exit 1
            ;;
    esac
    
    # Check if docker and docker-compose are installed
    if ! command -v docker &> /dev/null; then
        error "Docker is not installed"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check if compose file exists
    if [ ! -f "$COMPOSE_FILE" ]; then
        error "Docker compose file not found: $COMPOSE_FILE"
        exit 1
    fi
    
    debug "Environment validation passed"
}

# Setup environment files
setup_environment() {
    debug "Setting up environment configuration"
    
    # Create .env file for the specific environment
    ENV_FILE=".env.$ENVIRONMENT"
    ENV_TEMPLATE=".env.$ENVIRONMENT.template"
    
    if [ -f "$ENV_TEMPLATE" ] && [ ! -f "$ENV_FILE" ]; then
        warn "Environment file $ENV_FILE not found"
        warn "Creating from template: $ENV_TEMPLATE"
        cp "$ENV_TEMPLATE" "$ENV_FILE"
        warn "Please edit $ENV_FILE with your actual configuration values"
    fi
    
    # Ensure required directories exist
    mkdir -p logs backups config uploads
    
    debug "Environment setup completed"
}

# Build Docker images
build_images() {
    if [ "$BUILD_IMAGES" = true ]; then
        log "Building Docker images..."
        
        docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" build --no-cache
        
        if [ $? -eq 0 ]; then
            log "Images built successfully"
        else
            error "Failed to build images"
            exit 1
        fi
    fi
}

# Pull Docker images
pull_images() {
    if [ "$PULL_IMAGES" = true ]; then
        log "Pulling Docker images..."
        
        docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" pull
        
        if [ $? -eq 0 ]; then
            log "Images pulled successfully"
        else
            error "Failed to pull images"
            exit 1
        fi
    fi
}

# Create backup
create_backup() {
    if [ "$BACKUP_BEFORE_DEPLOY" = true ]; then
        log "Creating backup before deployment..."
        
        BACKUP_DIR="backups/$(date +'%Y%m%d_%H%M%S')"
        mkdir -p "$BACKUP_DIR"
        
        # Backup database
        debug "Backing up database..."
        docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" exec -T postgres pg_dump -U mcpuser mcpdb_v21 > "$BACKUP_DIR/database.sql"
        
        # Backup configuration files
        debug "Backing up configuration..."
        cp -r config "$BACKUP_DIR/" 2>/dev/null || true
        cp ".env.$ENVIRONMENT" "$BACKUP_DIR/" 2>/dev/null || true
        
        # Backup uploads
        debug "Backing up uploads..."
        docker cp $(docker-compose -f "$COMPOSE_FILE" ps -q mcp-server):/app/uploads "$BACKUP_DIR/" 2>/dev/null || true
        
        # Create backup manifest
        cat > "$BACKUP_DIR/manifest.json" << EOF
{
    "timestamp": "$(date -u +%Y-%m-%dT%H:%M:%SZ)",
    "environment": "$ENVIRONMENT",
    "version": "v2.1",
    "components": {
        "database": "database.sql",
        "config": "config/",
        "uploads": "uploads/",
        "environment": ".env.$ENVIRONMENT"
    }
}
EOF
        
        log "Backup created: $BACKUP_DIR"
    fi
}

# Run database migrations
run_migrations() {
    if [ "$RUN_MIGRATIONS" = true ]; then
        log "Running database migrations..."
        
        # Wait for database to be ready
        info "Waiting for database to be ready..."
        docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" exec postgres pg_isready -U mcpuser -d mcpdb_v21
        
        # Run migrations
        docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" exec mcp-server alembic upgrade head
        
        if [ $? -eq 0 ]; then
            log "Database migrations completed successfully"
        else
            error "Database migrations failed"
            exit 1
        fi
    fi
}

# Start services
start_services() {
    log "Starting MCP WordPress Publisher v2.1 services..."
    
    # Start services based on environment
    case $ENVIRONMENT in
        development)
            # Start core services for development
            docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" up -d postgres redis mcp-server web-ui
            ;;
        production)
            # Start all services for production
            docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" up -d postgres redis mcp-server web-ui prometheus grafana
            ;;
        testing)
            # Start minimal services for testing
            docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" up -d postgres redis
            ;;
        *)
            # Default: start all services
            docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" up -d
            ;;
    esac
    
    if [ $? -eq 0 ]; then
        log "Services started successfully"
        show_service_info
    else
        error "Failed to start services"
        exit 1
    fi
}

# Stop services
stop_services() {
    log "Stopping services..."
    
    docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" down
    
    if [ $? -eq 0 ]; then
        log "Services stopped successfully"
    else
        error "Failed to stop services"
        exit 1
    fi
}

# Restart services
restart_services() {
    log "Restarting services..."
    
    stop_services
    start_services
}

# Show logs
show_logs() {
    log "Showing service logs..."
    
    if [ -n "$SERVICE_NAME" ]; then
        docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" logs -f "$SERVICE_NAME"
    else
        docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" logs -f
    fi
}

# Show service status
show_status() {
    log "Service status:"
    
    docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" ps
    
    echo ""
    info "Service health checks:"
    
    # Check MCP server health
    if curl -f -s http://localhost:${MCP_PORT:-8000}/health > /dev/null; then
        echo -e "${GREEN}✓${NC} MCP Server: Healthy"
    else
        echo -e "${RED}✗${NC} MCP Server: Unhealthy"
    fi
    
    # Check Web UI health
    if curl -f -s http://localhost:${WEB_UI_PORT:-3000}/api/health > /dev/null; then
        echo -e "${GREEN}✓${NC} Web UI: Healthy"
    else
        echo -e "${RED}✗${NC} Web UI: Unhealthy"
    fi
    
    # Check database connection
    if docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" exec postgres pg_isready -U mcpuser -d mcpdb_v21 > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Database: Connected"
    else
        echo -e "${RED}✗${NC} Database: Connection failed"
    fi
}

# Show service information
show_service_info() {
    echo ""
    info "Service Information:"
    echo "  Environment: $ENVIRONMENT"
    echo "  MCP Server: http://localhost:${MCP_PORT:-8000}"
    echo "  Web UI: http://localhost:${WEB_UI_PORT:-3000}"
    echo "  Prometheus: http://localhost:${PROMETHEUS_PORT:-9090}"
    echo "  Grafana: http://localhost:${GRAFANA_PORT:-3001}"
    echo ""
}

# Run integration tests
run_tests() {
    log "Running integration tests..."
    
    # Build test images
    docker-compose -f "$COMPOSE_FILE" --env-file ".env.testing" --profile testing build
    
    # Run tests
    docker-compose -f "$COMPOSE_FILE" --env-file ".env.testing" --profile testing run --rm mcp-server test
    
    if [ $? -eq 0 ]; then
        log "Integration tests passed"
    else
        error "Integration tests failed"
        exit 1
    fi
}

# Clean up resources
cleanup() {
    log "Cleaning up Docker resources..."
    
    # Remove unused containers, networks, images
    docker system prune -f
    
    # Remove unused volumes (be careful!)
    read -p "Remove unused Docker volumes? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker volume prune -f
    fi
    
    log "Cleanup completed"
}

# Restore from backup
restore_backup() {
    if [ -z "$SERVICE_NAME" ]; then
        error "Please specify backup directory to restore from"
        error "Usage: $0 restore <backup_directory>"
        exit 1
    fi
    
    BACKUP_DIR="$SERVICE_NAME"
    
    if [ ! -d "$BACKUP_DIR" ]; then
        error "Backup directory not found: $BACKUP_DIR"
        exit 1
    fi
    
    log "Restoring from backup: $BACKUP_DIR"
    
    # Stop services
    stop_services
    
    # Restore database
    if [ -f "$BACKUP_DIR/database.sql" ]; then
        info "Restoring database..."
        docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" up -d postgres
        sleep 10
        cat "$BACKUP_DIR/database.sql" | docker-compose -f "$COMPOSE_FILE" --env-file ".env.$ENVIRONMENT" exec -T postgres psql -U mcpuser -d mcpdb_v21
    fi
    
    # Restore configuration
    if [ -d "$BACKUP_DIR/config" ]; then
        info "Restoring configuration..."
        cp -r "$BACKUP_DIR/config"/* config/ 2>/dev/null || true
    fi
    
    # Restore environment file
    if [ -f "$BACKUP_DIR/.env.$ENVIRONMENT" ]; then
        info "Restoring environment configuration..."
        cp "$BACKUP_DIR/.env.$ENVIRONMENT" ".env.$ENVIRONMENT"
    fi
    
    log "Restore completed. Starting services..."
    start_services
}

# Main execution function
main() {
    case $COMMAND in
        up|start)
            setup_environment
            create_backup
            pull_images
            build_images
            start_services
            run_migrations
            ;;
        down|stop)
            stop_services
            ;;
        restart)
            setup_environment
            create_backup
            pull_images
            build_images
            restart_services
            run_migrations
            ;;
        build)
            setup_environment
            BUILD_IMAGES=true
            build_images
            ;;
        pull)
            setup_environment
            PULL_IMAGES=true
            pull_images
            ;;
        logs)
            show_logs
            ;;
        status)
            show_status
            ;;
        backup)
            BACKUP_BEFORE_DEPLOY=true
            create_backup
            ;;
        restore)
            restore_backup
            ;;
        migrate)
            RUN_MIGRATIONS=true
            run_migrations
            ;;
        test)
            ENVIRONMENT="testing"
            setup_environment
            run_tests
            ;;
        clean)
            cleanup
            ;;
        *)
            error "Unknown command: $COMMAND"
            echo ""
            show_help
            exit 1
            ;;
    esac
}

# Check if running as script
if [ "${BASH_SOURCE[0]}" == "${0}" ]; then
    # Parse command line arguments
    parse_args "$@"
    
    # Validate inputs
    if [ -z "$COMMAND" ]; then
        error "No command specified"
        echo ""
        show_help
        exit 1
    fi
    
    # Validate environment
    validate_environment
    
    # Run main function
    main
fi