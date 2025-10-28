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
