# Phase 9 Federation Service Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build Federation Service foundation (Week 1-2): project catalog with heartbeat-based status tracking, NATS subscription, and REST query API.

**Architecture:** Separate FastAPI service (port 8001) with dedicated PostgreSQL database (`commandcenter_fed`). Projects publish heartbeats to NATS; federation service subscribes and maintains catalog. Dagger-orchestrated for consistency with Hub architecture.

**Tech Stack:** FastAPI, SQLAlchemy, Alembic, NATS, PostgreSQL, Dagger SDK, pytest

---

## Task 1: Federation Service Skeleton

**Files:**
- Create: `federation/app/__init__.py`
- Create: `federation/app/main.py`
- Create: `federation/app/config.py`
- Create: `federation/app/database.py`
- Create: `federation/requirements.txt`
- Create: `federation/dagger.json`
- Create: `federation/.env.example`

**Step 1: Create directory structure**

```bash
mkdir -p federation/app
mkdir -p federation/alembic
mkdir -p federation/config
mkdir -p federation/tests
mkdir -p federation/dagger_modules
```

**Step 2: Write requirements.txt**

```txt
# federation/requirements.txt
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy[asyncio]==2.0.23
asyncpg==0.29.0
alembic==1.12.1
pydantic==2.5.0
pydantic-settings==2.1.0
nats-py==2.6.0
pyyaml==6.0.1
pytest==7.4.3
pytest-asyncio==0.21.1
httpx==0.25.2
```

**Step 3: Write app/__init__.py**

```python
# federation/app/__init__.py
"""Federation Service - Multi-project catalog and orchestration."""

__version__ = "0.9.0"
```

**Step 4: Write config.py**

```python
# federation/app/config.py
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Federation service configuration."""

    DATABASE_URL: str = "postgresql+asyncpg://commandcenter:password@localhost:5432/commandcenter_fed"
    NATS_URL: str = "nats://localhost:4222"
    LOG_LEVEL: str = "info"
    SERVICE_PORT: int = 8001

    class Config:
        env_file = ".env"


settings = Settings()
```

**Step 5: Write database.py**

```python
# federation/app/database.py
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import declarative_base
from app.config import settings
from contextlib import asynccontextmanager

Base = declarative_base()

engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncSession:
    """Dependency for FastAPI routes."""
    async with AsyncSessionLocal() as session:
        yield session


@asynccontextmanager
async def get_async_session():
    """Context manager for background workers."""
    async with AsyncSessionLocal() as session:
        yield session
```

**Step 6: Write minimal main.py**

```python
# federation/app/main.py
from fastapi import FastAPI
from app.config import settings
import logging

logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Federation Service",
    version="0.9.0",
    description="Multi-project catalog and orchestration"
)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "federation",
        "version": "0.9.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT)
```

**Step 7: Write .env.example**

```bash
# federation/.env.example
DATABASE_URL=postgresql+asyncpg://commandcenter:password@postgres:5432/commandcenter_fed
NATS_URL=nats://nats:4222
LOG_LEVEL=info
SERVICE_PORT=8001
```

**Step 8: Write dagger.json**

```json
{
  "name": "federation-stack",
  "sdk": "python",
  "source": "dagger_modules"
}
```

**Step 9: Test health endpoint locally**

Run:
```bash
cd federation
python -m uvicorn app.main:app --reload --port 8001
```

In another terminal:
```bash
curl http://localhost:8001/health
```

Expected: `{"status":"ok","service":"federation","version":"0.9.0"}`

**Step 10: Commit**

```bash
git add federation/
git commit -m "feat: federation service skeleton with health endpoint

- FastAPI app structure
- Configuration management
- Database session factory
- Health check endpoint

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 2: Database Schema & Migrations

**Files:**
- Create: `federation/app/models/__init__.py`
- Create: `federation/app/models/project.py`
- Create: `federation/alembic.ini`
- Create: `federation/alembic/env.py`
- Create: `federation/alembic/script.py.mako`
- Modify: `federation/app/database.py` (add init_db function)

**Step 1: Write Project model**

```python
# federation/app/models/__init__.py
from .project import Project

__all__ = ["Project"]
```

```python
# federation/app/models/project.py
from sqlalchemy import Column, Integer, String, DateTime, JSON, Enum as SQLEnum
from sqlalchemy.sql import func
from datetime import datetime
from app.database import Base
import enum


