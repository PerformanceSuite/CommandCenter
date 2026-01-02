# Week 2 Hub Security Tests Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Implement Hub-specific security tests for multi-instance isolation, Dagger orchestration security, and port conflict handling (16 tests total).

**Architecture:** Security testing for Hub's orchestration layer using mocked Dagger clients for unit tests, real project configurations for isolation testing, and comprehensive security validation for container orchestration. All tests use mocked Dagger SDK (no real containers) to ensure fast, predictable execution.

**Tech Stack:** pytest, pytest-asyncio, unittest.mock, Dagger SDK (mocked), FastAPI TestClient

**Worktree:** `.worktrees/testing-hub-security` → `testing/week2-hub-security` branch

---

## Task 1: Hub Security Test Infrastructure

**Files:**
- Create: `hub/backend/tests/security/conftest.py`
- Create: `hub/backend/tests/security/__init__.py`

**Step 1: Create Hub security test directory structure**

```bash
mkdir -p hub/backend/tests/security
touch hub/backend/tests/security/__init__.py
```

**Step 2: Write Hub security fixtures**

Create `hub/backend/tests/security/conftest.py`:

```python
"""Hub security test fixtures."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.models.project import CommandCenterConfig, PortSet


@pytest.fixture
def project_configs():
    """Multiple project configurations for isolation testing.

    Creates 3 distinct project configurations with:
    - Unique project names
    - Different directory paths
    - Non-overlapping port assignments
    """
    return [
        CommandCenterConfig(
            project_name="project-alpha",
            project_path="/tmp/test-projects/alpha",
            ports=PortSet(
                backend=8000,
                frontend=3000,
                postgres=5432,
                redis=6379
            ),
            secrets={
                "secret_key": "alpha-secret-123",
                "db_password": "alpha-db-pass-456"
            }
        ),
        CommandCenterConfig(
            project_name="project-beta",
            project_path="/tmp/test-projects/beta",
            ports=PortSet(
                backend=8010,
                frontend=3010,
                postgres=5433,
                redis=6380
            ),
            secrets={
                "secret_key": "beta-secret-789",
                "db_password": "beta-db-pass-012"
            }
        ),
        CommandCenterConfig(
            project_name="project-gamma",
            project_path="/tmp/test-projects/gamma",
            ports=PortSet(
                backend=8020,
                frontend=3020,
                postgres=5434,
                redis=6381
            ),
            secrets={
                "secret_key": "gamma-secret-345",
                "db_password": "gamma-db-pass-678"
            }
        )
    ]


@pytest.fixture
def mock_dagger_client():
    """Mock Dagger client for security tests.

    Provides a fully mocked Dagger client that simulates container
    operations without actually creating containers. Tracks all
    method calls for assertion in tests.

    Returns:
        MagicMock: Mocked Dagger client with container operations
    """
    client = MagicMock()

    # Mock container builder
    mock_container = MagicMock()
    mock_container.with_mounted_directory = MagicMock(return_value=mock_container)
    mock_container.with_env_variable = MagicMock(return_value=mock_container)
    mock_container.with_exposed_port = MagicMock(return_value=mock_container)
    mock_container.with_user = MagicMock(return_value=mock_container)
    mock_container.with_workdir = MagicMock(return_value=mock_container)
    mock_container.start = AsyncMock(return_value=mock_container)
    mock_container.stop = AsyncMock()

    # Mock directory operations
    mock_directory = MagicMock()
    client.directory = MagicMock(return_value=mock_directory)

    # Container factory returns mock container
    client.container = MagicMock(return_value=mock_container)

    # Track created containers
    client._created_containers = []

    def track_container(*args, **kwargs):
        container = mock_container
        client._created_containers.append(container)
        return container

    client.container.side_effect = track_container

    return client


@pytest.fixture
async def mock_orchestration_service(mock_dagger_client):
    """OrchestrationService with mocked Dagger client.

    Returns:
        OrchestrationService: Service instance with mocked Dagger
    """
    from app.services.orchestration_service import OrchestrationService

    # Mock database session
    mock_db = MagicMock()

    service = OrchestrationService(db_session=mock_db)

    # Inject mocked Dagger client
    service._dagger_client = mock_dagger_client

    return service


@pytest.fixture
def mock_commandcenter_stack():
    """Mock CommandCenterStack for testing.

    Returns:
        MagicMock: Mocked stack with container operations
    """
    stack = MagicMock()

    # Mock container properties
    stack.postgres = MagicMock()
    stack.redis = MagicMock()
    stack.backend = MagicMock()
    stack.frontend = MagicMock()

    # Mock lifecycle methods
    stack.start = AsyncMock()
    stack.stop = AsyncMock()
    stack.restart = AsyncMock()
    stack.remove = AsyncMock()

    # Mock status methods
    stack.postgres.is_running = AsyncMock(return_value=True)
    stack.redis.is_running = AsyncMock(return_value=True)
    stack.backend.is_running = AsyncMock(return_value=True)
    stack.frontend.is_running = AsyncMock(return_value=True)

    # Mock configuration methods
    stack.get_volume_names = MagicMock(return_value=[
        "project_postgres_data",
        "project_redis_data"
    ])
    stack.get_environment_variables = MagicMock(return_value={
        "SECRET_KEY": "test-secret",
        "DB_PASSWORD": "test-password",
        "DATABASE_URL": "postgresql://user:pass@postgres:5432/db"
    })

    return stack
```

