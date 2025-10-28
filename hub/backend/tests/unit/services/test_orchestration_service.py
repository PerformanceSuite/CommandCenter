"""
Unit tests for OrchestrationService

Tests Dagger-based orchestration logic with mocked Dagger SDK.
DOES NOT actually start containers - all Dagger calls are mocked.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from app.services.orchestration_service import OrchestrationService
from app.models import Project
from tests.utils.helpers import create_mock_dagger_stack, create_port_conflict_mock


@pytest.mark.asyncio
async def test_start_project_success(db_session, sample_project, mock_port_available):
    """Test successfully starting a project with Dagger"""
    service = OrchestrationService(db_session)

    # Mock Dagger stack
    mock_stack = create_mock_dagger_stack()

    with patch(
        "app.services.orchestration_service.CommandCenterStack",
        return_value=mock_stack,
    ):
        result = await service.start_project(sample_project.id)

    assert result["success"] is True
    assert result["status"] == "running"
    assert "started successfully" in result["message"].lower()

    # Verify project status updated
    await db_session.refresh(sample_project)
    assert sample_project.status == "running"
    assert sample_project.last_started is not None


@pytest.mark.asyncio
async def test_start_project_already_running(db_session, running_project):
    """Test starting a project that's already running"""
    service = OrchestrationService(db_session)

    result = await service.start_project(running_project.id)

    assert result["success"] is True
    assert result["status"] == "running"
    assert "already running" in result["message"].lower()


@pytest.mark.asyncio
async def test_start_project_port_conflict(db_session, sample_project):
    """Test starting project fails when ports are in use"""
    service = OrchestrationService(db_session)

    # Mock ports as in use
    conflicting_ports = [
        sample_project.frontend_port,
        sample_project.backend_port,
    ]
    mock_sock = create_port_conflict_mock(conflicting_ports)

    with patch("socket.socket", return_value=mock_sock):
        with pytest.raises(RuntimeError, match="ports are already in use"):
            await service.start_project(sample_project.id)

    # Project status should remain unchanged
    await db_session.refresh(sample_project)
    assert sample_project.status == "stopped"


@pytest.mark.asyncio
async def test_start_project_dagger_failure(
    db_session, sample_project, mock_port_available
):
    """Test handling Dagger stack start failure"""
    service = OrchestrationService(db_session)

    # Mock Dagger stack that fails
    mock_stack = create_mock_dagger_stack()
    mock_stack.start = AsyncMock(side_effect=Exception("Dagger error"))

    with patch(
        "app.services.orchestration_service.CommandCenterStack",
        return_value=mock_stack,
    ):
        with pytest.raises(RuntimeError, match="Failed to start project"):
            await service.start_project(sample_project.id)

    # Project status should be error
    await db_session.refresh(sample_project)
    assert sample_project.status == "error"


@pytest.mark.asyncio
async def test_start_project_updates_timestamps(
    db_session, sample_project, mock_port_available
):
    """Test that starting a project updates last_started timestamp"""
    service = OrchestrationService(db_session)
    mock_stack = create_mock_dagger_stack()

    # Store initial timestamp (or None)
    initial_started = sample_project.last_started

    with patch(
        "app.services.orchestration_service.CommandCenterStack",
        return_value=mock_stack,
    ):
        await service.start_project(sample_project.id)

    await db_session.refresh(sample_project)
    assert sample_project.last_started is not None
    # Verify timestamp was updated (different from initial)
    assert sample_project.last_started != initial_started


@pytest.mark.asyncio
async def test_stop_project_success(db_session, running_project):
    """Test successfully stopping a running project"""
    service = OrchestrationService(db_session)

    # Add mock stack to active stacks
    mock_stack = create_mock_dagger_stack()
    service._active_stacks[running_project.id] = mock_stack

    result = await service.stop_project(running_project.id)

    assert result["success"] is True
    assert result["status"] == "stopped"
    assert "stopped successfully" in result["message"].lower()

    # Verify stack was stopped and removed
    assert mock_stack.stop.called
    assert mock_stack.__aexit__.called
    assert running_project.id not in service._active_stacks

    # Verify project status updated
    await db_session.refresh(running_project)
    assert running_project.status == "stopped"
    assert running_project.last_stopped is not None


