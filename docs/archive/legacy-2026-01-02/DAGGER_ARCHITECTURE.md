# Dagger Architecture

CommandCenter Hub uses Dagger SDK for container orchestration instead of docker-compose.

## Overview

The CommandCenter Hub orchestrates multiple isolated CommandCenter instances across different projects. Instead of using subprocess calls to `docker-compose`, we leverage **Dagger's Python SDK** to define, build, and manage containers programmatically.

## Key Benefits

### 1. No CommandCenter Cloning Required
Previously, each project required a full CommandCenter clone into its folder. With Dagger, the CommandCenter stack is defined once as code in `hub/backend/app/dagger_modules/commandcenter.py` and instantiated per-project with unique configurations.

### 2. Type-Safe Container Configuration
Dagger's Python SDK provides:
- Type hints for all container operations
- IDE autocomplete and validation
- Compile-time error checking
- Clear API contracts

### 3. Better Error Handling
Instead of parsing `stderr` from subprocess calls, Dagger raises proper Python exceptions with detailed error messages. This makes debugging significantly easier.

### 4. Programmatic Control
Full control over container lifecycle:
- Start/stop containers with async/await
- Query container status in real-time
- Access container logs programmatically
- Manage service dependencies explicitly

### 5. Intelligent Caching
Dagger automatically caches:
- Container layer builds
- Dependency installations
- File system states

This results in faster subsequent starts and rebuilds.

## Architecture Flow

### Project Creation Flow

```
User creates project via Hub UI
        ↓
Hub Backend stores:
  - project name
  - project path (folder to mount)
  - port assignments (frontend, backend, postgres, redis)
  - status, timestamps
        ↓
No CommandCenter cloning occurs
Project folder remains untouched
```

### Project Start Flow

```
User clicks "Start" on project
        ↓
Hub creates CommandCenterConfig:
  - project_name: "MyProject"
  - project_path: "/Users/me/myproject"
  - ports: 8000, 3000, 5432, 6379
  - secrets: auto-generated db_password, secret_key
        ↓
Hub instantiates CommandCenterStack(config)
        ↓
Dagger SDK:
  1. Initializes Dagger client (connects to Docker)
  2. Builds PostgreSQL container (postgres:15-alpine)
  3. Builds Redis container (redis:7-alpine)
  4. Builds Backend container (python:3.11-slim)
     - Mounts project_path as /workspace
     - Installs Python dependencies
     - Sets environment variables
  5. Builds Frontend container (node:18-alpine)
     - Sets VITE_API_BASE_URL to backend
     - Installs Node dependencies
  6. Starts all containers as services
        ↓
Containers run with project folder mounted
User can access CommandCenter at localhost:<ports>
```

### Project Stop Flow

```
User clicks "Stop" on project
        ↓
Hub calls stack.stop()
        ↓
Dagger SDK:
  1. Stops all containers
  2. Cleans up resources
  3. Closes Dagger connection
        ↓
Containers removed automatically (ephemeral)
Project folder remains intact
```

## Core Components

### 1. CommandCenterConfig

Located in `hub/backend/app/dagger_modules/commandcenter.py`

```python
@dataclass
class CommandCenterConfig:
    """Configuration for a CommandCenter instance"""
    project_name: str       # Display name
    project_path: str       # Absolute path to project folder
    backend_port: int       # 8000, 8010, 8020...
    frontend_port: int      # 3000, 3010, 3020...
    postgres_port: int      # 5432, 5433, 5434...
    redis_port: int         # 6379, 6380, 6381...
    db_password: str        # Auto-generated per project
    secret_key: str         # Auto-generated per project
```

**Key Features:**
- Immutable dataclass for configuration
- All ports configurable per project (no conflicts)
- Secrets generated at runtime (not stored in database)
- Project path points directly to user's folder

### 2. CommandCenterStack

Located in `hub/backend/app/dagger_modules/commandcenter.py`

The main orchestration class that manages the complete CommandCenter stack.

#### Lifecycle Management

