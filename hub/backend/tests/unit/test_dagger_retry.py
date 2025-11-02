import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.dagger_modules.commandcenter import CommandCenterStack, CommandCenterConfig
from app.dagger_modules.retry import retry_with_backoff


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
async def test_retry_with_backoff_succeeds_on_first_try():
    """Test that retry decorator passes through successful calls"""
    call_count = 0

    @retry_with_backoff(max_attempts=3, initial_delay=0.1)
    async def successful_operation():
        nonlocal call_count
        call_count += 1
        return "success"

    result = await successful_operation()

    assert result == "success"
    assert call_count == 1


@pytest.mark.asyncio
async def test_retry_with_backoff_retries_on_failure():
    """Test that retry decorator retries on transient failures"""
    call_count = 0

    @retry_with_backoff(max_attempts=3, initial_delay=0.01)
    async def failing_then_succeeding():
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            raise RuntimeError("Transient error")
        return "success"

    result = await failing_then_succeeding()

    assert result == "success"
    assert call_count == 3  # Failed twice, succeeded third time


@pytest.mark.asyncio
async def test_retry_with_backoff_gives_up_after_max_attempts():
    """Test that retry decorator gives up after max attempts"""
    call_count = 0

    @retry_with_backoff(max_attempts=3, initial_delay=0.01)
    async def always_failing():
        nonlocal call_count
        call_count += 1
        raise RuntimeError("Persistent error")

    with pytest.raises(RuntimeError, match="Persistent error"):
        await always_failing()

    assert call_count == 3  # Tried 3 times then gave up


@pytest.mark.asyncio
async def test_retry_with_backoff_exponential_delay(mock_config):
    """Test that retry delays increase exponentially"""
    delays = []

    @retry_with_backoff(max_attempts=4, initial_delay=0.1)
    async def failing_operation():
        raise RuntimeError("Error")

    with patch('asyncio.sleep', new_callable=AsyncMock) as mock_sleep:
        try:
            await failing_operation()
        except RuntimeError:
            pass

        # Get all sleep durations
        for call in mock_sleep.call_args_list:
            delays.append(call[0][0])

    # Should have 3 delays (after 1st, 2nd, 3rd attempt)
    assert len(delays) == 3
    # Delays should increase: 0.1, 0.2, 0.4
    assert delays[0] == pytest.approx(0.1, rel=0.1)
    assert delays[1] == pytest.approx(0.2, rel=0.1)
    assert delays[2] == pytest.approx(0.4, rel=0.1)


@pytest.mark.asyncio
async def test_stack_start_with_retry(mock_config):
    """Test that CommandCenterStack.start() uses retry logic"""
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

    # Should succeed without raising
    result = await stack.start()

    assert result["success"] is True
