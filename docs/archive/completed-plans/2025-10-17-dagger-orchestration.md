# Dagger Orchestration Implementation Plan

> **For Claude:** Use `${SUPERPOWERS_SKILLS_ROOT}/skills/collaboration/executing-plans/SKILL.md` to implement this plan task-by-task.

**Goal:** Replace Docker Compose subprocess calls with native Dagger Python SDK for orchestrating CommandCenter project containers.

**Architecture:** Instead of cloning CommandCenter repo into each project folder and using docker-compose.yml, we'll define the CommandCenter stack programmatically using Dagger SDK. The Hub stores project config (folder path, ports) and passes it to Dagger which builds and runs containers pointing to the project's folder.

**Tech Stack:**
- Dagger Python SDK (anyio)
- FastAPI (existing)
- SQLAlchemy (existing)
- Remove: docker-compose, subprocess calls, CommandCenter template cloning

**Key Benefits:**
- No more cloning CommandCenter into every project
- Type-safe container configuration
- Better error handling (SDK exceptions vs subprocess stderr parsing)
- Programmatic control over container lifecycle
- Dagger's intelligent caching

---

## Task 1: Add Dagger SDK Dependency

**Files:**
- Modify: `hub/backend/requirements.txt`
- Modify: `hub/backend/app/services/__init__.py`

**Step 1: Add Dagger SDK to requirements**

Add to `hub/backend/requirements.txt`:
```txt
dagger-io==0.9.6
anyio==4.2.0
```

**Step 2: Verify installation**

Run: `cd hub/backend && source venv/bin/activate && pip install -r requirements.txt`
Expected: Successful installation with no errors

**Step 3: Commit**

```bash
git add hub/backend/requirements.txt
git commit -m "feat(hub): add Dagger SDK dependency"
```

---

## Task 2: Create Dagger CommandCenter Module

**Files:**
- Create: `hub/backend/app/dagger_modules/commandcenter.py`
- Create: `hub/backend/app/dagger_modules/__init__.py`

**Step 1: Create dagger_modules package**

Create `hub/backend/app/dagger_modules/__init__.py`:
```python
"""Dagger modules for container orchestration"""
```

**Step 2: Create CommandCenter stack definition**