class ProjectStatus(str, enum.Enum):
    """Project status enumeration."""
    ONLINE = "online"
    OFFLINE = "offline"
    DEGRADED = "degraded"


class Project(Base):
    """Project catalog entry."""

    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    slug = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    hub_url = Column(String(500), nullable=False)
    mesh_namespace = Column(String(100))
    status = Column(
        SQLEnum(ProjectStatus, name="project_status", create_type=True),
        default=ProjectStatus.OFFLINE,
        nullable=False,
        index=True
    )
    tags = Column(JSON)
    last_heartbeat_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<Project(slug={self.slug}, status={self.status})>"
```

**Step 2: Initialize Alembic**

```bash
cd federation
alembic init alembic
```

**Step 3: Configure alembic.ini**

Edit `federation/alembic.ini`, find the line starting with `sqlalchemy.url` and change to:

```ini
# Leave this blank - we'll set it dynamically
sqlalchemy.url =
```

**Step 4: Write alembic/env.py**

```python
# federation/alembic/env.py
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys

# Add app to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from app.database import Base
from app.models import Project  # noqa
from app.config import settings

config = context.config

# Override sqlalchemy.url from settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL.replace("+asyncpg", ""))

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

**Step 5: Create initial migration**

```bash
cd federation
alembic revision --autogenerate -m "Initial schema - projects table"
```

**Step 6: Create commandcenter_fed database**

```bash
docker exec -it commandcenter_postgres psql -U commandcenter -c "CREATE DATABASE commandcenter_fed;"
docker exec -it commandcenter_postgres psql -U commandcenter -c "GRANT ALL PRIVILEGES ON DATABASE commandcenter_fed TO commandcenter;"
```

**Step 7: Run migrations**

```bash
cd federation
DATABASE_URL="postgresql://commandcenter:yourpassword@localhost:5432/commandcenter_fed" alembic upgrade head
```

Expected: `INFO  [alembic.runtime.migration] Running upgrade  -> <revision>, Initial schema - projects table`

**Step 8: Verify table created**

```bash
docker exec -it commandcenter_postgres psql -U commandcenter -d commandcenter_fed -c "\dt"
```

Expected: Table `projects` exists

**Step 9: Commit**

```bash
git add federation/app/models/ federation/alembic/
git commit -m "feat: add Project model and database migrations

- Project model with status enum
- Alembic migration setup
- Initial migration creating projects table

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 3: CatalogService Implementation

**Files:**
- Create: `federation/app/services/__init__.py`
- Create: `federation/app/services/catalog_service.py`
- Create: `federation/tests/__init__.py`
- Create: `federation/tests/conftest.py`
- Create: `federation/tests/test_catalog_service.py`

**Step 1: Write the failing test**

```python
# federation/tests/__init__.py
"""Federation service tests."""
```

```python
# federation/tests/conftest.py
import pytest
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from app.database import Base
from app.models import Project


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="function")
async def test_db():
    """Create test database."""
    engine = create_async_engine(
        "postgresql+asyncpg://commandcenter:yourpassword@localhost:5432/commandcenter_fed_test",
        echo=False,
    )

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    yield engine

    await engine.dispose()


@pytest.fixture
async def db_session(test_db):
    """Create test database session."""
    async_session = async_sessionmaker(
        test_db, class_=AsyncSession, expire_on_commit=False
    )

    async with async_session() as session:
        yield session
```

```python
# federation/tests/test_catalog_service.py
import pytest
from app.services.catalog_service import CatalogService
from app.models.project import ProjectStatus


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
    assert project.name == "CommandCenter"
    assert project.status == ProjectStatus.OFFLINE
    assert project.tags == ["python", "fastapi"]
```

**Step 2: Run test to verify it fails**

```bash
cd federation
pytest tests/test_catalog_service.py::test_register_project_creates_new -v
```

Expected: FAIL - `ModuleNotFoundError: No module named 'app.services.catalog_service'`

**Step 3: Write minimal CatalogService implementation**

```python
# federation/app/services/__init__.py
from .catalog_service import CatalogService

