# MCP WordPress Publisher v2.1

A comprehensive multi-agent, multi-site WordPress content publishing system built on the Model Context Protocol (MCP). This system enables multiple AI agents to submit articles for human review and automatic publishing across multiple WordPress sites.

## 🚀 Key Features v2.1

### Multi-Agent Support
- **Individual Agent Authentication**: Each agent has unique API keys and permissions
- **Configurable Rate Limiting**: Per-agent request limits and security controls
- **Agent-Specific Permissions**: Fine-grained control over categories, tags, and actions
- **Comprehensive Agent Statistics**: Track performance and success rates per agent

### Multi-Site Publishing
- **Multiple WordPress Sites**: Publish to different WordPress installations
- **Site-Specific Configuration**: Individual settings, credentials, and rules per site
- **Intelligent Load Balancing**: Distribute publishing load across sites
- **Site Health Monitoring**: Real-time monitoring and alerting for all sites

### Advanced Security
- **JWT-Based Authentication**: Secure multi-agent authentication system
- **Rate Limiting & Throttling**: Prevent abuse and ensure system stability
- **Audit Logging**: Comprehensive logging of all agent activities
- **IP Whitelisting**: Optional IP-based access controls

### Web Management Interface
- **React-based Dashboard**: Modern, responsive web interface
- **Real-time Updates**: Live status updates via Server-Sent Events
- **Article Management**: Review, approve, and manage articles
- **Agent & Site Monitoring**: Visual dashboards for system health
- **Security Monitoring**: Track authentication and security events

### Production-Ready Deployment
- **Docker Orchestration**: Complete Docker Compose configuration
- **Monitoring Stack**: Prometheus and Grafana integration
- **Backup & Recovery**: Automated backup and restore capabilities
- **Load Balancing**: Nginx reverse proxy with SSL support

## 📋 Requirements

### System Requirements
- Docker 20.10+ and Docker Compose v2.0+
- Python 3.11+ (for development)
- Node.js 18+ (for Web UI development)
- PostgreSQL 16+ (provided via Docker)
- Redis 7+ (provided via Docker)

### WordPress Requirements
- WordPress 5.8+ with REST API enabled
- Application Password authentication
- User with `publish_posts` capability
- HTTPS recommended for production

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌──────────────────┐
│   AI Agents     │───▶│  MCP Server      │───▶│  WordPress Sites │
│   (Multiple)    │    │  (FastMCP v2.1)  │    │  (Multiple)      │
│                 │    │  Port: 8000      │    │                  │
└─────────────────┘    └──────────────────┘    └──────────────────┘
         │                       │                       │
         │              ┌──────────────────┐             │
         └──────────────│  Web Management  │─────────────┘
                        │  Interface       │
                        │  (Next.js)       │
                        │  Port: 3000      │
                        └──────────────────┘
                                 │
                    ┌──────────────────┐
                    │   PostgreSQL     │
                    │   Database       │
                    │   Port: 5433     │
                    └──────────────────┘
                                 │
                    ┌──────────────────┐
                    │     Redis        │
                    │   Cache/Sessions │
                    │   Port: 6380     │
                    └──────────────────┘
```

### Core Components

1. **MCP Server**: FastMCP-based server handling agent requests (Port 8000)
2. **Multi-Agent Auth**: JWT-based authentication with per-agent permissions
3. **Multi-Site Publisher**: Intelligent publishing engine for multiple WordPress sites
4. **Web Management UI**: React-based dashboard for system administration (Port 3000)
5. **Database Layer**: PostgreSQL with async SQLModel ORM (Port 5433)
6. **Caching Layer**: Redis for sessions and caching (Port 6380)
7. **Monitoring Stack**: Prometheus metrics and Grafana dashboards

## 🚀 Quick Start

### 1. Clone and Setup

```bash
git clone <repository-url>
cd mcp-publish-wordpress

# Make deployment script executable
chmod +x deploy.sh
```

### 2. Configure Environment

```bash
# Copy environment template
cp .env.production.template .env.production

