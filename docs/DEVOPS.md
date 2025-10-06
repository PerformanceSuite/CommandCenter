# DevOps & Infrastructure Guide

This document provides comprehensive documentation for the Command Center's DevOps infrastructure, including CI/CD, monitoring, logging, and backup systems.

## Table of Contents

- [CI/CD Pipeline](#cicd-pipeline)
- [Production Deployment](#production-deployment)
- [Monitoring & Metrics](#monitoring--metrics)
- [Logging](#logging)
- [Backup & Restore](#backup--restore)
- [Security](#security)
- [Troubleshooting](#troubleshooting)

## CI/CD Pipeline

### Overview

The CI/CD pipeline is implemented using GitHub Actions and runs on every push and pull request.

### Pipeline Stages

1. **Backend Tests & Linting**
   - Black code formatting check
   - Flake8 linting
   - MyPy type checking
   - Bandit security scanning
   - Safety dependency vulnerability check
   - pytest with coverage

2. **Frontend Tests & Linting**
   - ESLint
   - TypeScript type checking
   - Unit tests
   - Build verification

3. **Docker Build Test**
   - Build backend and frontend images
   - Cache layers for faster builds

4. **Integration Tests**
   - Start all services with docker-compose
   - Run integration tests
   - Verify service health

5. **Security Scanning**
   - Trivy vulnerability scanner
   - Upload results to GitHub Security

### Running Locally

```bash
# Backend linting and tests
cd backend
black --check app/
flake8 app/
pytest -v --cov=app

# Frontend linting and tests
cd frontend
npm run lint
npm run type-check
npm test
```

### Coverage Reports

Coverage reports are automatically uploaded to Codecov on each CI run. To generate local coverage reports:

```bash
cd backend
pytest --cov=app --cov-report=html
open htmlcov/index.html
```

## Production Deployment

### Prerequisites

- Docker and Docker Compose installed
- Domain name with DNS configured
- SSL certificate email for Let's Encrypt

### Environment Variables

Create a `.env.prod` file with the following variables:

```bash
# Project
COMPOSE_PROJECT_NAME=commandcenter
DOMAIN=your-domain.com

# Database
DB_PASSWORD=secure_password_here

# Application
SECRET_KEY=long_random_secret_key_here
ENVIRONMENT=production
LOG_LEVEL=INFO

# API Keys
ANTHROPIC_API_KEY=your_key
OPENAI_API_KEY=your_key
GITHUB_TOKEN=your_token

# Let's Encrypt
ACME_EMAIL=admin@your-domain.com

# Traefik Dashboard (generate with: htpasswd -nb admin password)
TRAEFIK_DASHBOARD_USER=admin:$apr1$...

# Monitoring Authentication
PROMETHEUS_USER=admin:$apr1$...
GRAFANA_ADMIN_USER=admin
GRAFANA_ADMIN_PASSWORD=secure_password
LOKI_USER=admin:$apr1$...
```

### Deploy Production Stack

```bash
# Deploy with production configuration
docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Check service status
docker-compose -f docker-compose.prod.yml ps
```

### Services & Endpoints

| Service | Internal Port | External URL | Description |
|---------|--------------|--------------|-------------|
| Frontend | 80 | https://your-domain.com | Main application |
| Backend | 8000 | https://api.your-domain.com | API endpoints |
| Traefik | 443 | https://traefik.your-domain.com | Reverse proxy dashboard |
| Grafana | 3000 | https://grafana.your-domain.com | Metrics visualization |
| Prometheus | 9090 | https://prometheus.your-domain.com | Metrics collection |
| Loki | 3100 | https://loki.your-domain.com | Log aggregation |

### SSL/TLS Configuration

- Automatic certificate generation via Let's Encrypt
- HTTP to HTTPS redirect enabled
- TLS 1.2+ enforced
- Modern cipher suite configuration
- HSTS headers enabled

### Scaling Services

```bash
# Scale backend instances
docker-compose -f docker-compose.prod.yml up -d --scale backend=3

# Traefik will automatically load balance requests
```

## Monitoring & Metrics

### Prometheus

Prometheus collects metrics from:
- FastAPI backend (custom application metrics)
- PostgreSQL (via postgres_exporter)
- Redis (via redis_exporter)
- System metrics (via node-exporter)
- Container metrics (via cAdvisor)
- Traefik metrics

**Configuration:** `monitoring/prometheus.yml`

**Custom Metrics:**
- `commandcenter_repository_operations_total`
- `commandcenter_technology_operations_total`
- `commandcenter_research_task_duration_seconds`
- `commandcenter_rag_operations_total`
- `commandcenter_rag_query_duration_seconds`
- `commandcenter_active_research_tasks`
- `commandcenter_cache_operations_total`

### Grafana Dashboards

Pre-configured dashboards:
1. **System Overview** - Overall system health and performance
2. **Application Metrics** - Custom business metrics
3. **Infrastructure** - System resources and containers

Access: https://grafana.your-domain.com

Default credentials in `.env.prod`

### Alerts

Configured alerts in `monitoring/alerts.yml`:
- Service downtime
- High request latency
- High error rate
- Database connection issues
- High CPU/memory usage
- Disk space warnings

### Adding Custom Metrics

```python
from app.utils.metrics import (
    track_repository_operation,
    track_rag_operation,
    research_task_duration
)

# Track operations
track_repository_operation('create', success=True)
track_rag_operation('query', success=True)

# Track duration
with research_task_duration.labels(task_type='analysis').time():
    # Your code here
    pass
```

## Logging

### Structured Logging

The application uses JSON-structured logging for easy parsing and analysis.

**Features:**
- JSON format for machine readability
- Request ID tracking
- User ID tracking
- Performance metrics
- Exception stack traces

**Log Levels:**
- DEBUG: Detailed debugging information
- INFO: General informational messages
- WARNING: Warning messages
- ERROR: Error messages
- CRITICAL: Critical issues

### Centralized Logging with Loki

All logs are aggregated in Loki and can be queried in Grafana.

**Query Examples:**

```logql
# All backend errors
{service="commandcenter-backend"} |= "ERROR"

# Specific endpoint logs
{service="commandcenter-backend"} | json | path="/api/v1/repositories"

# Logs for a specific request
{service="commandcenter-backend"} | json | request_id="abc-123"

# High latency requests
{service="commandcenter-backend"} | json | duration > 1
```

### Log Retention

- Default retention: 30 days (720 hours)
- Configurable in `monitoring/loki-config.yml`

### Viewing Logs

```bash
# Real-time logs from specific service
docker-compose -f docker-compose.prod.yml logs -f backend

# All logs
docker-compose -f docker-compose.prod.yml logs -f

# Logs for specific time period
docker-compose -f docker-compose.prod.yml logs --since 1h backend
```

## Backup & Restore

### Automated Backups

Backups run daily at 2 AM (configurable) and include:
- PostgreSQL database
- RAG storage (ChromaDB and documents)
- Redis data

**Setup:**

```bash
# Install backup cron job
./scripts/setup-backup-cron.sh

# Manual backup
./scripts/backup.sh

# View backup logs
tail -f /var/log/commandcenter-backup.log
```

### Backup Retention

- Default: 30 days
- Configurable via `RETENTION_DAYS` environment variable
- Old backups are automatically cleaned up

### Backup Location

```
backups/
├── postgres/       # Database dumps
├── rag/           # RAG storage archives
└── redis/         # Redis snapshots
```

### Restore from Backup

```bash
# Restore latest backup
./scripts/restore.sh

# Restore specific backup
./scripts/restore.sh 20240101_020000

# List available backups
ls -lh backups/postgres/
```

### Remote Backup Storage

For production, configure remote backup to S3, Google Cloud Storage, or similar.

**Example (AWS S3):**

Uncomment the S3 section in `scripts/backup.sh` and configure:

```bash
export AWS_ACCESS_KEY_ID=your_key
export AWS_SECRET_ACCESS_KEY=your_secret
export AWS_DEFAULT_REGION=us-east-1
```

## Security

### Security Measures Implemented

1. **Application Security**
   - Secret key encryption
   - HTTPS-only in production
   - CORS configuration
   - Security headers (HSTS, CSP, etc.)
   - Input validation

2. **Infrastructure Security**
   - TLS 1.2+ only
   - Modern cipher suites
   - Automated security scanning (Bandit, Safety, Trivy)
   - Regular dependency updates
   - Network isolation

3. **Authentication**
   - Basic auth for monitoring tools
   - API key management
   - Request ID tracking

4. **Data Security**
   - Encrypted database connections
   - Secure credential storage
   - Automated backups
   - Data isolation

### Security Scanning

```bash
# Run security scans
cd backend
bandit -r app/
safety check

# Scan Docker images
trivy image commandcenter-backend:latest
```

### Secret Management

**Never commit secrets to Git!**

Use environment variables for all sensitive data:
- Database passwords
- API keys
- Secret keys
- Certificates

## Troubleshooting

### Common Issues

#### Services won't start

```bash
# Check service logs
docker-compose -f docker-compose.prod.yml logs backend

# Check service health
docker-compose -f docker-compose.prod.yml ps

# Restart specific service
docker-compose -f docker-compose.prod.yml restart backend
```

#### High memory usage

```bash
# Check container memory usage
docker stats

# Adjust memory limits in docker-compose.prod.yml
deploy:
  resources:
    limits:
      memory: 4G
```

#### Certificate issues

```bash
# Check Traefik logs
docker-compose -f docker-compose.prod.yml logs traefik

# Verify DNS is pointing to server
dig your-domain.com

# Use Let's Encrypt staging for testing
# (uncomment staging server line in docker-compose.prod.yml)
```

#### Database connection issues

```bash
# Check database health
docker exec commandcenter_db pg_isready -U commandcenter

# View database logs
docker-compose -f docker-compose.prod.yml logs postgres

# Connect to database
docker exec -it commandcenter_db psql -U commandcenter
```

#### Backup failures

```bash
# Check backup logs
cat backups/backup.log

# Test backup manually
./scripts/backup.sh

# Verify backup files
ls -lh backups/postgres/
```

### Performance Optimization

1. **Database**
   - Increase shared_buffers
   - Add indexes for frequent queries
   - Enable query caching

2. **Redis**
   - Adjust maxmemory policy
   - Monitor cache hit rate
   - Increase memory limits if needed

3. **Application**
   - Enable response caching
   - Optimize database queries
   - Use connection pooling

4. **Infrastructure**
   - Scale horizontally (add more containers)
   - Use CDN for static assets
   - Optimize Docker images

### Monitoring Health

```bash
# Check all service endpoints
curl https://your-domain.com
curl https://api.your-domain.com/health
curl https://grafana.your-domain.com/api/health

# View metrics
curl http://localhost:8000/metrics

# Check Prometheus targets
# Visit: https://prometheus.your-domain.com/targets
```

## Maintenance

### Regular Maintenance Tasks

1. **Weekly**
   - Review monitoring dashboards
   - Check error logs
   - Verify backups are running

2. **Monthly**
   - Update dependencies
   - Review security scan results
   - Analyze performance metrics
   - Clean up old logs

3. **Quarterly**
   - Review and update documentation
   - Security audit
   - Disaster recovery testing
   - Capacity planning

### Updating the Application

```bash
# Pull latest changes
git pull

# Rebuild and restart services
docker-compose -f docker-compose.prod.yml build
docker-compose -f docker-compose.prod.yml up -d

# Run database migrations if needed
docker-compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

## Support

For issues or questions:
- Check this documentation
- Review logs in Grafana
- Check monitoring dashboards
- Contact DevOps team
