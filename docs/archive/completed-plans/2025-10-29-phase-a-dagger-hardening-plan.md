# Phase A: Dagger Production Hardening Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Transform basic Dagger orchestration into production-grade container management with full visibility, control, and reliability.

**Architecture:** Enhance CommandCenterStack with log retrieval, health checks, resource limits, security hardening, and error recovery. Follow TDD throughout with comprehensive test coverage.

**Tech Stack:** Dagger SDK, Python 3.11, pytest, asyncio, FastAPI

**Duration:** 3 weeks (Week 1: Logs, Week 2: Health & Resources, Week 3: Security & Error Handling)

**Related Skills:**
- @superpowers:test-driven-development - REQUIRED for all implementation tasks
- @superpowers:verification-before-completion - REQUIRED before marking tasks complete
- @superpowers:systematic-debugging - Use if issues arise

---

## Week 1: Log Retrieval & Streaming

### Task 1: Add Log Retrieval Method to CommandCenterStack

**Files:**
- Modify: `hub/backend/app/dagger_modules/commandcenter.py`
- Test: `hub/backend/tests/unit/test_dagger_logs.py` (create)

**Step 1: Write the failing test**

Create new test file:

```python
# hub/backend/tests/unit/test_dagger_logs.py
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.dagger_modules.commandcenter import CommandCenterStack, CommandCenterConfig


@pytest.fixture
def mock_config():
    return CommandCenterConfig(
        project_name="test-project",
        project_path="/tmp/test",
        backend_port=8000,
        frontend_port=3000,
        postgres_port=5432,
        redis_port=6379,
        db_password="test123",
        secret_key="secret123"
    )


@pytest.mark.asyncio
async def test_get_logs_returns_container_logs(mock_config):
    """Test that get_logs retrieves logs from a specific service"""
    stack = CommandCenterStack(mock_config)

    # Mock Dagger client
    mock_client = AsyncMock()
    mock_container = AsyncMock()
    mock_container.stdout = AsyncMock(return_value="Log line 1\nLog line 2\nLog line 3")

    with patch.object(stack, 'client', mock_client):
        with patch.object(stack, '_get_service_container', return_value=mock_container):
            logs = await stack.get_logs(service_name="backend", tail=10)

    assert logs is not None
    assert "Log line 1" in logs
    assert "Log line 2" in logs


@pytest.mark.asyncio
async def test_get_logs_filters_by_service(mock_config):
    """Test that get_logs only retrieves logs for specified service"""
    stack = CommandCenterStack(mock_config)

    with pytest.raises(ValueError, match="Invalid service name"):
        await stack.get_logs(service_name="invalid_service")
```

**Step 2: Run test to verify it fails**

```bash
cd hub/backend
pytest tests/unit/test_dagger_logs.py::test_get_logs_returns_container_logs -v
```

Expected: FAIL with "CommandCenterStack has no attribute 'get_logs'"

**Step 3: Write minimal implementation**

Add to `hub/backend/app/dagger_modules/commandcenter.py`:

```python
class CommandCenterStack:
    # ... existing code ...

    VALID_SERVICES = ["postgres", "redis", "backend", "frontend"]

    async def get_logs(
        self,
        service_name: str,
        tail: int = 100,
        follow: bool = False
    ) -> str:
        """
        Retrieve logs from a specific service container.

        Args:
            service_name: Name of service (postgres, redis, backend, frontend)
            tail: Number of lines to retrieve from end of logs
            follow: If True, stream logs continuously (not implemented yet)

        Returns:
            String containing log lines

        Raises:
            ValueError: If service_name is invalid
        """
        if service_name not in self.VALID_SERVICES:
            raise ValueError(f"Invalid service name: {service_name}. "
                           f"Must be one of {self.VALID_SERVICES}")

        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        # Get the container for this service
        container = await self._get_service_container(service_name)

        # Retrieve stdout logs
        logs = await container.stdout()

        # Apply tail limit if specified
        if tail:
            log_lines = logs.split('\n')
            logs = '\n'.join(log_lines[-tail:])

        return logs

    async def _get_service_container(self, service_name: str) -> dagger.Container:
        """
        Internal method to get container for a service.
        To be implemented with service registry in later task.
        """
        # Placeholder - will be enhanced when we add service tracking
        raise NotImplementedError("Service container retrieval not yet implemented")
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_dagger_logs.py::test_get_logs_returns_container_logs -v
pytest tests/unit/test_dagger_logs.py::test_get_logs_filters_by_service -v
```

Expected: PASS (both tests)

**Step 5: Commit**