# Edit configuration with your values
nano .env.production
```

**Required Configuration:**
- Database credentials
- JWT secrets and encryption keys
- Agent API keys
- WordPress site credentials
- SMTP settings for notifications

### 3. Configure Agents and Sites

```bash
# Copy configuration templates
cp config/agents.yml.template config/agents.yml
cp config/sites.yml.template config/sites.yml

# Edit with your agent and site configurations
nano config/agents.yml
nano config/sites.yml
```

### 4. Deploy System

```bash
# Development environment
./deploy.sh -e development up

# Production deployment with backup and migrations
./deploy.sh -e production -b -m --backup up

# View deployment status
./deploy.sh -e production status
```

### 5. Access Interfaces

- **Web Management Interface**: http://localhost:3000
- **MCP Server API**: http://localhost:8000  
- **Server-Sent Events**: http://localhost:8000/sse
- **Prometheus Metrics**: http://localhost:9090
- **Grafana Dashboards**: http://localhost:3001

All services are now accessible directly without reverse proxy.

## 📖 Configuration Guide

### Agent Configuration

Configure multiple AI agents in `config/agents.yml`:

```yaml
agents:
  - id: "content-creator-001"
    name: "Content Creator Agent"
    api_key: "${CONTENT_CREATOR_API_KEY}"
    rate_limit:
      requests_per_minute: 15
      requests_per_hour: 150
    permissions:
      can_submit_articles: true
      allowed_categories: ["Technology", "Programming"]
      allowed_tags: ["ai", "tech", "tutorial"]
    status: "active"
```

### Site Configuration

Configure multiple WordPress sites in `config/sites.yml`:

```yaml
sites:
  - id: "prod-blog-001"
    name: "Main Production Blog"
    wordpress_config:
      api_url: "https://yourblog.com/wp-json/wp/v2"
      username: "your_wp_username"
      app_password: "xxxx xxxx xxxx xxxx"
    publishing_rules:
      allowed_agents: ["content-creator-001"]
      auto_approve: false
      auto_publish_approved: true
    status: "active"
```

## 🔧 Development

### Setting up Development Environment

```bash
# Create virtual environment
python -m venv venv_mcp_publish_wordpress
source venv_mcp_publish_wordpress/bin/activate

# Install dependencies
pip install -r requirements-dev.txt

# Setup database
./deploy.sh -e development up postgres redis
alembic upgrade head

# Start MCP server in development mode
python -m mcp_wordpress.server sse
```

### Web UI Development

```bash
cd web-ui
npm install
npm run dev
```

### Running Tests

```bash
# Unit tests
python run_tests.py

# Integration tests
./deploy.sh -e testing test