__all__ = ["CatalogService"]
```

```python
# federation/app/services/catalog_service.py
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from app.models.project import Project, ProjectStatus


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
                status=ProjectStatus.OFFLINE
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
                status=ProjectStatus.ONLINE,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_projects(
        self,
        status_filter: Optional[ProjectStatus] = None
    ) -> List[Project]:
        """
        List all projects, optionally filtered by status.

        Args:
            status_filter: ProjectStatus enum value or None (all)
        """
        stmt = select(Project)
        if status_filter:
            stmt = stmt.where(Project.status == status_filter)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

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
                Project.status == ProjectStatus.ONLINE,
                Project.last_heartbeat_at < stale_threshold
            )
            .values(
                status=ProjectStatus.OFFLINE,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount
```

**Step 4: Create test database**

```bash
docker exec -it commandcenter_postgres psql -U commandcenter -c "CREATE DATABASE commandcenter_fed_test;"
```

**Step 5: Run test to verify it passes**

```bash
cd federation
pytest tests/test_catalog_service.py::test_register_project_creates_new -v
```

Expected: PASS

**Step 6: Add more tests**

Add to `federation/tests/test_catalog_service.py`:

```python
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
    assert project.status == ProjectStatus.ONLINE
    assert project.last_heartbeat_at is not None


@pytest.mark.asyncio
async def test_get_projects_filter_by_status(db_session):
    """Test filtering projects by status."""
    service = CatalogService(db_session)

    # Create 2 projects
    await service.register_project(slug="project1", name="P1", hub_url="http://localhost:8000", mesh_namespace="hub.p1", tags=[])
    await service.register_project(slug="project2", name="P2", hub_url="http://localhost:8001", mesh_namespace="hub.p2", tags=[])

    # Heartbeat one
    await service.update_heartbeat("project1")

    # Filter online
    online = await service.get_projects(status_filter=ProjectStatus.ONLINE)
    assert len(online) == 1
    assert online[0].slug == "project1"

    # Filter offline
    offline = await service.get_projects(status_filter=ProjectStatus.OFFLINE)
    assert len(offline) == 1
    assert offline[0].slug == "project2"
```

**Step 7: Run all tests**

```bash
cd federation
pytest tests/test_catalog_service.py -v
```

Expected: 3 tests PASS

**Step 8: Commit**

```bash
git add federation/app/services/ federation/tests/
git commit -m "feat: implement CatalogService with tests

- register_project() with upsert logic
- update_heartbeat() for status tracking
- get_projects() with status filtering
- get_project() single lookup
- mark_stale_projects() for cleanup
- 3 passing tests

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 4: REST API Endpoints

**Files:**
- Create: `federation/app/schemas/__init__.py`
- Create: `federation/app/schemas/project.py`
- Create: `federation/app/routers/__init__.py`
- Create: `federation/app/routers/projects.py`
- Modify: `federation/app/main.py`

**Step 1: Write Pydantic schemas**

```python
# federation/app/schemas/__init__.py
from .project import ProjectCreate, ProjectResponse

__all__ = ["ProjectCreate", "ProjectResponse"]
```

```python
# federation/app/schemas/project.py
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from app.models.project import ProjectStatus


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
    status: ProjectStatus
    tags: List[str]
    last_heartbeat_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

**Step 2: Write projects router**

```python
# federation/app/routers/__init__.py
from .projects import router as projects_router

__all__ = ["projects_router"]
```

```python
# federation/app/routers/projects.py
from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.database import get_db
from app.services.catalog_service import CatalogService
from app.schemas.project import ProjectCreate, ProjectResponse
from app.models.project import ProjectStatus
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/fed", tags=["federation"])


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[str] = Query(None, regex="^(online|offline|degraded)$"),
    db: AsyncSession = Depends(get_db)
):
    """List all registered projects, optionally filtered by status."""
    service = CatalogService(db)

    status_filter = None
    if status:
        status_filter = ProjectStatus(status)

    projects = await service.get_projects(status_filter=status_filter)
    return projects


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def register_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Manually register a new project."""
    service = CatalogService(db)

    try:
        project = await service.register_project(
            slug=data.slug,
            name=data.name,
            hub_url=data.hub_url,
            mesh_namespace=data.mesh_namespace,
            tags=data.tags
        )
        return project
    except Exception as e:
        logger.error(f"Failed to register project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{slug}", response_model=ProjectResponse)
async def get_project(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get single project by slug."""
    service = CatalogService(db)
    project = await service.get_project(slug)

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{slug}' not found")

    return project
