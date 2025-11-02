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
    mock_container.with_user = MagicMock(return_value=mock_container)
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