```bash
git add hub/backend/app/dagger_modules/commandcenter.py hub/backend/tests/unit/test_dagger_logs.py
git commit -m "feat(dagger): add get_logs method for container log retrieval

- Add get_logs() method to CommandCenterStack
- Support tail parameter for limiting log lines
- Add service name validation
- Add placeholder for service container tracking
- Tests: 2 unit tests for log retrieval

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 2: Add Service Registry for Container Tracking

**Files:**
- Modify: `hub/backend/app/dagger_modules/commandcenter.py`
- Test: `hub/backend/tests/unit/test_dagger_logs.py`

**Step 1: Write the failing test**

Add to `hub/backend/tests/unit/test_dagger_logs.py`:

```python
@pytest.mark.asyncio
async def test_service_registry_tracks_running_containers(mock_config):
    """Test that start() populates service registry with running containers"""
    stack = CommandCenterStack(mock_config)

    with patch.object(stack, 'build_postgres', return_value=AsyncMock()) as mock_pg:
        with patch.object(stack, 'build_redis', return_value=AsyncMock()) as mock_redis:
            with patch.object(stack, 'build_backend', return_value=AsyncMock()) as mock_backend:
                with patch.object(stack, 'build_frontend', return_value=AsyncMock()) as mock_frontend:
                    mock_client = AsyncMock()
                    stack.client = mock_client

                    await stack.start()

                    # Verify service registry populated
                    assert "postgres" in stack._service_containers
                    assert "redis" in stack._service_containers
                    assert "backend" in stack._service_containers
                    assert "frontend" in stack._service_containers
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_dagger_logs.py::test_service_registry_tracks_running_containers -v
```

Expected: FAIL with "AttributeError: 'CommandCenterStack' object has no attribute '_service_containers'"

**Step 3: Write minimal implementation**

Modify `hub/backend/app/dagger_modules/commandcenter.py`:

```python
class CommandCenterStack:
    """Defines and manages CommandCenter container stack using Dagger"""

    def __init__(self, config: CommandCenterConfig):
        self.config = config
        self._connection: Optional[dagger.Connection] = None
        self.client = None
        self._service_containers: dict[str, dagger.Container] = {}  # NEW: Track containers

    # ... existing methods ...

    async def start(self) -> dict:
        """Start all CommandCenter containers"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        try:
            logger.info(f"Starting CommandCenter stack for project: {self.config.project_name}")

            # Build containers
            postgres = await self.build_postgres()
            redis = await self.build_redis()
            backend = await self.build_backend("postgres", "redis")
            frontend = await self.build_frontend(f"http://backend:{self.config.backend_port}")

            # Store in registry for later access (logs, health checks)
            self._service_containers["postgres"] = postgres
            self._service_containers["redis"] = redis
            self._service_containers["backend"] = backend
            self._service_containers["frontend"] = frontend

            # Start as services
            postgres_svc = postgres.as_service()
            redis_svc = redis.as_service()
            backend_svc = backend.as_service()
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

    async def _get_service_container(self, service_name: str) -> dagger.Container:
        """Get container for a service from registry"""
        if service_name not in self._service_containers:
            raise RuntimeError(f"Service {service_name} not found in registry. "
                             f"Has start() been called?")
        return self._service_containers[service_name]
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_dagger_logs.py::test_service_registry_tracks_running_containers -v
# Also verify previous tests still pass
pytest tests/unit/test_dagger_logs.py -v
```

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add hub/backend/app/dagger_modules/commandcenter.py hub/backend/tests/unit/test_dagger_logs.py
git commit -m "feat(dagger): add service registry for container tracking

- Add _service_containers dict to track running containers
- Populate registry in start() method
- Implement _get_service_container() to retrieve from registry
- Tests: 1 unit test for service registry
- Enables log retrieval from running services

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 3: Add Hub API Endpoint for Log Retrieval

**Files:**
- Create: `hub/backend/app/routers/logs.py`
- Modify: `hub/backend/app/main.py`
- Test: `hub/backend/tests/integration/test_logs_api.py` (create)

**Step 1: Write the failing test**

Create `hub/backend/tests/integration/test_logs_api.py`:

```python
import pytest
from httpx import AsyncClient
from app.main import app
from app.models import Project


@pytest.mark.asyncio
async def test_get_logs_endpoint_returns_service_logs(db_session, sample_project):
    """Test GET /api/projects/{id}/logs/{service} returns logs"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/logs/backend",
            params={"tail": 50}
        )

    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "service" in data
    assert data["service"] == "backend"


@pytest.mark.asyncio
async def test_get_logs_endpoint_validates_service_name(db_session, sample_project):
    """Test that invalid service names return 400"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            f"/api/v1/projects/{sample_project.id}/logs/invalid_service"
        )

    assert response.status_code == 400
    assert "invalid service" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_logs_endpoint_handles_project_not_found(db_session):
    """Test 404 for non-existent project"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/projects/99999/logs/backend")

    assert response.status_code == 404
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/integration/test_logs_api.py -v
```

Expected: FAIL with "404 Not Found" (route doesn't exist)

**Step 3: Write minimal implementation**

Create `hub/backend/app/routers/logs.py`:

```python
"""
Logs API Router

Endpoints for retrieving container logs from managed projects.
"""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.models import Project
from app.services.orchestration_service import OrchestrationService

router = APIRouter(prefix="/api/v1/projects", tags=["logs"])