**Step 3: Verify fixtures import correctly**

Run:
```bash
cd hub/backend
python -c "from tests.security.conftest import *; print('Hub security fixtures loaded successfully')"
```

Expected: "Hub security fixtures loaded successfully"

**Step 4: Commit**

```bash
git add hub/backend/tests/security/
git commit -m "test: Add Hub security test infrastructure and fixtures

- Create Hub security test directory structure
- Add project_configs fixture (3 isolated projects)
- Add mock_dagger_client fixture for unit testing
- Add mock_orchestration_service fixture
- Add mock_commandcenter_stack fixture
- All fixtures use mocks (no real containers)"
```

---

## Task 2: Multi-Instance Isolation Tests (Part 1 - Volumes & Secrets)

**Files:**
- Create: `hub/backend/tests/security/test_multi_instance_isolation.py`

**Step 1: Write failing test for Docker volume isolation**

Create `hub/backend/tests/security/test_multi_instance_isolation.py`:

```python
"""Multi-instance isolation security tests."""
import pytest


@pytest.mark.asyncio
async def test_project_volumes_are_isolated(
    mock_orchestration_service, project_configs
):
    """Each project uses isolated Docker volumes.

    Critical security requirement: Projects must not share volumes
    as this could leak data between projects.
    """
    # Start two projects
    stack_a = await mock_orchestration_service.start_project(project_configs[0])
    stack_b = await mock_orchestration_service.start_project(project_configs[1])

    # Get volume names for each project
    volumes_a = stack_a.get_volume_names()
    volumes_b = stack_b.get_volume_names()

    # Assert no shared volumes
    shared = set(volumes_a).intersection(set(volumes_b))
    assert len(shared) == 0, (
        f"SECURITY VIOLATION: Found shared volumes between projects: {shared}. "
        f"Projects must have completely isolated storage."
    )

    # Assert volumes include project name for identification
    assert all(project_configs[0].project_name in v for v in volumes_a), (
        "Volume names must include project name for isolation"
    )
    assert all(project_configs[1].project_name in v for v in volumes_b), (
        "Volume names must include project name for isolation"
    )
```

**Step 2: Run test to verify it fails**

Run:
```bash
cd hub/backend
pytest tests/security/test_multi_instance_isolation.py::test_project_volumes_are_isolated -v
```

Expected: FAIL (volume isolation not yet implemented)

**Step 3: Write test for environment variable isolation**

Add to `hub/backend/tests/security/test_multi_instance_isolation.py`:

```python
@pytest.mark.asyncio
async def test_environment_variables_not_leaked(
    mock_orchestration_service, project_configs
):
    """Project A secrets not accessible from Project B.

    Each project must have unique secrets that cannot be accessed
    by other projects.
    """
    # Start both projects
    stack_a = await mock_orchestration_service.start_project(project_configs[0])
    stack_b = await mock_orchestration_service.start_project(project_configs[1])

    # Get environment variables for each
    env_a = stack_a.get_environment_variables()
    env_b = stack_b.get_environment_variables()

    # Assert different secrets
    assert env_a["SECRET_KEY"] != env_b["SECRET_KEY"], (
        "SECURITY VIOLATION: Projects sharing SECRET_KEY. "
        "Each project must have unique secrets."
    )

    assert env_a["DB_PASSWORD"] != env_b["DB_PASSWORD"], (
        "SECURITY VIOLATION: Projects sharing DB_PASSWORD. "
        "Database credentials must be isolated per project."
    )

    # Assert project-specific database URLs
    assert project_configs[0].project_name in env_a["DATABASE_URL"], (
        "Database URL must be project-specific"
    )
    assert project_configs[1].project_name in env_b["DATABASE_URL"], (
        "Database URL must be project-specific"
    )
```

**Step 4: Write test for database file isolation**

Add to `hub/backend/tests/security/test_multi_instance_isolation.py`:

```python
import os


@pytest.mark.asyncio
async def test_database_files_isolated_per_project(
    mock_orchestration_service, project_configs
):
    """Each project has isolated database storage.

    Database files must be stored in project-specific locations
    to prevent data leakage.
    """
    # Start two projects
    stack_a = await mock_orchestration_service.start_project(project_configs[0])
    stack_b = await mock_orchestration_service.start_project(project_configs[1])

    # Get database file paths
    db_path_a = stack_a.get_database_path()
    db_path_b = stack_b.get_database_path()

    # Assert different paths
    assert db_path_a != db_path_b, (
        "SECURITY VIOLATION: Projects sharing database file path"
    )

    # Assert paths include project identifier
    assert project_configs[0].project_name in db_path_a
    assert project_configs[1].project_name in db_path_b

    # Assert paths are in isolated directories
    parent_a = os.path.dirname(db_path_a)
    parent_b = os.path.dirname(db_path_b)
    assert parent_a != parent_b, (
        "Database files must be in separate directories per project"
    )
```

**Step 5: Run tests to verify they fail**

Run:
```bash
cd hub/backend
pytest tests/security/test_multi_instance_isolation.py -v
```

Expected: 3 FAIL (isolation not yet implemented)

**Step 6: Commit**

```bash
git add hub/backend/tests/security/test_multi_instance_isolation.py
git commit -m "test: Add multi-instance isolation tests for volumes and secrets (3 tests)

- Test Docker volumes isolated between projects
- Test environment variables not leaked between projects
- Test database files isolated per project

Tests failing as expected (TDD red phase)"
```

---