@pytest.mark.asyncio
async def test_stop_project_already_stopped(db_session, sample_project):
    """Test stopping a project that's already stopped"""
    service = OrchestrationService(db_session)

    result = await service.stop_project(sample_project.id)

    assert result["success"] is True
    assert result["status"] == "stopped"
    assert "already stopped" in result["message"].lower()


@pytest.mark.asyncio
async def test_stop_project_not_in_active_stacks(db_session, running_project):
    """Test stopping a project not in active stacks (graceful handling)"""
    service = OrchestrationService(db_session)

    # Don't add to active stacks
    result = await service.stop_project(running_project.id)

    # Should still succeed (idempotent)
    assert result["success"] is True
    await db_session.refresh(running_project)
    assert running_project.status == "stopped"


@pytest.mark.asyncio
async def test_stop_project_dagger_failure(db_session, running_project):
    """Test handling Dagger stack stop failure"""
    service = OrchestrationService(db_session)

    # Mock stack that fails to stop
    mock_stack = create_mock_dagger_stack()
    mock_stack.stop = AsyncMock(side_effect=Exception("Dagger stop error"))
    service._active_stacks[running_project.id] = mock_stack

    with pytest.raises(RuntimeError, match="Failed to stop project"):
        await service.stop_project(running_project.id)

    # Project status should be error
    await db_session.refresh(running_project)
    assert running_project.status == "error"


@pytest.mark.asyncio
async def test_restart_project(db_session, running_project, mock_port_available):
    """Test restarting a project (stop then start)"""
    service = OrchestrationService(db_session)

    # Add mock stack to active stacks
    mock_stack = create_mock_dagger_stack()
    service._active_stacks[running_project.id] = mock_stack

    with patch(
        "app.services.orchestration_service.CommandCenterStack",
        return_value=mock_stack,
    ):
        result = await service.restart_project(running_project.id)

    assert result["success"] is True
    assert result["status"] == "running"

    # Verify stop was called (old stack)
    assert mock_stack.stop.called


@pytest.mark.asyncio
async def test_get_project_status_running(db_session, running_project):
    """Test getting status of a running project"""
    service = OrchestrationService(db_session)

    # Add mock stack to active stacks
    mock_stack = create_mock_dagger_stack(
        status_result={"status": "running", "health": "healthy", "containers": []}
    )
    service._active_stacks[running_project.id] = mock_stack

    result = await service.get_project_status(running_project.id)

    assert result["status"] == "running"
    assert result["health"] == "healthy"


@pytest.mark.asyncio
async def test_get_project_status_stopped(db_session, sample_project):
    """Test getting status of a stopped project"""
    service = OrchestrationService(db_session)

    result = await service.get_project_status(sample_project.id)

    assert result["status"] == "stopped"
    assert result["health"] == "stopped"


@pytest.mark.asyncio
async def test_get_project_status_not_found(db_session):
    """Test getting status of non-existent project"""
    service = OrchestrationService(db_session)

    with pytest.raises(ValueError, match="not found"):
        await service.get_project_status(999)


@pytest.mark.asyncio
async def test_active_stacks_registry_management(db_session, sample_project):
    """Test that active stacks are properly managed in registry"""
    service = OrchestrationService(db_session)

    # Initially empty
    assert len(service._active_stacks) == 0

    # Start project - should add to registry
    mock_stack = create_mock_dagger_stack()
    with patch(
        "app.services.orchestration_service.CommandCenterStack",
        return_value=mock_stack,
    ), patch("socket.socket") as mock_socket:
        mock_sock = MagicMock()
        mock_sock.connect_ex.return_value = 1  # Port available
        mock_sock.__enter__ = MagicMock(return_value=mock_sock)
        mock_sock.__exit__ = MagicMock(return_value=None)
        mock_socket.return_value = mock_sock

        await service.start_project(sample_project.id)

    assert sample_project.id in service._active_stacks

    # Stop project - should remove from registry
    await service.stop_project(sample_project.id)
    assert sample_project.id not in service._active_stacks


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
