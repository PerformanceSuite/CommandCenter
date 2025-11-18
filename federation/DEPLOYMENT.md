# Federation Service - Production Deployment Guide

## Overview

The Federation Service provides centralized orchestration for multiple CommandCenter instances across different projects. It handles:

- **Project Catalog**: Registry of all CommandCenter instances
- **Heartbeat Monitoring**: Real-time health tracking via NATS
- **Cross-Project Intelligence**: Federation and ecosystem awareness
- **Prometheus Metrics**: Production-grade observability
- **Grafana Dashboards**: Real-time visualization

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Federation Service                        │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌───────────┐  ┌──────────┐  │
│  │ FastAPI  │  │PostgreSQL│  │   NATS    │  │Prometheus│  │
│  │  :8001   │─▶│  :5433   │  │   :4223   │◀─│  :9091   │  │
│  └──────────┘  └──────────┘  └───────────┘  └──────────┘  │
│       │                            │              │         │
│       └────────────────────────────┴──────────────┘         │
│                                           │                 │
│                                     ┌──────────┐            │
│                                     │ Grafana  │            │
│                                     │  :3001   │            │
│                                     └──────────┘            │
└─────────────────────────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼───┐  ┌────▼───┐  ┌────▼───┐
   │ Hub 1  │  │ Hub 2  │  │ Hub 3  │
   │Heartbeat│ │Heartbeat│ │Heartbeat│
   └────────┘  └────────┘  └────────┘
```

## Quick Start

### 1. Prerequisites

```bash
# Required
- Docker 20.10+ with Compose V2
- 4GB RAM minimum
- Ports available: 5433, 4223, 8223, 8001, 9091, 3001

# Optional (for development)
- Python 3.11+
- PostgreSQL client (psql)
- NATS CLI (nats)
```

### 2. Initial Setup

```bash
# Navigate to federation directory
cd federation/

# Copy production environment template
cp .env.production .env

# Generate secure credentials
python -c "import secrets; print('DB_PASSWORD=' + secrets.token_urlsafe(32))" >> .env
python -c "import secrets; print('GRAFANA_PASSWORD=' + secrets.token_urlsafe(16))" >> .env

# Generate API keys (at least 2 for key rotation)
python -c "import secrets; print('API_KEY_1=' + secrets.token_urlsafe(32))"
python -c "import secrets; print('API_KEY_2=' + secrets.token_urlsafe(32))"

# Edit .env and add API keys to FEDERATION_API_KEYS
# Format: FEDERATION_API_KEYS=["key1","key2"]
nano .env
```

### 3. Deploy Services

```bash
# Start all services (postgres, nats, federation, prometheus, grafana)
docker-compose up -d

# View logs
docker-compose logs -f federation

# Check service health
docker-compose ps
curl http://localhost:8001/health
curl http://localhost:8001/health/nats
```

### 4. Run Database Migrations

```bash
# Apply Alembic migrations
docker-compose exec federation alembic upgrade head

# Verify database schema
docker-compose exec postgres psql -U commandcenter -d commandcenter_fed -c "\dt"
```

### 5. Verify Monitoring

```bash
# Prometheus metrics available
curl http://localhost:8001/metrics

# Prometheus UI
open http://localhost:9091

# Grafana dashboards
open http://localhost:3001
# Login: admin / <GRAFANA_PASSWORD from .env>
```

## Configuration

### Environment Variables

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_PASSWORD` | ✅ | - | PostgreSQL password |
| `POSTGRES_PORT` | ❌ | 5433 | PostgreSQL external port |
| `NATS_PORT` | ❌ | 4223 | NATS client port |
| `NATS_HTTP_PORT` | ❌ | 8223 | NATS monitoring port |
| `FEDERATION_PORT` | ❌ | 8001 | Federation API port |
| `FEDERATION_API_KEYS` | ✅ | [] | Valid API keys (JSON array) |
| `HEARTBEAT_STALE_THRESHOLD_SECONDS` | ❌ | 90 | Offline threshold |
| `HEARTBEAT_STALE_CHECK_INTERVAL_SECONDS` | ❌ | 60 | Cleanup interval |
| `PROMETHEUS_PORT` | ❌ | 9091 | Prometheus UI port |
| `GRAFANA_PORT` | ❌ | 3001 | Grafana UI port |
| `GRAFANA_PASSWORD` | ✅ | admin | Grafana admin password |
| `LOG_LEVEL` | ❌ | info | Logging level (debug/info/warning/error) |

### Projects Configuration

Edit `config/projects.yaml` to register CommandCenter instances:

```yaml
projects:
  - project_slug: commandcenter
    name: Main CommandCenter
    hub_url: http://localhost:9001
    mesh_namespace: hub.commandcenter
    tags: [primary, production]
    allow_fanout: [hub.projecta, hub.projectb]

  - project_slug: projecta
    name: Project A CommandCenter
    hub_url: http://localhost:9002
    mesh_namespace: hub.projecta
    tags: [client, staging]
    allow_fanout: []
```