## Task 3: Multi-Instance Isolation Tests (Part 2 - Network & Containers)

**Files:**
- Modify: `hub/backend/tests/security/test_multi_instance_isolation.py`

**Step 1: Write test for network isolation**

Add to `hub/backend/tests/security/test_multi_instance_isolation.py`:

```python
@pytest.mark.asyncio
async def test_network_isolation_between_project_stacks(
    mock_orchestration_service, project_configs
):
    """Each project stack has isolated network.

    Projects must not be able to communicate directly via Docker
    networking to prevent unauthorized access.
    """
    # Start two projects
    stack_a = await mock_orchestration_service.start_project(project_configs[0])
    stack_b = await mock_orchestration_service.start_project(project_configs[1])

    # Get network names
    network_a = stack_a.get_network_name()
    network_b = stack_b.get_network_name()

    # Assert different networks
    assert network_a != network_b, (
        "SECURITY VIOLATION: Projects sharing Docker network. "
        "Each project must have isolated network."
    )

    # Assert networks include project name
    assert project_configs[0].project_name in network_a
    assert project_configs[1].project_name in network_b
```

**Step 2: Write test for container naming uniqueness**

Add to `hub/backend/tests/security/test_multi_instance_isolation.py`:

```python
@pytest.mark.asyncio
async def test_container_names_unique_per_project(
    mock_orchestration_service, project_configs
):
    """Container names must be unique per project.

    Prevents conflicts and ensures proper isolation.
    """
    # Start two projects
    stack_a = await mock_orchestration_service.start_project(project_configs[0])
    stack_b = await mock_orchestration_service.start_project(project_configs[1])

    # Get container names
    containers_a = stack_a.get_container_names()
    containers_b = stack_b.get_container_names()

    # Assert no name collisions
    shared_names = set(containers_a).intersection(set(containers_b))
    assert len(shared_names) == 0, (
        f"Container name collision detected: {shared_names}. "
        f"Each project must have unique container names."
    )

    # Assert container names include project identifier
    for name in containers_a:
        assert project_configs[0].project_name in name, (
            f"Container name '{name}' must include project name"
        )

    for name in containers_b:
        assert project_configs[1].project_name in name, (
            f"Container name '{name}' must include project name"
        )
```

**Step 3: Write test for secrets uniqueness**

Add to `hub/backend/tests/security/test_multi_instance_isolation.py`:

```python
@pytest.mark.asyncio
async def test_secrets_unique_per_project(
    mock_orchestration_service, project_configs
):
    """Secrets (DB_PASSWORD, SECRET_KEY) must be unique per project.

    Reusing secrets across projects is a security vulnerability.
    """
    # Start three projects
    stacks = []
    for config in project_configs:
        stack = await mock_orchestration_service.start_project(config)
        stacks.append(stack)

    # Collect all secrets
    all_secret_keys = [s.get_environment_variables()["SECRET_KEY"] for s in stacks]
    all_db_passwords = [s.get_environment_variables()["DB_PASSWORD"] for s in stacks]

    # Assert no duplicate secret keys
    assert len(all_secret_keys) == len(set(all_secret_keys)), (
        "SECURITY VIOLATION: Multiple projects sharing SECRET_KEY. "
        "Each project must have unique SECRET_KEY."
    )

    # Assert no duplicate database passwords
    assert len(all_db_passwords) == len(set(all_db_passwords)), (
        "SECURITY VIOLATION: Multiple projects sharing DB_PASSWORD. "
        "Each project must have unique database password."
    )
```

**Step 4: Write test for port mapping non-overlap**

Add to `hub/backend/tests/security/test_multi_instance_isolation.py`:

```python
@pytest.mark.asyncio
async def test_port_mappings_non_overlapping(
    mock_orchestration_service, project_configs
):
    """Port mappings must not overlap between projects.

    Each project must expose services on unique ports to avoid conflicts.
    """
    # Start all projects
    stacks = []
    for config in project_configs:
        stack = await mock_orchestration_service.start_project(config)
        stacks.append(stack)

    # Collect all exposed ports
    all_ports = []
    for stack in stacks:
        ports = stack.get_exposed_ports()
        all_ports.extend(ports)

    # Assert no duplicate ports
    assert len(all_ports) == len(set(all_ports)), (
        f"Port conflict detected. Overlapping ports: "
        f"{[p for p in all_ports if all_ports.count(p) > 1]}. "
        f"Each project must use unique ports."
    )
```

**Step 5: Write test for log file isolation**

Add to `hub/backend/tests/security/test_multi_instance_isolation.py`:

```python
@pytest.mark.asyncio
async def test_log_files_isolated_per_project(
    mock_orchestration_service, project_configs
):
    """Log files must be stored separately per project.

    Prevents log data leakage between projects.
    """
    # Start two projects
    stack_a = await mock_orchestration_service.start_project(project_configs[0])
    stack_b = await mock_orchestration_service.start_project(project_configs[1])

    # Get log paths
    log_path_a = stack_a.get_log_directory()
    log_path_b = stack_b.get_log_directory()

    # Assert different log directories
    assert log_path_a != log_path_b, (
        "Log files must be in separate directories per project"
    )

    # Assert log paths include project identifier
    assert project_configs[0].project_name in log_path_a
    assert project_configs[1].project_name in log_path_b
```

**Step 6: Run tests to verify they fail**

Run:
```bash
cd hub/backend
pytest tests/security/test_multi_instance_isolation.py -v
```