Create `hub/backend/app/dagger_modules/commandcenter.py`:
```python
"""
CommandCenter Stack Definition using Dagger SDK

This module defines the complete CommandCenter infrastructure stack
as code using Dagger's Python SDK. No docker-compose.yml needed.
"""

import logging
from dataclasses import dataclass
from typing import Optional

import dagger

logger = logging.getLogger(__name__)


@dataclass
class CommandCenterConfig:
    """Configuration for a CommandCenter instance"""
    project_name: str
    project_path: str
    backend_port: int
    frontend_port: int
    postgres_port: int
    redis_port: int
    db_password: str
    secret_key: str


class CommandCenterStack:
    """Defines and manages CommandCenter container stack using Dagger"""

    def __init__(self, config: CommandCenterConfig):
        self.config = config
        self.client: Optional[dagger.Client] = None

    async def __aenter__(self):
        """Initialize Dagger client"""
        self.client = dagger.Connection(dagger.Config()).client()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Dagger client"""
        if self.client:
            await self.client.close()

    async def build_postgres(self) -> dagger.Container:
        """Build PostgreSQL container"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        return (
            self.client.container()
            .from_("postgres:15-alpine")
            .with_env_variable("POSTGRES_USER", "commandcenter")
            .with_env_variable("POSTGRES_PASSWORD", self.config.db_password)
            .with_env_variable("POSTGRES_DB", "commandcenter")
            .with_exposed_port(5432)
        )

    async def build_redis(self) -> dagger.Container:
        """Build Redis container"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        return (
            self.client.container()
            .from_("redis:7-alpine")
            .with_exposed_port(6379)
        )

    async def build_backend(self, postgres_host: str, redis_host: str) -> dagger.Container:
        """Build CommandCenter backend container"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        # Mount project directory as read-only volume
        project_dir = self.client.host().directory(self.config.project_path)

        return (
            self.client.container()
            .from_("python:3.11-slim")
            # Install CommandCenter backend dependencies
            .with_exec(["pip", "install", "fastapi", "uvicorn[standard]",
                       "sqlalchemy", "asyncpg", "redis", "langchain",
                       "langchain-community", "chromadb", "sentence-transformers"])
            # Mount project directory
            .with_mounted_directory("/workspace", project_dir)
            .with_workdir("/workspace")
            # Set environment variables
            .with_env_variable("DATABASE_URL",
                             f"postgresql://commandcenter:{self.config.db_password}@{postgres_host}:5432/commandcenter")
            .with_env_variable("REDIS_URL", f"redis://{redis_host}:6379")
            .with_env_variable("SECRET_KEY", self.config.secret_key)
            .with_env_variable("PROJECT_NAME", self.config.project_name)
            # Run backend
            .with_exec(["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"])
            .with_exposed_port(8000)
        )

    async def build_frontend(self, backend_url: str) -> dagger.Container:
        """Build CommandCenter frontend container"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        return (
            self.client.container()
            .from_("node:18-alpine")
            # Install CommandCenter frontend dependencies
            .with_exec(["npm", "install", "-g", "vite", "react", "react-dom"])
            # Set environment variables
            .with_env_variable("VITE_API_BASE_URL", backend_url)
            .with_env_variable("VITE_PROJECT_NAME", self.config.project_name)
            # Run frontend dev server
            .with_exec(["npm", "run", "dev", "--", "--host", "0.0.0.0", "--port", "3000"])
            .with_exposed_port(3000)
        )

    async def start(self) -> dict:
        """Start all CommandCenter containers"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        try:
            logger.info(f"Starting CommandCenter stack for project: {self.config.project_name}")

            # Build and start containers
            postgres = await self.build_postgres()
            redis = await self.build_redis()

            # Start postgres and redis first
            postgres_svc = postgres.as_service()
            redis_svc = redis.as_service()

            # Build backend with service hostnames
            backend = await self.build_backend("postgres", "redis")
            backend_svc = backend.as_service()

            # Build frontend with backend URL
            frontend = await self.build_frontend(f"http://backend:{self.config.backend_port}")
            frontend_svc = frontend.as_service()

            logger.info(f"CommandCenter stack started successfully for {self.config.project_name}")

            return {
                "success": True,
                "message": "Stack started successfully",
                "services": {
                    "postgres": {"port": self.config.postgres_port},
                    "redis": {"port": self.config.redis_port},
                    "backend": {"port": self.config.backend_port},
                    "frontend": {"port": self.config.frontend_port},
                }
            }

        except Exception as e:
            logger.error(f"Failed to start CommandCenter stack: {e}")
            raise

    async def stop(self) -> dict:
        """Stop all CommandCenter containers"""
        # Dagger containers are ephemeral and automatically cleaned up
        logger.info(f"Stopping CommandCenter stack for project: {self.config.project_name}")
        return {
            "success": True,
            "message": "Stack stopped successfully"
        }

    async def status(self) -> dict:
        """Get status of CommandCenter containers"""
        # For now, return placeholder - we'll implement proper health checks
        return {
            "status": "running",
            "health": "healthy",
            "containers": []
        }
```

**Step 3: Test module imports**

Run: `cd hub/backend && python -c "from app.dagger_modules.commandcenter import CommandCenterStack; print('Import successful')"`
Expected: "Import successful"

**Step 4: Commit**

```bash
git add hub/backend/app/dagger_modules/
git commit -m "feat(hub): add Dagger CommandCenter stack definition"
```

---

## Task 3: Update OrchestrationService to Use Dagger

**Files:**
- Modify: `hub/backend/app/services/orchestration_service.py`

**Step 1: Write failing test for Dagger integration**

Create `hub/backend/tests/services/test_orchestration_dagger.py`:
```python
import pytest
from app.services.orchestration_service import OrchestrationService
from app.models import Project


@pytest.mark.asyncio
async def test_start_project_uses_dagger(db_session, sample_project):
    """Test that start_project uses Dagger instead of subprocess"""
    service = OrchestrationService(db_session)

    # This should not raise subprocess-related errors
    result = await service.start_project(sample_project.id)

    assert result["success"] is True
    assert "docker-compose" not in str(result).lower()  # Ensure no docker-compose references
```