**Validation**: The YAML is validated on startup with Pydantic schemas. Invalid config will fail fast with clear error messages.

## API Endpoints

### Health & Status

```bash
# Service health
GET http://localhost:8001/health
# Response: {"status": "healthy", "timestamp": "..."}

# NATS connectivity
GET http://localhost:8001/health/nats
# Response: {"status": "connected", "url": "nats://nats:4222"}
```

### Project Catalog

```bash
# List all projects
GET http://localhost:8001/api/fed/projects
Header: X-API-Key: <your-api-key>
# Response: [{"slug": "...", "status": "online", ...}, ...]

# Register new project
POST http://localhost:8001/api/fed/projects
Header: X-API-Key: <your-api-key>
Content-Type: application/json
{
  "project_slug": "newproject",
  "name": "New Project",
  "hub_url": "http://localhost:9003",
  "mesh_namespace": "hub.newproject"
}
```

### Metrics

```bash
# Prometheus metrics (no auth required)
GET http://localhost:8001/metrics
# Response: Prometheus exposition format

# Available metrics:
# - heartbeat_total
# - catalog_projects_by_status{status="online|offline"}
# - catalog_register_total
# - catalog_lookup_total
# - nats_publish_total
# - stale_projects_total
```

## Hub Integration

Configure each CommandCenter Hub to send heartbeats:

### Hub Configuration

Add to Hub backend `.env`:

```bash
# Federation Configuration
FEDERATION_URL=http://localhost:8001
FEDERATION_API_KEY=<your-api-key>
FEDERATION_ENABLED=true
NATS_URL=nats://localhost:4223
```

### Hub Heartbeat Publisher

The Hub backend automatically publishes heartbeats every 30 seconds to `hub.presence.<project_slug>`:

```python
# hub/backend/app/services/heartbeat_publisher.py
await nats.publish(
    subject=f"hub.presence.{project_slug}",
    payload={
        "project_slug": "commandcenter",
        "mesh_namespace": "hub.commandcenter",
        "hub_url": "http://localhost:9001",
        "status": "online",
        "timestamp": "2025-11-18T12:00:00Z"
    }
)
```

## Monitoring & Alerting

### Grafana Dashboards

Access Grafana at http://localhost:3001

**Pre-configured dashboards**:
1. **Federation Overview**: Heartbeat metrics, project status, NATS throughput
2. **Catalog Operations**: Registration/lookup rates, status distribution
3. **Stale Detection**: Projects going offline, recovery patterns

### Prometheus Queries

Useful queries for ad-hoc investigation:

```promql
# Projects currently online
sum(catalog_projects_by_status{status="online"})

# Heartbeat rate (last 5 minutes)
rate(heartbeat_total[5m]) * 60

# NATS message rate
rate(nats_publish_total[1m]) * 60

# Catalog lookup latency (if histogram available)
histogram_quantile(0.95, rate(catalog_lookup_duration_seconds_bucket[5m]))
```

### Alerting (Optional)

Create `monitoring/alerts.yml` for Prometheus Alertmanager integration:

```yaml
groups:
  - name: federation_alerts
    interval: 30s
    rules:
      - alert: NoProjectsOnline
        expr: sum(catalog_projects_by_status{status="online"}) == 0
        for: 5m
        annotations:
          summary: "No CommandCenter projects are online"
          description: "All projects have gone offline. Check heartbeat publishers."

      - alert: HighStaleRate
        expr: rate(stale_projects_total[5m]) > 1
        for: 2m
        annotations:
          summary: "High rate of projects going stale"
          description: "Multiple projects are timing out. Check NATS connectivity."
```

## Operations

### Logs

```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f federation
docker-compose logs -f postgres
docker-compose logs -f nats

# Filter for errors
docker-compose logs federation | grep ERROR
```

### Database Operations

```bash
# Backup database
docker-compose exec postgres pg_dump -U commandcenter commandcenter_fed > backup_$(date +%Y%m%d).sql

# Restore database
cat backup_20251118.sql | docker-compose exec -T postgres psql -U commandcenter commandcenter_fed

# Inspect catalog
docker-compose exec postgres psql -U commandcenter -d commandcenter_fed
# SQL: SELECT * FROM projects;
```

### Service Management

```bash
# Restart specific service
docker-compose restart federation

# Rebuild and restart
docker-compose build federation
docker-compose up -d federation

# View resource usage
docker stats federation-service federation-postgres federation-nats

# Scale (not applicable for single-instance services)
# docker-compose up -d --scale federation=3  # NOT supported, use load balancer
```

### Updates & Migrations

```bash
# Pull latest code
git pull origin main

# Rebuild services
docker-compose build

# Run new migrations
docker-compose exec federation alembic upgrade head

# Restart with zero downtime (if using load balancer)
docker-compose up -d --no-deps --build federation
```