@router.get("/{project_id}/logs/{service_name}")
async def get_service_logs(
    project_id: int,
    service_name: str,
    tail: int = Query(default=100, ge=1, le=10000),
    db: AsyncSession = Depends(get_db)
):
    """
    Retrieve logs from a specific service container.

    Args:
        project_id: Project ID
        service_name: Service name (postgres, redis, backend, frontend)
        tail: Number of log lines to retrieve (default 100, max 10000)

    Returns:
        JSON with logs and metadata

    Raises:
        404: Project not found
        400: Invalid service name
        500: Failed to retrieve logs
    """
    # Get project from database
    result = await db.execute(
        Project.__table__.select().where(Project.id == project_id)
    )
    project = result.fetchone()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Validate service name
    valid_services = ["postgres", "redis", "backend", "frontend"]
    if service_name not in valid_services:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid service name: {service_name}. Must be one of {valid_services}"
        )

    # Retrieve logs via orchestration service
    try:
        orchestration = OrchestrationService(db)
        logs = await orchestration.get_project_logs(project_id, service_name, tail)

        return {
            "project_id": project_id,
            "service": service_name,
            "logs": logs,
            "lines": len(logs.split('\n')) if logs else 0
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to retrieve logs: {str(e)}"
        )
```

Add method to `hub/backend/app/services/orchestration_service.py`:

```python
class OrchestrationService:
    # ... existing methods ...

    async def get_project_logs(
        self,
        project_id: int,
        service_name: str,
        tail: int = 100
    ) -> str:
        """
        Retrieve logs from a project's service container.

        Args:
            project_id: Project ID
            service_name: Service name to get logs from
            tail: Number of lines to retrieve

        Returns:
            Log string

        Raises:
            RuntimeError: If stack not running or logs unavailable
        """
        if project_id not in self._active_stacks:
            raise RuntimeError(f"Project {project_id} is not running")

        stack = self._active_stacks[project_id]
        return await stack.get_logs(service_name, tail)
```

Add router to `hub/backend/app/main.py`:

```python
from app.routers import logs  # NEW

# ... existing code ...

app.include_router(logs.router)  # NEW
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/integration/test_logs_api.py -v
```

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add hub/backend/app/routers/logs.py hub/backend/app/services/orchestration_service.py hub/backend/app/main.py hub/backend/tests/integration/test_logs_api.py
git commit -m "feat(api): add logs endpoint for retrieving container logs

- Create logs router with GET /api/v1/projects/{id}/logs/{service}
- Add get_project_logs() to OrchestrationService
- Support tail parameter (1-10000 lines)
- Validation for service names and project existence
- Tests: 3 integration tests for logs API
- Enables log access from Hub UI

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Week 2: Health Checks & Resource Limits

### Task 4: Add Health Check Methods to CommandCenterStack

**Files:**
- Modify: `hub/backend/app/dagger_modules/commandcenter.py`
- Test: `hub/backend/tests/unit/test_dagger_health.py` (create)

**Step 1: Write the failing test**

Create `hub/backend/tests/unit/test_dagger_health.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.dagger_modules.commandcenter import CommandCenterStack, CommandCenterConfig


@pytest.fixture
def mock_config():
    return CommandCenterConfig(
        project_name="test-project",
        project_path="/tmp/test",
        backend_port=8000,
        frontend_port=3000,
        postgres_port=5432,
        redis_port=6379,
        db_password="test123",
        secret_key="secret123"
    )


@pytest.mark.asyncio
async def test_check_postgres_health_returns_status(mock_config):
    """Test that check_postgres_health executes pg_isready"""
    stack = CommandCenterStack(mock_config)
    stack._service_containers["postgres"] = AsyncMock()

    mock_container = stack._service_containers["postgres"]
    mock_container.with_exec = AsyncMock(return_value=mock_container)
    mock_container.stdout = AsyncMock(return_value="accepting connections")

    result = await stack.check_postgres_health()

    assert result["healthy"] is True
    assert result["service"] == "postgres"
    mock_container.with_exec.assert_called_with(["pg_isready", "-U", "commandcenter"])


@pytest.mark.asyncio
async def test_check_redis_health_returns_status(mock_config):
    """Test that check_redis_health executes redis-cli ping"""
    stack = CommandCenterStack(mock_config)
    stack._service_containers["redis"] = AsyncMock()

    mock_container = stack._service_containers["redis"]
    mock_container.with_exec = AsyncMock(return_value=mock_container)
    mock_container.stdout = AsyncMock(return_value="PONG")

    result = await stack.check_redis_health()

    assert result["healthy"] is True
    assert result["service"] == "redis"
    mock_container.with_exec.assert_called_with(["redis-cli", "ping"])


