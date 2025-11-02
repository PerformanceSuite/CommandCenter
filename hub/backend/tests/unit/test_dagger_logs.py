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