```python
class CommandCenterStack:
    async def __aenter__(self):
        """Initialize Dagger client connection"""
        self.client = dagger.Connection(dagger.Config())
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Cleanup Dagger client and containers"""
        if self.client:
            await self.client.__aexit__(exc_type, exc_val, exc_tb)
```

**Context Manager Pattern:**
- Automatic resource cleanup
- Proper exception handling
- Connection pooling via Dagger client

#### Container Builders

**PostgreSQL:**
```python
async def build_postgres(self) -> dagger.Container:
    return (
        self.client.container()
        .from_("postgres:15-alpine")
        .with_env_variable("POSTGRES_USER", "commandcenter")
        .with_env_variable("POSTGRES_PASSWORD", self.config.db_password)
        .with_env_variable("POSTGRES_DB", "commandcenter")
        .with_exposed_port(5432)
    )
```

**Redis:**
```python
async def build_redis(self) -> dagger.Container:
    return (
        self.client.container()
        .from_("redis:7-alpine")
        .with_exposed_port(6379)
    )
```

**Backend:**
```python
async def build_backend(self, postgres_host: str, redis_host: str) -> dagger.Container:
    project_dir = self.client.host().directory(self.config.project_path)

    return (
        self.client.container()
        .from_("python:3.11-slim")
        .with_exec(["pip", "install", "fastapi", "uvicorn[standard]", ...])
        .with_mounted_directory("/workspace", project_dir)  # Mount project folder
        .with_workdir("/workspace")
        .with_env_variable("DATABASE_URL", f"postgresql://...")
        .with_env_variable("REDIS_URL", f"redis://...")
        .with_env_variable("SECRET_KEY", self.config.secret_key)
        .with_exec(["uvicorn", "app.main:app", "--host", "0.0.0.0"])
        .with_exposed_port(8000)
    )
```

**Frontend:**
```python
async def build_frontend(self, backend_url: str) -> dagger.Container:
    return (
        self.client.container()
        .from_("node:18-alpine")
        .with_exec(["npm", "install", "-g", "vite", "react", "react-dom"])
        .with_env_variable("VITE_API_BASE_URL", backend_url)
        .with_exec(["npm", "run", "dev", "--", "--host", "0.0.0.0"])
        .with_exposed_port(3000)
    )
```

#### Container Mounting & Workspace Setup

**Key Concept: Mount, Don't Clone**

```python
# OLD WAY (docker-compose):
# - Clone CommandCenter to ~/myproject/commandcenter/
# - Run docker-compose in that directory
# - Project tightly coupled to CommandCenter copy

# NEW WAY (Dagger):
project_dir = self.client.host().directory(self.config.project_path)
container.with_mounted_directory("/workspace", project_dir)
```

**Benefits:**
- Project folder remains clean (no CommandCenter files)
- Single source of truth for CommandCenter code
- Easy to update all projects (update Hub, not each project)
- Read-only mounts prevent accidental modifications

**Mount Behavior:**
- Files from `project_path` appear in container at `/workspace`
- Changes in container persist to host (unless read-only mount)
- Dagger handles file watching and syncing automatically

### 3. OrchestrationService

Located in `hub/backend/app/services/orchestration_service.py`

Bridges the Hub database layer with Dagger stack management.

#### Active Stack Management

```python
class OrchestrationService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self._active_stacks: dict[int, CommandCenterStack] = {}
```

**Key Feature: In-Memory Stack Registry**
- Maps `project_id` → `CommandCenterStack` instance
- Keeps stacks alive while projects are running
- Allows real-time status queries without database roundtrips

#### Start Project

```python
async def start_project(self, project_id: int) -> dict:
    # 1. Check port availability
    # 2. Create CommandCenterConfig from project data
    # 3. Initialize CommandCenterStack
    # 4. Start stack (build & run containers)
    # 5. Store stack reference in _active_stacks
    # 6. Update project status in database
```

**Port Conflict Detection:**
```python
def _check_port_available(self, port: int) -> tuple[bool, str]:
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            result = sock.connect_ex(('localhost', port))
            return result != 0, ""
    except Exception:
        return True, ""
```

#### Stop Project

