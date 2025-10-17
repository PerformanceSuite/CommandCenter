"""
Integration test for complete Dagger orchestration flow

Tests the full project lifecycle: create → start → status check → stop
Uses mocks for Dagger calls to avoid requiring real Dagger engine.
"""

import pytest
from unittest.mock import AsyncMock, patch
from app.services.project_service import ProjectService
from app.services.orchestration_service import OrchestrationService
from app.schemas import ProjectCreate


@pytest.mark.asyncio
@pytest.mark.integration
async def test_complete_dagger_flow(db_session, tmp_path):
    """Test complete project lifecycle with Dagger"""
    project_service = ProjectService(db_session)
    orch_service = OrchestrationService(db_session)

    # Mock the CommandCenterStack to avoid needing a real Dagger engine
    with patch('app.services.orchestration_service.CommandCenterStack') as MockStack:
        # Setup mock stack
        mock_stack_instance = AsyncMock()
        mock_stack_instance.__aenter__ = AsyncMock(return_value=mock_stack_instance)
        mock_stack_instance.__aexit__ = AsyncMock(return_value=None)
        mock_stack_instance.start = AsyncMock(return_value={
            "success": True,
            "message": "Stack started successfully",
            "services": {
                "postgres": {"port": 5432},
                "redis": {"port": 6379},
                "backend": {"port": 8000},
                "frontend": {"port": 3000},
            }
        })
        mock_stack_instance.status = AsyncMock(return_value={
            "status": "running",
            "health": "healthy",
            "containers": []
        })
        mock_stack_instance.stop = AsyncMock(return_value={
            "success": True,
            "message": "Stack stopped successfully"
        })
        MockStack.return_value = mock_stack_instance

        # Step 1: Create project
        project_data = ProjectCreate(
            name="TestProject",
            path=str(tmp_path),
        )
        project = await project_service.create_project(project_data)

        # Verify project created
        assert project is not None
        assert project.name == "TestProject"
        assert project.slug == "testproject"
        assert project.status == "stopped"
        assert project.is_configured is True

        # Step 2: Start project (should use Dagger)
        result = await orch_service.start_project(project.id)

        # Verify start succeeded
        assert result["success"] is True
        assert "Dagger" in result["message"]
        assert result["status"] == "running"
        assert MockStack.called, "CommandCenterStack should be instantiated"
        assert mock_stack_instance.start.called, "Stack start should be called"

        # Verify project status updated
        await db_session.refresh(project)
        assert project.status == "running"
        assert project.last_started is not None

        # Step 3: Check status
        status = await orch_service.get_project_status(project.id)

        # Verify status check
        assert status["status"] == "running"
        assert status["health"] == "healthy"
        assert mock_stack_instance.status.called, "Stack status should be called"

        # Step 4: Stop project
        stop_result = await orch_service.stop_project(project.id)

        # Verify stop succeeded
        assert stop_result["success"] is True
        assert stop_result["status"] == "stopped"
        assert mock_stack_instance.stop.called, "Stack stop should be called"

        # Verify project status updated
        await db_session.refresh(project)
        assert project.status == "stopped"
        assert project.last_stopped is not None


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dagger_flow_with_port_conflicts(db_session, tmp_path):
    """Test that port conflicts are properly detected before starting Dagger"""
    project_service = ProjectService(db_session)
    orch_service = OrchestrationService(db_session)

    # Create project
    project_data = ProjectCreate(
        name="PortConflictTest",
        path=str(tmp_path),
    )
    project = await project_service.create_project(project_data)

    # Mock port check to simulate conflict
    with patch.object(orch_service, '_check_port_available', return_value=(False, "Port in use")):
        # Attempt to start should fail due to port conflict
        with pytest.raises(RuntimeError) as exc_info:
            await orch_service.start_project(project.id)

        assert "already in use" in str(exc_info.value)

        # Verify project status is still stopped (not stuck in 'starting')
        await db_session.refresh(project)
        # Note: The service sets status to 'error' on failure
        assert project.status in ["error", "stopped"]


@pytest.mark.asyncio
@pytest.mark.integration
async def test_dagger_flow_idempotent_operations(db_session, tmp_path):
    """Test that start/stop operations are idempotent"""
    project_service = ProjectService(db_session)
    orch_service = OrchestrationService(db_session)

    # Mock the CommandCenterStack
    with patch('app.services.orchestration_service.CommandCenterStack') as MockStack:
        mock_stack_instance = AsyncMock()
        mock_stack_instance.__aenter__ = AsyncMock(return_value=mock_stack_instance)
        mock_stack_instance.__aexit__ = AsyncMock(return_value=None)
        mock_stack_instance.start = AsyncMock(return_value={
            "success": True,
            "message": "Stack started successfully",
            "services": {
                "postgres": {"port": 5432},
                "redis": {"port": 6379},
                "backend": {"port": 8000},
                "frontend": {"port": 3000},
            }
        })
        mock_stack_instance.stop = AsyncMock(return_value={
            "success": True,
            "message": "Stack stopped successfully"
        })
        MockStack.return_value = mock_stack_instance

        # Create project
        project_data = ProjectCreate(
            name="IdempotentTest",
            path=str(tmp_path),
        )
        project = await project_service.create_project(project_data)

        # Start project
        result1 = await orch_service.start_project(project.id)
        assert result1["success"] is True
        assert result1["status"] == "running"

        # Start again (should be idempotent)
        result2 = await orch_service.start_project(project.id)
        assert result2["success"] is True
        assert result2["message"] == "Project is already running"

        # Stop project
        stop_result1 = await orch_service.stop_project(project.id)
        assert stop_result1["success"] is True
        assert stop_result1["status"] == "stopped"

        # Stop again (should be idempotent)
        stop_result2 = await orch_service.stop_project(project.id)
        assert stop_result2["success"] is True
        assert stop_result2["message"] == "Project is already stopped"