Expected: 8 FAIL (isolation features not yet implemented)

**Step 7: Commit**

```bash
git add hub/backend/tests/security/test_multi_instance_isolation.py
git commit -m "test: Add multi-instance isolation tests for network and containers (5 tests)

- Test network isolation between project stacks
- Test container names unique per project
- Test secrets unique per project (SECRET_KEY, DB_PASSWORD)
- Test port mappings non-overlapping
- Test log files isolated per project

Total multi-instance isolation tests: 8 (all failing as expected)"
```

---

## Task 4: Dagger Orchestration Security Tests (Part 1 - Container Security)

**Files:**
- Create: `hub/backend/tests/security/test_dagger_security.py`

**Step 1: Write test for non-root container execution**

Create `hub/backend/tests/security/test_dagger_security.py`:

```python
"""Dagger orchestration security tests."""
import pytest


@pytest.mark.asyncio
async def test_containers_run_as_non_root(
    mock_dagger_client, project_configs
):
    """Dagger containers run with non-root user.

    Running as root is a security risk. Containers should use
    dedicated non-privileged users.
    """
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(mock_dagger_client, project_configs[0])
    await stack.start()

    # Get all container creation calls
    container_calls = mock_dagger_client.container.call_args_list

    # Check that user is configured
    user_calls = []
    for container in mock_dagger_client._created_containers:
        if hasattr(container, 'with_user'):
            user_calls.extend([
                call for call in container.with_user.call_args_list
            ])

    assert len(user_calls) > 0, (
        "SECURITY VIOLATION: No user configuration found. "
        "Containers must explicitly set non-root user."
    )

    # Verify not running as root (UID 0)
    for call in user_calls:
        user = call[0][0] if call[0] else None
        assert user not in ['0', 'root', None], (
            f"SECURITY VIOLATION: Container running as root (user: {user}). "
            f"Must use non-privileged user."
        )
```

**Step 2: Write test for filesystem mount restrictions**

Add to `hub/backend/tests/security/test_dagger_security.py`:

```python
@pytest.mark.asyncio
async def test_host_filesystem_not_fully_exposed(
    mock_dagger_client, project_configs
):
    """Only project folder mounted, not entire host filesystem.

    Mounting root or sensitive directories is a security risk.
    """
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(mock_dagger_client, project_configs[0])
    await stack.start()

    # Get all mount directory calls
    mount_calls = []
    for container in mock_dagger_client._created_containers:
        if hasattr(container, 'with_mounted_directory'):
            mount_calls.extend(
                container.with_mounted_directory.call_args_list
            )

    # Verify no dangerous mounts
    dangerous_paths = ['/', '/home', '/root', '/etc', '/var', '/usr', '/sys', '/proc']

    for call in mount_calls:
        # Get the host path being mounted
        if len(call[0]) >= 2:
            host_path = call[0][0]  # First arg is typically source path

            for dangerous in dangerous_paths:
                assert not str(host_path).startswith(dangerous), (
                    f"SECURITY VIOLATION: Mounting dangerous path '{host_path}'. "
                    f"Only project directories should be mounted."
                )

    # Verify project path IS mounted
    project_path_mounted = any(
        str(project_configs[0].project_path) in str(call)
        for call in mount_calls
    )
    assert project_path_mounted, (
        "Project directory must be mounted for application to function"
    )
```

**Step 3: Write test for Docker socket access restriction**

Add to `hub/backend/tests/security/test_dagger_security.py`:

```python
@pytest.mark.asyncio
async def test_docker_socket_not_exposed_to_non_privileged_containers(
    mock_dagger_client, project_configs
):
    """Docker socket not exposed to application containers.

    Only orchestration layer should have Docker socket access.
    Application containers must not have Docker control.
    """
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(mock_dagger_client, project_configs[0])
    await stack.start()

    # Check mount calls for Docker socket
    docker_socket_mounts = []

    for container in mock_dagger_client._created_containers:
        if hasattr(container, 'with_mounted_directory'):
            for call in container.with_mounted_directory.call_args_list:
                if '/var/run/docker.sock' in str(call):
                    docker_socket_mounts.append(call)

    # Docker socket should NEVER be mounted to application containers
    assert len(docker_socket_mounts) == 0, (
        f"SECURITY VIOLATION: Docker socket exposed to {len(docker_socket_mounts)} "
        f"application containers. This grants escalated privileges and is a security risk."
    )
```

**Step 4: Run tests to verify behavior**

Run:
```bash
cd hub/backend
pytest tests/security/test_dagger_security.py -v
```

Expected: FAIL if security not implemented (or PASS if already implemented)

**Step 5: Commit**

```bash
git add hub/backend/tests/security/test_dagger_security.py
git commit -m "test: Add Dagger container security tests (3 tests)

- Test containers run as non-root user
- Test host filesystem not fully exposed
- Test Docker socket not exposed to application containers

Dagger security tests: 3"
```

---

## Task 5: Dagger Orchestration Security Tests (Part 2 - Secrets & Capabilities)

**Files:**
- Modify: `hub/backend/tests/security/test_dagger_security.py`

**Step 1: Write test for secrets passed via environment**

Add to `hub/backend/tests/security/test_dagger_security.py`:

```python
@pytest.mark.asyncio
async def test_secrets_passed_via_environment_not_files(
    mock_dagger_client, project_configs
):
    """Secrets passed via environment variables, not mounted files.

    File-based secrets can persist and be harder to rotate.
    Environment variables are more secure for container secrets.
    """
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(mock_dagger_client, project_configs[0])
    await stack.start()

    # Check for environment variable calls
    env_calls = []
    for container in mock_dagger_client._created_containers:
        if hasattr(container, 'with_env_variable'):
            env_calls.extend(container.with_env_variable.call_args_list)

    # Verify secrets are set via environment
    secret_env_vars = ['SECRET_KEY', 'DB_PASSWORD', 'DATABASE_URL']
    found_secrets = []

    for call in env_calls:
        if len(call[0]) >= 1:
            var_name = call[0][0]
            if var_name in secret_env_vars:
                found_secrets.append(var_name)

    assert len(found_secrets) > 0, (
        "No secrets configured via environment variables. "
        "Secrets must be passed as environment variables."
    )

    # Check that secret files are NOT mounted
    secret_file_patterns = [
        'secrets.json', '.env.secrets', 'credentials', 'password.txt'
    ]

    mount_calls = []
    for container in mock_dagger_client._created_containers:
        if hasattr(container, 'with_mounted_directory'):
            mount_calls.extend(container.with_mounted_directory.call_args_list)

    for call in mount_calls:
        mount_path = str(call)
        for pattern in secret_file_patterns:
            assert pattern not in mount_path.lower(), (
                f"SECURITY VIOLATION: Secret file '{pattern}' appears to be mounted. "
                f"Use environment variables for secrets instead."
            )
```

**Step 2: Write test for container capabilities minimization**

Add to `hub/backend/tests/security/test_dagger_security.py`:

```python
@pytest.mark.asyncio
async def test_container_capabilities_minimized(
    mock_dagger_client, project_configs
):
    """Container capabilities minimized (no --privileged).

    Privileged mode grants all Linux capabilities and is a
    major security risk. Containers should have minimal capabilities.
    """
    from app.dagger_modules.commandcenter import CommandCenterStack

    stack = CommandCenterStack(mock_dagger_client, project_configs[0])
    await stack.start()

    # Check container creation for privileged mode or capabilities
    for container in mock_dagger_client._created_containers:
        # Check for privileged flag (should not exist)
        if hasattr(container, 'with_privileged'):
            privileged_calls = container.with_privileged.call_args_list
            assert len(privileged_calls) == 0, (
                "SECURITY VIOLATION: Container created with privileged mode. "
                "Privileged mode should never be used."
            )

        # Check for capability additions (should be minimal)
        if hasattr(container, 'with_capabilities'):
            cap_calls = container.with_capabilities.call_args_list
            dangerous_caps = [
                'SYS_ADMIN', 'SYS_MODULE', 'SYS_RAWIO',
                'SYS_PTRACE', 'NET_ADMIN', 'CAP_SYS_ADMIN'
            ]

            for call in cap_calls:
                caps = call[0] if call[0] else []
                for cap in caps:
                    assert cap not in dangerous_caps, (
                        f"SECURITY VIOLATION: Dangerous capability '{cap}' granted. "
                        f"Minimize container capabilities."
                    )
```

**Step 3: Run all Dagger security tests**

Run:
```bash
cd hub/backend
pytest tests/security/test_dagger_security.py -v
```

Expected: 5 tests (FAIL or PASS depending on implementation)

**Step 4: Commit**

```bash
git add hub/backend/tests/security/test_dagger_security.py
git commit -m "test: Add Dagger secrets and capabilities security tests (2 tests)

- Test secrets passed via environment variables (not files)
- Test container capabilities minimized (no privileged mode)

Total Dagger security tests: 5"
```

---

## Task 6: Port Conflict Handling Tests

**Files:**
- Create: `hub/backend/tests/security/test_port_conflicts.py`

**Step 1: Write test for port conflict detection**

Create `hub/backend/tests/security/test_port_conflicts.py`:

```python
"""Port conflict handling security tests."""
import pytest
from app.exceptions import PortConflictError
from app.models.project import CommandCenterConfig, PortSet


@pytest.mark.asyncio
async def test_detect_port_conflict_before_container_creation(
    mock_orchestration_service, project_configs
):
    """Port conflict detected before container creation.

    Prevents partial stack deployment and resource leaks.
    """
    # Start first project on port 8000
    stack_a = await mock_orchestration_service.start_project(project_configs[0])

    # Try to start second project with same backend port
    conflicting_config = CommandCenterConfig(
        project_name="conflict-project",
        project_path="/tmp/conflict",
        ports=PortSet(
            backend=8000,  # CONFLICT!
            frontend=3010,
            postgres=5433,
            redis=6380
        )
    )

    # Should raise PortConflictError
    with pytest.raises(PortConflictError) as exc_info:
        await mock_orchestration_service.start_project(conflicting_config)

    # Verify error message contains port number
    error_msg = str(exc_info.value).lower()
    assert "8000" in error_msg, "Error message must specify conflicting port"
    assert "already in use" in error_msg or "conflict" in error_msg, (
        "Error message must indicate port is already in use"
    )

    # Verify no containers created for conflicting project
    active_stacks = mock_orchestration_service.get_active_stacks()
    assert len(active_stacks) == 1, (
        "Failed project should not create any containers"
    )
    assert active_stacks[0] == stack_a, "Only first project should be active"
```

**Step 2: Write test for alternative port suggestions**

Add to `hub/backend/tests/security/test_port_conflicts.py`:

```python
@pytest.mark.asyncio
async def test_suggest_alternative_ports_on_conflict(
    mock_orchestration_service, project_configs
):
    """Conflict error suggests available alternative ports.

    Helps users resolve conflicts quickly.
    """
    # Start project on port 8000
    await mock_orchestration_service.start_project(project_configs[0])

    # Try conflicting project
    conflicting_config = CommandCenterConfig(
        project_name="conflict-project",
        project_path="/tmp/conflict",
        ports=PortSet(backend=8000, frontend=3010, postgres=5433, redis=6380)
    )

    try:
        await mock_orchestration_service.start_project(conflicting_config)
        pytest.fail("Should have raised PortConflictError")
    except PortConflictError as e:
        error_msg = str(e).lower()

        # Should suggest alternatives
        assert "try" in error_msg or "available" in error_msg or "alternative" in error_msg, (
            "Error should suggest alternative ports"
        )

        # Should mention specific alternative ports
        suggested_ports = [8010, 8020, 8030]
        has_suggestion = any(str(port) in str(e) for port in suggested_ports)
        assert has_suggestion, (
            f"Error should suggest specific alternative ports (e.g., {suggested_ports})"
        )
```

**Step 3: Write test for graceful error messaging**

Add to `hub/backend/tests/security/test_port_conflicts.py`:

```python
@pytest.mark.asyncio
async def test_port_conflict_error_message_is_clear(
    mock_orchestration_service, project_configs
):
    """Port conflict error has clear, actionable message.

    Error should not be generic; should explain exactly what went wrong.
    """
    # Start first project
    await mock_orchestration_service.start_project(project_configs[0])

    # Create config with multiple conflicts
    conflicting_config = CommandCenterConfig(
        project_name="multi-conflict",
        project_path="/tmp/multi-conflict",
        ports=PortSet(
            backend=8000,   # Conflict
            frontend=3000,  # Conflict
            postgres=5434,  # OK
            redis=6381      # OK
        )
    )

    try:
        await mock_orchestration_service.start_project(conflicting_config)
        pytest.fail("Should have raised PortConflictError")
    except PortConflictError as e:
        error_msg = str(e)

        # Should NOT be generic error
        generic_messages = [
            "error occurred",
            "something went wrong",
            "failed to start",
            "exception"
        ]
        for generic in generic_messages:
            assert generic not in error_msg.lower(), (
                f"Error message is too generic: '{error_msg}'"
            )

        # Should be actionable
        actionable_keywords = ["port", "conflict", "use", "try", "available"]
        has_actionable = any(keyword in error_msg.lower() for keyword in actionable_keywords)
        assert has_actionable, (
            f"Error message should be actionable. Got: '{error_msg}'"
        )

        # Should mention specific ports
        assert "8000" in error_msg or "3000" in error_msg, (
            "Error should specify which ports conflict"
        )
```

**Step 4: Run tests**

Run:
```bash
cd hub/backend
pytest tests/security/test_port_conflicts.py -v
```

Expected: 3 FAIL (port conflict handling not yet implemented)

**Step 5: Commit**

```bash
git add hub/backend/tests/security/test_port_conflicts.py
git commit -m "test: Add port conflict handling tests (3 tests)

- Test port conflict detected before container creation
- Test alternative ports suggested on conflict
- Test port conflict error message is clear and actionable

Total port conflict tests: 3
Total Hub security tests: 16 (8 isolation + 5 Dagger + 3 port)"
```

---

## Task 7: Documentation & Summary

**Files:**
- Create: `hub/backend/tests/security/README.md`
- Create: `hub/backend/tests/security/IMPLEMENTATION_SUMMARY.md`

**Step 1: Write Hub security tests README**

Create `hub/backend/tests/security/README.md`:

```markdown
# Hub Security Tests

## Overview

Hub security tests validate multi-instance isolation, Dagger orchestration security, and port conflict handling.

## Test Structure

### Multi-Instance Isolation Tests (`test_multi_instance_isolation.py`)

**Goal:** Ensure complete isolation between CommandCenter instances managed by Hub.

**Tests (8 total):**
- Docker volumes isolated between projects (1 test)
- Environment variables not leaked between projects (1 test)
- Database files isolated per project (1 test)
- Network isolation between project stacks (1 test)
- Container names unique per project (1 test)
- Secrets unique per project (SECRET_KEY, DB_PASSWORD) (1 test)
- Port mappings non-overlapping (1 test)
- Log files isolated per project (1 test)

**Critical Security Requirements:**
- **No shared volumes**: Projects must not share Docker volumes
- **Unique secrets**: Each project must have unique SECRET_KEY and DB_PASSWORD
- **Network isolation**: Projects must not communicate directly
- **No port conflicts**: Each project must use unique ports

**Key Fixtures:**
- `project_configs`: 3 distinct project configurations
- `mock_dagger_client`: Mocked Dagger SDK (no real containers)
- `mock_orchestration_service`: OrchestrationService with mocked Dagger

### Dagger Orchestration Security Tests (`test_dagger_security.py`)

**Goal:** Validate Dagger SDK container security best practices.

**Tests (5 total):**
- Containers run as non-root user (1 test)
- Host filesystem not fully exposed (1 test)
- Docker socket not exposed to application containers (1 test)
- Secrets passed via environment variables (not files) (1 test)
- Container capabilities minimized (no privileged mode) (1 test)

**Security Principles:**
- **Least privilege**: Containers run with minimal permissions
- **No root**: Never run containers as root user (UID 0)
- **Limited mounts**: Only mount project directory, not sensitive paths
- **No Docker socket**: Application containers must not control Docker
- **Environment secrets**: Pass secrets via env vars, not mounted files
- **Minimal capabilities**: No --privileged mode or dangerous capabilities

**Key Fixtures:**
- `mock_dagger_client`: Tracks all Dagger SDK calls for assertions

### Port Conflict Handling Tests (`test_port_conflicts.py`)

**Goal:** Validate early detection and clear messaging for port conflicts.

**Tests (3 total):**
- Port conflict detected before container creation (1 test)
- Alternative ports suggested on conflict (1 test)
- Port conflict error message clear and actionable (1 test)

**Conflict Prevention:**
- Check port availability before starting containers
- Suggest alternative ports (8010, 8020, etc.)
- Clear error messages with specific ports and solutions

**Key Exception:**
- `PortConflictError`: Raised when port conflicts detected

## Running Hub Security Tests

**All security tests:**
```bash
cd hub/backend
pytest tests/security/ -v
```

**Specific test file:**
```bash
pytest tests/security/test_multi_instance_isolation.py -v
```

**Specific test:**
```bash
pytest tests/security/test_dagger_security.py::test_containers_run_as_non_root -v
```

**In Docker:**
```bash
make test-security  # Includes Hub security tests
```

## Test Count

**Total: 16 tests**
- Multi-instance isolation: 8 tests
- Dagger orchestration security: 5 tests
- Port conflict handling: 3 tests

## Security Violations

Tests are designed to catch critical security violations:

### ❌ Shared Volumes
```python
# VIOLATION
volumes_a = ["commandcenter_postgres_data"]
volumes_b = ["commandcenter_postgres_data"]  # Same volume!