# Specific test categories
pytest mcp_wordpress/tests/ -m unit
pytest mcp_wordpress/tests/ -m integration
```

## 🔧 API Reference

### MCP Tools

#### Submit Article
```python
# Submit new article for review
POST /tools/submit_article
Authorization: Bearer <agent_api_key>
{
    "title": "Article Title",
    "content_markdown": "# Article Content...",
    "category": "Technology",
    "tags": "ai,tech,tutorial"
}
```

#### Get Article Status
```python
# Check article status
GET /tools/get_article_status?article_id=123
Authorization: Bearer <agent_api_key>
```

#### Approve Article
```python
# Approve article for publishing
POST /tools/approve_article
Authorization: Bearer <reviewer_api_key>
{
    "article_id": 123,
    "reviewer_notes": "Approved for publishing"
}
```

### MCP Resources

#### Published Articles
```python
# Get published articles
GET /resources/published_articles
Authorization: Bearer <agent_api_key>
```

#### Agent Statistics
```python
# Get agent performance statistics
GET /resources/agent_statistics
Authorization: Bearer <agent_api_key>
```

#### System Health
```python
# Get system health status
GET /resources/system_health
```

## 🔒 Security Features

### Authentication & Authorization
- **JWT-based Authentication**: Secure token-based auth for all agents
- **Per-Agent API Keys**: Unique authentication credentials per agent
- **Role-Based Permissions**: Fine-grained access control
- **Session Management**: Redis-backed session handling

### Security Monitoring
- **Audit Logging**: Complete audit trail of all actions
- **Rate Limiting**: Configurable rate limits per agent and endpoint
- **IP Whitelisting**: Optional IP-based access controls
- **Failed Attempt Tracking**: Automatic account lockout on repeated failures

### Data Protection
- **Encryption at Rest**: Sensitive data encrypted in database
- **Secure Communication**: HTTPS/TLS for all external communication
- **Input Validation**: Comprehensive input sanitization
- **SQL Injection Prevention**: Parameterized queries and ORM protection

## 📊 Monitoring & Observability

### Metrics Collection
- **Application Metrics**: Request rates, response times, error rates
- **Business Metrics**: Article counts, success rates, agent performance
- **System Metrics**: Database performance, Redis usage, resource utilization
- **Custom Dashboards**: Grafana dashboards for visual monitoring

### Health Monitoring
- **Service Health Checks**: Automated health monitoring for all components
- **WordPress Site Monitoring**: Real-time WordPress API health checks
- **Database Connectivity**: Connection pool and query performance monitoring
- **Alert Management**: Configurable alerting via Prometheus AlertManager

### Logging
- **Structured Logging**: JSON-formatted logs for easy processing
- **Log Aggregation**: Centralized logging with configurable levels
- **Audit Trail**: Complete audit log of all security-relevant events
- **Error Tracking**: Detailed error logging with stack traces

## 🔄 Backup & Recovery

### Automated Backup
```bash
# Create full system backup
./deploy.sh backup

# Backup includes:
# - PostgreSQL database dump
# - Configuration files
# - Uploaded content
# - Environment settings
```

### Recovery Process
```bash
# Restore from backup
./deploy.sh restore backup/20241201_143022

# The restore process:
# 1. Stops services safely
# 2. Restores database from dump
# 3. Restores configuration files
# 4. Restarts services
```

## 🚀 Deployment Options

### Docker Compose Profiles

```bash
# Development profile
./deploy.sh -e development up

# Production profile (includes monitoring)
./deploy.sh -e production up

# Testing profile
./deploy.sh -e testing up
```

### Environment-Specific Deployment

#### Development
- Single instance deployment
- Debug logging enabled
- Hot reload for development
- Minimal resource requirements

#### Staging
- Production-like environment
- Integration testing
- Performance testing
- Security testing

#### Production
- High availability setup
- Full monitoring stack
- Automated backups
- SSL/TLS termination
- Resource optimization

## 🔧 Troubleshooting

### Common Issues

#### Services Won't Start
```bash
# Check service logs
./deploy.sh logs <service-name>

# Check system status
./deploy.sh status

# View detailed health information
curl http://localhost:8000/health
```

#### Database Connection Issues
```bash
# Check database connectivity
./deploy.sh logs postgres

# Test connection manually
docker-compose exec postgres pg_isready -U mcpuser -d mcpdb_v21
```

#### WordPress Publishing Failures
```bash
# Check WordPress credentials in sites.yml
# Verify WordPress REST API is enabled
# Check application password format
# Review site-specific logs
./deploy.sh logs mcp-server | grep "wordpress"
```

### Debug Mode

Enable debug mode for detailed logging:

```bash
# Set DEBUG=true in environment file
echo "DEBUG=true" >> .env.production

# Restart with verbose logging
./deploy.sh -v restart
```

## 📚 Additional Resources

- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [FastMCP Framework](https://github.com/jlowin/fastmcp)
- [WordPress REST API](https://developer.wordpress.org/rest-api/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch: `git checkout -b feature/amazing-feature`
3. Commit changes: `git commit -m 'Add amazing feature'`
4. Push to branch: `git push origin feature/amazing-feature`
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📞 Support

For support and questions:
- Create an issue in the GitHub repository
- Check the troubleshooting section above
- Review the configuration documentation
- Monitor the system logs for detailed error information

---

**MCP WordPress Publisher v2.1** - A modern, scalable solution for multi-agent WordPress content publishing.