```

**Step 3: Update main.py to include router**

```python
# federation/app/main.py
from fastapi import FastAPI
from app.config import settings
from app.routers import projects_router
import logging

logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Federation Service",
    version="0.9.0",
    description="Multi-project catalog and orchestration"
)

# Include routers
app.include_router(projects_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "federation",
        "version": "0.9.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT)
```

**Step 4: Test endpoints manually**

Start federation service:
```bash
cd federation
DATABASE_URL="postgresql+asyncpg://commandcenter:yourpassword@localhost:5432/commandcenter_fed" python -m uvicorn app.main:app --reload --port 8001
```

Test POST /api/fed/projects:
```bash
curl -X POST http://localhost:8001/api/fed/projects \
  -H "Content-Type: application/json" \
  -d '{
    "slug": "commandcenter",
    "name": "CommandCenter",
    "hub_url": "http://localhost:8000",
    "mesh_namespace": "hub.commandcenter",
    "tags": ["python", "fastapi"]
  }'
```

Expected: 201 response with project JSON

Test GET /api/fed/projects:
```bash
curl http://localhost:8001/api/fed/projects
```

Expected: Array with commandcenter project

Test GET /api/fed/projects?status=offline:
```bash
curl "http://localhost:8001/api/fed/projects?status=offline"
```

Expected: Array with commandcenter (status=offline initially)

**Step 5: Commit**

```bash
git add federation/app/schemas/ federation/app/routers/ federation/app/main.py
git commit -m "feat: add Federation REST API endpoints

- Pydantic schemas for request/response
- GET /api/fed/projects with status filtering
- POST /api/fed/projects for manual registration
- GET /api/fed/projects/{slug} for single lookup

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 5: NATS Heartbeat Worker

**Files:**
- Create: `federation/app/workers/__init__.py`
- Create: `federation/app/workers/heartbeat_worker.py`
- Modify: `federation/app/main.py`
- Create: `federation/config/projects.yaml`
- Create: `federation/app/loader.py`

**Step 1: Write HeartbeatWorker**

```python
# federation/app/workers/__init__.py
from .heartbeat_worker import HeartbeatWorker

__all__ = ["HeartbeatWorker"]
```

```python
# federation/app/workers/heartbeat_worker.py
import asyncio
import json
from nats.aio.client import Client as NATS
from typing import Optional
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
        self.stale_checker_task: Optional[asyncio.Task] = None

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
        self.stale_checker_task = asyncio.create_task(self._stale_checker_loop())

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

        if self.stale_checker_task:
            self.stale_checker_task.cancel()
            try:
                await self.stale_checker_task
            except asyncio.CancelledError:
                pass

        if self.nats:
            await self.nats.close()
            logger.info("Disconnected from NATS")
```

**Step 2: Write projects.yaml loader**

```yaml
# federation/config/projects.yaml
projects:
  - slug: commandcenter
    name: CommandCenter
    hub_url: http://localhost:8000
    mesh_namespace: hub.commandcenter
    tags:
      - python
      - fastapi
      - rag
    allow_fanout: []
```

```python
# federation/app/loader.py
import yaml
from pathlib import Path
from app.services.catalog_service import CatalogService
from app.database import get_async_session
import logging

logger = logging.getLogger(__name__)


async def load_projects_from_yaml():
    """Load projects from config/projects.yaml and register them."""
    config_path = Path(__file__).parent.parent / "config" / "projects.yaml"

    if not config_path.exists():
        logger.warning(f"Config file not found: {config_path}")
        return

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
            logger.info(f"Registered project: {project_data['slug']}")
```

**Step 3: Update main.py with lifespan**

```python
# federation/app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import settings
from app.routers import projects_router
from app.workers import HeartbeatWorker
from app.loader import load_projects_from_yaml
import logging

logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Federation Service...")

    # Load projects from config
    await load_projects_from_yaml()

    # Start heartbeat worker
    worker = HeartbeatWorker()
    await worker.start()

    yield

    # Shutdown
    logger.info("Shutting down Federation Service...")
    await worker.stop()


app = FastAPI(
    title="Federation Service",
    version="0.9.0",
    description="Multi-project catalog and orchestration",
    lifespan=lifespan
)

# Include routers
app.include_router(projects_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "federation",
        "version": "0.9.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT)
```