# CORRECT
volumes_a = ["project-alpha_postgres_data"]
volumes_b = ["project-beta_postgres_data"]
```

### ❌ Leaked Secrets
```python
# VIOLATION
env_a["SECRET_KEY"] = "shared-secret-123"
env_b["SECRET_KEY"] = "shared-secret-123"  # Same secret!

# CORRECT
env_a["SECRET_KEY"] = "alpha-secret-xyz"
env_b["SECRET_KEY"] = "beta-secret-abc"
```

### ❌ Root Execution
```python
# VIOLATION
container.with_user("root")  # Running as root!

# CORRECT
container.with_user("1000")  # Non-privileged user
```

### ❌ Docker Socket Exposure
```python
# VIOLATION
container.with_mounted_directory("/var/run/docker.sock", "/var/run/docker.sock")

# CORRECT
# Don't mount Docker socket to application containers
```

### ❌ Privileged Containers
```python
# VIOLATION
container.with_privileged(True)  # Full host access!

# CORRECT
# Don't use privileged mode; minimize capabilities
```

## Notes

- **All tests use mocks**: No real containers started (fast, predictable)
- **Tests designed to fail initially**: TDD red phase
- **Security-first approach**: Violations cause test failures with clear messages
- **Integration with CI**: Automated security validation on every PR
```

**Step 2: Create implementation summary**

Create `hub/backend/tests/security/IMPLEMENTATION_SUMMARY.md`:

```markdown
# Hub Security Tests Implementation Summary

**Branch:** `testing/week2-hub-security`
**Date:** 2025-10-28
**Status:** ✅ Complete

## Deliverables

### Tests Implemented: 16

1. **Multi-Instance Isolation (8 tests)**
   - ✅ Docker volumes isolated between projects
   - ✅ Environment variables not leaked between projects
   - ✅ Database files isolated per project
   - ✅ Network isolation between project stacks
   - ✅ Container names unique per project
   - ✅ Secrets unique per project (SECRET_KEY, DB_PASSWORD)
   - ✅ Port mappings non-overlapping
   - ✅ Log files isolated per project

2. **Dagger Orchestration Security (5 tests)**
   - ✅ Containers run as non-root user
   - ✅ Host filesystem not fully exposed
   - ✅ Docker socket not exposed to application containers
   - ✅ Secrets passed via environment variables (not files)
   - ✅ Container capabilities minimized (no privileged mode)

3. **Port Conflict Handling (3 tests)**
   - ✅ Port conflict detected before container creation
   - ✅ Alternative ports suggested on conflict
   - ✅ Port conflict error message clear and actionable

### Infrastructure Created

- ✅ `hub/backend/tests/security/conftest.py` - Hub security fixtures
- ✅ `hub/backend/tests/security/test_multi_instance_isolation.py` - 8 tests
- ✅ `hub/backend/tests/security/test_dagger_security.py` - 5 tests
- ✅ `hub/backend/tests/security/test_port_conflicts.py` - 3 tests
- ✅ `hub/backend/tests/security/README.md` - Documentation

### Fixtures

- ✅ `project_configs`: 3 isolated project configurations
- ✅ `mock_dagger_client`: Mocked Dagger SDK for unit testing
- ✅ `mock_orchestration_service`: OrchestrationService with mocked Dagger
- ✅ `mock_commandcenter_stack`: Mocked CommandCenter stack

### Test Execution

```bash
# Run all Hub security tests
cd hub/backend
pytest tests/security/ -v

