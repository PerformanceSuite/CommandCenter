"""Unit tests for Celery orchestration tasks"""
import pytest
from unittest.mock import patch, MagicMock, AsyncMock
from app.tasks.orchestration import (
    start_project_task,
    stop_project_task,
    restart_project_task,
    get_project_logs_task,
)


class TestStartProjectTask:
    """Tests for start_project_task"""

    @patch('app.tasks.orchestration.OrchestrationService')
    @patch('app.tasks.orchestration.AsyncSessionLocal')
    def test_start_project_success(self, mock_session_local, mock_service_class):
        """Test successful project start"""
        # Arrange
        project_id = 1
        expected_result = {
            "status": "running",
            "ports": {"backend": 8010, "frontend": 3010}
        }

        # Mock async context manager for database session
        mock_db = MagicMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_session_local.return_value.__aexit__.return_value = AsyncMock()

        # Mock service
        mock_service = MagicMock()
        mock_service.start_project = AsyncMock(return_value=expected_result)
        mock_service_class.return_value = mock_service

        # Act - Use apply() to run task synchronously
        result = start_project_task.apply(args=[project_id]).result

        # Assert
        assert result["success"] is True
        assert result["project_id"] == project_id
        assert result["result"] == expected_result
        mock_service.start_project.assert_called_once_with(project_id)

    # Note: Error handling test is covered by integration tests
    # Unit testing async exceptions through _run_async helper is complex
    # and better tested end-to-end


class TestStopProjectTask:
    """Tests for stop_project_task"""

    @patch('app.tasks.orchestration.OrchestrationService')
    @patch('app.tasks.orchestration.AsyncSessionLocal')
    def test_stop_project_success(self, mock_session_local, mock_service_class):
        """Test successful project stop"""
        # Arrange
        project_id = 1
        expected_result = {"status": "stopped"}

        # Mock async context manager
        mock_db = MagicMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_session_local.return_value.__aexit__.return_value = AsyncMock()

        # Mock service
        mock_service = MagicMock()
        mock_service.stop_project = AsyncMock(return_value=expected_result)
        mock_service_class.return_value = mock_service

        # Act - Use apply() to run task synchronously
        result = stop_project_task.apply(args=[project_id]).result

        # Assert
        assert result["success"] is True
        assert result["project_id"] == project_id
        assert result["result"] == expected_result


class TestRestartProjectTask:
    """Tests for restart_project_task"""

    @patch('app.tasks.orchestration.OrchestrationService')
    @patch('app.tasks.orchestration.AsyncSessionLocal')
    def test_restart_project_success(self, mock_session_local, mock_service_class):
        """Test successful project restart"""
        # Arrange
        project_id = 1
        service_name = "backend"
        expected_result = {"status": "restarted", "service": service_name}

        # Mock async context manager
        mock_db = MagicMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_session_local.return_value.__aexit__.return_value = AsyncMock()

        # Mock service
        mock_service = MagicMock()
        mock_service.restart_service = AsyncMock(return_value=expected_result)
        mock_service_class.return_value = mock_service

        # Act - Use apply() to run task synchronously
        result = restart_project_task.apply(args=[project_id, service_name]).result

        # Assert
        assert result["success"] is True
        assert result["project_id"] == project_id
        assert result["result"] == expected_result


class TestGetProjectLogsTask:
    """Tests for get_project_logs_task"""

    @patch('app.tasks.orchestration.OrchestrationService')
    @patch('app.tasks.orchestration.AsyncSessionLocal')
    def test_get_logs_success(self, mock_session_local, mock_service_class):
        """Test successful log retrieval"""
        # Arrange
        project_id = 1
        service_name = "backend"
        lines = 50
        expected_logs = "Log line 1\nLog line 2\nLog line 3"

        # Mock async context manager
        mock_db = MagicMock()
        mock_session_local.return_value.__aenter__.return_value = mock_db
        mock_session_local.return_value.__aexit__.return_value = AsyncMock()

        # Mock service
        mock_service = MagicMock()
        mock_service.get_service_logs = AsyncMock(return_value=expected_logs)
        mock_service_class.return_value = mock_service

        # Act - Use apply() to run task synchronously
        result = get_project_logs_task.apply(args=[project_id, service_name, lines]).result

        # Assert
        assert result["success"] is True
        assert result["project_id"] == project_id
        assert result["logs"] == expected_logs
        mock_service.get_service_logs.assert_called_once_with(project_id, service_name, lines)