```python
async def stop_project(self, project_id: int) -> dict:
    # 1. Get stack from _active_stacks
    # 2. Call stack.stop() (graceful shutdown)
    # 3. Call stack.__aexit__() (cleanup)
    # 4. Remove from _active_stacks
    # 5. Update project status in database
```

**Graceful Shutdown:**
- Dagger automatically stops containers
- Resources cleaned up immediately
- No orphaned containers or networks

## No Template Required

### Old Architecture (docker-compose)

```
~/Projects/
├── performia/
│   └── commandcenter/          ← Full CC clone (1.2 GB)
│       ├── backend/
│       ├── frontend/
│       ├── docker-compose.yml
│       └── .env
├── ai-research/
│   └── commandcenter/          ← Full CC clone (1.2 GB)
│       ├── backend/
│       ├── frontend/
│       ├── docker-compose.yml
│       └── .env
└── ecommerce/
    └── commandcenter/          ← Full CC clone (1.2 GB)
        ├── backend/
        ├── frontend/
        ├── docker-compose.yml
        └── .env

Total: 3.6 GB for 3 projects
```

**Problems:**
- Disk space waste (duplicate code)
- Update nightmare (must update each clone)
- Version drift (projects on different CC versions)
- Cluttered project folders

### New Architecture (Dagger)

```
~/Projects/
├── performia/                  ← Clean project folder
│   ├── src/
│   ├── docs/
│   └── README.md
├── ai-research/                ← Clean project folder
│   ├── experiments/
│   └── notes.md
└── ecommerce/                  ← Clean project folder
    ├── api/
    └── frontend/

CommandCenter Hub (single installation):
├── hub/backend/app/dagger_modules/
│   └── commandcenter.py        ← Stack definition (once)
└── Database:
    ├── Project: performia (path: ~/Projects/performia, ports: 8000/3000)
    ├── Project: ai-research (path: ~/Projects/ai-research, ports: 8010/3010)
    └── Project: ecommerce (path: ~/Projects/ecommerce, ports: 8020/3020)

Total: <50 MB for 3 projects (just Hub)
```

**Benefits:**
- Zero duplication
- Single update point
- Consistent versions
- Clean project folders

## Comparison: docker-compose vs Dagger

| Aspect | docker-compose | Dagger SDK |
|--------|----------------|------------|
| **Configuration** | YAML files | Python code |
| **Type Safety** | None | Full type hints |
| **Error Handling** | Parse stderr | Python exceptions |
| **Lifecycle Control** | subprocess.run() | async/await API |
| **IDE Support** | YAML linting | Full autocomplete |
| **Testing** | Shell mocking | Unit testable |
| **Reusability** | Copy YAML files | Import Python classes |
| **Caching** | Docker layer cache | Dagger intelligent cache |
| **Template Management** | Copy files | No templates needed |

## Technical Details

### Dagger Connection

```python
# Initialize connection to Dagger engine
self.client = dagger.Connection(dagger.Config())
await self.client.__aenter__()
```

**What Dagger Does:**
1. Connects to Docker daemon (via Docker socket)
2. Starts Dagger engine container (if not running)
3. Opens gRPC connection to engine
4. Provides high-level container API

**Requirements:**
- Docker Desktop or Docker Engine running
- Docker socket accessible (`/var/run/docker.sock`)
- Dagger SDK installed (`pip install dagger-io`)

### Container Service API

```python
# Build container
postgres = await self.build_postgres()

# Convert to long-running service
postgres_svc = postgres.as_service()

# Use service in other containers (hostname = "postgres")
backend = await self.build_backend("postgres", "redis")
```

**Service Features:**
- Automatic service discovery (hostname = container name)
- Dependency ordering (services start in order)
- Health checking (containers wait for dependencies)
- Network isolation (services can communicate)

### Error Handling

```python
try:
    result = await stack.start()
except dagger.ExecError as e:
    # Container command failed
    logger.error(f"Container exec failed: {e.stderr}")
except dagger.BuildError as e:
    # Container build failed
    logger.error(f"Build failed: {e.message}")
except Exception as e:
    # Other errors
    logger.error(f"Unexpected error: {e}")
```