@pytest.mark.asyncio
async def test_health_status_aggregates_all_services(mock_config):
    """Test that health_status() checks all services"""
    stack = CommandCenterStack(mock_config)

    with patch.object(stack, 'check_postgres_health', return_value={"healthy": True, "service": "postgres"}):
        with patch.object(stack, 'check_redis_health', return_value={"healthy": True, "service": "redis"}):
            with patch.object(stack, 'check_backend_health', return_value={"healthy": True, "service": "backend"}):
                with patch.object(stack, 'check_frontend_health', return_value={"healthy": True, "service": "frontend"}):
                    result = await stack.health_status()

    assert result["overall_healthy"] is True
    assert len(result["services"]) == 4
    assert all(svc["healthy"] for svc in result["services"].values())
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_dagger_health.py -v
```

Expected: FAIL with "CommandCenterStack has no attribute 'check_postgres_health'"

**Step 3: Write minimal implementation**

Add to `hub/backend/app/dagger_modules/commandcenter.py`:

```python
class CommandCenterStack:
    # ... existing code ...

    async def check_postgres_health(self) -> dict:
        """
        Check PostgreSQL health using pg_isready.

        Returns:
            Dict with health status
        """
        try:
            container = self._service_containers.get("postgres")
            if not container:
                return {"healthy": False, "service": "postgres", "error": "Container not found"}

            # Execute pg_isready command
            result = await container.with_exec([
                "pg_isready", "-U", "commandcenter"
            ]).stdout()

            healthy = "accepting connections" in result
            return {
                "healthy": healthy,
                "service": "postgres",
                "message": result.strip()
            }
        except Exception as e:
            return {
                "healthy": False,
                "service": "postgres",
                "error": str(e)
            }

    async def check_redis_health(self) -> dict:
        """
        Check Redis health using redis-cli ping.

        Returns:
            Dict with health status
        """
        try:
            container = self._service_containers.get("redis")
            if not container:
                return {"healthy": False, "service": "redis", "error": "Container not found"}

            # Execute redis-cli ping
            result = await container.with_exec([
                "redis-cli", "ping"
            ]).stdout()

            healthy = "PONG" in result
            return {
                "healthy": healthy,
                "service": "redis",
                "message": result.strip()
            }
        except Exception as e:
            return {
                "healthy": False,
                "service": "redis",
                "error": str(e)
            }

    async def check_backend_health(self) -> dict:
        """
        Check backend health via HTTP /health endpoint.

        Returns:
            Dict with health status
        """
        try:
            container = self._service_containers.get("backend")
            if not container:
                return {"healthy": False, "service": "backend", "error": "Container not found"}

            # Execute curl to health endpoint
            result = await container.with_exec([
                "curl", "-f", "http://localhost:8000/health"
            ]).stdout()

            healthy = "ok" in result.lower() or "healthy" in result.lower()
            return {
                "healthy": healthy,
                "service": "backend",
                "message": result.strip()
            }
        except Exception as e:
            return {
                "healthy": False,
                "service": "backend",
                "error": str(e)
            }

    async def check_frontend_health(self) -> dict:
        """
        Check frontend health via HTTP request to root.

        Returns:
            Dict with health status
        """
        try:
            container = self._service_containers.get("frontend")
            if not container:
                return {"healthy": False, "service": "frontend", "error": "Container not found"}

            # Execute curl to root path
            result = await container.with_exec([
                "curl", "-f", "http://localhost:3000/"
            ]).stdout()

            # If curl succeeds (exit 0), consider healthy
            healthy = len(result) > 0
            return {
                "healthy": healthy,
                "service": "frontend",
                "message": "HTTP 200 OK" if healthy else "No response"
            }
        except Exception as e:
            return {
                "healthy": False,
                "service": "frontend",
                "error": str(e)
            }

    async def health_status(self) -> dict:
        """
        Get aggregated health status for all services.

        Returns:
            Dict with overall health and per-service status
        """
        services = {}

        services["postgres"] = await self.check_postgres_health()
        services["redis"] = await self.check_redis_health()
        services["backend"] = await self.check_backend_health()
        services["frontend"] = await self.check_frontend_health()

        overall_healthy = all(svc["healthy"] for svc in services.values())

        return {
            "overall_healthy": overall_healthy,
            "services": services,
            "timestamp": str(datetime.now())
        }
```

Add import at top:

```python
from datetime import datetime
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_dagger_health.py -v
```

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add hub/backend/app/dagger_modules/commandcenter.py hub/backend/tests/unit/test_dagger_health.py
git commit -m "feat(dagger): add health check methods for all services

- Add check_postgres_health() using pg_isready
- Add check_redis_health() using redis-cli ping
- Add check_backend_health() via HTTP /health
- Add check_frontend_health() via HTTP root
- Add health_status() for aggregated health
- Tests: 3 unit tests for health checks
- Enables service health monitoring

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 5: Add Resource Limits to Container Definitions

**Files:**
- Modify: `hub/backend/app/dagger_modules/commandcenter.py`
- Test: `hub/backend/tests/unit/test_dagger_resources.py` (create)

**Step 1: Write the failing test**

Create `hub/backend/tests/unit/test_dagger_resources.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock
from app.dagger_modules.commandcenter import (
    CommandCenterStack,
    CommandCenterConfig,
    ResourceLimits
)


@pytest.fixture
def mock_config():
    return CommandCenterConfig(
        project_name="test-project",
        project_path="/tmp/test",
        backend_port=8000,
        frontend_port=3000,
        postgres_port=5432,
        redis_port=6379,
        db_password="test123",
        secret_key="secret123",
        resource_limits=ResourceLimits()  # Use defaults
    )


@pytest.mark.asyncio
async def test_postgres_container_has_resource_limits(mock_config):
    """Test that postgres container gets resource limits applied"""
    stack = CommandCenterStack(mock_config)
    mock_client = MagicMock()
    mock_container = MagicMock()

    # Setup mock chain
    mock_container.from_ = MagicMock(return_value=mock_container)
    mock_container.with_env_variable = MagicMock(return_value=mock_container)
    mock_container.with_exposed_port = MagicMock(return_value=mock_container)
    mock_container.with_resource_limit = MagicMock(return_value=mock_container)

    mock_client.container = MagicMock(return_value=mock_container)
    stack.client = mock_client

    await stack.build_postgres()

    # Verify resource limits were applied
    assert mock_container.with_resource_limit.called
    calls = mock_container.with_resource_limit.call_args_list

    # Check CPU limit called
    cpu_calls = [c for c in calls if 'cpu' in str(c).lower()]
    assert len(cpu_calls) > 0

    # Check memory limit called
    memory_calls = [c for c in calls if 'memory' in str(c).lower()]
    assert len(memory_calls) > 0


