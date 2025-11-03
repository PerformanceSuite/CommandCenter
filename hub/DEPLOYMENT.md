# Hub Deployment Guide

## Prerequisites

**Required:**
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM minimum
- 10GB disk space

**Optional (development):**
- Node.js 18+
- Python 3.11+
- Redis CLI (for debugging)

## Architecture

```
┌─────────────┐
│   Browser   │
└──────┬──────┘
       │ HTTP (9000)
┌──────▼──────────────────────┐
│   Hub Frontend (React)      │
└──────┬──────────────────────┘
       │ API (9002)
┌──────▼──────────────────────┐
│   Hub Backend (FastAPI)     │
└──────┬──────────────────────┘
       │ Celery Tasks
┌──────▼──────────────────────┐
│   Redis (Message Broker)    │
└──────┬──────────────────────┘
       │ Task Queue
┌──────▼──────────────────────┐
│   Celery Workers (2)        │
│   - Runs Dagger operations  │
│   - Updates task progress   │
└─────────────────────────────┘
```

## Quick Start (Docker)

### 1. Production Deployment

```bash
# Clone repository
git clone https://github.com/yourusername/commandcenter.git
cd commandcenter/hub

# Start all services
docker-compose -f docker-compose.monitoring.yml up -d

# Verify health
docker-compose -f docker-compose.monitoring.yml ps
```

**Access Points:**
- Hub Frontend: http://localhost:9000
- Hub Backend: http://localhost:9002
- Flower (monitoring): http://localhost:5555

### 2. Development Setup

```bash
# Terminal 1: Redis
docker-compose -f docker-compose.monitoring.yml up -d redis

# Terminal 2: Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
export DATABASE_URL="sqlite+aiosqlite:///./data/hub.db"
export CELERY_BROKER_URL="redis://localhost:6379/0"
uvicorn app.main:app --reload --port 9002

# Terminal 3: Celery Worker
cd backend
source venv/bin/activate
celery -A app.celery_app worker --loglevel=info

# Terminal 4: Frontend
cd frontend
npm install
npm run dev
```

## Environment Configuration

### Backend (.env)

```bash
# Database
DATABASE_URL=sqlite+aiosqlite:///./data/hub.db

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Task Configuration
CELERY_WORKER_CONCURRENCY=2
TASK_SOFT_TIME_LIMIT=3600
TASK_TIME_LIMIT=7200

# Security (production)
SECRET_KEY=<generate-with-openssl-rand-hex-32>
```

### Frontend (.env)

```bash
VITE_API_URL=http://localhost:9002
```

## Port Configuration

Default ports (customize in docker-compose.yml):

| Service | Port | Purpose |
|---------|------|---------|
| Frontend | 9000 | React UI |
| Backend | 9002 | FastAPI API |
| Redis | 6379 | Message broker |
| Flower | 5555 | Monitoring dashboard |

**Port Conflicts:**
If ports are in use, update in:
- `docker-compose.monitoring.yml`
- `frontend/.env` (VITE_API_URL)

## Health Checks

### Verify Services

```bash
# Redis
docker exec hub-redis redis-cli ping
# Expected: PONG

# Backend
curl http://localhost:9002/health
# Expected: {"status":"healthy"}

# Celery Worker
docker logs hub-celery-worker | grep "ready"
# Expected: [timestamp] [MainProcess] celery@<hostname> ready.

# Flower
curl http://localhost:5555/
# Expected: HTML response
```

### Monitoring

**Flower Dashboard** (http://localhost:5555):
- Workers tab: Should show 2 active workers
- Tasks tab: View task history
- Monitor tab: Real-time graphs

**Logs:**
```bash
# All services
docker-compose -f docker-compose.monitoring.yml logs -f

# Specific service
docker logs -f hub-celery-worker
docker logs -f hub-backend
```

## Database Management

### Migrations (Alembic)

```bash
cd backend
source venv/bin/activate

# Create migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

### Backup

```bash
# SQLite backup
cp backend/data/hub.db backend/data/hub.db.backup-$(date +%Y%m%d)

# Redis backup
docker exec hub-redis redis-cli SAVE
docker cp hub-redis:/data/dump.rdb ./redis-backup-$(date +%Y%m%d).rdb
```

## Scaling

### Horizontal Scaling (Multiple Workers)

Edit `docker-compose.monitoring.yml`:

```yaml
celery-worker:
  deploy:
    replicas: 4  # Increase from 2
```

Or start additional workers:

```bash
docker-compose -f docker-compose.monitoring.yml up -d --scale celery-worker=4
```

### Vertical Scaling (Worker Concurrency)

```yaml
celery-worker:
  command: celery -A app.celery_app worker --loglevel=info --concurrency=4
```

**Recommendation:** 1-2 workers per CPU core

## Security

### Production Checklist

- [ ] Change default SECRET_KEY
- [ ] Enable Flower authentication
- [ ] Use HTTPS (reverse proxy)
- [ ] Restrict Redis to localhost
- [ ] Set strong database password (if PostgreSQL)
- [ ] Enable CORS only for frontend domain
- [ ] Regular security updates

### Flower Authentication

```yaml
# In docker-compose.monitoring.yml
flower:
  command: celery -A app.celery_app flower --port=5555 --basic_auth=admin:$(openssl rand -hex 16)
```

## Troubleshooting

### Tasks Not Running

```bash
# 1. Check Redis
docker exec hub-redis redis-cli ping

# 2. Check worker status
docker logs hub-celery-worker

# 3. Check task queue
docker exec hub-redis redis-cli LLEN celery
# Should return queue depth
```

### Worker Crashes

```bash
# View logs
docker logs hub-celery-worker --tail 100

# Common issues:
# - Out of memory: Reduce concurrency
# - Dagger errors: Check Docker socket access
# - Import errors: Rebuild container
```

### Slow Tasks

```bash
# Check Flower: Tasks tab
# Look for tasks taking > 30 minutes

# Possible causes:
# - First Dagger build (normal, 20-30 min)
# - Network issues (check internet)
# - Resource constraints (check CPU/RAM)
```

## Maintenance

### Regular Tasks

**Daily:**
- Check Flower for failed tasks
- Review worker logs for errors

**Weekly:**
- Backup database
- Check disk space
- Update dependencies (security patches)

**Monthly:**
- Clean old task results (Redis)
- Review and optimize slow tasks
- Update documentation

### Cleanup

```bash
# Stop all services
docker-compose -f docker-compose.monitoring.yml down

# Remove volumes (clears data)
docker-compose -f docker-compose.monitoring.yml down -v

# Remove images
docker-compose -f docker-compose.monitoring.yml down --rmi all
```

## Performance Tuning

### Task Result Expiry

```python
# app/celery_app.py
celery_app.conf.update(
    result_expires=3600,  # 1 hour (increase if needed)
)
```

### Redis Memory

```bash
# Check memory usage
docker exec hub-redis redis-cli INFO memory

# Set max memory (docker-compose.monitoring.yml)
redis:
  command: redis-server --maxmemory 256mb --maxmemory-policy allkeys-lru
```

### Worker Prefetch

```yaml
# Reduce prefetch for long tasks
celery-worker:
  command: celery -A app.celery_app worker --loglevel=info --prefetch-multiplier=1
```

## Support

**Documentation:**
- Hub README: `hub/README.md`
- Monitoring Guide: `hub/MONITORING.md`
- Background Tasks Design: `docs/plans/2025-11-02-hub-background-tasks-design.md`

**Issues:**
- GitHub: https://github.com/yourusername/commandcenter/issues
- Tag: `component:hub`, `type:deployment`