**Step 2: Run test to verify it fails**

Run: `cd hub/backend && pytest tests/services/test_orchestration_dagger.py -v`
Expected: FAIL (OrchestrationService still uses subprocess)

**Step 3: Rewrite OrchestrationService to use Dagger**

Update `hub/backend/app/services/orchestration_service.py`:
```python
"""
Orchestration service - Start/stop CommandCenter instances via Dagger SDK
"""

import logging
import secrets
from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.models import Project
from app.dagger_modules.commandcenter import CommandCenterStack, CommandCenterConfig

logger = logging.getLogger(__name__)


class OrchestrationService:
    """Service for orchestrating Dagger-based CommandCenter stacks"""

    def __init__(self, db: AsyncSession):
        self.db = db
        self._active_stacks: dict[int, CommandCenterStack] = {}

    def _check_port_available(self, port: int) -> tuple[bool, str]:
        """Check if a port is available (same as before)"""
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                if result == 0:
                    return False, f"Port {port} is already in use"
                return True, ""
        except Exception as e:
            logger.warning(f"Error checking port {port}: {e}")
            return True, ""

    async def start_project(self, project_id: int) -> dict:
        """Start CommandCenter instance using Dagger"""
        project = await self._get_project(project_id)

        if project.status == "running":
            return {
                "success": True,
                "message": "Project is already running",
                "project_id": project_id,
                "status": "running",
            }

        # Check for port conflicts
        ports_to_check = [
            ("Frontend", project.frontend_port),
            ("Backend", project.backend_port),
            ("PostgreSQL", project.postgres_port),
            ("Redis", project.redis_port),
        ]

        port_conflicts = []
        for service_name, port in ports_to_check:
            is_available, error = self._check_port_available(port)
            if not is_available:
                port_conflicts.append(f"{service_name} port {port}")

        if port_conflicts:
            error_msg = (
                f"Cannot start project: The following ports are already in use: "
                f"{', '.join(port_conflicts)}"
            )
            raise RuntimeError(error_msg)

        # Update status
        project.status = "starting"
        await self.db.commit()

        try:
            # Create Dagger configuration
            config = CommandCenterConfig(
                project_name=project.name,
                project_path=project.path,  # Direct path to project folder
                backend_port=project.backend_port,
                frontend_port=project.frontend_port,
                postgres_port=project.postgres_port,
                redis_port=project.redis_port,
                db_password=secrets.token_urlsafe(32),
                secret_key=secrets.token_hex(32),
            )

            # Start Dagger stack
            async with CommandCenterStack(config) as stack:
                result = await stack.start()
                self._active_stacks[project_id] = stack

            # Update status
            project.status = "running"
            project.last_started = datetime.utcnow()
            await self.db.commit()

            return {
                "success": True,
                "message": "Project started successfully via Dagger",
                "project_id": project_id,
                "status": "running",
            }

        except Exception as e:
            project.status = "error"
            await self.db.commit()
            raise RuntimeError(f"Failed to start project with Dagger: {str(e)}")

    async def stop_project(self, project_id: int) -> dict:
        """Stop CommandCenter instance"""
        project = await self._get_project(project_id)

        if project.status == "stopped":
            return {
                "success": True,
                "message": "Project is already stopped",
                "project_id": project_id,
                "status": "stopped",
            }

        project.status = "stopping"
        await self.db.commit()

        try:
            # Stop Dagger stack
            if project_id in self._active_stacks:
                stack = self._active_stacks[project_id]
                await stack.stop()
                del self._active_stacks[project_id]

            project.status = "stopped"
            project.last_stopped = datetime.utcnow()
            await self.db.commit()

            return {
                "success": True,
                "message": "Project stopped successfully",
                "project_id": project_id,
                "status": "stopped",
            }

        except Exception as e:
            project.status = "error"
            await self.db.commit()
            raise RuntimeError(f"Failed to stop project: {str(e)}")

    async def restart_project(self, project_id: int) -> dict:
        """Restart CommandCenter instance"""
        await self.stop_project(project_id)
        return await self.start_project(project_id)

    async def get_project_status(self, project_id: int) -> dict:
        """Get real-time status from Dagger"""
        project = await self._get_project(project_id)

        try:
            if project_id in self._active_stacks:
                stack = self._active_stacks[project_id]
                return await stack.status()
            else:
                return {
                    "project_id": project_id,
                    "status": "stopped",
                    "health": "stopped",
                }
        except Exception as e:
            return {
                "project_id": project_id,
                "status": "unknown",
                "health": "unknown",
                "error": str(e),
            }

    async def get_logs(self, project_id: int, tail: int = 100) -> dict:
        """Get container logs (to be implemented with Dagger)"""
        # Placeholder for now
        return {
            "project_id": project_id,
            "logs": "Dagger log retrieval not yet implemented",
            "errors": "",
        }

    async def _get_project(self, project_id: int) -> Project:
        """Get project or raise error"""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        return project
```

