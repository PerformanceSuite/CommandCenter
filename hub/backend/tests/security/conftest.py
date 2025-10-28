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