# Expected: Tests may FAIL initially (TDD red phase)
# Implementation needed to make tests pass
```

## Security Requirements Validated

### Multi-Instance Isolation
- ✅ Each project has isolated Docker volumes
- ✅ Secrets (SECRET_KEY, DB_PASSWORD) unique per project
- ✅ Database files stored in project-specific locations
- ✅ Docker networks isolated per project
- ✅ Container names include project identifier
- ✅ Ports non-overlapping across projects
- ✅ Log files separated by project

### Dagger Container Security
- ✅ No root user execution (all containers non-root)
- ✅ Limited filesystem mounts (project directory only)
- ✅ Docker socket NOT exposed to application containers
- ✅ Secrets via environment variables (not mounted files)
- ✅ Minimal Linux capabilities (no privileged mode)

### Port Conflict Prevention
- ✅ Early detection (before container creation)
- ✅ Helpful error messages with specific ports
- ✅ Alternative port suggestions
- ✅ No partial deployments on conflicts

## Next Steps

1. **Implement multi-instance isolation:**
   - Add project-specific prefixes to volume names
   - Generate unique secrets per project at runtime
   - Create isolated Docker networks per project
   - Include project identifier in container names

2. **Implement Dagger security:**
   - Configure non-root user in Dagger containers
   - Restrict filesystem mounts to project directory only
   - Ensure Docker socket not mounted to app containers
   - Pass secrets via `with_env_variable()`, not file mounts
   - Avoid privileged mode and dangerous capabilities

3. **Implement port conflict detection:**
   - Check port availability before starting containers
   - Raise `PortConflictError` with clear message
   - Suggest alternative ports (8010, 8020, 8030)
   - Prevent partial deployments on conflicts

4. **Run tests after implementation:**
   ```bash
   pytest hub/backend/tests/security/ -v
   ```
   Expected: All 16 tests PASS

## Files Created

- `hub/backend/tests/security/__init__.py`
- `hub/backend/tests/security/conftest.py`
- `hub/backend/tests/security/test_multi_instance_isolation.py`
- `hub/backend/tests/security/test_dagger_security.py`
- `hub/backend/tests/security/test_port_conflicts.py`
- `hub/backend/tests/security/README.md`
- `hub/backend/tests/security/IMPLEMENTATION_SUMMARY.md`

## Commits

Total commits: 7
- Infrastructure setup (1)
- Multi-instance isolation tests (2)
- Dagger security tests (2)
- Port conflict tests (1)
- Documentation (1)

## Success Metrics

- ✅ 16 tests implemented
- ✅ Test infrastructure complete
- ✅ All tests syntactically valid
- ✅ Mocked Dagger client (no real containers)
- ✅ Clear security violation messages
- ✅ Documentation complete
- ✅ Ready for consolidation
```

**Step 3: Commit documentation**

```bash
git add hub/backend/tests/security/README.md hub/backend/tests/security/IMPLEMENTATION_SUMMARY.md
git commit -m "docs: Add Hub security tests documentation

- Create README with test overview and security principles
- Create implementation summary with deliverables checklist
- Document multi-instance isolation requirements
- Document Dagger security best practices
- Document port conflict prevention

Week 2 Hub Security Track Complete: 16 tests + infrastructure + docs"
```

**Step 4: Verify all tests are discoverable**

Run:
```bash
cd hub/backend
pytest tests/security/ --collect-only
```

Expected output showing 16 tests collected

**Step 5: Final commit with summary**

```bash
git commit --allow-empty -m "test: Week 2 Hub Security Tests - Track Complete

Summary:
- 16 security tests implemented
- Multi-instance isolation: 8 tests
- Dagger orchestration security: 5 tests
- Port conflict handling: 3 tests

Infrastructure:
- Mock Dagger client (no real containers)
- Project configuration fixtures (3 isolated projects)
- Mock orchestration service
- Complete test documentation

Security Validated:
- Volume isolation per project
- Unique secrets per project
- Network isolation
- Non-root container execution
- Limited filesystem mounts
- No Docker socket exposure
- Port conflict detection

Status: Ready for consolidation to main branch

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>"
```

---

## Verification Checklist

Before marking track complete:

- [ ] All 16 tests implemented and syntactically valid
- [ ] Tests organized in 3 files (isolation, Dagger, ports)
- [ ] Hub security fixtures complete (project_configs, mock_dagger_client)
- [ ] README.md created with security principles
- [ ] IMPLEMENTATION_SUMMARY.md created with requirements
- [ ] All tests discoverable via pytest --collect-only
- [ ] No syntax errors in test files
- [ ] All tests use mocked Dagger (no real containers)
- [ ] Git commits follow conventions
- [ ] Branch ready for merge to main

## Notes for Implementation

**These tests are designed to FAIL initially** (TDD red phase). This is expected and correct.

After tests are written, implementation work is needed:

1. **Multi-Instance Isolation:**
   - Add project-specific prefixes to all resources
   - Generate unique secrets per project
   - Create isolated Docker networks
   - Validate no shared resources

2. **Dagger Security:**
   - Configure non-root user in CommandCenterStack
   - Restrict mounts to project directory only
   - Never mount Docker socket to app containers
   - Pass secrets via environment only

3. **Port Conflicts:**
   - Implement port availability checking
   - Create `PortConflictError` exception class
   - Add helpful error messages with suggestions
   - Prevent partial deployments on conflicts

Once implementation is complete, re-run tests:
```bash
pytest hub/backend/tests/security/ -v
```

Expected: All 16 tests PASS (TDD green phase)

---

**Plan Status:** Complete
**Next Action:** Use superpowers:executing-plans or superpowers:subagent-driven-development to implement this plan
**Estimated Time:** 3-4 hours for test implementation
