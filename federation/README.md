# Federation Service

Multi-project catalog and orchestration for CommandCenter instances.

## Overview

The Federation Service provides:
- **Project Catalog**: Central registry of CommandCenter instances
- **Heartbeat Monitoring**: Live status tracking via NATS
- **Query API**: REST endpoints for federation queries

## Architecture

- **Service**: FastAPI on port 8001
- **Database**: PostgreSQL (`commandcenter_fed`)
- **Messaging**: NATS for heartbeat subscription
- **Orchestration**: Dagger SDK

## Quick Start

### Local Development

1. **Create database:**
   ```bash
   docker exec -it commandcenter_db psql -U commandcenter -c "CREATE DATABASE commandcenter_fed;"
   ```

2. **Run migrations:**
   ```bash
   DATABASE_URL="postgresql://commandcenter:password@127.0.0.1:5432/commandcenter_fed" alembic upgrade head
   ```

3. **Start service:**
   ```bash
   DATABASE_URL="postgresql+asyncpg://commandcenter:password@127.0.0.1:5432/commandcenter_fed" \
   NATS_URL="nats://127.0.0.1:4222" \
   python -m uvicorn app.main:app --reload --port 8001
   ```

### Dagger

**Run migrations:**
```bash
dagger call run-migrations --db-url="postgresql://commandcenter:password@127.0.0.1:5432/commandcenter_fed"
```

**Start service:**
```bash
dagger call serve \
  --db-url="postgresql+asyncpg://commandcenter:password@postgres:5432/commandcenter_fed" \
  --nats-url="nats://nats:4222" \
  --port=8001
```

**Run tests:**
```bash
dagger call test --db-url="postgresql+asyncpg://commandcenter:password@127.0.0.1:5432/commandcenter_fed_test"
```

## API Endpoints

### GET /health
Health check

### GET /api/fed/projects
List all projects
- Query: `?status=online|offline|degraded`

### POST /api/fed/projects
Register project
```json
{
  "slug": "commandcenter",
  "name": "CommandCenter",
  "hub_url": "http://localhost:8000",
  "mesh_namespace": "hub.commandcenter",
  "tags": ["python"]
}
```

### GET /api/fed/projects/{slug}
Get single project

## Configuration

**Environment Variables:**
- `DATABASE_URL`: PostgreSQL connection string
- `NATS_URL`: NATS connection URL
- `LOG_LEVEL`: Logging level (default: info)
- `SERVICE_PORT`: Service port (default: 8001)

**Projects Config:**
Edit `config/projects.yaml` to add projects to catalog.

## Project Heartbeat

Projects publish heartbeats to NATS:
- **Subject:** `hub.presence.{project_slug}`
- **Interval:** 30 seconds
- **Payload:**
  ```json
  {
    "project_slug": "commandcenter",
    "hub_url": "http://localhost:8000",
    "mesh_namespace": "hub.commandcenter",
    "timestamp": "2025-11-18T12:00:00Z",
    "version": "0.9.0"
  }
  ```

Projects marked **offline** after 90 seconds without heartbeat.

## Testing

```bash
# Unit tests
pytest tests/ -v

# Specific test
pytest tests/test_catalog_service.py::test_register_project_creates_new -v
```

## Design Document

See: `docs/plans/2025-11-18-phase-9-federation-service-design.md`