**Exception Types:**
- `dagger.ExecError`: Command execution failed in container
- `dagger.BuildError`: Container image build failed
- `dagger.ConnectionError`: Dagger engine unreachable
- Standard Python exceptions for other issues

## Production Hardening (Phase A)

### Overview

Phase A adds production-grade reliability, observability, and security to the Dagger orchestration layer. These features transform the basic container management into a robust system suitable for production workloads.

### 1. Log Retrieval

**Feature**: Programmatic access to container logs via Dagger SDK

**Implementation** (`commandcenter.py:212-250`):
```python
async def get_logs(self, service_name: str, tail: int = 100) -> str:
    """
    Retrieve logs from a specific service container.

    Args:
        service_name: Name of service (postgres, redis, backend, frontend)
        tail: Number of lines to retrieve from end of logs

    Returns:
        String containing log lines
    """
    container = self._service_containers[service_name]
    logs = await container.stdout()

    if tail:
        log_lines = logs.split('\n')
        logs = '\n'.join(log_lines[-tail:])

    return logs
```

**API Endpoint** (`logs.py:15-35`):
```python
@router.get("/{project_id}/logs/{service_name}")
async def get_service_logs(
    project_id: int,
    service_name: str,
    tail: int = Query(default=100, ge=1, le=10000)
):
    orchestration = OrchestrationService(db)
    logs = await orchestration.get_project_logs(project_id, service_name, tail)
    return {"project_id": project_id, "service": service_name, "logs": logs}
```

**Usage**:
```bash
# Via API
curl http://localhost:9001/api/v1/projects/1/logs/backend?tail=50

# Returns last 50 lines of backend container logs
```

**Benefits**:
- Real-time debugging without SSH/docker exec
- Tail support for performance (avoid downloading GB of logs)
- Service registry tracks running containers
- REST API for UI integration

### 2. Health Check System

**Feature**: Automated health monitoring for all services using native tools

**Implementation**:

**PostgreSQL Health** (`commandcenter.py:262-287`):
```python
@retry_with_backoff(max_attempts=2, initial_delay=1.0)
async def check_postgres_health(self) -> dict:
    """Check PostgreSQL health using pg_isready"""
    container = self._service_containers.get("postgres")
    result = await container.with_exec([
        "pg_isready", "-U", "commandcenter"
    ]).stdout()

    healthy = "accepting connections" in result
    return {
        "healthy": healthy,
        "service": "postgres",
        "message": result.strip()
    }
```

**Redis Health** (`commandcenter.py:293-317`):
```python
@retry_with_backoff(max_attempts=2, initial_delay=1.0)
async def check_redis_health(self) -> dict:
    """Check Redis health using redis-cli ping"""
    container = self._service_containers.get("redis")
    result = await container.with_exec([
        "redis-cli", "ping"
    ]).stdout()

    healthy = "PONG" in result
    return {"healthy": healthy, "service": "redis", "message": result.strip()}
```

**Backend/Frontend Health** (`commandcenter.py:324-378`):
```python
async def check_backend_health(self) -> dict:
    """Check backend health via HTTP /health endpoint"""
    result = await container.with_exec([
        "curl", "-f", "http://localhost:8000/health"
    ]).stdout()

    healthy = "ok" in result.lower() or "healthy" in result.lower()
    return {"healthy": healthy, "service": "backend"}
```

**Aggregated Status** (`commandcenter.py:386-407`):
```python
async def health_status(self) -> dict:
    """Get aggregated health status for all services"""
    services = {
        "postgres": await self.check_postgres_health(),
        "redis": await self.check_redis_health(),
        "backend": await self.check_backend_health(),
        "frontend": await self.check_frontend_health()
    }

    overall_healthy = all(svc["healthy"] for svc in services.values())

    return {
        "overall_healthy": overall_healthy,
        "services": services,
        "timestamp": str(datetime.now())
    }
```

**Benefits**:
- Native health check commands (pg_isready, redis-cli)
- Per-service status reporting
- Aggregated overall health
- Retry logic for transient failures
- Timestamp tracking for monitoring

