# DevOps & Infrastructure Review
# CommandCenter Project

**Review Date:** October 5, 2025
**Reviewer:** DevOps & Infrastructure Agent
**Project Version:** 1.0.0

---

## Executive Summary

The CommandCenter project demonstrates a **solid foundation** for containerized deployment with Docker Compose. The infrastructure is well-designed for local development and small-scale deployments with strong emphasis on:

- Multi-stage Docker builds for optimization
- Health checks across all services
- Data persistence through named volumes
- Port conflict detection and management
- Comprehensive documentation for Traefik integration

### Overall Rating: 7.5/10

**Strengths:**
- Excellent multi-stage Dockerfile implementations
- Strong health check coverage
- Well-documented Traefik setup for multi-project environments
- Thoughtful port management with automated conflict detection
- Good separation of concerns between services

**Areas for Improvement:**
- Missing CI/CD automation
- No production-grade logging/monitoring
- Lack of backup automation
- Missing .dockerignore files
- No secrets management solution
- Absence of resource limits and quotas
- Limited security hardening

---

## 1. Infrastructure Overview

### Architecture

```
┌─────────────────────────────────────────────────────┐
│                  Docker Network                      │
│                  (commandcenter)                     │
│                                                      │
│  ┌──────────┐   ┌──────────┐   ┌──────────┐       │
│  │ Frontend │   │ Backend  │   │ Postgres │       │
│  │ (Nginx)  │───│(FastAPI) │───│  (16)    │       │
│  │  :3000   │   │  :8000   │   │  :5432   │       │
│  └──────────┘   └──────────┘   └──────────┘       │
│                       │                              │
│                  ┌──────────┐                       │
│                  │  Redis   │                       │
│                  │  (7)     │                       │
│                  │  :6379   │                       │
│                  └──────────┘                       │
└─────────────────────────────────────────────────────┘

Volumes:
- postgres_data (Database persistence)
- rag_storage (AI/ML embeddings)
- redis_data (Cache persistence)
- ./backend/output (Bind mount for outputs)
```

### Service Dependencies

```yaml
frontend → backend → postgres
                  → redis
```

All dependencies use health check conditions (`condition: service_healthy`), ensuring proper startup order.

---

## 2. Docker Configuration Analysis

### 2.1 Backend Dockerfile (EXCELLENT)

**File:** `/Users/danielconnolly/Projects/CommandCenter/backend/Dockerfile`

**Strengths:**
- Multi-stage build separating builder and runtime
- Alpine-based Python 3.11 for minimal image size
- Non-root user (appuser) for security
- Proper layer caching strategy
- Build-time and runtime dependencies separated
- Health check included

**Issues & Recommendations:**

#### CRITICAL: Missing .dockerignore
```dockerfile
# Create /Users/danielconnolly/Projects/CommandCenter/backend/.dockerignore

__pycache__
*.pyc
*.pyo
*.pyd
.Python
*.so
*.egg
*.egg-info
dist
build
.pytest_cache
.coverage
htmlcov
.tox
.env
.venv
env/
venv/
.git
.gitignore
.dockerignore
.vscode
.idea
*.swp
*.bak
*.log
*.sql
*.sqlite
*.db
tests/
test_*.py
docs/
*.md
```

**Impact:** Without .dockerignore, the build context includes unnecessary files (tests, docs, cache, .git), slowing builds and increasing image size.

#### ISSUE: Python dependencies copied to root user directory

**Current:**
```dockerfile
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH
```

**Problem:** Installing as root user in builder, then copying to runtime. Should install as appuser.

**Recommended Fix:**
```dockerfile
# Build stage
FROM python:3.11-slim AS builder

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Create app user early
RUN useradd -m -u 1000 appuser

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install as appuser
RUN pip install --user --no-cache-dir -r requirements.txt


# Runtime stage
FROM python:3.11-slim AS runtime

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# Create app user
RUN useradd -m -u 1000 appuser

# Install runtime dependencies only
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python dependencies from builder
COPY --from=builder --chown=appuser:appuser /root/.local /home/appuser/.local

# Set PATH for appuser
ENV PATH=/home/appuser/.local/bin:$PATH

WORKDIR /app

# Copy application code
COPY --chown=appuser:appuser . .

# Create necessary directories
RUN mkdir -p /app/logs /app/data /app/rag_storage && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Run migrations and start server
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
```

#### ISSUE: Migrations in CMD may fail silently

**Current:** `CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]`

**Problem:** If migrations fail, the container may still attempt to start the server, leading to database schema mismatches.

**Recommendation:**
```dockerfile
# Create backend/docker-entrypoint.sh
#!/bin/bash
set -e

echo "Running database migrations..."
alembic upgrade head

echo "Starting application server..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
```

```dockerfile
# In Dockerfile
COPY --chown=appuser:appuser docker-entrypoint.sh /app/
RUN chmod +x /app/docker-entrypoint.sh

CMD ["/app/docker-entrypoint.sh"]
```

### 2.2 Frontend Dockerfile (GOOD)

**File:** `/Users/danielconnolly/Projects/CommandCenter/frontend/Dockerfile`

**Strengths:**
- Multi-stage build (builder + nginx)
- Alpine-based Node 20 and Nginx
- Clean separation of build and serve stages

**Issues & Recommendations:**

#### CRITICAL: Missing .dockerignore
```dockerfile
# Create /Users/danielconnolly/Projects/CommandCenter/frontend/.dockerignore

node_modules
npm-debug.log
.npm
.env
.env.local
.env.*.local
dist
build
coverage
.vscode
.idea
*.swp
*.bak
.git
.gitignore
.dockerignore
*.md
.DS_Store
```

