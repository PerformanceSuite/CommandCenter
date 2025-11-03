"""
Integration tests for Dagger port forwarding and service persistence.

These tests use REAL Dagger containers (not mocks) to verify:
1. Port forwarding works correctly
2. Services persist after context
3. Build process uses project files correctly
"""

import pytest
import asyncio
import socket
from pathlib import Path

from app.dagger_modules.commandcenter import CommandCenterStack, CommandCenterConfig, ResourceLimits


def is_port_available(port: int) -> bool:
    """Check if a port is available (not in use)."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(('127.0.0.1', port))
            return True
        except OSError:
            return False


def find_available_ports(base_port: int, count: int) -> list[int]:
    """Find N available ports starting from base_port."""
    ports = []
    current = base_port
    while len(ports) < count:
        if is_port_available(current):
            ports.append(current)
        current += 1
    return ports


@pytest.fixture
def test_ports():
    """Get available ports for testing."""
    # Try to find 4 available ports starting from 15000
    ports = find_available_ports(15000, 4)
    return {
        'postgres': ports[0],
        'redis': ports[1],
        'backend': ports[2],
        'frontend': ports[3],
    }


@pytest.fixture
def test_config(test_ports, tmp_path):
    """Create test configuration with available ports."""
    # Create a minimal test project structure
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create backend directory with requirements.txt
    backend_dir = project_dir / "backend"
    backend_dir.mkdir()
    (backend_dir / "requirements.txt").write_text("fastapi==0.104.1\nuvicorn[standard]==0.24.0\n")

    # Create frontend directory with package.json
    frontend_dir = project_dir / "frontend"
    frontend_dir.mkdir()
    (frontend_dir / "package.json").write_text('{"name":"test","version":"1.0.0","scripts":{"dev":"echo \\"dev\\""}}')

    return CommandCenterConfig(
        project_name="test_project",
        project_path=str(project_dir),
        postgres_port=test_ports['postgres'],
        redis_port=test_ports['redis'],
        backend_port=test_ports['backend'],
        frontend_port=test_ports['frontend'],
        db_password="test_password_123",
        secret_key="test_secret_key_456",
        resource_limits=ResourceLimits()
    )


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(120)  # 2 minute timeout for container startup
async def test_port_forwarding_postgres(test_config):
    """Test that PostgreSQL port forwarding works correctly."""
    async with CommandCenterStack(test_config) as stack:
        # Build and start just postgres
        postgres = await stack.build_postgres()
        postgres_svc = postgres.as_service()

        # Start with port forwarding
        import dagger
        await postgres_svc.up(ports=[
            dagger.PortForward(backend=5432, frontend=test_config.postgres_port)
        ])

        # Give it a moment to start
        await asyncio.sleep(2)

        # Check that the configured port is now in use
        assert not is_port_available(test_config.postgres_port), \
            f"Port {test_config.postgres_port} should be in use by postgres"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(120)
async def test_port_forwarding_redis(test_config):
    """Test that Redis port forwarding works correctly."""
    async with CommandCenterStack(test_config) as stack:
        # Build and start just redis
        redis = await stack.build_redis()
        redis_svc = redis.as_service()

        # Start with port forwarding
        import dagger
        await redis_svc.up(ports=[
            dagger.PortForward(backend=6379, frontend=test_config.redis_port)
        ])

        # Give it a moment to start
        await asyncio.sleep(2)

        # Check that the configured port is now in use
        assert not is_port_available(test_config.redis_port), \
            f"Port {test_config.redis_port} should be in use by redis"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_build_process_uses_project_files(test_config):
    """Test that backend build process correctly uses requirements.txt from mounted project."""
    async with CommandCenterStack(test_config) as stack:
        # This should NOT raise an error about missing requirements.txt
        # because we mount the project dir BEFORE running pip install
        backend = await stack.build_backend("postgres", "redis")

        # Verify the container was built successfully
        assert backend is not None


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(300)  # 5 minute timeout for full stack
async def test_full_stack_startup_with_port_forwarding(test_config):
    """Test that full stack starts with correct port forwarding."""
    async with CommandCenterStack(test_config) as stack:
        # Start full stack
        result = await stack.start()

        # Verify success
        assert result["success"] is True
        assert "Stack started successfully" in result["message"]

        # Give services time to fully initialize
        await asyncio.sleep(5)

        # Verify all configured ports are in use
        assert not is_port_available(test_config.postgres_port), \
            f"Postgres port {test_config.postgres_port} should be in use"
        assert not is_port_available(test_config.redis_port), \
            f"Redis port {test_config.redis_port} should be in use"
        assert not is_port_available(test_config.backend_port), \
            f"Backend port {test_config.backend_port} should be in use"
        assert not is_port_available(test_config.frontend_port), \
            f"Frontend port {test_config.frontend_port} should be in use"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_service_persistence_across_context(test_config):
    """Test that services persist when stored in instance variables."""
    async with CommandCenterStack(test_config) as stack:
        # Start just postgres
        postgres = await stack.build_postgres()
        postgres_svc = postgres.as_service()

        import dagger
        await postgres_svc.up(ports=[
            dagger.PortForward(backend=5432, frontend=test_config.postgres_port)
        ])

        # Store reference (this is what keeps it alive)
        stack._services['postgres'] = postgres_svc

        # Wait a bit
        await asyncio.sleep(3)

        # Port should still be in use (service still running)
        assert not is_port_available(test_config.postgres_port), \
            "Service should persist while reference is held"


@pytest.mark.integration
@pytest.mark.asyncio
@pytest.mark.timeout(180)
async def test_restart_service_maintains_port_forwarding(test_config):
    """Test that restart_service correctly re-establishes port forwarding."""
    async with CommandCenterStack(test_config) as stack:
        # Start postgres
        postgres = await stack.build_postgres()
        postgres_svc = postgres.as_service()

        import dagger
        await postgres_svc.up(ports=[
            dagger.PortForward(backend=5432, frontend=test_config.postgres_port)
        ])

        stack._service_containers['postgres'] = postgres
        stack._services['postgres'] = postgres_svc

        # Initial port should be in use
        await asyncio.sleep(2)
        assert not is_port_available(test_config.postgres_port)

        # Restart the service
        await stack.restart_service('postgres')

        # Port should still be in use after restart
        await asyncio.sleep(2)
        assert not is_port_available(test_config.postgres_port), \
            "Port should remain in use after service restart"