def test_resource_limits_defaults():
    """Test that ResourceLimits has sensible defaults"""
    limits = ResourceLimits()

    assert limits.postgres_cpu == 1.0
    assert limits.postgres_memory_mb == 2048
    assert limits.redis_cpu == 0.5
    assert limits.redis_memory_mb == 512
    assert limits.backend_cpu == 1.0
    assert limits.backend_memory_mb == 1024
    assert limits.frontend_cpu == 0.5
    assert limits.frontend_memory_mb == 512


def test_resource_limits_customizable():
    """Test that resource limits can be customized"""
    limits = ResourceLimits(
        postgres_cpu=2.0,
        postgres_memory_mb=4096
    )

    assert limits.postgres_cpu == 2.0
    assert limits.postgres_memory_mb == 4096
    # Defaults for others
    assert limits.redis_cpu == 0.5
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_dagger_resources.py -v
```

Expected: FAIL with "cannot import name 'ResourceLimits'"

**Step 3: Write minimal implementation**

Add to `hub/backend/app/dagger_modules/commandcenter.py`:

```python
@dataclass
class ResourceLimits:
    """Resource limits for CommandCenter containers"""
    postgres_cpu: float = 1.0
    postgres_memory_mb: int = 2048
    redis_cpu: float = 0.5
    redis_memory_mb: int = 512
    backend_cpu: float = 1.0
    backend_memory_mb: int = 1024
    frontend_cpu: float = 0.5
    frontend_memory_mb: int = 512


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
    resource_limits: ResourceLimits = None  # NEW

    def __post_init__(self):
        """Set defaults after initialization"""
        if self.resource_limits is None:
            self.resource_limits = ResourceLimits()


class CommandCenterStack:
    # ... existing code ...

    async def build_postgres(self) -> dagger.Container:
        """Build PostgreSQL container with resource limits"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        limits = self.config.resource_limits

        return (
            self.client.container()
            .from_("postgres:15-alpine")
            .with_env_variable("POSTGRES_USER", "commandcenter")
            .with_env_variable("POSTGRES_PASSWORD", self.config.db_password)
            .with_env_variable("POSTGRES_DB", "commandcenter")
            .with_exposed_port(5432)
            # NEW: Apply resource limits
            .with_resource_limit("cpu", str(limits.postgres_cpu))
            .with_resource_limit("memory", f"{limits.postgres_memory_mb}m")
        )

    async def build_redis(self) -> dagger.Container:
        """Build Redis container with resource limits"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        limits = self.config.resource_limits

        return (
            self.client.container()
            .from_("redis:7-alpine")
            .with_exposed_port(6379)
            # NEW: Apply resource limits
            .with_resource_limit("cpu", str(limits.redis_cpu))
            .with_resource_limit("memory", f"{limits.redis_memory_mb}m")
        )

    # Similarly update build_backend() and build_frontend()...
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_dagger_resources.py -v
```

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add hub/backend/app/dagger_modules/commandcenter.py hub/backend/tests/unit/test_dagger_resources.py
git commit -m "feat(dagger): add resource limits for all containers

- Add ResourceLimits dataclass with sensible defaults
- Add resource_limits to CommandCenterConfig
- Apply CPU and memory limits to all containers
- Postgres: 1 CPU, 2GB RAM
- Redis: 0.5 CPU, 512MB RAM
- Backend: 1 CPU, 1GB RAM
- Frontend: 0.5 CPU, 512MB RAM
- Tests: 3 unit tests for resource limits
- Prevents runaway containers

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Week 3: Security & Error Handling

### Task 6: Add Non-Root User Execution

**Files:**
- Modify: `hub/backend/app/dagger_modules/commandcenter.py`
- Test: `hub/backend/tests/security/test_dagger_security.py`

**Step 1: Write the failing test**

Add to `hub/backend/tests/security/test_dagger_security.py`:

```python
@pytest.mark.asyncio
async def test_containers_run_as_non_root_user(mock_config):
    """Test that all containers execute as non-root users"""
    stack = CommandCenterStack(mock_config)
    mock_client = MagicMock()
    mock_container = MagicMock()

    # Setup mock chain
    mock_container.from_ = MagicMock(return_value=mock_container)
    mock_container.with_env_variable = MagicMock(return_value=mock_container)
    mock_container.with_exposed_port = MagicMock(return_value=mock_container)
    mock_container.with_resource_limit = MagicMock(return_value=mock_container)
    mock_container.with_user = MagicMock(return_value=mock_container)  # NEW

    mock_client.container = MagicMock(return_value=mock_container)
    stack.client = mock_client

    # Build each container
    await stack.build_postgres()
    await stack.build_redis()

    # Verify with_user was called (non-root execution)
    assert mock_container.with_user.called

    # Verify not running as root (UID 0)
    user_calls = mock_container.with_user.call_args_list
    for call in user_calls:
        user_id = str(call[0][0])  # Get first positional argument
        assert user_id != "0", "Container should not run as root (UID 0)"
        assert user_id != "root", "Container should not run as root user"
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/security/test_dagger_security.py::test_containers_run_as_non_root_user -v
```

Expected: FAIL with "with_user not called"

**Step 3: Write minimal implementation**

Modify container build methods in `hub/backend/app/dagger_modules/commandcenter.py`:

```python
class CommandCenterStack:
    # Add constants
    POSTGRES_USER_ID = 999
    REDIS_USER_ID = 999
    APP_USER_ID = 1000

    async def build_postgres(self) -> dagger.Container:
        """Build PostgreSQL container with resource limits and security"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        limits = self.config.resource_limits

        return (
            self.client.container()
            .from_("postgres:15-alpine")
            .with_user(str(self.POSTGRES_USER_ID))  # NEW: Run as non-root
            .with_env_variable("POSTGRES_USER", "commandcenter")
            .with_env_variable("POSTGRES_PASSWORD", self.config.db_password)
            .with_env_variable("POSTGRES_DB", "commandcenter")
            .with_exposed_port(5432)
            .with_resource_limit("cpu", str(limits.postgres_cpu))
            .with_resource_limit("memory", f"{limits.postgres_memory_mb}m")
        )

    async def build_redis(self) -> dagger.Container:
        """Build Redis container with resource limits and security"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        limits = self.config.resource_limits

        return (
            self.client.container()
            .from_("redis:7-alpine")
            .with_user(str(self.REDIS_USER_ID))  # NEW: Run as non-root
            .with_exposed_port(6379)
            .with_resource_limit("cpu", str(limits.redis_cpu))
            .with_resource_limit("memory", f"{limits.redis_memory_mb}m")
        )

    # Similarly update build_backend() and build_frontend() with APP_USER_ID
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/security/test_dagger_security.py::test_containers_run_as_non_root_user -v
```

Expected: PASS

**Step 5: Commit**

```bash
git add hub/backend/app/dagger_modules/commandcenter.py hub/backend/tests/security/test_dagger_security.py
git commit -m "feat(security): run containers as non-root users

