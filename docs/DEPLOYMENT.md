# Command Center Deployment Guide

Complete guide for deploying Command Center in development, staging, and production environments.

## Table of Contents

- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Docker Deployment](#docker-deployment)
- [Traefik Deployment](#traefik-deployment)
- [Production Deployment](#production-deployment)
- [Database Management](#database-management)
- [Monitoring and Logging](#monitoring-and-logging)
- [Backup and Recovery](#backup-and-recovery)
- [Troubleshooting](#troubleshooting)
- [Security Checklist](#security-checklist)

---

## Overview

Command Center supports multiple deployment strategies:

- **Development:** Docker Compose with hot-reload
- **Staging:** Docker Compose with production builds
- **Production:** Docker Compose + Traefik (recommended)
- **Multi-Project:** Traefik with subdomain routing

### Deployment Architecture

**Phase 2 Architecture** (with async processing):

```
┌─────────────────┐
│   Internet      │
└────────┬────────┘
         │
    ┌────▼────┐
    │ Traefik │  (Optional, recommended)
    │  :80    │
    └────┬────┘
         │
    ┌────┴────────────────────────────────────┐
    │                                          │
┌───▼────┐         ┌──────▼──┐         ┌──────▼──────┐
│Frontend│         │ Backend │◄────WS──┤ Celery      │
│  :3000 │         │  :8000  │         │ Workers (4) │
└────────┘         └─────┬───┘         └──────┬──────┘
                         │                    │
                ┌────────┴────────┬───────────┴──────────┐
                │                 │                      │
           ┌────▼────┐      ┌─────▼────┐          ┌─────▼────┐
           │PostgreSQL│      │  Redis   │          │Celery Beat│
           │  :5432  │      │  :6379   │          │(scheduler)│
           └─────────┘      └──────────┘          └──────────┘
```

**Key Components:**
- **Backend API** (FastAPI) - REST API + WebSocket server
- **Celery Workers** - Async task processing (4+ workers)
- **Celery Beat** - Periodic task scheduler
- **Redis** - Message broker + result backend
- **PostgreSQL** - Primary database
- **WebSocket** - Real-time job progress updates

---

## Prerequisites

### System Requirements

**Minimum:**
- 2 CPU cores
- 4GB RAM
- 20GB disk space
- Docker 20.10+
- Docker Compose 2.0+

**Recommended (Phase 2 with Celery):**
- 4-6 CPU cores (for Celery workers)
- 8-12GB RAM (Celery workers + Redis)
- 50GB disk space (for knowledge base + job results)
- Docker 24.0+
- Docker Compose 2.20+
- Redis 7.0+ (required for Celery)

**Phase 2 Services:**
- **Celery Workers**: 4 concurrent workers for async jobs
- **Celery Beat**: Periodic task scheduler
- **Redis**: Message broker + result backend + caching
- **WebSocket Server**: Real-time progress updates

### Software Dependencies

**Required:**
```bash
docker --version        # Docker 20.10+
docker compose version  # 2.0+
```

**Optional (for development):**
```bash
python --version       # Python 3.11+
node --version         # Node.js 18+
git --version          # Git 2.30+
redis-cli --version    # Redis CLI (for debugging)
celery --version       # Celery 5.3+ (for local development)
```

---

## Environment Configuration

### 1. Create Environment File

```bash
# Copy template
cp .env.template .env

# Edit configuration
nano .env
```

### 2. Required Configuration

**Critical Settings:**

```bash
# Project Isolation - MUST be unique per project
COMPOSE_PROJECT_NAME=myproject-commandcenter

# Security - Generate with: openssl rand -hex 32
SECRET_KEY=your-32-character-random-key-here

# Database Password - Use strong password
DB_PASSWORD=strong-secure-password-here
```

**Database Configuration:**

```bash
DATABASE_URL=postgresql://commandcenter:changeme@postgres:5432/commandcenter
DB_PASSWORD=changeme
```

**Security Settings:**

```bash
SECRET_KEY=your-secret-key-here
ENCRYPT_TOKENS=true  # Always true in production
```

### 3. Optional Configuration

**AI/ML APIs (for RAG features):**

```bash
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
```

**GitHub Integration:**

```bash
GITHUB_TOKEN=ghp_...
```

**Port Configuration:**

```bash
BACKEND_PORT=8000
FRONTEND_PORT=3000
POSTGRES_PORT=5432
REDIS_PORT=6379
```

**Celery Configuration (Phase 2):**

```bash
# Celery workers
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CELERY_WORKER_CONCURRENCY=4

# Redis
REDIS_URL=redis://redis:6379
REDIS_MAX_CONNECTIONS=50
```

### 4. Environment Variable Reference

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `COMPOSE_PROJECT_NAME` | Yes | `commandcenter` | Unique project identifier |
| `SECRET_KEY` | Yes | - | Encryption key (32+ chars) |
| `DB_PASSWORD` | Yes | `changeme` | PostgreSQL password |
| `DATABASE_URL` | Yes | Auto-generated | Full database URL |
| `ANTHROPIC_API_KEY` | No | - | Anthropic API key |
| `OPENAI_API_KEY` | No | - | OpenAI API key |
| `GITHUB_TOKEN` | No | - | GitHub PAT |
| `BACKEND_PORT` | No | `8000` | Backend port |
| `FRONTEND_PORT` | No | `3000` | Frontend port |
| `POSTGRES_PORT` | No | `5432` | PostgreSQL port |
| `REDIS_PORT` | No | `6379` | Redis port |
| `DEBUG` | No | `false` | Debug mode |

---

## Docker Deployment

### Development Deployment

**1. Clone Repository:**

```bash
# Clone into project-specific directory
cd ~/projects/myproject/
git clone https://github.com/PerformanceSuite/CommandCenter.git commandcenter
cd commandcenter
```

**2. Configure Environment:**

```bash
cp .env.template .env
nano .env

# Set unique project name
COMPOSE_PROJECT_NAME=myproject-commandcenter
```

**3. Check Port Availability:**

```bash
# Use built-in script
./scripts/check-ports.sh

# Or manually
lsof -i :3000  # Frontend
lsof -i :8000  # Backend
lsof -i :5432  # PostgreSQL
lsof -i :6379  # Redis
```

**4. Start Services:**

```bash
# Build and start all services
docker compose up -d

# View logs
docker compose logs -f

# Check service health
docker compose ps
```

**5. Initialize Database:**

```bash
# Database migrations run automatically on startup
# Or manually:
docker compose exec backend alembic upgrade head
```

**6. Access Application:**

- **Frontend:** http://localhost:3000
- **Backend API:** http://localhost:8000
- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **Metrics (Prometheus):** http://localhost:8000/metrics

**Phase 2 Services**:
- **Jobs API:** http://localhost:8000/api/v1/jobs
- **WebSocket:** ws://localhost:8000/api/v1/jobs/ws/{job_id}
- **Export API:** http://localhost:8000/api/v1/export
- **Schedules API:** http://localhost:8000/api/v1/schedules
- **Webhooks API:** http://localhost:8000/api/v1/webhooks

### Production Deployment

**1. Use Production Configuration:**

```bash
# .env for production
DEBUG=false
ENCRYPT_TOKENS=true
SECRET_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 32)
```

**2. Build Production Images:**

```bash
# Build with production optimizations
docker compose build --no-cache

# Or use production compose file
docker compose -f docker-compose.prod.yml up -d
```

**3. Enable HTTPS (recommended):**

See [Traefik Deployment](#traefik-deployment) section.

### Useful Commands

```bash
# Start services
docker compose up -d

# Stop services
docker compose down

# View logs
docker compose logs -f [service_name]

# Restart service
docker compose restart [service_name]

# Rebuild service
docker compose up -d --build [service_name]

# Execute command in container
docker compose exec backend [command]
docker compose exec postgres psql -U commandcenter

# View service status
docker compose ps

# Remove all containers and volumes (DANGER!)
docker compose down -v
```

### Phase 2 Service Management

**Celery Workers:**

```bash
# View Celery worker logs
docker compose logs -f celery-worker

# Check active tasks
docker compose exec celery-worker celery -A app.tasks inspect active

# View worker stats
docker compose exec celery-worker celery -A app.tasks inspect stats

# Restart workers (pick up new code)
docker compose restart celery-worker

# Scale workers (run 8 instead of 4)
docker compose up -d --scale celery-worker=8
```

**Celery Beat (Scheduler):**

```bash
# View Beat scheduler logs
docker compose logs -f celery-beat

# Check scheduled tasks
docker compose exec celery-beat celery -A app.tasks inspect scheduled

# Restart Beat (reload schedule)
docker compose restart celery-beat
```

**Redis:**

```bash
# Connect to Redis CLI
docker compose exec redis redis-cli

# Check Redis info
docker compose exec redis redis-cli info

# Monitor Redis commands (real-time)
docker compose exec redis redis-cli monitor

# Clear all Redis data (DANGER!)
docker compose exec redis redis-cli FLUSHALL
```

**WebSocket Debugging:**

```bash
# Test WebSocket connection
# Install wscat: npm install -g wscat
wscat -c ws://localhost:8000/api/v1/jobs/ws/123

# Monitor WebSocket connections
docker compose logs -f backend | grep -i websocket
```

**Job Monitoring:**

```bash
# View active jobs
curl http://localhost:8000/api/v1/jobs/active/list | jq

# Get job statistics
curl http://localhost:8000/api/v1/jobs/statistics/summary | jq

# Cancel a running job
curl -X POST http://localhost:8000/api/v1/jobs/123/cancel
```

---

## Traefik Deployment

For zero port conflicts and multiple CommandCenter instances.

### Why Traefik?

- **Zero Port Conflicts:** Access via subdomains, not ports
- **Automatic HTTPS:** Let's Encrypt integration
- **Multi-Project Support:** Run unlimited instances
- **Load Balancing:** Easy horizontal scaling

### Setup Traefik

**1. Create Traefik Network:**

```bash
# Create external network for Traefik
docker network create traefik-public
```

**2. Deploy Traefik:**

```bash
# Create traefik directory
mkdir -p ~/traefik
cd ~/traefik

# Create docker-compose.yml
cat > docker-compose.yml <<EOF
version: '3.8'

services:
  traefik:
    image: traefik:v2.10
    container_name: traefik
    command:
      - "--api.dashboard=true"
      - "--providers.docker=true"
      - "--providers.docker.exposedbydefault=false"
      - "--entrypoints.web.address=:80"
    ports:
      - "80:80"
      - "8080:8080"  # Traefik dashboard
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock:ro
    networks:
      - traefik-public

networks:
  traefik-public:
    external: true
EOF

# Start Traefik
docker compose up -d
```

**3. Configure CommandCenter for Traefik:**

Create `docker-compose.traefik.yml` in your CommandCenter directory:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16-alpine
    container_name: ${COMPOSE_PROJECT_NAME}_db
    environment:
      POSTGRES_DB: commandcenter
      POSTGRES_USER: commandcenter
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    networks:
      - internal

  redis:
    image: redis:7-alpine
    container_name: ${COMPOSE_PROJECT_NAME}_redis
    volumes:
      - redis_data:/data
    networks:
      - internal

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: ${COMPOSE_PROJECT_NAME}_backend
    environment:
      DATABASE_URL: postgresql://commandcenter:${DB_PASSWORD}@postgres:5432/commandcenter
      SECRET_KEY: ${SECRET_KEY}
      RAG_STORAGE_PATH: /app/rag_storage
      REDIS_URL: redis://redis:6379
    volumes:
      - rag_storage:/app/rag_storage
    depends_on:
      - postgres
      - redis
    networks:
      - internal
      - traefik-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.${COMPOSE_PROJECT_NAME}-backend.rule=Host(`api.${COMPOSE_PROJECT_NAME}.localhost`)"
      - "traefik.http.services.${COMPOSE_PROJECT_NAME}-backend.loadbalancer.server.port=8000"

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: production
    container_name: ${COMPOSE_PROJECT_NAME}_frontend
    environment:
      VITE_API_URL: http://api.${COMPOSE_PROJECT_NAME}.localhost
    depends_on:
      - backend
    networks:
      - traefik-public
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.${COMPOSE_PROJECT_NAME}-frontend.rule=Host(`${COMPOSE_PROJECT_NAME}.localhost`)"
      - "traefik.http.services.${COMPOSE_PROJECT_NAME}-frontend.loadbalancer.server.port=80"

volumes:
  postgres_data:
  rag_storage:
  redis_data:

networks:
  internal:
    driver: bridge
  traefik-public:
    external: true
```

**4. Deploy with Traefik:**

```bash
# Set project name in .env
COMPOSE_PROJECT_NAME=project-a

# Start services
docker compose -f docker-compose.traefik.yml up -d

# Access application
# Frontend: http://project-a.localhost
# Backend: http://api.project-a.localhost
```

**5. Production HTTPS:**

For production with real domains and HTTPS:

```yaml
# In traefik docker-compose.yml, add:
command:
  - "--certificatesresolvers.letsencrypt.acme.email=your@email.com"
  - "--certificatesresolvers.letsencrypt.acme.storage=/letsencrypt/acme.json"
  - "--certificatesresolvers.letsencrypt.acme.httpchallenge.entrypoint=web"
  - "--entrypoints.websecure.address=:443"

# Add label to services:
labels:
  - "traefik.http.routers.backend.tls.certresolver=letsencrypt"
```

See [TRAEFIK_SETUP.md](./TRAEFIK_SETUP.md) for complete guide.

---

## Production Deployment

### Best Practices

**1. Use Strong Secrets:**

```bash
# Generate secure secrets
SECRET_KEY=$(openssl rand -hex 32)
DB_PASSWORD=$(openssl rand -base64 32)

# Store in .env (never commit to git)
echo "SECRET_KEY=$SECRET_KEY" >> .env
echo "DB_PASSWORD=$DB_PASSWORD" >> .env
```

**2. Enable HTTPS:**

```bash
# Use Traefik with Let's Encrypt
# See Traefik section above
```

**3. Configure CORS:**

```bash
# In backend/.env or environment
CORS_ORIGINS=["https://yourdomain.com", "https://api.yourdomain.com"]
```

**4. Set Production Debug Mode:**

```bash
DEBUG=false
PYTHONUNBUFFERED=1
```

**5. Use Health Checks:**

```yaml
# Already configured in docker-compose.yml
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

**6. Resource Limits:**

```yaml
# Add to docker-compose.yml
services:
  backend:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

**7. Restart Policies:**

```yaml
# Add to docker-compose.yml
services:
  backend:
    restart: unless-stopped
```

---

## Database Management

### Migrations

**Create Migration:**

```bash
# Enter backend container
docker compose exec backend bash

# Create migration
alembic revision --autogenerate -m "Description of changes"

# Exit container
exit
```

**Apply Migrations:**

```bash
# Apply all pending migrations
docker compose exec backend alembic upgrade head

# Apply specific migration
docker compose exec backend alembic upgrade <revision>
```

**Rollback Migrations:**

```bash
# Rollback one migration
docker compose exec backend alembic downgrade -1

# Rollback to specific revision
docker compose exec backend alembic downgrade <revision>

# Show current revision
docker compose exec backend alembic current
```

### Database Access

**PostgreSQL Shell:**

```bash
# Access database
docker compose exec postgres psql -U commandcenter

# Run SQL commands
\dt                    # List tables
\d repositories        # Describe table
SELECT * FROM repositories;

# Exit
\q
```

**Database Dump:**

```bash
# Export database
docker compose exec postgres pg_dump -U commandcenter commandcenter > backup.sql

# With compression
docker compose exec postgres pg_dump -U commandcenter commandcenter | gzip > backup.sql.gz
```

**Database Restore:**

```bash
# Restore from dump
docker compose exec -T postgres psql -U commandcenter commandcenter < backup.sql

# From compressed dump
gunzip -c backup.sql.gz | docker compose exec -T postgres psql -U commandcenter commandcenter
```

---

## Monitoring and Logging

### View Logs

**All Services:**

```bash
# Follow all logs
docker compose logs -f

# Last 100 lines
docker compose logs --tail=100
```

**Specific Service:**

```bash
# Backend logs
docker compose logs -f backend

# Frontend logs
docker compose logs -f frontend

# PostgreSQL logs
docker compose logs -f postgres
```

**Export Logs:**

```bash
# Save logs to file
docker compose logs --no-color > logs.txt

# With timestamp
docker compose logs --timestamps > logs-$(date +%Y%m%d-%H%M%S).txt
```

### Health Checks

**Manual Health Check:**

```bash
# Backend health
curl http://localhost:8000/health

# Check all services
docker compose ps
```

**Automated Monitoring:**

```bash
# Install monitoring stack (optional)
# Prometheus + Grafana
# See monitoring/ directory for configs
```

### Performance Monitoring

**Resource Usage:**

```bash
# Real-time stats
docker stats

# Specific service
docker stats commandcenter_backend
```

**Database Performance:**

```bash
# Active connections
docker compose exec postgres psql -U commandcenter -c "SELECT count(*) FROM pg_stat_activity;"

# Slow queries
docker compose exec postgres psql -U commandcenter -c "SELECT * FROM pg_stat_statements ORDER BY total_time DESC LIMIT 10;"
```

---

## Backup and Recovery

### Automated Backups

**Create Backup Script:**

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR=/backups/commandcenter
DATE=$(date +%Y%m%d-%H%M%S)

# Create backup directory
mkdir -p $BACKUP_DIR

# Backup database
docker compose exec -T postgres pg_dump -U commandcenter commandcenter | \
  gzip > $BACKUP_DIR/db-$DATE.sql.gz

# Backup RAG storage
docker compose exec -T backend tar -czf - /app/rag_storage | \
  cat > $BACKUP_DIR/rag-$DATE.tar.gz

# Delete old backups (keep last 30 days)
find $BACKUP_DIR -name "*.gz" -mtime +30 -delete

echo "Backup completed: $DATE"
```

**Schedule Backups:**

```bash
# Add to crontab
crontab -e

# Daily backup at 2 AM
0 2 * * * /path/to/backup.sh >> /var/log/commandcenter-backup.log 2>&1
```

### Restore from Backup

**Database Restore:**

```bash
# Stop application
docker compose down

# Start only database
docker compose up -d postgres

# Restore database
gunzip -c db-20251005-020000.sql.gz | \
  docker compose exec -T postgres psql -U commandcenter commandcenter

# Restart application
docker compose up -d
```

**RAG Storage Restore:**

```bash
# Restore RAG data
docker compose exec -T backend tar -xzf - -C / < rag-20251005-020000.tar.gz

# Restart backend
docker compose restart backend
```

---

## Troubleshooting

### Common Issues

**1. Port Already in Use:**

```bash
# Check what's using the port
lsof -i :8000

# Change port in .env
BACKEND_PORT=8001

# Restart services
docker compose up -d
```

**2. Database Connection Failed:**

```bash
# Check PostgreSQL health
docker compose ps postgres

# View PostgreSQL logs
docker compose logs postgres

# Restart PostgreSQL
docker compose restart postgres
```

**3. Migration Errors:**

```bash
# Check current migration state
docker compose exec backend alembic current

# View migration history
docker compose exec backend alembic history

# Force migration state (DANGER!)
docker compose exec backend alembic stamp head
```

**4. Frontend Not Loading:**

```bash
# Check frontend logs
docker compose logs frontend

# Rebuild frontend
docker compose up -d --build frontend

# Check API connection
curl http://localhost:8000/health
```

**5. Out of Disk Space:**

```bash
# Check disk usage
docker system df

# Clean up unused resources
docker system prune -a --volumes

# Remove old images
docker image prune -a
```

**6. Container Won't Start:**

```bash
# Check container logs
docker compose logs [service_name]

# Recreate container
docker compose up -d --force-recreate [service_name]

# Reset everything (DANGER!)
docker compose down -v
docker compose up -d
```

### Debug Mode

**Enable Debug Logging:**

```bash
# In .env
DEBUG=true

# Restart backend
docker compose restart backend

# View verbose logs
docker compose logs -f backend
```

---

## Security Checklist

### Pre-Deployment

- [ ] Change default `SECRET_KEY`
- [ ] Change default `DB_PASSWORD`
- [ ] Set unique `COMPOSE_PROJECT_NAME`
- [ ] Enable `ENCRYPT_TOKENS=true`
- [ ] Configure CORS origins
- [ ] Disable DEBUG mode (`DEBUG=false`)
- [ ] Review `.env` file (never commit to git)
- [ ] Add `.env` to `.gitignore`

### Production

- [ ] Enable HTTPS with Traefik + Let's Encrypt
- [ ] Configure firewall rules
- [ ] Set up automated backups
- [ ] Enable monitoring and alerts
- [ ] Configure log rotation
- [ ] Review security headers
- [ ] Implement rate limiting
- [ ] Set resource limits
- [ ] Enable restart policies
- [ ] Document disaster recovery plan

### Network Security

- [ ] Use internal Docker networks
- [ ] Expose only necessary ports
- [ ] Configure Traefik security headers
- [ ] Enable HTTPS redirect
- [ ] Implement authentication (if required)
- [ ] Review CORS configuration

### Data Security

- [ ] Encrypt GitHub tokens (enabled by default)
- [ ] Backup database regularly
- [ ] Test restore procedures
- [ ] Secure backup storage
- [ ] Implement data retention policy
- [ ] Follow data isolation guidelines

---

## Quick Reference

### Essential Commands

```bash
# Start
docker compose up -d

# Stop
docker compose down

# Logs
docker compose logs -f

# Restart
docker compose restart

# Rebuild
docker compose up -d --build

# Database shell
docker compose exec postgres psql -U commandcenter

# Backend shell
docker compose exec backend bash

# Migrations
docker compose exec backend alembic upgrade head

# Health check
curl http://localhost:8000/health

# View stats
docker stats
```

### File Locations

- **Configuration:** `.env`
- **Docker Compose:** `docker-compose.yml`
- **Database Data:** Docker volume `postgres_data`
- **RAG Storage:** Docker volume `rag_storage`
- **Logs:** `docker compose logs`
- **Backups:** `/backups/commandcenter/`

---

## Next Steps

After deployment:

1. **Configure Repositories:** Add your GitHub repositories
2. **Set Up Technologies:** Create technology radar entries
3. **Start Research:** Create research tasks
4. **Build Knowledge Base:** Process documents with Docling
5. **Monitor Health:** Set up health check monitoring
6. **Schedule Backups:** Configure automated backups

---

## Additional Resources

- [Configuration Guide](./CONFIGURATION.md) - Detailed configuration options
- [Data Isolation](./DATA_ISOLATION.md) - Multi-project setup
- [Traefik Setup](./TRAEFIK_SETUP.md) - Complete Traefik guide
- [Port Management](./PORT_MANAGEMENT.md) - Handling port conflicts
- [API Documentation](./API.md) - API reference
- [Architecture](./ARCHITECTURE.md) - System architecture

---

**Deployment Version:** 1.0.0
**Last Updated:** 2025-10-05
