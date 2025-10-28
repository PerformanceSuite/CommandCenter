import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.orchestration_service import OrchestrationService
from app.models import Project


@pytest.mark.asyncio
async def test_start_project_uses_dagger(db_session, sample_project):
    """Test that start_project uses Dagger instead of subprocess"""
    service = OrchestrationService(db_session)

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
        MockStack.return_value = mock_stack_instance

        # This should not raise subprocess-related errors
        result = await service.start_project(sample_project.id)

        # Verify Dagger was used
        assert MockStack.called, "CommandCenterStack should be instantiated"
        assert mock_stack_instance.start.called, "Stack start should be called"

        # Verify result
        assert result["success"] is True
        assert "Dagger" in result["message"]
        assert "docker-compose" not in str(result).lower()  # Ensure no docker-compose references