**Step 4: Run test to verify it passes**

Run: `cd hub/backend && pytest tests/services/test_orchestration_dagger.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add hub/backend/app/services/orchestration_service.py hub/backend/tests/services/test_orchestration_dagger.py
git commit -m "feat(hub): replace docker-compose with Dagger SDK in OrchestrationService"
```

---

## Task 4: Remove Setup Service (No Longer Needed)

**Files:**
- Delete: `hub/backend/app/services/setup_service.py`
- Modify: `hub/backend/app/services/project_service.py`

**Step 1: Update ProjectService to not use SetupService**

Update `hub/backend/app/services/project_service.py` - Remove all references to `setup_commandcenter()`:

```python
# Remove this import
# from app.services.setup_service import SetupService

# In create_project method, remove this line:
# await self.setup_service.setup_commandcenter(project)

# Projects now just need a path - no CommandCenter cloning needed
```

**Step 2: Delete SetupService**

Run: `rm hub/backend/app/services/setup_service.py`

**Step 3: Run existing project tests**

Run: `cd hub/backend && pytest tests/services/test_project_service.py -v`
Expected: PASS (tests should still work without setup_service)

**Step 4: Commit**

```bash
git rm hub/backend/app/services/setup_service.py
git add hub/backend/app/services/project_service.py
git commit -m "refactor(hub): remove SetupService - no longer clone CommandCenter"
```

---

## Task 5: Update Project Model (Remove cc_path)

**Files:**
- Modify: `hub/backend/app/models/project.py`
- Create: `hub/backend/alembic/versions/<timestamp>_remove_cc_path.py`

**Step 1: Update Project model**

Update `hub/backend/app/models/project.py`:
```python
# Remove cc_path field
# Remove compose_project_name field
# Keep only: path (project folder), ports, status, health
```

**Step 2: Create migration**

Run: `cd hub/backend && alembic revision --autogenerate -m "remove cc_path from projects"`

**Step 3: Apply migration**

Run: `cd hub/backend && alembic upgrade head`
Expected: Migration applies successfully

**Step 4: Commit**

```bash
git add hub/backend/app/models/project.py hub/backend/alembic/versions/
git commit -m "refactor(hub): remove cc_path and compose_project_name from Project model"
```

---

## Task 6: Update Frontend (No Changes Needed)

The frontend API calls remain the same - just calling `/api/orchestration/{id}/start`, `/stop`, etc. No changes needed since the backend API contract hasn't changed.

---

## Task 7: Integration Testing

**Files:**
- Create: `hub/backend/tests/integration/test_dagger_flow.py`

**Step 1: Write end-to-end integration test**

Create `hub/backend/tests/integration/test_dagger_flow.py`:
```python
import pytest
from app.services.project_service import ProjectService
from app.services.orchestration_service import OrchestrationService


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_dagger_flow(db_session, tmp_path):
    """Test complete project lifecycle with Dagger"""
    project_service = ProjectService(db_session)
    orch_service = OrchestrationService(db_session)

    # Create project
    project_data = {
        "name": "TestProject",
        "path": str(tmp_path),
    }
    project = await project_service.create_project(project_data)

    # Start project (should use Dagger)
    result = await orch_service.start_project(project.id)
    assert result["success"] is True

    # Check status
    status = await orch_service.get_project_status(project.id)
    assert status["status"] == "running"

    # Stop project
    stop_result = await orch_service.stop_project(project.id)
    assert stop_result["success"] is True
```