## Troubleshooting

### Federation service won't start

```bash
# Check logs for errors
docker-compose logs federation

# Common issues:
# 1. Database not ready → Wait for postgres health check
# 2. NATS not reachable → Check NATS service
# 3. Missing migrations → Run `alembic upgrade head`
# 4. Port conflicts → Change ports in .env
```

### No heartbeats received

```bash
# Check NATS connectivity
curl http://localhost:8223/varz

# Test publish from Hub
nats pub hub.presence.test '{"test": true}' --server=nats://localhost:4223

# Check federation logs for NATS errors
docker-compose logs federation | grep NATS
```

### Projects showing offline

```bash
# Check last heartbeat time
docker-compose exec postgres psql -U commandcenter -d commandcenter_fed \
  -c "SELECT slug, status, last_heartbeat_at FROM projects;"

# Check stale threshold
echo $HEARTBEAT_STALE_THRESHOLD_SECONDS  # Should be > heartbeat interval

# Verify Hub is publishing heartbeats
docker-compose logs hub | grep heartbeat
```

### Prometheus not scraping metrics

```bash
# Check Prometheus targets
open http://localhost:9091/targets

# Verify federation metrics endpoint
curl http://localhost:8001/metrics

# Check Prometheus config
docker-compose exec prometheus cat /etc/prometheus/prometheus.yml
```

### Grafana dashboards not loading

```bash
# Check Grafana logs
docker-compose logs grafana

# Verify datasource
curl -u admin:<GRAFANA_PASSWORD> http://localhost:3001/api/datasources

# Re-provision dashboards
docker-compose restart grafana
```

## Security Considerations

### Production Hardening

1. **API Key Rotation**: Change `FEDERATION_API_KEYS` regularly
   ```bash
   # Generate new key
   python -c "import secrets; print(secrets.token_urlsafe(32))"

   # Add to .env (keep old key temporarily)
   FEDERATION_API_KEYS=["old-key","new-key"]

   # Update all Hubs to use new key
   # Remove old key after verification
   FEDERATION_API_KEYS=["new-key"]
   ```

2. **Database Security**:
   - Use strong `DB_PASSWORD` (32+ characters)
   - Restrict postgres port to localhost only (don't expose 5433 publicly)
   - Enable SSL for external connections

3. **NATS Security** (optional):
   - Enable NATS authentication
   - Use TLS for production
   - See: https://docs.nats.io/nats-server/configuration/securing_nats

4. **Grafana Security**:
   - Change default admin password immediately
   - Enable HTTPS (reverse proxy recommended)
   - Configure OAuth/SSO for team access

5. **Network Isolation**:
   - Run in private network (VPC)
   - Use reverse proxy (nginx/traefik) for HTTPS
   - Firewall rules: Only allow necessary ports

### TLS/HTTPS Setup

For production, use a reverse proxy:

```yaml
# Example nginx config
server {
    listen 443 ssl http2;
    server_name federation.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:8001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## Performance Tuning

### Database Connection Pooling

Edit `federation/app/database.py`:

```python
engine = create_async_engine(
    DATABASE_URL,
    pool_size=20,        # Increase for high load
    max_overflow=40,     # Max connections beyond pool_size
    pool_pre_ping=True,  # Verify connections before use
)
```

### NATS Performance

For high-throughput deployments:

```yaml
# docker-compose.yml - NATS service
command:
  - "--max_payload"
  - "10485760"  # 10MB max message size
  - "--max_connections"
  - "1000"
```

### Resource Limits

Add to `docker-compose.yml`:

```yaml
services:
  federation:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## Backup & Recovery

### Automated Backups

Add to crontab:

```bash
# Backup federation database daily at 2 AM
0 2 * * * cd /path/to/federation && docker-compose exec -T postgres pg_dump -U commandcenter commandcenter_fed | gzip > /backups/federation_$(date +\%Y\%m\%d).sql.gz
```

### Disaster Recovery

1. **Database Restore**:
   ```bash
   gunzip < backup.sql.gz | docker-compose exec -T postgres psql -U commandcenter commandcenter_fed
   ```

2. **Configuration Restore**:
   - Restore `.env` from secure backup
   - Restore `config/projects.yaml`

3. **Verify**:
   ```bash
   docker-compose up -d
   curl http://localhost:8001/health
   curl http://localhost:8001/api/fed/projects -H "X-API-Key: <key>"
   ```

## Next Steps

1. ✅ Federation service deployed
2. Configure Hub instances to send heartbeats
3. Set up alerting rules
4. Enable TLS via reverse proxy
5. Configure backup automation
6. Integrate with Phase 10 (Multi-tenant isolation audit)

## Support

- Documentation: `federation/README.md`
- Architecture: `docs/PROJECT.md` (Phase 9)
- Issues: GitHub Issues
