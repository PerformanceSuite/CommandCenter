"""
Unit tests for project service - Issue #44 race condition fix
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.project_service import ProjectService
from app.models import Project
from app.schemas import ProjectCreate, ProjectStats


@pytest.fixture
def mock_db():
    """Mock database session"""
    db = AsyncMock(spec=AsyncSession)
    return db


@pytest.fixture
def project_service(mock_db):
    """Create project service with mocked dependencies"""
    with patch('app.services.project_service.PortService'):
        service = ProjectService(mock_db)
        # Mock port allocation
        service.port_service.allocate_ports = AsyncMock(
            return_value=MagicMock(
                backend=8000, frontend=3000, postgres=5432, redis=6379
            )
        )
        return service


@pytest.mark.asyncio
async def test_list_projects_excludes_creating_status(project_service, mock_db):
    """
    Test that list_projects() excludes projects with status='creating'
    to prevent race condition (Issue #44)
    """
    # Mock database to return projects with different statuses
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = [
        Project(id=1, name="Project1", status="stopped"),
        Project(id=2, name="Project2", status="running"),
        # Project with 'creating' status should be filtered out by WHERE clause
    ]
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Call list_projects
    projects = await project_service.list_projects()

    # Verify WHERE clause excludes 'creating' status
    call_args = mock_db.execute.call_args[0][0]
    query_str = str(call_args)
    assert "status !=" in query_str or "status <>" in query_str

    # Verify results
    assert len(projects) == 2
    assert all(p.status != "creating" for p in projects)


@pytest.mark.asyncio
async def test_create_project_sets_stopped_status(project_service, mock_db):
    """
    Test that create_project() sets status='stopped' immediately
    (no setup needed - Dagger handles everything)
    """
    # Mock file system checks
    with patch('os.path.exists', return_value=True):
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock get_project_by_slug to return None (no existing project)
        project_service.get_project_by_slug = AsyncMock(return_value=None)

        # Create project data
        project_data = ProjectCreate(
            name="TestProject",
            path="/test/path",
            use_existing_cc=False,
        )

        # Call create_project
        project = await project_service.create_project(project_data)

        # Verify project was added with 'stopped' status (ready to use)
        added_project = mock_db.add.call_args[0][0]
        assert added_project.status == "stopped"

        # Verify project is configured (Dagger handles everything)
        assert project.is_configured is True


@pytest.mark.asyncio
async def test_create_project_existing_cc_skips_creating_status(project_service, mock_db):
    """
    Test that projects using existing CC don't use 'creating' status
    """
    with patch('os.path.exists', return_value=True):
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        project_service.get_project_by_slug = AsyncMock(return_value=None)
        project_service._read_ports_from_env = MagicMock(return_value=None)

        # Create project with existing CC
        project_data = ProjectCreate(
            name="ExistingProject",
            path="/test/path",
            use_existing_cc=True,
            existing_cc_path="/existing/cc",
        )

        project = await project_service.create_project(project_data)

        # Verify status is 'stopped', not 'creating'
        added_project = mock_db.add.call_args[0][0]
        assert added_project.status == "stopped"
        assert project.is_configured is True


@pytest.mark.asyncio
async def test_create_project_validates_path(project_service, mock_db):
    """
    Test that create_project() validates path exists
    """
    # Mock path to not exist
    with patch('os.path.exists', return_value=False):
        project_service.get_project_by_slug = AsyncMock(return_value=None)

        project_data = ProjectCreate(
            name="FailProject",
            path="/invalid/path",
            use_existing_cc=False,
        )

        # Should raise exception for invalid path
        with pytest.raises(ValueError, match="Path does not exist"):
            await project_service.create_project(project_data)


@pytest.mark.asyncio
async def test_get_stats_excludes_creating_projects(project_service, mock_db):
    """
    Test that get_stats() excludes 'creating' projects from total count
    """
    # Mock database result
    mock_result = MagicMock()
    mock_row = MagicMock()
    mock_row.total = 5
    mock_row.running = 2
    mock_row.stopped = 3
    mock_row.errors = 0
    mock_result.one.return_value = mock_row
    mock_db.execute = AsyncMock(return_value=mock_result)

    # Call get_stats
    stats = await project_service.get_stats()

    # Verify WHERE clause was used to exclude 'creating'
    call_args = mock_db.execute.call_args[0][0]
    query_str = str(call_args)
    assert "status !=" in query_str or "status <>" in query_str

    # Verify stats
    assert isinstance(stats, ProjectStats)
    assert stats.total_projects == 5
    assert stats.running == 2
    assert stats.stopped == 3
    assert stats.errors == 0


@pytest.mark.asyncio
async def test_create_project_successful(project_service, mock_db):
    """
    Test that project creation succeeds with valid inputs
    """
    with patch('os.path.exists', return_value=True):
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        project_service.get_project_by_slug = AsyncMock(return_value=None)

        project_data = ProjectCreate(
            name="SuccessProject",
            path="/test/path",
            use_existing_cc=False,
        )

        # Should succeed and return project
        project = await project_service.create_project(project_data)

        # Verify project was created successfully
        assert project is not None
        assert project.name == "SuccessProject"
        assert project.status == "stopped"
        assert project.is_configured is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