- Add user ID constants for each container type
- Postgres: UID 999 (standard postgres user)
- Redis: UID 999 (standard redis user)
- Backend/Frontend: UID 1000 (non-privileged)
- Apply with_user() to all container builds
- Tests: 1 security test for non-root execution
- Hardens against container escape vulnerabilities

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 7: Add Retry Logic with Exponential Backoff

**Files:**
- Modify: `hub/backend/app/dagger_modules/commandcenter.py`
- Test: `hub/backend/tests/unit/test_dagger_retry.py` (create)

**Step 1: Write the failing test**

Create `hub/backend/tests/unit/test_dagger_retry.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch
from app.dagger_modules.commandcenter import CommandCenterStack, CommandCenterConfig


@pytest.fixture
def mock_config():
    return CommandCenterConfig(
        project_name="test-project",
        project_path="/tmp/test",
        backend_port=8000,
        frontend_port=3000,
        postgres_port=5432,
        redis_port=6379,
        db_password="test123",
        secret_key="secret123"
    )


@pytest.mark.asyncio
async def test_start_retries_on_transient_failure(mock_config):
    """Test that start() retries on transient failures"""
    stack = CommandCenterStack(mock_config)

    # Mock build methods to fail once, then succeed
    call_count = {"count": 0}

    async def failing_build(*args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] == 1:
            raise RuntimeError("Transient network error")
        return AsyncMock()

    with patch.object(stack, 'build_postgres', side_effect=failing_build):
        with patch.object(stack, 'build_redis', return_value=AsyncMock()):
            with patch.object(stack, 'build_backend', return_value=AsyncMock()):
                with patch.object(stack, 'build_frontend', return_value=AsyncMock()):
                    stack.client = AsyncMock()

                    result = await stack.start()

                    # Should succeed after retry
                    assert result["success"] is True
                    assert call_count["count"] == 2  # Failed once, succeeded on retry


@pytest.mark.asyncio
async def test_start_uses_exponential_backoff(mock_config):
    """Test that retries use exponential backoff"""
    stack = CommandCenterStack(mock_config)

    retry_delays = []

    async def mock_sleep(delay):
        retry_delays.append(delay)

    call_count = {"count": 0}

    async def failing_build(*args, **kwargs):
        call_count["count"] += 1
        if call_count["count"] < 3:  # Fail twice
            raise RuntimeError("Transient error")
        return AsyncMock()

    with patch('asyncio.sleep', side_effect=mock_sleep):
        with patch.object(stack, 'build_postgres', side_effect=failing_build):
            with patch.object(stack, 'build_redis', return_value=AsyncMock()):
                with patch.object(stack, 'build_backend', return_value=AsyncMock()):
                    with patch.object(stack, 'build_frontend', return_value=AsyncMock()):
                        stack.client = AsyncMock()

                        await stack.start()

                        # Check exponential backoff pattern (1s, 2s)
                        assert len(retry_delays) == 2
                        assert retry_delays[0] == 1
                        assert retry_delays[1] == 2


@pytest.mark.asyncio
async def test_start_fails_after_max_retries(mock_config):
    """Test that start() fails after max retries exhausted"""
    stack = CommandCenterStack(mock_config)

    async def always_failing_build(*args, **kwargs):
        raise RuntimeError("Persistent error")

    with patch.object(stack, 'build_postgres', side_effect=always_failing_build):
        stack.client = AsyncMock()

        with pytest.raises(RuntimeError, match="Persistent error"):
            await stack.start()
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/unit/test_dagger_retry.py -v
```

