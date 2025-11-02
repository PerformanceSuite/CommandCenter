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
async def test_restart_service_validates_service_name(mock_config):
    """Test that restart_service validates service name"""
    stack = CommandCenterStack(mock_config)
    stack.client = MagicMock()

    with pytest.raises(ValueError, match="Invalid service name"):
        await stack.restart_service("invalid_service")


@pytest.mark.asyncio
async def test_restart_service_rebuilds_container(mock_config):
    """Test that restart_service rebuilds the container"""
    stack = CommandCenterStack(mock_config)

    # Mock Dagger client
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_container.from_ = MagicMock(return_value=mock_container)
    mock_container.with_user = MagicMock(return_value=mock_container)
    mock_container.with_env_variable = MagicMock(return_value=mock_container)
    mock_container.with_exposed_port = MagicMock(return_value=mock_container)
    mock_container.with_resource_limit = MagicMock(return_value=mock_container)
    mock_container.as_service = MagicMock()

    mock_client.container = MagicMock(return_value=mock_container)
    stack.client = mock_client

    # Add existing container to registry
    old_container = MagicMock()
    stack._service_containers["postgres"] = old_container

    # Restart postgres
    result = await stack.restart_service("postgres")

    assert result["success"] is True
    assert result["service"] == "postgres"
    assert "restarted" in result["message"].lower()

    # Verify new container was built
    assert stack._service_containers["postgres"] is not old_container


@pytest.mark.asyncio
async def test_restart_service_handles_redis(mock_config):
    """Test that restart_service works for Redis"""
    stack = CommandCenterStack(mock_config)

    # Mock Dagger client
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_container.from_ = MagicMock(return_value=mock_container)
    mock_container.with_user = MagicMock(return_value=mock_container)
    mock_container.with_exposed_port = MagicMock(return_value=mock_container)
    mock_container.with_resource_limit = MagicMock(return_value=mock_container)
    mock_container.as_service = MagicMock()

    mock_client.container = MagicMock(return_value=mock_container)
    stack.client = mock_client

    stack._service_containers["redis"] = MagicMock()

    result = await stack.restart_service("redis")

    assert result["success"] is True
    assert result["service"] == "redis"


@pytest.mark.asyncio
async def test_restart_service_handles_backend(mock_config):
    """Test that restart_service works for backend"""
    stack = CommandCenterStack(mock_config)

    # Mock Dagger client
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_container.from_ = MagicMock(return_value=mock_container)
    mock_container.with_user = MagicMock(return_value=mock_container)
    mock_container.with_env_variable = MagicMock(return_value=mock_container)
    mock_container.with_exposed_port = MagicMock(return_value=mock_container)
    mock_container.with_resource_limit = MagicMock(return_value=mock_container)
    mock_container.with_exec = MagicMock(return_value=mock_container)
    mock_container.with_mounted_directory = MagicMock(return_value=mock_container)
    mock_container.with_workdir = MagicMock(return_value=mock_container)
    mock_container.as_service = MagicMock()

    mock_host = MagicMock()
    mock_host.directory = MagicMock(return_value=MagicMock())

    mock_client.container = MagicMock(return_value=mock_container)
    mock_client.host = MagicMock(return_value=mock_host)
    stack.client = mock_client

    stack._service_containers["backend"] = MagicMock()

    result = await stack.restart_service("backend")

    assert result["success"] is True
    assert result["service"] == "backend"


@pytest.mark.asyncio
async def test_restart_service_handles_frontend(mock_config):
    """Test that restart_service works for frontend"""
    stack = CommandCenterStack(mock_config)

    # Mock Dagger client
    mock_client = MagicMock()
    mock_container = MagicMock()
    mock_container.from_ = MagicMock(return_value=mock_container)
    mock_container.with_user = MagicMock(return_value=mock_container)
    mock_container.with_env_variable = MagicMock(return_value=mock_container)
    mock_container.with_exposed_port = MagicMock(return_value=mock_container)
    mock_container.with_resource_limit = MagicMock(return_value=mock_container)
    mock_container.with_exec = MagicMock(return_value=mock_container)
    mock_container.as_service = MagicMock()

    mock_client.container = MagicMock(return_value=mock_container)
    stack.client = mock_client

    stack._service_containers["frontend"] = MagicMock()

    result = await stack.restart_service("frontend")

    assert result["success"] is True
    assert result["service"] == "frontend"


@pytest.mark.asyncio
async def test_restart_service_fails_if_service_not_in_registry(mock_config):
    """Test that restart_service fails gracefully if service not running"""
    stack = CommandCenterStack(mock_config)
    stack.client = MagicMock()

    # No services in registry
    with pytest.raises(RuntimeError, match="not found in registry"):
        await stack.restart_service("postgres")
