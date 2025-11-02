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
async def test_check_postgres_health_returns_status(mock_config):
    """Test that check_postgres_health executes pg_isready"""
    stack = CommandCenterStack(mock_config)

    # Create mock - with_exec() is sync, stdout() is async
    mock_exec_result = MagicMock()
    mock_exec_result.stdout = AsyncMock(return_value="accepting connections")

    mock_container = MagicMock()
    mock_container.with_exec = MagicMock(return_value=mock_exec_result)

    stack._service_containers["postgres"] = mock_container

    result = await stack.check_postgres_health()

    assert result["healthy"] is True
    assert result["service"] == "postgres"
    mock_container.with_exec.assert_called_with(["pg_isready", "-U", "commandcenter"])


@pytest.mark.asyncio
async def test_check_redis_health_returns_status(mock_config):
    """Test that check_redis_health executes redis-cli ping"""
    stack = CommandCenterStack(mock_config)

    # Create mock - with_exec() is sync, stdout() is async
    mock_exec_result = MagicMock()
    mock_exec_result.stdout = AsyncMock(return_value="PONG")

    mock_container = MagicMock()
    mock_container.with_exec = MagicMock(return_value=mock_exec_result)

    stack._service_containers["redis"] = mock_container

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