#### MISSING: Custom Nginx configuration

**Current:** Using default nginx configuration

**Recommendation:** Create custom nginx.conf for:
- SPA routing (redirect all routes to index.html)
- Gzip compression
- Security headers
- Cache control

```nginx
# Create /Users/danielconnolly/Projects/CommandCenter/frontend/nginx.conf

server {
    listen 80;
    server_name localhost;

    root /usr/share/nginx/html;
    index index.html;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/json;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Cache static assets
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg|woff|woff2|ttf|eot)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # SPA routing - redirect all routes to index.html
    location / {
        try_files $uri $uri/ /index.html;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

```dockerfile
# Update Dockerfile
FROM nginx:alpine

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

#### ISSUE: No non-root user in production stage

**Recommendation:**
```dockerfile
FROM nginx:alpine

# Create nginx user (if not exists)
RUN addgroup -g 101 -S nginx || true && \
    adduser -S -D -H -u 101 -h /var/cache/nginx -s /sbin/nologin -G nginx -g nginx nginx || true

# Copy built files
COPY --from=builder /app/dist /usr/share/nginx/html

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Set permissions
RUN chown -R nginx:nginx /usr/share/nginx/html && \
    chown -R nginx:nginx /var/cache/nginx && \
    chown -R nginx:nginx /var/log/nginx && \
    touch /var/run/nginx.pid && \
    chown -R nginx:nginx /var/run/nginx.pid

USER nginx

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
```

### 2.3 Docker Compose Configuration

**File:** `/Users/danielconnolly/Projects/CommandCenter/docker-compose.yml`

**Overall:** Well-structured with proper networking, volumes, and health checks.

#### Strengths:
1. Named volumes for persistence
2. Health checks on all services
3. Proper dependency ordering with health conditions
4. Environment variable templating
5. Custom network isolation

#### Issues & Recommendations:

##### CRITICAL: No resource limits

**Risk:** Runaway processes could consume all host resources

**Recommendation:**
```yaml
services:
  postgres:
    image: postgres:16-alpine
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 1G
        reservations:
          cpus: '0.25'
          memory: 256M
    # ... rest of config

  redis:
    image: redis:7-alpine
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
        reservations:
          cpus: '0.1'
          memory: 128M

  backend:
    build:
      context: ./backend
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M

  frontend:
    build:
      context: ./frontend
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
        reservations:
          cpus: '0.1'
          memory: 64M
```

##### ISSUE: Database credentials in plain text

**Current:**
```yaml
environment:
  POSTGRES_PASSWORD: ${DB_PASSWORD:-changeme}
```

**Problem:** Default "changeme" password is insecure

**Recommendation:**
```yaml
# Use Docker secrets (for Swarm mode)
secrets:
  db_password:
    file: ./secrets/db_password.txt

services:
  postgres:
    secrets:
      - db_password
    environment:
      POSTGRES_PASSWORD_FILE: /run/secrets/db_password

# For Compose (non-Swarm), enforce .env file:
environment:
  POSTGRES_PASSWORD: ${DB_PASSWORD:?DB_PASSWORD must be set in .env file}
```

##### MISSING: Logging configuration

**Recommendation:**
```yaml
services:
  postgres:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
        labels: "service,environment"
    labels:
      - "service=postgres"
      - "environment=production"

  redis:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"

  backend:
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "5"
        labels: "service,environment"
    labels:
      - "service=backend"
      - "environment=production"

  frontend:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

##### ISSUE: Bind mount security risk

**Current:**
```yaml
volumes:
  - ./backend/output:/app/output
```

**Problem:** Bind mounts can expose host filesystem

**Recommendation:**
```yaml
# Use named volumes instead
volumes:
  backend_output:
    driver: local

services:
  backend:
    volumes:
      - backend_output:/app/output
      # Only use bind mounts in development override
```

##### MISSING: Restart policies

**Recommendation:**
```yaml
services:
  postgres:
    restart: unless-stopped

  redis:
    restart: unless-stopped

  backend:
    restart: unless-stopped

  frontend:
    restart: unless-stopped
```

##### IMPROVEMENT: Network mode for better isolation

**Current:** All services on same bridge network

**Recommendation:** Create separate networks for frontend-backend and backend-data layers:

```yaml
networks:
  frontend_network:
    driver: bridge
  backend_network:
    driver: bridge

services:
  postgres:
    networks:
      - backend_network

  redis:
    networks:
      - backend_network

  backend:
    networks:
      - frontend_network
      - backend_network

  frontend:
    networks:
      - frontend_network
```

This prevents frontend from directly accessing database.

---

## 3. Service Orchestration Review

### 3.1 Health Checks (EXCELLENT)

All services have appropriate health checks:

```yaml
postgres:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U commandcenter"]
    interval: 10s
    timeout: 5s
    retries: 5

redis:
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 10s
    timeout: 5s
    retries: 5

backend:
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
    start_period: 40s  # Good: allows time for migrations

frontend:
  healthcheck:
    test: ["CMD", "wget", "--no-verbose", "--tries=1", "--spider", "http://localhost:80"]
    interval: 30s
    timeout: 10s
    retries: 3
```

**Recommendation:** Add health check endpoints with more detail:

```python
# In backend/app/main.py
from fastapi import status
from sqlalchemy import text