**Step 4: Test heartbeat worker**

Start federation service (should load commandcenter from projects.yaml):
```bash
cd federation
DATABASE_URL="postgresql+asyncpg://commandcenter:yourpassword@localhost:5432/commandcenter_fed" \
NATS_URL="nats://localhost:4222" \
python -m uvicorn app.main:app --reload --port 8001
```

Check logs - should see: `Registered project: commandcenter`

Verify project registered:
```bash
curl http://localhost:8001/api/fed/projects
```

Expected: commandcenter project with status=offline

**Step 5: Commit**

```bash
git add federation/app/workers/ federation/app/loader.py federation/config/ federation/app/main.py
git commit -m "feat: add NATS heartbeat worker and project loader

- HeartbeatWorker subscribing to hub.presence.*
- Stale project checker (90s timeout)
- projects.yaml loader on startup
- FastAPI lifespan for worker management

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 6: Backend Heartbeat Publisher

**Files:**
- Create: `backend/app/services/federation_heartbeat.py`
- Modify: `backend/app/main.py`
- Modify: `backend/.env.example`

**Step 1: Write FederationHeartbeat service**

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

**Step 2: Update backend main.py**

Find the `lifespan` function in `backend/app/main.py` and add heartbeat:

```python
# backend/app/main.py (modify existing lifespan function)
from app.services.federation_heartbeat import FederationHeartbeat

@asynccontextmanager
async def lifespan(app: FastAPI):
    # ... existing startup tasks ...

    # Start federation heartbeat
    heartbeat = FederationHeartbeat()
    heartbeat_task = asyncio.create_task(heartbeat.start_heartbeat_loop())

    yield

    # Cleanup
    heartbeat.stop()
    heartbeat_task.cancel()
    try:
        await heartbeat_task
    except asyncio.CancelledError:
        pass
```

**Step 3: Update backend .env.example**

Add to `backend/.env.example`:

```bash
# Federation settings (optional - has defaults)
PROJECT_SLUG=commandcenter
HUB_URL=http://localhost:8000
HEARTBEAT_INTERVAL=30
```

**Step 4: Test end-to-end**

Terminal 1 - Start federation service:
```bash
cd federation
DATABASE_URL="postgresql+asyncpg://commandcenter:yourpassword@localhost:5432/commandcenter_fed" \
NATS_URL="nats://localhost:4222" \
python -m uvicorn app.main:app --reload --port 8001
```

Terminal 2 - Start backend (with heartbeat):
```bash
cd backend
docker-compose up -d postgres redis nats
uvicorn app.main:app --reload --port 8000
```

Wait 5 seconds, then query federation:
```bash
curl http://localhost:8001/api/fed/projects
```

Expected: commandcenter with `status: "online"` and recent `last_heartbeat_at`

Stop backend, wait 90 seconds, query again:
Expected: commandcenter with `status: "offline"`

**Step 5: Commit**

```bash
git add backend/app/services/federation_heartbeat.py backend/app/main.py backend/.env.example
git commit -m "feat: add federation heartbeat publisher to backend

- FederationHeartbeat service publishing to NATS
- 30s interval (configurable)
- Integration in backend lifespan
- End-to-end federation flow working

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 7: Dagger Orchestration

**Files:**
- Create: `federation/dagger_modules/__init__.py`
- Create: `federation/dagger_modules/federation_stack.py`
- Create: `federation/Dockerfile`

**Step 1: Write Dockerfile**

```dockerfile
# federation/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Run migrations on startup (optional - can be separate step)
# CMD alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8001

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]
```

**Step 2: Write Dagger module**

