"""Integration test fixtures for Docker functionality.

IMPORTANT: These tests use REAL Dagger SDK (not mocked).
They create actual Docker containers for integration testing.
"""
import pytest
import os


@pytest.fixture
async def dagger_client():
    """Real Dagger client for integration tests.

    WARNING: Creates real containers. Cleanup is critical.
    """
    import dagger

    async with dagger.Connection() as client:
        yield client


@pytest.fixture
def temp_project_dir(tmp_path):
    """Temporary project directory with minimal structure."""
    project_dir = tmp_path / "test-project"
    project_dir.mkdir()

    # Create .env
    (project_dir / ".env").write_text("""
DATABASE_URL=postgresql://test:test@postgres:5432/test
REDIS_URL=redis://redis:6379
SECRET_KEY=test-secret-key
BACKEND_PORT=18000
FRONTEND_PORT=13000
POSTGRES_PORT=15432
REDIS_PORT=16379
""")

    # Create minimal structure
    (project_dir / "backend").mkdir()
    (project_dir / "backend" / "app").mkdir()
    (project_dir / "backend" / "app" / "__init__.py").write_text("")
    (project_dir / "frontend").mkdir()
    (project_dir / "frontend" / "src").mkdir()

    return str(project_dir)


@pytest.fixture
def project_config(temp_project_dir):
    """Test project configuration with high ports."""
    from app.models.project import CommandCenterConfig, PortSet

    return CommandCenterConfig(
        project_name="integration-test",
        project_path=temp_project_dir,
        ports=PortSet(
            backend=18000,
            frontend=13000,
            postgres=15432,
            redis=16379
        ),
        secrets={
            "secret_key": "integration-test-secret",
            "db_password": "integration-test-password"
        }
    )