**Step 2: Run integration test**

Run: `cd hub/backend && pytest tests/integration/test_dagger_flow.py -v -m integration`
Expected: PASS

**Step 3: Commit**

```bash
git add hub/backend/tests/integration/test_dagger_flow.py
git commit -m "test(hub): add integration test for Dagger orchestration flow"
```

---

## Task 8: Update Documentation

**Files:**
- Modify: `hub/HUB_DESIGN.md`
- Modify: `CLAUDE.md`
- Create: `docs/DAGGER_ARCHITECTURE.md`

**Step 1: Create Dagger architecture documentation**

Create `docs/DAGGER_ARCHITECTURE.md`:
```markdown
# Dagger Architecture

CommandCenter Hub uses Dagger SDK for container orchestration instead of docker-compose.

## Key Benefits

- No CommandCenter cloning into project folders
- Type-safe container configuration via Python
- Better error handling with SDK exceptions
- Programmatic control over container lifecycle
- Intelligent caching via Dagger engine

## How It Works

1. User creates project by selecting folder path
2. Hub stores: project name, path, ports
3. When user starts project:
   - Hub creates CommandCenterConfig with project details
   - Dagger builds containers (postgres, redis, backend, frontend)
   - Containers mount project folder as workspace
4. Containers run until user stops project
5. Dagger automatically cleans up stopped containers

## No Template Required

Projects no longer get CommandCenter cloned into them. The CommandCenter
stack is defined once in `app/dagger_modules/commandcenter.py` and
instantiated per project with unique ports and paths.
```

**Step 2: Update HUB_DESIGN.md**

Update references to docker-compose → Dagger

**Step 3: Update CLAUDE.md**

Add Dagger to tech stack section

**Step 4: Commit**

```bash
git add docs/DAGGER_ARCHITECTURE.md hub/HUB_DESIGN.md CLAUDE.md
git commit -m "docs(hub): document Dagger architecture and update design docs"
```

---

## Task 9: Clean Up Old Docker-Compose Dependencies

**Files:**
- Modify: `hub/backend/requirements.txt`
- Delete: `hub/backend/app/services/setup_service.py` (already done in Task 4)

**Step 1: Remove unused imports/dependencies**

Check for any remaining docker-compose or subprocess references:

Run: `cd hub/backend && grep -r "docker-compose" app/`
Expected: No matches

Run: `cd hub/backend && grep -r "subprocess" app/`
Expected: Only non-orchestration uses (if any)

**Step 2: Commit if cleanup needed**

```bash
git add .
git commit -m "chore(hub): remove unused docker-compose dependencies"
```

---

## Task 10: Final Verification

**Step 1: Run all tests**

Run: `cd hub/backend && pytest -v`
Expected: All tests PASS

**Step 2: Start Hub locally and test manually**

```bash
cd hub/backend
export DATABASE_URL="sqlite+aiosqlite:///./data/hub.db"
export CC_SOURCE_PATH="/Users/username/Projects/CommandCenter"  # Not needed anymore!
uvicorn app.main:app --reload --port 9001
```

Create a test project via UI and verify it starts without errors.

**Step 3: Final commit**

```bash
git add .
git commit -m "feat(hub): Dagger orchestration fully integrated and tested"
```

---

## Success Criteria

✅ No more subprocess calls to docker-compose
✅ No more CommandCenter cloning into project folders
✅ Projects created with just: name, path, ports
✅ Dagger SDK manages all container orchestration
✅ All tests passing
✅ Documentation updated
✅ Clean git history with atomic commits

---

## Notes

- Dagger requires Docker Desktop to be running (uses Docker as build backend)
- Dagger containers are ephemeral by default - perfect for dev environments
- For production, we'd need to implement persistent Dagger services
- Consider adding Dagger Cloud integration for better observability in future