```python
# federation/dagger_modules/__init__.py
from .federation_stack import FederationStack

__all__ = ["FederationStack"]
```

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

        # Convert asyncpg URL to psycopg2 for Alembic
        sync_db_url = db_url.replace("+asyncpg", "")

        return await (
            container
            .with_env_variable("DATABASE_URL", sync_db_url)
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

**Step 3: Test Dagger functions**

Build service:
```bash
cd federation
dagger call build-service
```

Expected: Container builds successfully

Run migrations:
```bash
dagger call run-migrations --db-url="postgresql://commandcenter:yourpassword@localhost:5432/commandcenter_fed"
```

Expected: Migration output

Run tests:
```bash
dagger call test --db-url="postgresql+asyncpg://commandcenter:yourpassword@localhost:5432/commandcenter_fed_test"
```

Expected: Tests pass

**Step 4: Commit**

```bash
git add federation/dagger_modules/ federation/Dockerfile
git commit -m "feat: add Dagger orchestration for federation service

- FederationStack module with build/serve/test functions
- Dockerfile for containerization
- Migration runner via Dagger
- Test runner via Dagger

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Task 8: Documentation & Validation

**Files:**
- Create: `federation/README.md`
- Modify: `docs/PROJECT.md`

**Step 1: Write federation README**

```markdown
# federation/README.md
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
   docker exec -it commandcenter_postgres psql -U commandcenter -c "CREATE DATABASE commandcenter_fed;"
   ```

2. **Run migrations:**
   ```bash
   DATABASE_URL="postgresql://commandcenter:password@localhost:5432/commandcenter_fed" alembic upgrade head
   ```

3. **Start service:**
   ```bash
   DATABASE_URL="postgresql+asyncpg://commandcenter:password@localhost:5432/commandcenter_fed" \
   NATS_URL="nats://localhost:4222" \
   python -m uvicorn app.main:app --reload --port 8001
   ```

### Dagger

**Run migrations:**
```bash
dagger call run-migrations --db-url="postgresql://commandcenter:password@localhost:5432/commandcenter_fed"
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
dagger call test --db-url="postgresql+asyncpg://commandcenter:password@localhost:5432/commandcenter_fed_test"
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
```

**Step 2: Update PROJECT.md**

Add to `docs/PROJECT.md` under "Active Work":

```markdown
  - **Phase 9**: Federation & Ecosystem Mode **IN PROGRESS** 🔄 (Started 2025-11-18)
    - ✅ **Week 1-2**: Federation Service Foundation
      - Federation service skeleton (port 8001)
      - Database schema (`commandcenter_fed`)
      - CatalogService with project registration
      - REST API endpoints (GET/POST /api/fed/projects)
      - NATS heartbeat worker
      - Backend heartbeat publisher
      - Dagger orchestration module
      - End-to-end validation complete
    - 📋 **Week 3-4**: Metrics & VISLZR (planned)
    - **8 tasks complete**, foundation ready for Week 3-4
```

**Step 3: Manual validation checklist**

```bash
# 1. Health check
curl http://localhost:8001/health
# Expected: {"status":"ok","service":"federation","version":"0.9.0"}

# 2. Projects loaded from YAML
curl http://localhost:8001/api/fed/projects
# Expected: Array with commandcenter

# 3. Start backend (publishes heartbeats)
cd backend && docker-compose up -d && uvicorn app.main:app --reload --port 8000

# 4. Wait 5 seconds, check status
curl http://localhost:8001/api/fed/projects
# Expected: commandcenter with status="online"

# 5. Stop backend
# (Ctrl+C in terminal)

# 6. Wait 90 seconds, check status
curl http://localhost:8001/api/fed/projects
# Expected: commandcenter with status="offline"

# 7. Filter by status
curl "http://localhost:8001/api/fed/projects?status=offline"
# Expected: Array with commandcenter

# 8. Run tests
cd federation && pytest tests/ -v
# Expected: All tests pass
```

**Step 4: Commit**

```bash
git add federation/README.md docs/PROJECT.md
git commit -m "docs: add federation service documentation

- Federation README with setup and API docs
- Updated PROJECT.md Phase 9 status
- Manual validation checklist

Week 1-2 complete: Foundation ready for metrics & VISLZR

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Success Criteria

✅ **All 8 tasks complete when:**

1. Federation service runs on port 8001
2. `commandcenter_fed` database exists with `projects` table
3. CatalogService tests passing (3+ tests)
4. GET/POST /api/fed/projects endpoints working
5. NATS heartbeat worker subscribing to `hub.presence.*`
6. Backend publishes heartbeats every 30s
7. Status transitions: offline → online → offline (stale)
8. Dagger orchestration working (build/serve/test functions)
9. Manual validation checklist complete
10. Documentation complete (README + PROJECT.md)

---

## Next Steps (Week 3-4)

- Metrics aggregation (`project_metrics` table)
- VISLZR ecosystem view
- Integration edge discovery
- Fan-out actions

**See:** `docs/plans/2025-11-18-phase-9-federation-service-design.md` (Future Work section)