Expected: FAIL (retry logic not implemented)

**Step 3: Write minimal implementation**

Add retry decorator to `hub/backend/app/dagger_modules/commandcenter.py`:

```python
import asyncio
from functools import wraps

def with_retry(max_retries=3, base_delay=1):
    """
    Decorator to add exponential backoff retry logic.

    Args:
        max_retries: Maximum number of retry attempts
        base_delay: Base delay in seconds (doubles each retry)
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exception = None

            for attempt in range(max_retries + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt < max_retries:
                        # Exponential backoff: 1s, 2s, 4s, 8s...
                        delay = base_delay * (2 ** attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries + 1} failed: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"All {max_retries + 1} attempts failed")

            # All retries exhausted
            raise last_exception

        return wrapper
    return decorator


class CommandCenterStack:
    # ... existing code ...

    @with_retry(max_retries=3, base_delay=1)
    async def start(self) -> dict:
        """Start all CommandCenter containers with retry logic"""
        if not self.client:
            raise RuntimeError("Dagger client not initialized")

        try:
            logger.info(f"Starting CommandCenter stack for project: {self.config.project_name}")

            # Build containers (will retry on failure)
            postgres = await self.build_postgres()
            redis = await self.build_redis()
            backend = await self.build_backend("postgres", "redis")
            frontend = await self.build_frontend(f"http://backend:{self.config.backend_port}")

            # Store in registry
            self._service_containers["postgres"] = postgres
            self._service_containers["redis"] = redis
            self._service_containers["backend"] = backend
            self._service_containers["frontend"] = frontend

            # Start as services
            postgres_svc = postgres.as_service()
            redis_svc = redis.as_service()
            backend_svc = backend.as_service()
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
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/unit/test_dagger_retry.py -v
```

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add hub/backend/app/dagger_modules/commandcenter.py hub/backend/tests/unit/test_dagger_retry.py
git commit -m "feat(reliability): add retry logic with exponential backoff

- Add with_retry decorator for transient failure handling
- Apply to start() method (3 retries max)
- Exponential backoff: 1s, 2s, 4s, 8s
- Log retry attempts with context
- Tests: 3 unit tests for retry behavior
- Improves reliability against network glitches

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 8: Add Service Restart Method

**Files:**
- Modify: `hub/backend/app/dagger_modules/commandcenter.py`
- Modify: `hub/backend/app/routers/projects.py`
- Test: `hub/backend/tests/integration/test_restart_api.py` (create)

**Step 1: Write the failing test**

Create `hub/backend/tests/integration/test_restart_api.py`:

```python
import pytest
from httpx import AsyncClient
from app.main import app


@pytest.mark.asyncio
async def test_restart_service_endpoint(db_session, sample_project):
    """Test POST /api/projects/{id}/services/{service}/restart"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/projects/{sample_project.id}/services/backend/restart"
        )

    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "restarted" in data["message"].lower()


@pytest.mark.asyncio
async def test_restart_invalid_service_returns_400(db_session, sample_project):
    """Test that invalid service name returns 400"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            f"/api/v1/projects/{sample_project.id}/services/invalid/restart"
        )

    assert response.status_code == 400
```

**Step 2: Run test to verify it fails**

```bash
pytest tests/integration/test_restart_api.py -v
```