### 3. Resource Limits

**Feature**: Prevent resource exhaustion with CPU and memory limits

**Configuration** (`commandcenter.py:18-28`):
```python
@dataclass
class ResourceLimits:
    """Resource limits for CommandCenter containers"""
    postgres_cpu: float = 1.0         # 1 CPU core
    postgres_memory_mb: int = 2048    # 2 GB RAM
    redis_cpu: float = 0.5            # 0.5 CPU cores
    redis_memory_mb: int = 512        # 512 MB RAM
    backend_cpu: float = 1.0          # 1 CPU core
    backend_memory_mb: int = 1024     # 1 GB RAM
    frontend_cpu: float = 0.5         # 0.5 CPU cores
    frontend_memory_mb: int = 512     # 512 MB RAM
```

**Application** (`commandcenter.py:77-94`):
```python
async def build_postgres(self) -> dagger.Container:
    limits = self.config.resource_limits

    return (
        self.client.container()
        .from_("postgres:15-alpine")
        # ... other config ...
        .with_resource_limit("cpu", str(limits.postgres_cpu))
        .with_resource_limit("memory", f"{limits.postgres_memory_mb}m")
    )
```

**Customization**:
```python
# Custom limits for high-load projects
custom_limits = ResourceLimits(
    postgres_cpu=2.0,          # Double CPU for large DB
    postgres_memory_mb=4096,   # 4 GB for query cache
    backend_cpu=2.0,
    backend_memory_mb=2048
)

config = CommandCenterConfig(
    # ... other config ...
    resource_limits=custom_limits
)
```

**Benefits**:
- Prevent single project from consuming all resources
- Predictable performance under load
- Easy to adjust per-project requirements
- Defaults suitable for development workloads

### 4. Security Hardening

**Feature**: Non-root container execution following security best practices

**User IDs** (`commandcenter.py:55-58`):
```python
class CommandCenterStack:
    # User IDs for non-root execution
    POSTGRES_USER_ID = 999    # Standard postgres UID
    REDIS_USER_ID = 999       # Standard redis UID
    APP_USER_ID = 1000        # Standard non-privileged user
```

**Application** (`commandcenter.py:77-94`, `96-110`, `112-144`, `146-168`):
```python
# PostgreSQL runs as UID 999
async def build_postgres(self) -> dagger.Container:
    return (
        self.client.container()
        .from_("postgres:15-alpine")
        .with_user(str(self.POSTGRES_USER_ID))  # Run as postgres user
        # ... rest of config
    )

# Redis runs as UID 999
async def build_redis(self) -> dagger.Container:
    return (
        self.client.container()
        .from_("redis:7-alpine")
        .with_user(str(self.REDIS_USER_ID))     # Run as redis user
        # ... rest of config
    )

# Backend and Frontend run as UID 1000
async def build_backend(self, postgres_host, redis_host) -> dagger.Container:
    return (
        self.client.container()
        .from_("python:3.11-slim")
        .with_user(str(self.APP_USER_ID))       # Run as non-root
        # ... rest of config
    )
```

**Security Benefits**:
- Principle of least privilege
- Container escape mitigation
- Filesystem permission isolation
- Standard practice for production containers

**Verification**:
```bash
# Check container user
docker exec <container_id> whoami
# Should NOT return "root"
```

### 5. Retry Logic with Exponential Backoff

**Feature**: Automatic retry for transient failures in network/I/O operations

**Implementation** (`retry.py:11-64`):
```python
def retry_with_backoff(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0
):
    """
    Decorator that retries async functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds before first retry
        backoff_factor: Multiplier for delay after each attempt (default: 2.0)
        max_delay: Maximum delay between retries in seconds
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None

            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_exception = e

                    if attempt == max_attempts:
                        logger.error(f"{func.__name__} failed after {max_attempts} attempts")
                        raise

                    logger.warning(
                        f"{func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. "
                        f"Retrying in {delay:.2f}s..."
                    )

                    await asyncio.sleep(delay)
                    delay = min(delay * backoff_factor, max_delay)

            raise last_exception
        return wrapper
    return decorator
```

