import pytest
from unittest.mock import AsyncMock, MagicMock
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
    mock_container.with_user = MagicMock(return_value=mock_container)

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
