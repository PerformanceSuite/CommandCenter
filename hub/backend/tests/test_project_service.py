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
    with patch('app.services.project_service.PortService'), \
         patch('app.services.project_service.SetupService'):
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
async def test_create_project_uses_creating_status(project_service, mock_db):
    """
    Test that create_project() sets status='creating' during setup
    """
    # Mock file system checks
    with patch('os.path.exists', return_value=True):
        # Mock database operations
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock setup service to succeed
        project_service.setup_service.setup_commandcenter = AsyncMock()

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

        # Verify project was added with 'creating' status initially
        added_project = mock_db.add.call_args[0][0]
        assert added_project.status == "creating"

        # Verify setup was called
        assert project_service.setup_service.setup_commandcenter.called

        # Verify status was updated to 'stopped' after success
        assert project.status == "stopped"
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
async def test_failed_setup_marks_project_as_error(project_service, mock_db):
    """
    Test that setup failure updates status to 'error' (Issue #44)
    """
    with patch('os.path.exists', return_value=True):
        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock setup to fail
        project_service.setup_service.setup_commandcenter = AsyncMock(
            side_effect=Exception("Git clone failed")
        )
        project_service.get_project_by_slug = AsyncMock(return_value=None)

        project_data = ProjectCreate(
            name="FailProject",
            path="/test/path",
            use_existing_cc=False,
        )

        # Should raise exception
        with pytest.raises(Exception, match="Git clone failed"):
            await project_service.create_project(project_data)

        # Verify project status was updated to 'error'
        # The project object was created and should have been updated
        added_project = mock_db.add.call_args[0][0]

        # After exception, project should be marked as error
        # This is verified by checking the status attribute was set
        assert added_project.status == "error"
        assert added_project.health == "unhealthy"


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
async def test_exception_logging_on_setup_failure(project_service, mock_db):
    """
    Test that exceptions are properly logged with context
    """
    with patch('os.path.exists', return_value=True), \
         patch('app.services.project_service.logger') as mock_logger:

        mock_db.add = MagicMock()
        mock_db.commit = AsyncMock()
        mock_db.refresh = AsyncMock()

        # Mock setup to fail
        error_msg = "Setup failed: Permission denied"
        project_service.setup_service.setup_commandcenter = AsyncMock(
            side_effect=Exception(error_msg)
        )
        project_service.get_project_by_slug = AsyncMock(return_value=None)

        project_data = ProjectCreate(
            name="LogTestProject",
            path="/test/path",
            use_existing_cc=False,
        )

        # Should raise and log exception
        with pytest.raises(Exception):
            await project_service.create_project(project_data)

        # Verify logger.error was called with correct parameters
        assert mock_logger.error.called
        call_args = mock_logger.error.call_args

        # Check error message contains project info
        assert "LogTestProject" in call_args[0][0] or "LogTestProject" in str(call_args)

        # Check exc_info=True for full traceback
        assert call_args[1].get('exc_info') is True

        # Check extra context
        extra = call_args[1].get('extra', {})
        assert 'project_name' in extra or 'project_id' in extra


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