@app.get("/health", tags=["health"])
async def health_check() -> JSONResponse:
    """Comprehensive health check"""
    health_status = {
        "status": "healthy",
        "app": settings.app_name,
        "version": settings.app_version,
        "checks": {}
    }

    # Check database
    try:
        async with database.session() as session:
            await session.execute(text("SELECT 1"))
        health_status["checks"]["database"] = "healthy"
    except Exception as e:
        health_status["checks"]["database"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    # Check Redis
    try:
        # Add Redis ping check
        health_status["checks"]["redis"] = "healthy"
    except Exception as e:
        health_status["checks"]["redis"] = f"unhealthy: {str(e)}"
        health_status["status"] = "degraded"

    status_code = 200 if health_status["status"] == "healthy" else 503

    return JSONResponse(
        content=health_status,
        status_code=status_code
    )
```

### 3.2 Dependency Management (GOOD)

Using `depends_on` with `condition: service_healthy` is the correct approach.

**Recommendation:** Add graceful shutdown handling:

```python
# In backend/app/main.py
import signal
import sys

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully"""
    print(f"Received signal {signum}, shutting down gracefully...")
    sys.exit(0)

signal.signal(signal.SIGTERM, signal_handler)
signal.signal(signal.SIGINT, signal_handler)
```

### 3.3 Volume Management (GOOD)

Named volumes used for all persistent data:
- `postgres_data` - Database
- `redis_data` - Cache
- `rag_storage` - AI embeddings

**Recommendation:** Add volume backup configurations:

```yaml
volumes:
  postgres_data:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/lib/commandcenter/postgres

  rag_storage:
    driver: local
    driver_opts:
      type: none
      o: bind
      device: /var/lib/commandcenter/rag_storage
```

---

## 4. Security Configuration

### Current Security Posture: 6/10

#### Implemented:
- Non-root users in Docker containers
- Health checks
- Network isolation
- Alpine-based images (smaller attack surface)

#### Missing:

##### 1. Secret Management

**Issue:** Secrets in environment variables

**Recommendation:** Use Docker secrets or external secret management:

```yaml
# Option 1: Docker Secrets (Swarm mode)
secrets:
  db_password:
    external: true
  secret_key:
    external: true
  anthropic_api_key:
    external: true

services:
  backend:
    secrets:
      - db_password
      - secret_key
      - anthropic_api_key
    environment:
      DATABASE_URL: postgresql://commandcenter@postgres:5432/commandcenter
      # Use _FILE suffix for secret files
      DB_PASSWORD_FILE: /run/secrets/db_password
      SECRET_KEY_FILE: /run/secrets/secret_key
```

```bash
# Create secrets
echo "secure_db_password" | docker secret create db_password -
echo "$(openssl rand -hex 32)" | docker secret create secret_key -
echo "sk-ant-..." | docker secret create anthropic_api_key -
```

```python
# Update backend config to read from files
import os

def read_secret(secret_name: str, default: str = None) -> str:
    """Read secret from file or environment variable"""
    secret_file = os.getenv(f"{secret_name}_FILE")
    if secret_file and os.path.exists(secret_file):
        with open(secret_file) as f:
            return f.read().strip()
    return os.getenv(secret_name, default)

class Settings(BaseSettings):
    SECRET_KEY: str = Field(default_factory=lambda: read_secret("SECRET_KEY", "dev-key"))
```

**Option 2:** Use HashiCorp Vault, AWS Secrets Manager, or Azure Key Vault

##### 2. Image Scanning

**Recommendation:** Add Trivy scanning to Makefile:

```makefile
# Add to Makefile
security-scan: ## Scan Docker images for vulnerabilities
	@echo "Scanning images for vulnerabilities..."
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image commandcenter_backend:latest
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image commandcenter_frontend:latest

security-scan-critical: ## Scan for critical vulnerabilities only
	@docker run --rm -v /var/run/docker.sock:/var/run/docker.sock \
		aquasec/trivy image --severity CRITICAL,HIGH commandcenter_backend:latest
```

##### 3. Network Security

**Recommendation:** Disable inter-container communication:

```yaml
networks:
  commandcenter:
    driver: bridge
    driver_opts:
      com.docker.network.bridge.enable_icc: "false"
```

##### 4. Read-only Filesystem

**Recommendation:** Make containers read-only where possible:

```yaml
services:
  frontend:
    read_only: true
    tmpfs:
      - /tmp
      - /var/cache/nginx
      - /var/run
```

##### 5. Security Headers

Already recommended in Nginx configuration above. Additionally:

```python
# In backend/app/main.py
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware

# Add security middleware
app.add_middleware(TrustedHostMiddleware, allowed_hosts=["localhost", "*.localhost"])

# Add security headers
@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    return response
```

---

## 5. Performance Optimization

### Current State: 7/10

#### Implemented:
- Multi-stage builds
- Layer caching
- Alpine images
- Health checks

#### Recommendations:

##### 1. Build Cache Optimization

**Backend Dockerfile:**
```dockerfile
# Optimize layer caching by copying requirements first
FROM python:3.11-slim AS builder

WORKDIR /app

# Copy only requirements first (cached if requirements.txt unchanged)
COPY requirements.txt .
RUN pip install --user --no-cache-dir -r requirements.txt

# Copy source code last (changes frequently)
COPY . .
```

##### 2. Enable BuildKit

**Recommendation:**
```bash
# Add to .env.template
DOCKER_BUILDKIT=1
COMPOSE_DOCKER_CLI_BUILD=1
```

```makefile
# Update Makefile
build: ## Rebuild all containers
	DOCKER_BUILDKIT=1 docker-compose build --parallel
```

##### 3. Image Size Reduction

**Current backend image:** ~300-400MB (estimated)
**Target:** <200MB

**Optimization:**
```dockerfile
# Use slim-bullseye instead of alpine for better compatibility
FROM python:3.11-slim-bullseye AS builder

# Install only required dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get purge -y --auto-remove

# Multi-stage copy only .so files needed
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
```

##### 4. Database Connection Pooling

**Add to backend requirements.txt:**
```txt
sqlalchemy[asyncio]==2.0.25
asyncpg==0.29.0  # Faster than psycopg2
```

**Update database configuration:**
```python
# In app/database.py
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.pool import NullPool, QueuePool

engine = create_async_engine(
    settings.database_url,
    poolclass=QueuePool,
    pool_size=20,          # Connections to keep open
    max_overflow=10,       # Additional connections when pool exhausted
    pool_pre_ping=True,    # Verify connections before using
    pool_recycle=3600,     # Recycle connections after 1 hour
    echo=settings.debug,
)
```

##### 5. Redis Configuration

**Recommendation:**
```yaml
services:
  redis:
    image: redis:7-alpine
    command: >
      redis-server
      --maxmemory 256mb
      --maxmemory-policy allkeys-lru
      --save 60 1000
      --appendonly yes
      --tcp-backlog 511
```

##### 6. Frontend Asset Optimization

**Add to frontend build:**
```json
// package.json
{
  "scripts": {
    "build": "vite build --mode production",
    "build:analyze": "vite build --mode production && vite-bundle-visualizer"
  }
}
```

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          'vendor': ['react', 'react-dom', 'react-router-dom'],
          'charts': ['chart.js', 'react-chartjs-2'],
        }
      }
    },
    chunkSizeWarningLimit: 1000,
    minify: 'terser',
    terserOptions: {
      compress: {
        drop_console: true,
        drop_debugger: true
      }
    }
  }
})
```

---

## 6. Monitoring & Logging

### Current State: 3/10 (NEEDS IMPROVEMENT)

**Issues:**
- No centralized logging
- No metrics collection
- No alerting
- Basic health checks only
- No distributed tracing

### Recommendations:

#### 6.1 Logging Stack (ELK/Loki)

**Option A: Loki (Lightweight)**

Create `docker-compose.monitoring.yml`:

```yaml
version: '3.8'

services:
  loki:
    image: grafana/loki:2.9.0
    ports:
      - "3100:3100"
    volumes:
      - loki_data:/loki
      - ./monitoring/loki-config.yml:/etc/loki/local-config.yaml
    command: -config.file=/etc/loki/local-config.yaml
    networks:
      - commandcenter

  promtail:
    image: grafana/promtail:2.9.0
    volumes:
      - /var/log:/var/log
      - /var/lib/docker/containers:/var/lib/docker/containers:ro
      - /var/run/docker.sock:/var/run/docker.sock
      - ./monitoring/promtail-config.yml:/etc/promtail/config.yml
    command: -config.file=/etc/promtail/config.yml
    networks:
      - commandcenter

  grafana:
    image: grafana/grafana:10.0.0
    ports:
      - "3001:3000"
    environment:
      - GF_SECURITY_ADMIN_USER=admin
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD:-admin}
      - GF_USERS_ALLOW_SIGN_UP=false
    volumes:
      - grafana_data:/var/lib/grafana
      - ./monitoring/grafana-datasources.yml:/etc/grafana/provisioning/datasources/datasources.yml
    networks:
      - commandcenter

volumes:
  loki_data:
  grafana_data:

networks:
  commandcenter:
    external: true
```

**Loki Config** (`monitoring/loki-config.yml`):
```yaml
auth_enabled: false

server:
  http_listen_port: 3100

ingester:
  lifecycler:
    address: 127.0.0.1
    ring:
      kvstore:
        store: inmemory
      replication_factor: 1
    final_sleep: 0s
  chunk_idle_period: 5m
  chunk_retain_period: 30s

schema_config:
  configs:
    - from: 2020-05-15
      store: boltdb
      object_store: filesystem
      schema: v11
      index:
        prefix: index_
        period: 168h

storage_config:
  boltdb:
    directory: /loki/index
  filesystem:
    directory: /loki/chunks

limits_config:
  enforce_metric_name: false
  reject_old_samples: true
  reject_old_samples_max_age: 168h

chunk_store_config:
  max_look_back_period: 0s

table_manager:
  retention_deletes_enabled: false
  retention_period: 0s
```

**Promtail Config** (`monitoring/promtail-config.yml`):
```yaml
server:
  http_listen_port: 9080
  grpc_listen_port: 0

positions:
  filename: /tmp/positions.yaml

clients:
  - url: http://loki:3100/loki/api/v1/push

scrape_configs:
  - job_name: docker
    docker_sd_configs:
      - host: unix:///var/run/docker.sock
        refresh_interval: 5s
    relabel_configs:
      - source_labels: ['__meta_docker_container_name']
        regex: '/(.*)'
        target_label: 'container'
      - source_labels: ['__meta_docker_container_log_stream']
        target_label: 'logstream'
      - source_labels: ['__meta_docker_container_label_com_docker_compose_service']
        target_label: 'service'
```

**Usage:**
```bash
# Start monitoring stack
docker-compose -f docker-compose.yml -f docker-compose.monitoring.yml up -d

# Access Grafana: http://localhost:3001
# Add Loki datasource: http://loki:3100
```

#### 6.2 Metrics Collection (Prometheus)

**Add to `docker-compose.monitoring.yml`:**

```yaml
services:
  prometheus:
    image: prom/prometheus:v2.45.0
    ports:
      - "9090:9090"
    volumes:
      - prometheus_data:/prometheus
      - ./monitoring/prometheus.yml:/etc/prometheus/prometheus.yml
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--storage.tsdb.retention.time=30d'
    networks:
      - commandcenter

  node-exporter:
    image: prom/node-exporter:v1.6.0
    ports:
      - "9100:9100"
    command:
      - '--path.rootfs=/host'
    volumes:
      - /:/host:ro,rslave
    networks:
      - commandcenter

  cadvisor:
    image: gcr.io/cadvisor/cadvisor:v0.47.0
    ports:
      - "8080:8080"
    volumes:
      - /:/rootfs:ro
      - /var/run:/var/run:ro
      - /sys:/sys:ro
      - /var/lib/docker/:/var/lib/docker:ro
      - /dev/disk/:/dev/disk:ro
    privileged: true
    networks:
      - commandcenter

volumes:
  prometheus_data:
```

**Prometheus Config** (`monitoring/prometheus.yml`):
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

scrape_configs:
  # Prometheus self-monitoring
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  # Node exporter (host metrics)
  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  # cAdvisor (container metrics)
  - job_name: 'cadvisor'
    static_configs:
      - targets: ['cadvisor:8080']

  # Backend application metrics
  - job_name: 'backend'
    static_configs:
      - targets: ['backend:8000']
    metrics_path: '/metrics'

  # PostgreSQL metrics
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']

  # Redis metrics
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
```

#### 6.3 Application Instrumentation

**Add to backend requirements.txt:**
```txt
prometheus-fastapi-instrumentator==6.1.0
opentelemetry-api==1.20.0
opentelemetry-sdk==1.20.0
opentelemetry-instrumentation-fastapi==0.41b0
```

**Update backend/app/main.py:**
```python
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(...)

# Add Prometheus metrics
Instrumentator().instrument(app).expose(app)

# Metrics will be available at /metrics
```

#### 6.4 Structured Logging

**Add to backend requirements.txt:**
```txt
python-json-logger==2.0.7
```

**Create logging configuration:**
```python
# backend/app/logging_config.py
import logging
import sys
from pythonjsonlogger import jsonlogger

def setup_logging():
    """Configure structured JSON logging"""
    logger = logging.getLogger()

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s',
        rename_fields={"levelname": "level", "asctime": "timestamp"}
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)

    return logger

# In main.py
from app.logging_config import setup_logging

logger = setup_logging()

@app.middleware("http")
async def log_requests(request, call_next):
    logger.info("request_started", extra={
        "method": request.method,
        "url": str(request.url),
        "client": request.client.host
    })

    response = await call_next(request)

    logger.info("request_completed", extra={
        "method": request.method,
        "url": str(request.url),
        "status_code": response.status_code
    })

    return response
```

#### 6.5 Alerting

**Add to `monitoring/prometheus.yml`:**
```yaml
rule_files:
  - 'alerts.yml'

alerting:
  alertmanagers:
    - static_configs:
        - targets: ['alertmanager:9093']
```

**Create `monitoring/alerts.yml`:**
```yaml
groups:
  - name: commandcenter_alerts
    interval: 30s
    rules:
      # Container down
      - alert: ContainerDown
        expr: up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Container {{ $labels.job }} is down"

      # High CPU usage
      - alert: HighCPUUsage
        expr: rate(container_cpu_usage_seconds_total[5m]) > 0.8
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High CPU usage on {{ $labels.name }}"

      # High memory usage
      - alert: HighMemoryUsage
        expr: (container_memory_usage_bytes / container_spec_memory_limit_bytes) > 0.9
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High memory usage on {{ $labels.name }}"

      # Database connection issues
      - alert: DatabaseConnectionFailed
        expr: pg_up == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "Cannot connect to PostgreSQL"
```

---

## 7. Backup & Disaster Recovery

### Current State: 5/10

**Implemented:**
- Manual database backup/restore in Makefile

**Missing:**
- Automated backups
- Backup verification
- Point-in-time recovery
- Volume snapshots

### Recommendations:

#### 7.1 Automated Backup Service

**Create `scripts/backup.sh`:**
```bash
#!/bin/bash
set -e

BACKUP_DIR="/var/backups/commandcenter"
RETENTION_DAYS=30
DATE=$(date +%Y%m%d-%H%M%S)

echo "Starting backup at $(date)"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Backup PostgreSQL
echo "Backing up PostgreSQL..."
docker-compose exec -T postgres pg_dump -U commandcenter -Fc commandcenter > \
    "$BACKUP_DIR/postgres-$DATE.dump"

# Backup volumes
echo "Backing up RAG storage..."
docker run --rm \
    -v commandcenter_rag_storage:/data \
    -v "$BACKUP_DIR":/backup \
    alpine tar czf "/backup/rag-storage-$DATE.tar.gz" -C /data .

# Backup Redis (if needed)
echo "Backing up Redis..."
docker-compose exec -T redis redis-cli BGSAVE
sleep 5
docker cp commandcenter_redis:/data/dump.rdb "$BACKUP_DIR/redis-$DATE.rdb"

# Cleanup old backups
echo "Cleaning up old backups..."
find "$BACKUP_DIR" -name "*.dump" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +$RETENTION_DAYS -delete
find "$BACKUP_DIR" -name "*.rdb" -mtime +$RETENTION_DAYS -delete

# Verify backup
echo "Verifying PostgreSQL backup..."
if pg_restore --list "$BACKUP_DIR/postgres-$DATE.dump" > /dev/null 2>&1; then
    echo "PostgreSQL backup verified successfully"
else
    echo "ERROR: PostgreSQL backup verification failed!"
    exit 1
fi

echo "Backup completed at $(date)"
```

**Create `scripts/restore.sh`:**
```bash
#!/bin/bash
set -e

if [ -z "$1" ]; then
    echo "Usage: $0 <backup-date>"
    echo "Example: $0 20241005-143000"
    exit 1
fi

BACKUP_DATE=$1
BACKUP_DIR="/var/backups/commandcenter"

echo "Restoring from backup: $BACKUP_DATE"

# Stop services
docker-compose stop backend frontend

# Restore PostgreSQL
echo "Restoring PostgreSQL..."
docker-compose exec -T postgres dropdb -U commandcenter commandcenter --if-exists
docker-compose exec -T postgres createdb -U commandcenter commandcenter
docker-compose exec -T postgres pg_restore -U commandcenter -d commandcenter < \
    "$BACKUP_DIR/postgres-$BACKUP_DATE.dump"

# Restore RAG storage
echo "Restoring RAG storage..."
docker run --rm \
    -v commandcenter_rag_storage:/data \
    -v "$BACKUP_DIR":/backup \
    alpine sh -c "rm -rf /data/* && tar xzf /backup/rag-storage-$BACKUP_DATE.tar.gz -C /data"

# Restore Redis
echo "Restoring Redis..."
docker-compose stop redis
docker cp "$BACKUP_DIR/redis-$BACKUP_DATE.rdb" commandcenter_redis:/data/dump.rdb
docker-compose start redis

# Start services
docker-compose start backend frontend

echo "Restore completed successfully"
```

**Add to Makefile:**
```makefile
backup-auto: ## Setup automated backups (cron)
	@echo "Setting up automated backups..."
	@chmod +x scripts/backup.sh
	@chmod +x scripts/restore.sh
	@(crontab -l 2>/dev/null; echo "0 2 * * * /path/to/commandcenter/scripts/backup.sh >> /var/log/commandcenter-backup.log 2>&1") | crontab -
	@echo "✅ Automated backups configured (daily at 2 AM)"

restore-backup: ## Restore from backup (provide DATE variable)
	@if [ -z "$(DATE)" ]; then \
		echo "Usage: make restore-backup DATE=20241005-143000"; \
		echo "Available backups:"; \
		ls -1 /var/backups/commandcenter/*.dump | xargs basename -s .dump; \
		exit 1; \
	fi
	@./scripts/restore.sh $(DATE)
```

#### 7.2 Volume Snapshots

**Using rsync for incremental backups:**
```bash
#!/bin/bash
# scripts/snapshot.sh

SNAPSHOT_DIR="/var/snapshots/commandcenter"
DATE=$(date +%Y%m%d-%H%M%S)

# Create snapshot directory
mkdir -p "$SNAPSHOT_DIR/$DATE"

# Rsync volumes with hard links (space-efficient)
docker run --rm \
    -v commandcenter_postgres_data:/source/postgres:ro \
    -v commandcenter_rag_storage:/source/rag:ro \
    -v "$SNAPSHOT_DIR":/backup \
    alpine rsync -avz --link-dest=/backup/latest \
        /source/ "/backup/$DATE/"

# Update latest symlink
ln -snf "$DATE" "$SNAPSHOT_DIR/latest"

echo "Snapshot created: $DATE"
```

#### 7.3 Disaster Recovery Plan

**Create `docs/DISASTER_RECOVERY.md`:**
```markdown
# Disaster Recovery Plan

## Recovery Time Objective (RTO): 30 minutes
## Recovery Point Objective (RPO): 24 hours

### Scenarios

#### 1. Database Corruption
**Detection:** Health check failures, error logs
**Recovery:**
```bash
make restore-backup DATE=20241005-020000
```

#### 2. Complete System Failure
**Recovery:**
1. Provision new server
2. Install Docker and Docker Compose
3. Clone repository
4. Restore volumes from backup
5. Start services

#### 3. Data Center Failure
**Requirement:** Off-site backup replication
**Solution:** S3 backup sync (see below)
```

#### 7.4 Off-site Backups (S3)

**Add to `scripts/backup.sh`:**
```bash
# S3 sync (requires AWS CLI)
if [ -n "$S3_BACKUP_BUCKET" ]; then
    echo "Syncing to S3..."
    aws s3 sync "$BACKUP_DIR" "s3://$S3_BACKUP_BUCKET/commandcenter/" \
        --storage-class GLACIER_IR \
        --exclude "*" --include "*.dump" --include "*.tar.gz"
fi
```

---

## 8. CI/CD Configuration

### Current State: 0/10 (NOT IMPLEMENTED)

**Critical Gap:** No automated testing, building, or deployment

### Recommendations:

#### 8.1 GitHub Actions Workflow

**Create `.github/workflows/ci.yml`:**

```yaml
name: CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

env:
  REGISTRY: ghcr.io
  IMAGE_NAME: ${{ github.repository }}

jobs:
  lint-and-test:
    name: Lint and Test
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
          cache: 'pip'

      - name: Install dependencies
        working-directory: ./backend
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov black flake8

      - name: Lint with flake8
        working-directory: ./backend
        run: flake8 app/ --max-line-length=100

      - name: Format check with black
        working-directory: ./backend
        run: black --check app/

      - name: Run tests
        working-directory: ./backend
        run: pytest --cov=app --cov-report=xml

      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./backend/coverage.xml
          flags: backend

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
          cache-dependency-path: ./frontend/package-lock.json

      - name: Install frontend dependencies
        working-directory: ./frontend
        run: npm ci

      - name: Lint frontend
        working-directory: ./frontend
        run: npm run lint

      - name: Type check
        working-directory: ./frontend
        run: npm run type-check

      - name: Test frontend
        working-directory: ./frontend
        run: npm test

  security-scan:
    name: Security Scan
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v4

      - name: Run Trivy vulnerability scanner
        uses: aquasecurity/trivy-action@master
        with:
          scan-type: 'fs'
          scan-ref: '.'
          format: 'sarif'
          output: 'trivy-results.sarif'

      - name: Upload Trivy results to GitHub Security
        uses: github/codeql-action/upload-sarif@v2
        with:
          sarif_file: 'trivy-results.sarif'

      - name: Check for secrets
        uses: trufflesecurity/trufflehog@main
        with:
          path: ./
          base: ${{ github.event.repository.default_branch }}
          head: HEAD

  build-and-push:
    name: Build and Push Images
    needs: [lint-and-test, security-scan]
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'

    permissions:
      contents: read
      packages: write

    strategy:
      matrix:
        service: [backend, frontend]

    steps:
      - uses: actions/checkout@v4

      - name: Set up Docker Buildx
        uses: docker/setup-buildx-action@v3

      - name: Log in to Container Registry
        uses: docker/login-action@v3
        with:
          registry: ${{ env.REGISTRY }}
          username: ${{ github.actor }}
          password: ${{ secrets.GITHUB_TOKEN }}

      - name: Extract metadata
        id: meta
        uses: docker/metadata-action@v5
        with:
          images: ${{ env.REGISTRY }}/${{ env.IMAGE_NAME }}/${{ matrix.service }}
          tags: |
            type=ref,event=branch
            type=ref,event=pr
            type=semver,pattern={{version}}
            type=semver,pattern={{major}}.{{minor}}
            type=sha,prefix={{branch}}-

      - name: Build and push
        uses: docker/build-push-action@v5
        with:
          context: ./${{ matrix.service }}
          push: true
          tags: ${{ steps.meta.outputs.tags }}
          labels: ${{ steps.meta.outputs.labels }}
          cache-from: type=gha
          cache-to: type=gha,mode=max
          platforms: linux/amd64,linux/arm64

  deploy-staging:
    name: Deploy to Staging
    needs: build-and-push
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'

    steps:
      - uses: actions/checkout@v4

      - name: Deploy to staging server
        uses: appleboy/ssh-action@master
        with:
          host: ${{ secrets.STAGING_HOST }}
          username: ${{ secrets.STAGING_USER }}
          key: ${{ secrets.STAGING_SSH_KEY }}
          script: |
            cd /opt/commandcenter
            git pull origin main
            docker-compose pull
            docker-compose up -d
            docker-compose exec -T backend alembic upgrade head
```

#### 8.2 Pre-commit Hooks

**Create `.pre-commit-config.yaml`:**
```yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: detect-private-key

  - repo: https://github.com/psf/black
    rev: 23.11.0
    hooks:
      - id: black
        language_version: python3.11
        files: ^backend/

  - repo: https://github.com/pycqa/flake8
    rev: 6.1.0
    hooks:
      - id: flake8
        files: ^backend/
        args: ['--max-line-length=100']

  - repo: https://github.com/pre-commit/mirrors-eslint
    rev: v8.55.0
    hooks:
      - id: eslint
        files: ^frontend/.*\.[jt]sx?$
        types: [file]
```

**Installation:**
```bash
# Add to Makefile
setup-hooks: ## Install pre-commit hooks
	pip install pre-commit
	pre-commit install
	@echo "✅ Pre-commit hooks installed"

run-hooks: ## Run pre-commit hooks manually
	pre-commit run --all-files
```

#### 8.3 Docker Compose Override for CI

**Create `docker-compose.ci.yml`:**
```yaml
version: '3.8'

services:
  postgres:
    environment:
      POSTGRES_PASSWORD: testpassword
    tmpfs:
      - /var/lib/postgresql/data  # Use tmpfs for faster tests

  redis:
    tmpfs:
      - /data

  backend:
    environment:
      DATABASE_URL: postgresql://commandcenter:testpassword@postgres:5432/commandcenter_test
      SECRET_KEY: test-secret-key
      DEBUG: true
    command: ["pytest", "-v", "--cov=app"]

  frontend:
    command: ["npm", "test", "--", "--coverage"]
```

---

## 9. Production Deployment Best Practices

### 9.1 Production Compose File

**Create `docker-compose.prod.yml`:**
```yaml
version: '3.8'

services:
  postgres:
    restart: always
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"
    # Use external managed database in production
    # This is just for reference

  redis:
    restart: always
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --maxmemory 512mb
      --maxmemory-policy allkeys-lru
      --save 900 1
      --save 300 10
      --save 60 10000
      --appendonly yes
    deploy:
      resources:
        limits:
          cpus: '1.0'
          memory: 768M

  backend:
    restart: always
    environment:
      DEBUG: false
      LOG_LEVEL: WARNING
    deploy:
      replicas: 2  # Multiple instances for high availability
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '0.5'
          memory: 512M
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
    logging:
      driver: "json-file"
      options:
        max-size: "50m"
        max-file: "10"

  frontend:
    restart: always
    deploy:
      replicas: 2
      resources:
        limits:
          cpus: '0.5'
          memory: 256M
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "5"

  # Add nginx reverse proxy for SSL/load balancing
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf:ro
      - ./nginx/ssl:/etc/nginx/ssl:ro
      - nginx_cache:/var/cache/nginx
    depends_on:
      - backend
      - frontend
    restart: always

volumes:
  nginx_cache:
```

### 9.2 Production Nginx Configuration

**Create `nginx/nginx.conf`:**
```nginx
upstream backend {
    least_conn;
    server backend:8000 max_fails=3 fail_timeout=30s;
}

upstream frontend {
    least_conn;
    server frontend:80 max_fails=3 fail_timeout=30s;
}

# Rate limiting
limit_req_zone $binary_remote_addr zone=api_limit:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=general_limit:10m rate=50r/s;

server {
    listen 80;
    server_name commandcenter.yourdomain.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name commandcenter.yourdomain.com;

    # SSL configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # API endpoints
    location /api/ {
        limit_req zone=api_limit burst=20 nodelay;

        proxy_pass http://backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Frontend
    location / {
        limit_req zone=general_limit burst=100 nodelay;

        proxy_pass http://frontend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Caching
        proxy_cache_bypass $http_pragma $http_authorization;
        proxy_no_cache $http_pragma $http_authorization;
    }

    # Health check (no rate limit)
    location /health {
        access_log off;
        proxy_pass http://backend/health;
    }
}
```

### 9.3 Environment Management

**Create separate .env files:**
```bash
# .env.production (never commit!)
COMPOSE_PROJECT_NAME=commandcenter-prod
DB_PASSWORD=<strong-random-password>
SECRET_KEY=<generated-with-openssl-rand-hex-32>
REDIS_PASSWORD=<strong-random-password>
ANTHROPIC_API_KEY=<actual-key>
OPENAI_API_KEY=<actual-key>
GITHUB_TOKEN=<actual-token>
DEBUG=false
```

**Add to Makefile:**
```makefile
deploy-prod: ## Deploy to production (use with caution)
	@if [ ! -f .env.production ]; then \
		echo "❌ .env.production not found"; \
		exit 1; \
	fi
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d
	@echo "✅ Production deployment complete"

deploy-prod-update: ## Update production deployment
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production pull
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml --env-file .env.production up -d --no-deps --build backend frontend
	@echo "✅ Production updated"
```

---

## 10. Specific Improvements Summary

### Priority 1 (Critical - Implement Immediately)

1. **Add .dockerignore files**
   - Backend: `/Users/danielconnolly/Projects/CommandCenter/backend/.dockerignore`
   - Frontend: `/Users/danielconnolly/Projects/CommandCenter/frontend/.dockerignore`

2. **Add resource limits to docker-compose.yml**
   ```yaml
   deploy:
     resources:
       limits:
         cpus: '1.0'
         memory: 1G
   ```

3. **Implement secrets management**
   - Remove default passwords
   - Use Docker secrets or environment validation

4. **Add restart policies**
   ```yaml
   restart: unless-stopped
   ```

5. **Setup CI/CD pipeline**
   - Create `.github/workflows/ci.yml`
   - Add automated testing and security scanning

### Priority 2 (High - Implement This Week)

6. **Add custom Nginx configuration**
   - Create `/Users/danielconnolly/Projects/CommandCenter/frontend/nginx.conf`
   - Add security headers and SPA routing

7. **Implement logging stack**
   - Add Loki/Promtail/Grafana
   - Configure structured logging in backend

8. **Add monitoring**
   - Prometheus + Grafana
   - Application metrics instrumentation

9. **Implement automated backups**
   - Create `scripts/backup.sh`
   - Setup cron job

10. **Add security scanning**
    - Trivy for image scanning
    - Dependency vulnerability checks

### Priority 3 (Medium - Implement This Month)

11. **Fix Dockerfile user permissions**
    - Install dependencies as appuser
    - Proper ownership in runtime stage

12. **Add production compose override**
    - Create `docker-compose.prod.yml`
    - Multiple replicas, proper limits

13. **Implement health check improvements**
    - Database connectivity check
    - Redis connectivity check
    - Detailed health status

14. **Add network segmentation**
    - Separate frontend and backend networks
    - Prevent direct DB access from frontend

15. **Create disaster recovery documentation**
    - RTO/RPO definition
    - Recovery procedures

### Priority 4 (Low - Nice to Have)

16. **Add distributed tracing**
    - OpenTelemetry instrumentation
    - Jaeger for trace visualization

17. **Implement blue-green deployment**
    - Zero-downtime deployments
    - Rollback capability

18. **Add performance testing**
    - Locust or K6 for load testing
    - CI integration

19. **Create development docker-compose override**
    - Hot reload
    - Debug ports

20. **Add database connection pooling optimization**
    - Tune pool sizes
    - Connection lifecycle management

---

## 11. Conclusion

The CommandCenter project has a **solid foundation** for Docker-based deployment but requires significant enhancements for production readiness:

### Strengths to Maintain:
- Multi-stage builds
- Health check coverage
- Volume persistence
- Port management strategy
- Comprehensive documentation

### Critical Gaps to Address:
1. **CI/CD:** No automation whatsoever
2. **Monitoring:** No observability stack
3. **Security:** Missing secrets management, scanning
4. **Backups:** Manual only, no automation
5. **Production Config:** No production-specific configuration

### Recommended Timeline:

**Week 1:** Priority 1 items (Security & Stability)
- .dockerignore files
- Resource limits
- Secrets management
- Restart policies
- Basic CI/CD

**Week 2:** Priority 2 items (Observability)
- Logging stack
- Monitoring setup
- Automated backups

**Week 3-4:** Priority 3 items (Production Readiness)
- Production configurations
- Network segmentation
- DR documentation

**Ongoing:** Priority 4 items as needed

### Next Steps:

1. Review this document with the team
2. Create GitHub issues for each priority 1 item
3. Assign owners and deadlines
4. Implement changes incrementally
5. Test thoroughly in staging before production

---

**Document Version:** 1.0
**Last Updated:** October 5, 2025
**Reviewed By:** DevOps & Infrastructure Agent