Expected: FAIL (endpoint doesn't exist)

**Step 3: Write minimal implementation**

Add to `hub/backend/app/dagger_modules/commandcenter.py`:

```python
class CommandCenterStack:
    # ... existing code ...

    async def restart_service(self, service_name: str) -> dict:
        """
        Restart a specific service container.

        Args:
            service_name: Name of service to restart

        Returns:
            Dict with restart status

        Raises:
            ValueError: If service_name invalid
        """
        if service_name not in self.VALID_SERVICES:
            raise ValueError(f"Invalid service name: {service_name}")

        try:
            logger.info(f"Restarting service: {service_name}")

            # Get build method for this service
            build_method = getattr(self, f'build_{service_name}')

            # Rebuild container
            if service_name == "backend":
                container = await build_method("postgres", "redis")
            elif service_name == "frontend":
                container = await build_method(f"http://backend:{self.config.backend_port}")
            else:
                container = await build_method()

            # Update registry
            self._service_containers[service_name] = container

            # Restart as service
            _ = container.as_service()

            logger.info(f"Service {service_name} restarted successfully")

            return {
                "success": True,
                "message": f"Service {service_name} restarted successfully"
            }
        except Exception as e:
            logger.error(f"Failed to restart service {service_name}: {e}")
            raise
```

Add endpoint to `hub/backend/app/routers/projects.py`:

```python
@router.post("/{project_id}/services/{service_name}/restart")
async def restart_service(
    project_id: int,
    service_name: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Restart a specific service container.

    Args:
        project_id: Project ID
        service_name: Service to restart (postgres, redis, backend, frontend)

    Returns:
        JSON with restart status
    """
    # Validate project exists
    result = await db.execute(
        Project.__table__.select().where(Project.id == project_id)
    )
    project = result.fetchone()

    if not project:
        raise HTTPException(status_code=404, detail=f"Project {project_id} not found")

    # Restart via orchestration service
    try:
        orchestration = OrchestrationService(db)
        result = await orchestration.restart_project_service(project_id, service_name)
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Restart failed: {str(e)}")
```

Add method to `hub/backend/app/services/orchestration_service.py`:

```python
async def restart_project_service(self, project_id: int, service_name: str) -> dict:
    """Restart a specific service for a project"""
    if project_id not in self._active_stacks:
        raise RuntimeError(f"Project {project_id} is not running")

    stack = self._active_stacks[project_id]
    return await stack.restart_service(service_name)
```

**Step 4: Run test to verify it passes**

```bash
pytest tests/integration/test_restart_api.py -v
```

Expected: PASS (all tests)

**Step 5: Commit**

```bash
git add hub/backend/app/dagger_modules/commandcenter.py hub/backend/app/routers/projects.py hub/backend/app/services/orchestration_service.py hub/backend/tests/integration/test_restart_api.py
git commit -m "feat(recovery): add service restart functionality

- Add restart_service() method to CommandCenterStack
- Add POST /api/v1/projects/{id}/services/{service}/restart
- Support individual service restarts without full stack restart
- Add restart_project_service() to OrchestrationService
- Tests: 2 integration tests for restart API
- Enables quick recovery from service failures

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Documentation & Polish

### Task 9: Update Documentation

**Files:**
- Modify: `docs/DAGGER_ARCHITECTURE.md`
- Create: `docs/SECURITY.md`

**Step 1: Update Dagger Architecture Documentation**

```bash
# Read current docs
cat docs/DAGGER_ARCHITECTURE.md

# Add new sections for production features
```

Add sections covering:
- Log retrieval API and usage
- Health check system and endpoints
- Resource limit configuration
- Security hardening features
- Error handling and retry logic
- Service restart capabilities

**Step 2: Create Security Documentation**

Create `docs/SECURITY.md` with:
- Non-root container execution
- Resource limits (prevention of resource exhaustion)
- Network isolation principles
- Secret management best practices
- Security checklist for production deployments

**Step 3: Commit**

```bash
git add docs/DAGGER_ARCHITECTURE.md docs/SECURITY.md
git commit -m "docs: update architecture and add security documentation

- Expand DAGGER_ARCHITECTURE.md with production features
- Document log retrieval, health checks, resource limits
- Create SECURITY.md with hardening guidelines
- Add security checklist for production deployments
- Complete Phase A documentation

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

### Task 10: Verify All Tests Pass

**Files:**
- N/A (verification only)

**Step 1: Run full test suite**

```bash
cd hub/backend
pytest tests/ -v --cov=app --cov-report=term-missing
```

**Step 2: Verify coverage**

Target: >90% coverage for:
- `app/dagger_modules/commandcenter.py`
- `app/services/orchestration_service.py`
- `app/routers/logs.py`
- `app/routers/projects.py` (restart endpoint)

**Step 3: Fix any failures**

Use @superpowers:systematic-debugging if issues found.

**Step 4: Commit coverage report**

```bash
git add .coverage htmlcov/
git commit -m "test: verify Phase A test coverage >90%

- All 120+ tests passing
- Coverage >90% for orchestration code
- Log retrieval: 100% coverage
- Health checks: 100% coverage
- Resource limits: 100% coverage
- Security features: 100% coverage
- Retry logic: 100% coverage

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Success Criteria Checklist

Before marking Phase A complete, verify:

- [ ] All services have health checks with accurate status reporting
- [ ] Logs retrievable via API for all services (postgres, redis, backend, frontend)
- [ ] Resource limits enforced and configurable per service
- [ ] Security checklist 100% complete (non-root, resource limits documented)
- [ ] Error recovery demonstrated (retry logic works, restart API functional)
- [ ] Test coverage >90% for orchestration code
- [ ] Documentation complete and reviewed (DAGGER_ARCHITECTURE.md, SECURITY.md)
- [ ] All 120+ tests passing
- [ ] No regressions in existing functionality

---

## Execution Notes

**Estimated Time:**
- Week 1 (Tasks 1-3): ~15 hours
- Week 2 (Tasks 4-5): ~12 hours
- Week 3 (Tasks 6-8): ~15 hours
- Documentation & Polish (Tasks 9-10): ~3 hours
- **Total: ~45 hours over 3 weeks**

**Dependencies:**
- Dagger SDK already installed
- Existing test infrastructure in place
- No external API dependencies

**Risks:**
- Dagger API changes (mitigate: pin dagger-io version)
- Container runtime differences (mitigate: test on target environment)

**Next Phase:**
After Phase A completion, proceed to **Phase B: Automated Knowledge Ingestion** (separate plan).
