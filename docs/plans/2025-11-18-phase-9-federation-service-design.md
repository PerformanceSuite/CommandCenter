# Phase 9 - Federation Service Design

**Date:** 2025-11-18
**Status:** Approved
**Scope:** Week 1-2 (Foundation)
**Timeline:** 4 weeks total (this design covers weeks 1-2)

## Overview

The Federation Service enables multi-project orchestration by providing a centralized catalog and health monitoring system for CommandCenter instances. This design focuses on the foundational Week 1-2 deliverables: project registration, heartbeat monitoring, and query APIs.

## Goals

### Week 1-2 (This Design)
- ✅ Federation service with separate database
- ✅ Project catalog with heartbeat-based status tracking
- ✅ REST API for querying registered projects
- ✅ NATS-based heartbeat subscription
- ✅ Dagger orchestration integration

### Week 3-4 (Future)
- 📋 Metrics aggregation (audit status, coverage, etc.)
- 📋 VISLZR ecosystem view
- 📋 Integration edge discovery
- 📋 Fan-out actions (global audits, etc.)

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────┐
│                   Federation Service                     │
│                      (Port 8001)                         │
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  │
│  │ REST API     │  │ Catalog      │  │ Heartbeat    │  │
│  │ /api/fed/*   │  │ Service      │  │ Worker       │  │
│  └──────────────┘  └──────────────┘  └──────────────┘  │
│         │                 │                   │         │
│         └─────────────────┴───────────────────┘         │
│                           │                             │
└───────────────────────────┼─────────────────────────────┘
                            ↓
                 ┌──────────────────────┐
                 │ commandcenter_fed DB │
                 │  (PostgreSQL)        │
                 └──────────────────────┘

┌─────────────────────────────────────────────────────────┐
│              CommandCenter Project Instance              │
│                      (Port 8000)                         │
│                                                          │
│  ┌──────────────┐                                        │
│  │ Heartbeat    │──────────┐                            │
│  │ Publisher    │          │                            │
│  └──────────────┘          ↓                            │
│                     ┌─────────────┐                     │
│                     │    NATS     │                     │
│                     │   (4222)    │                     │
│                     └─────────────┘                     │
│                            ↑                             │
└────────────────────────────┼─────────────────────────────┘
                             │
                    (hub.presence.*)
                             │
        ┌────────────────────┘
        ↓
  Federation Service
   subscribes here
```

### Data Flow

1. **Registration (Static):**
   - Federation service loads `config/projects.yaml` on startup
   - Creates/updates projects in database with `status=offline`

2. **Heartbeat (Dynamic):**
   - CommandCenter publishes `hub.presence.commandcenter` every 30s
   - Federation worker subscribes to `hub.presence.*`
   - Updates `last_heartbeat_at`, sets `status=online`

3. **Stale Detection:**
   - Background task runs every 60s
   - Marks projects as `offline` if no heartbeat in 90s

4. **Query:**
   - Client calls `GET /api/fed/projects`
   - Returns current catalog with live status

## Database Schema

### Database: `commandcenter_fed`

**New PostgreSQL database** in existing Postgres instance (port 5432).

**Connection strings:**
- Project DB: `postgresql://commandcenter:password@postgres:5432/commandcenter`
- Federation DB: `postgresql://commandcenter:password@postgres:5432/commandcenter_fed`

### Tables

#### `projects`

```sql
CREATE TABLE projects (
    id SERIAL PRIMARY KEY,
    slug VARCHAR(50) UNIQUE NOT NULL,           -- "commandcenter"
    name VARCHAR(200) NOT NULL,                 -- "CommandCenter"
    hub_url VARCHAR(500) NOT NULL,              -- "http://localhost:8000"
    mesh_namespace VARCHAR(100),                -- "hub.commandcenter"
    status VARCHAR(20) DEFAULT 'offline',       -- 'online'|'offline'|'degraded'
    tags JSONB,                                 -- ["python", "fastapi"]
    last_heartbeat_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_projects_status ON projects(status);
CREATE INDEX idx_projects_slug ON projects(slug);
```

**SQLAlchemy Model:**

```python
# federation/app/models/project.py
from sqlalchemy import Column, Integer, String, DateTime, JSON
from sqlalchemy.dialects.postgresql import ENUM
from app.database import Base

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    hub_url = Column(String(500), nullable=False)
    mesh_namespace = Column(String(100))
    status = Column(
        ENUM("online", "offline", "degraded", name="project_status"),
        default="offline",
        nullable=False,
        index=True
    )
    tags = Column(JSON)
    last_heartbeat_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
```

#### Future Tables (Week 3-4)

```sql
-- Metrics aggregation (not implementing yet)
CREATE TABLE project_metrics (
    id SERIAL PRIMARY KEY,
    project_id INTEGER REFERENCES projects(id),
    metric_type VARCHAR(100) NOT NULL,  -- "audit.ok_count", "coverage.percent"
    value_number FLOAT,
    value_text VARCHAR(500),
    observed_at TIMESTAMP DEFAULT NOW()
);

-- Integration edges (not implementing yet)
CREATE TABLE integration_edges (
    id SERIAL PRIMARY KEY,
    from_project_id INTEGER REFERENCES projects(id),
    to_project_id INTEGER REFERENCES projects(id),
    kind VARCHAR(50),               -- "api", "queue", "shared-schema"
    strength FLOAT DEFAULT 0.5,
    details JSONB
);
```

## Service Layer

### CatalogService

**Purpose:** Core business logic for project catalog management.

```python
# federation/app/services/catalog_service.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from app.models.project import Project

class CatalogService:
    """Manages project catalog with heartbeat tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_project(
        self,
        slug: str,
        name: str,
        hub_url: str,
        mesh_namespace: str,
        tags: List[str]
    ) -> Project:
        """
        Register or update project in catalog.

        Uses upsert pattern: Creates new project if slug doesn't exist,
        updates metadata if it does.
        """
        stmt = select(Project).where(Project.slug == slug)
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()

        if project:
            # Update existing
            project.name = name
            project.hub_url = hub_url
            project.mesh_namespace = mesh_namespace
            project.tags = tags
            project.updated_at = datetime.utcnow()
        else:
            # Create new
            project = Project(
                slug=slug,
                name=name,
                hub_url=hub_url,
                mesh_namespace=mesh_namespace,
                tags=tags,
                status="offline"
            )
            self.db.add(project)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def update_heartbeat(self, slug: str) -> None:
        """
        Update last_heartbeat_at and set status to online.

        Called by heartbeat worker when NATS message received.
        """
        stmt = (
            update(Project)
            .where(Project.slug == slug)
            .values(
                last_heartbeat_at=datetime.utcnow(),
                status="online",
                updated_at=datetime.utcnow()
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_projects(
        self,
        status_filter: Optional[str] = None
    ) -> List[Project]:
        """
        List all projects, optionally filtered by status.

        Args:
            status_filter: "online", "offline", or None (all)
        """
        stmt = select(Project)
        if status_filter:
            stmt = stmt.where(Project.status == status_filter)

        result = await self.db.execute(stmt)
        return result.scalars().all()

    async def get_project(self, slug: str) -> Optional[Project]:
        """Get single project by slug."""
        stmt = select(Project).where(Project.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_stale_projects(self) -> int:
        """
        Mark projects as offline if no heartbeat in 90 seconds.

        Returns number of projects marked stale.
        """
        stale_threshold = datetime.utcnow() - timedelta(seconds=90)

        stmt = (
            update(Project)
            .where(
                Project.status == "online",
                Project.last_heartbeat_at < stale_threshold
            )
            .values(
                status="offline",
                updated_at=datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount
```

## API Layer

### REST Endpoints

**Base URL:** `http://localhost:8001/api/fed`

#### GET /projects

List all projects with optional status filter.

**Request:**
```http
GET /api/fed/projects?status=online HTTP/1.1
```

**Query Parameters:**
- `status` (optional): Filter by status ("online", "offline", "degraded")

**Response:**
```json
[
  {
    "id": 1,
    "slug": "commandcenter",
    "name": "CommandCenter",
    "hub_url": "http://localhost:8000",
    "mesh_namespace": "hub.commandcenter",
    "status": "online",
    "tags": ["python", "fastapi", "rag"],
    "last_heartbeat_at": "2025-11-18T12:30:45.123Z",
    "created_at": "2025-11-18T10:00:00.000Z",
    "updated_at": "2025-11-18T12:30:45.123Z"
  }
]
```

**Implementation:**
```python
# federation/app/routers/projects.py
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.database import get_db
from app.services.catalog_service import CatalogService
from app.schemas.project import ProjectResponse

router = APIRouter(prefix="/api/fed", tags=["federation"])

@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[str] = Query(None, regex="^(online|offline|degraded)$"),
    db: AsyncSession = Depends(get_db)
):
    """List all registered projects, optionally filtered by status."""
    service = CatalogService(db)
    projects = await service.get_projects(status_filter=status)
    return projects
```

#### POST /projects

Manually register a project (optional - mostly handled by `projects.yaml`).

**Request:**
```json
{
  "slug": "commandcenter",
  "name": "CommandCenter",
  "hub_url": "http://localhost:8000",
  "mesh_namespace": "hub.commandcenter",
  "tags": ["python", "fastapi"]
}
```

**Response:** Same as GET /projects (single object)

**Implementation:**
```python
@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def register_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Manually register a new project."""
    service = CatalogService(db)
    project = await service.register_project(
        slug=data.slug,
        name=data.name,
        hub_url=data.hub_url,
        mesh_namespace=data.mesh_namespace,
        tags=data.tags
    )
    return project
```

#### GET /health

Health check endpoint.

**Response:**
```json
{
  "status": "ok",
  "service": "federation",
  "timestamp": "2025-11-18T12:30:00.000Z"
}
```

### Pydantic Schemas

```python
# federation/app/schemas/project.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime

class ProjectCreate(BaseModel):
    """Schema for creating/registering projects."""
    slug: str = Field(..., max_length=50, pattern="^[a-z0-9-]+$")
    name: str = Field(..., max_length=200)
    hub_url: str = Field(..., max_length=500)
    mesh_namespace: str = Field(..., max_length=100)
    tags: List[str] = Field(default_factory=list)

class ProjectResponse(BaseModel):
    """Schema for project responses."""
    id: int
    slug: str
    name: str
    hub_url: str
    mesh_namespace: str
    status: str
    tags: List[str]
    last_heartbeat_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

## NATS Integration

### Heartbeat Worker

**Purpose:** Subscribe to project heartbeats and update catalog.

```python
# federation/app/workers/heartbeat_worker.py
import asyncio
import json
from nats.aio.client import Client as NATS
from app.database import get_async_session
from app.services.catalog_service import CatalogService
from app.config import settings
import logging

logger = logging.getLogger(__name__)

class HeartbeatWorker:
    """Worker that subscribes to NATS heartbeats and updates catalog."""

    def __init__(self):
        self.nats: Optional[NATS] = None
        self.running = False

    async def start(self):
        """Start the heartbeat worker."""
        self.running = True

        # Connect to NATS
        self.nats = NATS()
        await self.nats.connect(settings.NATS_URL)
        logger.info(f"Connected to NATS at {settings.NATS_URL}")

        # Subscribe to all presence subjects
        await self.nats.subscribe("hub.presence.*", cb=self._handle_heartbeat)
        logger.info("Subscribed to hub.presence.* subjects")

        # Start stale checker
        asyncio.create_task(self._stale_checker_loop())

    async def _handle_heartbeat(self, msg):
        """Handle incoming heartbeat message."""
        try:
            data = json.loads(msg.data.decode())
            project_slug = data.get("project_slug")

            if not project_slug:
                logger.warning(f"Heartbeat missing project_slug: {data}")
                return

            # Update heartbeat in database
            async with get_async_session() as db:
                service = CatalogService(db)
                await service.update_heartbeat(project_slug)
                logger.debug(f"Updated heartbeat for {project_slug}")

        except Exception as e:
            logger.error(f"Error handling heartbeat: {e}", exc_info=True)

    async def _stale_checker_loop(self):
        """Periodically check for stale projects."""
        while self.running:
            try:
                async with get_async_session() as db:
                    service = CatalogService(db)
                    stale_count = await service.mark_stale_projects()
                    if stale_count > 0:
                        logger.info(f"Marked {stale_count} projects as offline")

            except Exception as e:
                logger.error(f"Error in stale checker: {e}", exc_info=True)

            await asyncio.sleep(60)  # Check every 60 seconds

    async def stop(self):
        """Stop the heartbeat worker."""
        self.running = False
        if self.nats:
            await self.nats.close()
            logger.info("Disconnected from NATS")
```

**Integration in main.py:**

```python
# federation/app/main.py
from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.workers.heartbeat_worker import HeartbeatWorker
from app.routers import projects
import logging

logging.basicConfig(level=logging.INFO)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    worker = HeartbeatWorker()
    await worker.start()

    # Load projects from config
    await load_projects_from_yaml()

    yield

    # Shutdown
    await worker.stop()

app = FastAPI(title="Federation Service", lifespan=lifespan)
app.include_router(projects.router)
```

### Heartbeat Subject Format

**Subject:** `hub.presence.{project_slug}`

**Payload:**
```json
{
  "project_slug": "commandcenter",
  "hub_url": "http://localhost:8000",
  "mesh_namespace": "hub.commandcenter",
  "timestamp": "2025-11-18T12:30:45.123Z",
  "version": "0.9.0"
}
```

## Project-Side Integration

### Heartbeat Publisher

**Add to CommandCenter backend:**

```python
# backend/app/services/federation_heartbeat.py
import asyncio
import json
import os
from datetime import datetime
from typing import Optional
from app.services.nats_client import get_nats_client
import logging

logger = logging.getLogger(__name__)

class FederationHeartbeat:
    """Publishes heartbeat to federation service via NATS."""

    def __init__(self):
        self.project_slug = os.getenv("PROJECT_SLUG", "commandcenter")
        self.hub_url = os.getenv("HUB_URL", "http://localhost:8000")
        self.mesh_namespace = f"hub.{self.project_slug}"
        self.interval = int(os.getenv("HEARTBEAT_INTERVAL", "30"))
        self.running = False

    async def publish_heartbeat(self):
        """Publish single heartbeat to NATS."""
        nats = await get_nats_client()

        payload = {
            "project_slug": self.project_slug,
            "hub_url": self.hub_url,
            "mesh_namespace": self.mesh_namespace,
            "timestamp": datetime.utcnow().isoformat(),
            "version": "0.9.0"
        }

        subject = f"hub.presence.{self.project_slug}"
        await nats.publish(subject, json.dumps(payload).encode())
        logger.debug(f"Published heartbeat to {subject}")

    async def start_heartbeat_loop(self):
        """Start periodic heartbeat publishing."""
        self.running = True
        logger.info(f"Starting heartbeat loop (every {self.interval}s)")

        while self.running:
            try:
                await self.publish_heartbeat()
            except Exception as e:
                logger.error(f"Failed to publish heartbeat: {e}")

            await asyncio.sleep(self.interval)

    def stop(self):
        """Stop heartbeat loop."""
        self.running = False
        logger.info("Stopped heartbeat loop")
```

**Integration in backend main.py:**

```python
# backend/app/main.py
from app.services.federation_heartbeat import FederationHeartbeat

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Existing startup tasks...

    # Start federation heartbeat
    heartbeat = FederationHeartbeat()
    heartbeat_task = asyncio.create_task(heartbeat.start_heartbeat_loop())

    yield

    # Cleanup
    heartbeat.stop()
    heartbeat_task.cancel()
```

### Environment Configuration

**Add to backend `.env`:**

```bash
# Federation settings (optional - has defaults)
PROJECT_SLUG=commandcenter
HUB_URL=http://localhost:8000
HEARTBEAT_INTERVAL=30
```

## Configuration

### projects.yaml

**Location:** `federation/config/projects.yaml`

```yaml
# Static project catalog
# Federation service loads this on startup

projects:
  - slug: commandcenter
    name: CommandCenter
    hub_url: http://localhost:8000
    mesh_namespace: hub.commandcenter
    tags:
      - python
      - fastapi
      - rag
    allow_fanout: []  # Week 3-4 feature

  # Future projects (when you have multiple instances):
  # - slug: veria
  #   name: Veria
  #   hub_url: http://localhost:8010
  #   mesh_namespace: hub.veria
  #   tags: [finance, compliance]
```

**Loading logic:**

```python
# federation/app/config.py
import yaml
from pathlib import Path
from app.services.catalog_service import CatalogService
from app.database import get_async_session

async def load_projects_from_yaml():
    """Load projects from config/projects.yaml and register them."""
    config_path = Path(__file__).parent.parent / "config" / "projects.yaml"

    with open(config_path) as f:
        config = yaml.safe_load(f)

    async with get_async_session() as db:
        service = CatalogService(db)

        for project_data in config.get("projects", []):
            await service.register_project(
                slug=project_data["slug"],
                name=project_data["name"],
                hub_url=project_data["hub_url"],
                mesh_namespace=project_data["mesh_namespace"],
                tags=project_data.get("tags", [])
            )
```

## Dagger Orchestration

### Federation Stack Module

```python
# federation/dagger_modules/federation_stack.py
from dagger import dag, function, object_type, Container, Service
from typing import Optional

@object_type
class FederationStack:
    """Dagger module for Federation service orchestration."""

    @function
    async def build_service(self) -> Container:
        """Build federation service container."""
        return (
            dag.container()
            .from_("python:3.11-slim")
            .with_workdir("/app")
            .with_file(
                "/app/requirements.txt",
                dag.host().directory("federation").file("requirements.txt")
            )
            .with_exec(["pip", "install", "--no-cache-dir", "-r", "requirements.txt"])
            .with_directory("/app", dag.host().directory("federation"))
            .with_exposed_port(8001)
        )

    @function
    async def serve(
        self,
        db_url: str,
        nats_url: str = "nats://nats:4222",
        port: int = 8001
    ) -> Service:
        """
        Run federation service as Dagger service.

        Args:
            db_url: PostgreSQL connection string for commandcenter_fed
            nats_url: NATS connection URL
            port: Service port (default 8001)
        """
        container = await self.build_service()

        return (
            container
            .with_env_variable("DATABASE_URL", db_url)
            .with_env_variable("NATS_URL", nats_url)
            .with_env_variable("LOG_LEVEL", "info")
            .with_exec([
                "uvicorn", "app.main:app",
                "--host", "0.0.0.0",
                f"--port", str(port)
            ])
            .as_service()
        )

    @function
    async def run_migrations(self, db_url: str) -> str:
        """
        Run Alembic migrations for federation database.

        Args:
            db_url: PostgreSQL connection string for commandcenter_fed

        Returns:
            Migration output
        """
        container = await self.build_service()

        return await (
            container
            .with_env_variable("DATABASE_URL", db_url)
            .with_exec(["alembic", "upgrade", "head"])
            .stdout()
        )

    @function
    async def test(self, db_url: str) -> str:
        """
        Run federation service tests.

        Args:
            db_url: Test database connection string

        Returns:
            Test output
        """
        container = await self.build_service()

        return await (
            container
            .with_env_variable("DATABASE_URL", db_url)
            .with_exec(["pytest", "tests/", "-v", "--tb=short"])
            .stdout()
        )
```

**Module manifest:**

```json
// federation/dagger.json
{
  "name": "federation-stack",
  "sdk": "python",
  "source": "dagger_modules"
}
```

### Hub Integration

**Hub can orchestrate federation alongside CommandCenter instances:**

```python
# hub/backend/app/dagger_modules/meta_stack.py
from dagger import dag, function, object_type, Service
from typing import Optional

@object_type
class MetaStack:
    """Orchestrate Federation + multiple CommandCenter instances."""

    @function
    async def start_federation(
        self,
        postgres_service: Service,
        nats_service: Service,
        db_password: str
    ) -> Service:
        """
        Start federation service with dependencies.

        Args:
            postgres_service: PostgreSQL service
            nats_service: NATS service
            db_password: Database password

        Returns:
            Running federation service
        """
        # Get federation module
        fed = dag.federation_stack()

        # Build connection strings
        db_url = f"postgresql://commandcenter:{db_password}@postgres:5432/commandcenter_fed"
        nats_url = "nats://nats:4222"

        # Run migrations first
        migration_output = await fed.run_migrations(db_url)
        print(f"Migrations: {migration_output}")

        # Start service
        return (
            await fed.serve(db_url=db_url, nats_url=nats_url, port=8001)
            .with_service_binding("postgres", postgres_service)
            .with_service_binding("nats", nats_service)
        )
```

## Testing Strategy

### Unit Tests

```python
# federation/tests/test_catalog_service.py
import pytest
from datetime import datetime, timedelta
from app.services.catalog_service import CatalogService
from app.models.project import Project

@pytest.mark.asyncio
async def test_register_project_creates_new(db_session):
    """Test registering a new project."""
    service = CatalogService(db_session)

    project = await service.register_project(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:8000",
        mesh_namespace="hub.commandcenter",
        tags=["python", "fastapi"]
    )

    assert project.id is not None
    assert project.slug == "commandcenter"
    assert project.status == "offline"
    assert project.tags == ["python", "fastapi"]

@pytest.mark.asyncio
async def test_register_project_updates_existing(db_session):
    """Test registering updates existing project."""
    service = CatalogService(db_session)

    # Create initial
    project1 = await service.register_project(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:8000",
        mesh_namespace="hub.commandcenter",
        tags=["python"]
    )

    # Update
    project2 = await service.register_project(
        slug="commandcenter",
        name="CommandCenter Updated",
        hub_url="http://localhost:8001",
        mesh_namespace="hub.commandcenter",
        tags=["python", "fastapi"]
    )

    assert project1.id == project2.id
    assert project2.name == "CommandCenter Updated"
    assert project2.hub_url == "http://localhost:8001"

@pytest.mark.asyncio
async def test_heartbeat_updates_status(db_session):
    """Test heartbeat updates status to online."""
    service = CatalogService(db_session)

    # Register project
    await service.register_project(
        slug="commandcenter",
        name="CommandCenter",
        hub_url="http://localhost:8000",
        mesh_namespace="hub.commandcenter",
        tags=[]
    )

    # Send heartbeat
    await service.update_heartbeat("commandcenter")

    # Verify status
    project = await service.get_project("commandcenter")
    assert project.status == "online"
    assert project.last_heartbeat_at is not None

@pytest.mark.asyncio
async def test_mark_stale_projects(db_session, freezer):
    """Test stale projects marked offline after 90s."""
    service = CatalogService(db_session)

    # Register and heartbeat
    await service.register_project(...)
    await service.update_heartbeat("commandcenter")

    # Simulate 2 minutes passing
    freezer.move_to(datetime.utcnow() + timedelta(seconds=120))

    # Mark stale
    stale_count = await service.mark_stale_projects()

    assert stale_count == 1

    project = await service.get_project("commandcenter")
    assert project.status == "offline"

@pytest.mark.asyncio
async def test_get_projects_filter_by_status(db_session):
    """Test filtering projects by status."""
    service = CatalogService(db_session)

    # Create 2 projects
    await service.register_project(slug="project1", ...)
    await service.register_project(slug="project2", ...)

    # Heartbeat one
    await service.update_heartbeat("project1")

    # Filter online
    online = await service.get_projects(status_filter="online")
    assert len(online) == 1
    assert online[0].slug == "project1"

    # Filter offline
    offline = await service.get_projects(status_filter="offline")
    assert len(offline) == 1
    assert offline[0].slug == "project2"
```

### Integration Tests

```python
# federation/tests/test_integration.py
import pytest
import asyncio
import httpx
from nats.aio.client import Client as NATS

@pytest.mark.integration
async def test_end_to_end_flow(federation_service_url, nats_url):
    """
    Test complete flow: heartbeat → update → query.

    Requires:
    - Federation service running
    - NATS running
    - Test database initialized
    """
    # 1. Connect to NATS
    nats = NATS()
    await nats.connect(nats_url)

    # 2. Publish heartbeat
    await nats.publish(
        "hub.presence.testproject",
        json.dumps({
            "project_slug": "testproject",
            "hub_url": "http://localhost:9000",
            "mesh_namespace": "hub.testproject",
            "timestamp": datetime.utcnow().isoformat()
        }).encode()
    )

    # 3. Wait for processing
    await asyncio.sleep(2)

    # 4. Query federation API
    async with httpx.AsyncClient() as client:
        response = await client.get(f"{federation_service_url}/api/fed/projects")
        assert response.status_code == 200

        projects = response.json()
        assert len(projects) >= 1

        # Find our test project
        test_project = next(p for p in projects if p["slug"] == "testproject")
        assert test_project["status"] == "online"
        assert test_project["last_heartbeat_at"] is not None

    # Cleanup
    await nats.close()
```

### Manual Validation

**Checklist:**

1. ✅ **Start federation service**
   ```bash
   dagger call federation-stack serve --db-url=postgresql://... --nats-url=nats://...
   ```

2. ✅ **Check health endpoint**
   ```bash
   curl http://localhost:8001/api/fed/health
   # Expected: {"status": "ok", "service": "federation", ...}
   ```

3. ✅ **Start CommandCenter backend**
   - Should publish heartbeats every 30s
   - Check logs for "Published heartbeat to hub.presence.commandcenter"

4. ✅ **Query projects API**
   ```bash
   curl http://localhost:8001/api/fed/projects
   # Expected: [{"slug": "commandcenter", "status": "online", ...}]
   ```

5. ✅ **Stop CommandCenter**
   - Wait 90 seconds
   - Query again: status should be "offline"

6. ✅ **Filter by status**
   ```bash
   curl "http://localhost:8001/api/fed/projects?status=online"
   curl "http://localhost:8001/api/fed/projects?status=offline"
   ```

## Directory Structure

```
CommandCenter/
├── backend/                    (existing - port 8000)
│   ├── app/
│   │   └── services/
│   │       └── federation_heartbeat.py    (new)
│   └── ...
│
├── federation/                 (new - port 8001)
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   └── project.py
│   │   ├── schemas/
│   │   │   ├── __init__.py
│   │   │   └── project.py
│   │   ├── services/
│   │   │   ├── __init__.py
│   │   │   └── catalog_service.py
│   │   ├── routers/
│   │   │   ├── __init__.py
│   │   │   └── projects.py
│   │   └── workers/
│   │       ├── __init__.py
│   │       └── heartbeat_worker.py
│   ├── alembic/
│   │   ├── versions/
│   │   ├── env.py
│   │   └── alembic.ini
│   ├── config/
│   │   └── projects.yaml
│   ├── dagger_modules/
│   │   └── federation_stack.py
│   ├── tests/
│   │   ├── __init__.py
│   │   ├── conftest.py
│   │   ├── test_catalog_service.py
│   │   └── test_integration.py
│   ├── dagger.json
│   ├── Dockerfile
│   ├── requirements.txt
│   └── README.md
│
├── hub/                        (existing)
│   └── backend/
│       └── app/
│           └── dagger_modules/
│               ├── commandcenter.py    (existing)
│               └── meta_stack.py       (new - orchestrates federation)
│
└── docker-compose.yml          (existing - add postgres DB creation)
```

## Rollout Plan

### Task Breakdown (8 tasks)

1. **Federation service skeleton** (1-2 hours)
   - Create directory structure
   - FastAPI app setup
   - Database configuration
   - Dagger module manifest

2. **Database schema + migrations** (2-3 hours)
   - Create `commandcenter_fed` database
   - SQLAlchemy models (Project)
   - Alembic setup
   - Initial migration

3. **CatalogService implementation** (2-3 hours)
   - register_project()
   - update_heartbeat()
   - get_projects()
   - mark_stale_projects()

4. **NATS heartbeat worker** (2-3 hours)
   - HeartbeatWorker class
   - Subscribe to hub.presence.*
   - Stale checker loop
   - Integration in main.py

5. **REST API endpoints** (2 hours)
   - GET /api/fed/projects
   - POST /api/fed/projects
   - GET /api/fed/health
   - Pydantic schemas

6. **Backend heartbeat publisher** (1-2 hours)
   - FederationHeartbeat class
   - Integration in backend main.py
   - Environment configuration

7. **Dagger orchestration** (2-3 hours)
   - FederationStack module
   - MetaStack integration
   - Migration runner
   - Service composition

8. **Testing & validation** (3-4 hours)
   - Unit tests (catalog service)
   - Integration test (end-to-end)
   - Manual validation checklist
   - Documentation

**Total estimate:** 15-22 hours

### Dependencies

- PostgreSQL running (existing)
- NATS running (existing)
- Backend NATS integration (existing from Phase 4)

## Success Criteria

### Week 1-2 Complete When:

- ✅ Federation service running on port 8001 (Dagger-orchestrated)
- ✅ `commandcenter_fed` database created with `projects` table
- ✅ `config/projects.yaml` loaded on startup
- ✅ CommandCenter publishes heartbeat every 30s to NATS
- ✅ Federation worker subscribes and updates catalog
- ✅ GET /api/fed/projects returns correct project list
- ✅ Status transitions work: offline → online → offline (stale)
- ✅ Filter by status works: `?status=online`
- ✅ Unit tests passing (5+ tests)
- ✅ Integration test passing (end-to-end flow)
- ✅ Manual validation checklist complete

## Future Work (Week 3-4)

### Metrics Aggregation

- `project_metrics` table implementation
- NATS subjects for metrics: `graph.summary.*`, `audit.summary.*`
- Metrics aggregator service
- GET /api/fed/metrics/{project_id} endpoint

### VISLZR Ecosystem View

- VISLZR page at `/ecosystem`
- ReactFlow visualization of all projects
- Project nodes with health indicators
- Click to open project's individual graph

### Integration Edges

- `integration_edges` table
- Auto-discovery from API calls, shared schemas
- Manual edge creation via config
- Visualization in VISLZR

### Fan-out Actions

- Global audit trigger (broadcasts to all projects)
- Allowlist validation per project
- Response aggregation
- VISLZR action buttons

## References

- **Blueprint:** `hub-prototype/phase_9_federation_ecosystem_mode_implementation_blueprint.md`
- **Roadmap:** `docs/plans/2025-11-03-commandcenter-phases-1-12-comprehensive-roadmap.md` (lines 1081-1305)
- **Phase 4 NATS Bridge:** `docs/NATS_BRIDGE.md` (existing NATS integration)
- **Hub Dagger Architecture:** `docs/DAGGER_ARCHITECTURE.md`

---

**Next Steps:** Create implementation plan with bite-sized tasks.
