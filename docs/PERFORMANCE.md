# Command Center Performance Optimization Guide

**Version:** 1.0.0
**Last Updated:** 2025-10-12

Complete guide to optimizing Command Center performance for production deployments.

## Table of Contents

- [Overview](#overview)
- [Database Optimization](#database-optimization)
- [Redis & Caching](#redis--caching)
- [Celery Workers](#celery-workers)
- [API Performance](#api-performance)
- [Frontend Optimization](#frontend-optimization)
- [Monitoring & Profiling](#monitoring--profiling)
- [Scalability Recommendations](#scalability-recommendations)

---

## Overview

Command Center's Phase 2 architecture introduces async processing with Celery, real-time WebSocket updates, and multi-format exports. This guide provides optimization strategies for production workloads.

**Performance Targets:**
- API Response Time: <200ms (p95)
- Job Dispatch Time: <50ms
- WebSocket Latency: <100ms
- Database Query Time: <50ms (p95)
- Export Generation: <10s for standard reports

---

## Database Optimization

### 1. Indexing Strategy

**Critical Indexes (already implemented):**

```sql
-- Jobs API
CREATE INDEX idx_jobs_project_status ON jobs(project_id, status);
CREATE INDEX idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX idx_jobs_celery_task_id ON jobs(celery_task_id);

-- Schedules API
CREATE INDEX idx_schedules_next_run ON schedules(next_run_at) WHERE enabled = true;
CREATE INDEX idx_schedules_project ON schedules(project_id);

-- Webhooks API
CREATE INDEX idx_webhook_deliveries_status ON webhook_deliveries(status);
CREATE INDEX idx_webhook_deliveries_scheduled ON webhook_deliveries(scheduled_for);
```

**Recommended Additional Indexes:**

```sql
-- For filtering by tags (JSONB GIN index)
CREATE INDEX idx_jobs_tags ON jobs USING GIN (tags);
CREATE INDEX idx_schedules_tags ON schedules USING GIN (tags);

-- For technology filtering
CREATE INDEX idx_technologies_domain_status ON technologies(domain, status);

-- For repository filtering
CREATE INDEX idx_repositories_project_id ON repositories(project_id);
```

### 2. Query Optimization

**Use Connection Pooling:**

```python
# In app/database.py
DATABASE_URL = "postgresql+asyncpg://..."
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,          # Increase for high load
    max_overflow=40,       # Allow burst connections
    pool_pre_ping=True,    # Health checks
    pool_recycle=3600,     # Recycle connections hourly
)
```

**Pagination Best Practices:**

```python
# ✅ Good - Use cursor-based pagination for large datasets
@router.get("/jobs")
async def list_jobs(
    cursor: Optional[int] = None,  # Last job ID seen
    limit: int = 100,
):
    query = select(Job).where(Job.id > cursor).limit(limit)

# ❌ Avoid - Offset pagination for large datasets
# offset = (page - 1) * limit  # Slow for page 1000+
```

**Eager Loading:**

```python
# ✅ Good - Eager load relationships
query = select(Schedule).options(
    selectinload(Schedule.project),
    selectinload(Schedule.repository),
)

# ❌ Avoid - N+1 queries
for schedule in schedules:
    print(schedule.project.name)  # Triggers separate query per schedule
```

### 3. Database Maintenance

**Regular Maintenance Schedule:**

```bash
# Weekly vacuum (during low-traffic periods)
docker compose exec postgres psql -U commandcenter -c "VACUUM ANALYZE;"

# Monthly full vacuum
docker compose exec postgres psql -U commandcenter -c "VACUUM FULL ANALYZE;"

# Check table sizes
docker compose exec postgres psql -U commandcenter -c "
SELECT
    relname AS table_name,
    pg_size_pretty(pg_total_relation_size(relid)) AS total_size
FROM pg_catalog.pg_statio_user_tables
ORDER BY pg_total_relation_size(relid) DESC;
"
```

**Archive Old Data:**

```python
# Archive completed jobs older than 30 days
from datetime import datetime, timedelta

cutoff_date = datetime.utcnow() - timedelta(days=30)
old_jobs = await db.execute(
    delete(Job).where(
        and_(
            Job.status.in_(["completed", "failed", "cancelled"]),
            Job.completed_at < cutoff_date
        )
    )
)
```

---

## Redis & Caching

### 1. Redis Configuration

**Optimize Redis for Production:**

```bash
# In docker-compose.yml or redis.conf
redis:
  command: >
    --maxmemory 2gb
    --maxmemory-policy allkeys-lru
    --save ""                          # Disable persistence for cache
    --appendonly no                    # Disable AOF
    --tcp-backlog 511
    --timeout 0
    --tcp-keepalive 300
```

**Connection Pooling:**

```python
# In app/services/redis_service.py
redis_pool = redis.ConnectionPool(
    host='redis',
    port=6379,
    db=0,
    max_connections=50,
    socket_timeout=5,
    socket_connect_timeout=5,
    health_check_interval=30,
)
```

### 2. Caching Strategy

**Cache Frequently Accessed Data:**

```python
from app.services.redis_service import redis_service

# Cache technology list (5 minute TTL)
cache_key = f"technologies:project:{project_id}"
cached_data = await redis_service.get(cache_key)

if not cached_data:
    technologies = await db.execute(select(Technology).where(...))
    await redis_service.set(cache_key, technologies, expire=300)
else:
    technologies = cached_data

# Cache dashboard stats (1 minute TTL)
cache_key = f"dashboard:stats:project:{project_id}"
stats = await redis_service.get_or_compute(
    key=cache_key,
    compute_fn=lambda: get_dashboard_stats(project_id),
    expire=60,
)
```

**Cache Invalidation:**

```python
# Invalidate cache on updates
@router.post("/technologies")
async def create_technology(tech: TechnologyCreate):
    new_tech = await service.create(tech)

    # Invalidate caches
    await redis_service.delete(f"technologies:project:{tech.project_id}")
    await redis_service.delete(f"dashboard:stats:project:{tech.project_id}")

    return new_tech
```

### 3. Celery Result Backend

**Optimize Result Storage:**

```python
# In celery config
app.conf.update(
    result_backend_transport_options={
        'master_name': 'mymaster',           # For Redis Sentinel
        'visibility_timeout': 3600,          # 1 hour
    },
    result_expires=3600,                     # Clean up results after 1 hour
    result_compression='gzip',               # Compress large results
)
```

---

## Celery Workers

### 1. Worker Configuration

**Optimize Worker Count:**

```bash
# CPU-bound tasks (analysis, export generation)
CELERY_WORKER_CONCURRENCY=4  # = number of CPU cores

# I/O-bound tasks (API calls, database queries)
CELERY_WORKER_CONCURRENCY=8  # = 2x CPU cores

# Mixed workload
CELERY_WORKER_CONCURRENCY=6  # Between CPU and I/O optimal
```

**Worker Pool Type:**

```python
# For CPU-bound tasks
celery -A app.tasks worker --pool=prefork --concurrency=4

# For I/O-bound tasks (better for async operations)
celery -A app.tasks worker --pool=eventlet --concurrency=100

# For mixed workload (recommended)
celery -A app.tasks worker --pool=prefork --concurrency=6
```

### 2. Task Optimization

**Task Time Limits:**

```python
@celery_app.task(
    bind=True,
    time_limit=600,        # Hard limit: 10 minutes
    soft_time_limit=540,   # Soft limit: 9 minutes (raises exception)
    max_retries=3,
    default_retry_delay=300,
)
def analyze_repository(self, repo_id: int):
    try:
        # Task logic
        pass
    except SoftTimeLimitExceeded:
        # Clean up and raise
        logger.warning(f"Analysis of repo {repo_id} exceeded soft time limit")
        raise
```

**Task Routing:**

```python
# Route tasks to different queues based on priority
celery_app.conf.task_routes = {
    'app.tasks.analysis.*': {'queue': 'analysis'},
    'app.tasks.export.*': {'queue': 'export'},
    'app.tasks.webhook.*': {'queue': 'webhooks'},
}

# Start workers for specific queues
# High-priority queue (more workers)
celery -A app.tasks worker -Q analysis --concurrency=8

# Low-priority queue (fewer workers)
celery -A app.tasks worker -Q export --concurrency=2
```

### 3. Monitoring & Autoscaling

**Monitor Worker Performance:**

```bash
# Check active tasks
celery -A app.tasks inspect active

# Check registered tasks
celery -A app.tasks inspect registered

# Monitor queue lengths
celery -A app.tasks inspect active_queues

# View worker stats
celery -A app.tasks inspect stats
```

**Autoscaling Workers:**

```bash
# Scale workers based on queue length
celery -A app.tasks worker --autoscale=10,3
# Max 10 workers, min 3 workers

# In docker-compose.yml
celery-worker:
  command: celery -A app.tasks worker --autoscale=10,4 --loglevel=info
```

---

## API Performance

### 1. Rate Limiting

**Configured Rate Limits:**

```python
# Per-endpoint rate limits (already implemented)
@router.get("/jobs")
@limiter.limit("100/minute")  # Standard endpoints

@router.get("/export/{id}/sarif")
@limiter.limit("10/minute")   # Resource-intensive exports

@router.post("/batch/analyze")
@limiter.limit("5/minute")    # Batch operations
```

**Adjust Limits for Production:**

```python
# In app/middleware.py
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200/minute", "2000/hour"],
    storage_uri="redis://redis:6379",
    strategy="fixed-window-elastic-expiry",
)
```

### 2. Response Compression

**Enable Gzip Compression:**

```python
# In app/main.py
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(
    GZipMiddleware,
    minimum_size=1000,  # Only compress responses > 1KB
    compresslevel=6,    # Balance between speed and compression
)
```

### 3. Async Optimization

**Use Async Database Queries:**

```python
# ✅ Good - Parallel queries
async def get_dashboard_data():
    repos_task = db.execute(select(Repository))
    techs_task = db.execute(select(Technology))
    jobs_task = db.execute(select(Job))

    repos, techs, jobs = await asyncio.gather(
        repos_task, techs_task, jobs_task
    )
    return {"repos": repos, "techs": techs, "jobs": jobs}

# ❌ Avoid - Sequential queries
async def get_dashboard_data():
    repos = await db.execute(select(Repository))
    techs = await db.execute(select(Technology))
    jobs = await db.execute(select(Job))
    return {"repos": repos, "techs": techs, "jobs": jobs}
```

---

## Frontend Optimization

### 1. Build Optimization

**Production Build Settings:**

```javascript
// vite.config.ts
export default defineConfig({
  build: {
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,  // Remove console.log in production
      },
    },
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom'],
          'charts': ['chart.js', 'react-chartjs-2'],
        },
      },
    },
    chunkSizeWarningLimit: 1000,
  },
});
```

### 2. Code Splitting

**Lazy Load Routes:**

```javascript
// App.tsx
import { lazy, Suspense } from 'react';

const Dashboard = lazy(() => import('./components/Dashboard'));
const Jobs = lazy(() => import('./components/Jobs'));
const Export = lazy(() => import('./components/Export'));

function App() {
  return (
    <Suspense fallback={<LoadingSpinner />}>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/jobs" element={<Jobs />} />
        <Route path="/export" element={<Export />} />
      </Routes>
    </Suspense>
  );
}
```

### 3. API Request Optimization

**Debounce Search Inputs:**

```javascript
import { debounce } from 'lodash';

const searchTechnologies = debounce(async (query) => {
  const response = await api.get(`/technologies?search=${query}`);
  setResults(response.data);
}, 300);  // Wait 300ms after last keystroke
```

**Batch API Requests:**

```javascript
// ✅ Good - Single request with all IDs
const jobs = await api.post('/jobs/batch', {
  job_ids: [1, 2, 3, 4, 5]
});

// ❌ Avoid - Multiple requests
for (const id of [1, 2, 3, 4, 5]) {
  await api.get(`/jobs/${id}`);
}
```

---

## Monitoring & Profiling

### 1. Prometheus Metrics

**Key Metrics to Monitor:**

```
# API Performance
http_request_duration_seconds{endpoint="/api/v1/jobs"}
http_requests_total{endpoint="/api/v1/jobs",status="200"}

# Job System
commandcenter_jobs_total{status="completed"}
commandcenter_job_duration_seconds
commandcenter_jobs_active

# Celery Workers
celery_task_runtime_seconds
celery_tasks_total{status="SUCCESS"}
celery_worker_tasks_active

# Database
pg_stat_database_tup_fetched
pg_stat_database_tup_returned
```

**Grafana Dashboard Recommendations:**
- Job completion rate (jobs/hour)
- API latency (p50, p95, p99)
- Worker utilization (active tasks / total workers)
- Database connection pool usage
- Redis memory usage

### 2. Application Profiling

**Profile Slow Endpoints:**

```python
import cProfile
import pstats
from io import StringIO

@router.get("/profile/jobs")
async def profile_list_jobs():
    profiler = cProfile.Profile()
    profiler.enable()

    # Your endpoint logic
    result = await list_jobs()

    profiler.disable()
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions

    return {"profile": s.getvalue(), "result": result}
```

### 3. Database Query Analysis

**Enable Query Logging (Development Only):**

```python
# In app/database.py
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Log all SQL queries (disable in production!)
)
```

**Analyze Slow Queries:**

```sql
-- Enable query logging in PostgreSQL
ALTER DATABASE commandcenter SET log_min_duration_statement = 1000;  -- Log queries > 1s

-- Find slow queries
SELECT
    query,
    mean_exec_time,
    calls,
    total_exec_time
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;
```

---

## Scalability Recommendations

### 1. Horizontal Scaling

**Scale Individual Services:**

```yaml
# docker-compose.yml
services:
  celery-worker:
    deploy:
      replicas: 4  # Run 4 worker containers

  backend:
    deploy:
      replicas: 2  # Run 2 API containers (behind load balancer)
```

**Load Balancing:**

```yaml
# With Traefik
backend:
  labels:
    - "traefik.enable=true"
    - "traefik.http.services.backend.loadbalancer.server.port=8000"
    - "traefik.http.services.backend.loadbalancer.sticky.cookie=true"
```

### 2. Vertical Scaling

**Resource Allocation:**

```yaml
# docker-compose.yml
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

  celery-worker:
    deploy:
      resources:
        limits:
          cpus: '4.0'   # More CPU for workers
          memory: 8G
        reservations:
          cpus: '2.0'
          memory: 4G
```

### 3. Database Scaling

**Read Replicas:**

```python
# Configure read replica for heavy read workloads
READ_DATABASE_URL = "postgresql+asyncpg://replica:5432/commandcenter"

# Use read replica for analytics queries
read_engine = create_async_engine(READ_DATABASE_URL, pool_size=20)

@router.get("/statistics")
async def get_statistics():
    async with read_engine.begin() as conn:
        result = await conn.execute(select(func.count(Job.id)))
        return {"total_jobs": result.scalar()}
```

**Connection Pooling with PgBouncer:**

```yaml
# docker-compose.yml
pgbouncer:
  image: pgbouncer/pgbouncer:latest
  environment:
    - DATABASES_HOST=postgres
    - DATABASES_PORT=5432
    - DATABASES_USER=commandcenter
    - DATABASES_PASSWORD=${DB_PASSWORD}
    - POOL_MODE=transaction
    - MAX_CLIENT_CONN=1000
    - DEFAULT_POOL_SIZE=25
```

### 4. Caching Layer

**Redis Cluster (High Availability):**

```yaml
# For production with Redis Sentinel
redis-master:
  image: redis:7-alpine
  command: redis-server --appendonly yes

redis-slave:
  image: redis:7-alpine
  command: redis-server --slaveof redis-master 6379

redis-sentinel:
  image: redis:7-alpine
  command: redis-sentinel /etc/redis/sentinel.conf
```

---

## Performance Checklist

### Pre-Deployment

- [ ] Database indexes created for all filtered columns
- [ ] Connection pooling configured (database + Redis)
- [ ] Celery workers scaled appropriately
- [ ] Rate limiting configured for all endpoints
- [ ] Response compression enabled
- [ ] Frontend code splitting implemented
- [ ] Environment variables optimized for production

### Monitoring

- [ ] Prometheus metrics exposed
- [ ] Grafana dashboards configured
- [ ] Alert rules created for critical metrics
- [ ] Log aggregation configured
- [ ] Error tracking enabled (e.g., Sentry)

### Regular Maintenance

- [ ] Weekly database vacuum
- [ ] Monthly full vacuum
- [ ] Archive old jobs (30+ days)
- [ ] Review slow query logs
- [ ] Check Redis memory usage
- [ ] Monitor worker queue lengths

---

## Troubleshooting Performance Issues

### High API Latency

```bash
# 1. Check database connection pool
docker compose logs backend | grep "pool"

# 2. Check for slow queries
docker compose exec postgres psql -U commandcenter -c "
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC LIMIT 5;
"

# 3. Check Redis latency
docker compose exec redis redis-cli --latency

# 4. Profile endpoint
# Use /profile/* endpoints in development
```

### Worker Overload

```bash
# 1. Check active tasks
celery -A app.tasks inspect active

# 2. Check queue lengths
celery -A app.tasks inspect active_queues

# 3. Scale workers
docker compose up -d --scale celery-worker=8

# 4. Review task time limits
# Check for tasks exceeding soft_time_limit
```

### Memory Issues

```bash
# 1. Check container memory
docker stats

# 2. Check Redis memory
docker compose exec redis redis-cli info memory

# 3. Check database cache
docker compose exec postgres psql -U commandcenter -c "
SELECT pg_size_pretty(pg_database_size('commandcenter'));
"

# 4. Identify memory hogs
docker compose exec backend python -m memory_profiler app/main.py
```

---

## Additional Resources

- [FastAPI Performance Tips](https://fastapi.tiangolo.com/deployment/concepts/)
- [Celery Optimization Guide](https://docs.celeryproject.org/en/stable/userguide/optimizing.html)
- [PostgreSQL Performance Tuning](https://wiki.postgresql.org/wiki/Performance_Optimization)
- [Redis Best Practices](https://redis.io/topics/optimization)
- [Prometheus Best Practices](https://prometheus.io/docs/practices/)

---

**Performance Guide Version:** 1.0.0
**Last Updated:** 2025-10-12
**Compatible with:** CommandCenter Phase 2.0