**Application**:
```python
@retry_with_backoff(max_attempts=3, initial_delay=2.0)
async def start(self) -> dict:
    """Start all CommandCenter containers (with retry)"""
    # Transient failures (network, Docker API) will auto-retry
    # ... start logic

@retry_with_backoff(max_attempts=2, initial_delay=1.0)
async def check_postgres_health(self) -> dict:
    """Check PostgreSQL health (with retry)"""
    # Database startup delays handled automatically
    # ... health check logic
```

**Retry Behavior**:
```
Attempt 1: Fails → Wait 2.0s
Attempt 2: Fails → Wait 4.0s (2.0 * 2.0)
Attempt 3: Fails → Raise exception (max attempts reached)

Attempt 1: Fails → Wait 1.0s
Attempt 2: Succeeds → Return result
```

**Benefits**:
- Handles transient Docker API failures
- Manages database startup timing issues
- Prevents false negatives in health checks
- Exponential backoff prevents overwhelming systems
- Configurable per-operation (start vs health check)

### 6. Service Restart Capability

**Feature**: Graceful restart of individual services without full stack restart

**Implementation** (`commandcenter.py:409-464`):
```python
@retry_with_backoff(max_attempts=3, initial_delay=2.0)
async def restart_service(self, service_name: str) -> dict:
    """
    Restart a specific service container.

    Args:
        service_name: Name of service to restart (postgres, redis, backend, frontend)

    Returns:
        Dict with restart status
    """
    # Validate service name
    if service_name not in self.VALID_SERVICES:
        raise ValueError(f"Invalid service name: {service_name}")

    # Verify service exists in registry
    if service_name not in self._service_containers:
        raise RuntimeError(f"Service {service_name} not found in registry")

    # Rebuild the container based on service type
    if service_name == "postgres":
        new_container = await self.build_postgres()
    elif service_name == "redis":
        new_container = await self.build_redis()
    elif service_name == "backend":
        new_container = await self.build_backend("postgres", "redis")
    elif service_name == "frontend":
        new_container = await self.build_frontend(f"http://backend:{self.config.backend_port}")

    # Update registry with new container
    self._service_containers[service_name] = new_container

    # Start as service
    _ = new_container.as_service()

    return {
        "success": True,
        "service": service_name,
        "message": f"Service {service_name} restarted successfully"
    }
```

**Usage**:
```python
# Restart backend after config change
result = await stack.restart_service("backend")

# Restart database after migration
result = await stack.restart_service("postgres")
```

**Benefits**:
- Zero downtime for other services
- Faster than full stack restart
- Useful for config updates, migrations, debugging
- Maintains service dependencies (backend still sees postgres)

### 7. Service Registry

**Feature**: Track running containers for log retrieval, health checks, and restarts

**Implementation** (`commandcenter.py:64`, `169-187`, `252-257`):
```python
class CommandCenterStack:
    def __init__(self, config: CommandCenterConfig):
        self._service_containers: dict[str, dagger.Container] = {}

    async def start(self) -> dict:
        # Build containers
        postgres = await self.build_postgres()
        redis = await self.build_redis()
        backend = await self.build_backend("postgres", "redis")
        frontend = await self.build_frontend(...)

        # Store in registry for later access
        self._service_containers["postgres"] = postgres
        self._service_containers["redis"] = redis
        self._service_containers["backend"] = backend
        self._service_containers["frontend"] = frontend

        # Start as services
        # ...

    async def _get_service_container(self, service_name: str) -> dagger.Container:
        """Get container for a service from registry"""
        if service_name not in self._service_containers:
            raise RuntimeError(f"Service {service_name} not found in registry")
        return self._service_containers[service_name]
```

**Benefits**:
- Central container reference storage
- Enables log retrieval without rebuilding containers
- Supports health checks on running services
- Required for restart functionality
- Lifetime matches stack lifetime (cleaned up on __aexit__)

### Testing

All production features include comprehensive unit tests:

- `tests/unit/test_dagger_logs.py` - Log retrieval (3 tests)
- `tests/unit/test_dagger_health.py` - Health checks (3 tests)
- `tests/unit/test_dagger_resources.py` - Resource limits (3 tests)
- `tests/security/test_dagger_security.py` - Non-root execution (1 test)
- `tests/unit/test_dagger_retry.py` - Retry logic (5 tests)
- `tests/unit/test_dagger_restart.py` - Service restart (6 tests)

**Total: 21 unit tests validating production hardening**

### Production Readiness Checklist

- [x] Log retrieval for debugging
- [x] Health checks for monitoring
- [x] Resource limits for stability
- [x] Security hardening (non-root)
- [x] Retry logic for resilience
- [x] Service restart for operations
- [x] Service registry for tracking
- [x] Comprehensive test coverage

## Future Enhancements

### 1. Persistent Services

Currently, stacks are ephemeral (destroyed on stop). For production:

```python
# Store service IDs in database
project.postgres_service_id = await postgres_svc.start()
project.backend_service_id = await backend_svc.start()

# Reconnect on restart
postgres_svc = await client.load_service(project.postgres_service_id)
```

### 2. Health Checks

```python
async def check_health(self) -> bool:
    try:
        # Check backend /health endpoint
        backend = self._active_stacks[project_id].backend_service
        result = await backend.exec(["curl", "localhost:8000/health"])
        return result.exit_code == 0
    except Exception:
        return False
```

### 3. Log Streaming

```python
async def stream_logs(self, project_id: int) -> AsyncIterator[str]:
    stack = self._active_stacks[project_id]
    async for log_line in stack.backend_service.logs():
        yield log_line
```

### 4. Resource Limits

```python
backend = (
    self.client.container()
    .from_("python:3.11-slim")
    .with_resource_limit("memory", "2GB")
    .with_resource_limit("cpu", "2.0")
)
```

### 5. Multi-Host Support

```python
# Deploy to remote Dagger engine
config = dagger.Config(
    workdir="/app",
    engine_address="tcp://remote-host:8080"
)
```

## Troubleshooting

### Dagger Engine Not Starting

**Symptom:** `ConnectionError: Cannot connect to Dagger engine`

**Solutions:**
1. Check Docker is running: `docker ps`
2. Restart Dagger engine: `dagger engine restart`
3. Check Docker socket permissions: `ls -l /var/run/docker.sock`

### Container Build Failures

**Symptom:** `BuildError: Failed to build container`

**Solutions:**
1. Check Dockerfile syntax in `commandcenter.py`
2. Verify base image exists: `docker pull python:3.11-slim`
3. Check network connectivity for package downloads

### Port Already in Use

**Symptom:** `RuntimeError: Port 8000 is already in use`

**Solutions:**
1. Stop conflicting service: `docker ps` and `docker stop <container>`
2. Change port in project settings
3. Run Hub's port availability check

### Mount Path Errors

**Symptom:** `Path does not exist: /Users/me/project`

**Solutions:**
1. Verify project path is absolute (not relative)
2. Check path exists: `ls -la /Users/me/project`
3. Ensure Hub has read access to project folder

## Additional Resources

- **Dagger Documentation**: https://docs.dagger.io/
- **Dagger Python SDK**: https://docs.dagger.io/sdk/python
- **Hub Implementation**: `hub/backend/app/dagger_modules/commandcenter.py`
- **Orchestration Service**: `hub/backend/app/services/orchestration_service.py`
- **Integration Tests**: `hub/backend/tests/integration/test_dagger_flow.py`

## Summary

Dagger transforms CommandCenter Hub from a subprocess-based orchestrator into a type-safe, programmatic container management system. By defining infrastructure as Python code, we gain:

- **Simplicity**: No YAML files, no template cloning, no subprocess calls
- **Reliability**: Type-safe API, proper exception handling, automatic cleanup
- **Efficiency**: Intelligent caching, resource pooling, ephemeral containers
- **Maintainability**: Single source of truth, testable code, IDE support

The result is a cleaner, faster, and more maintainable multi-project CommandCenter Hub.
