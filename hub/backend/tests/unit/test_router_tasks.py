"""Unit tests for background task router endpoints"""
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient

# Import app for testing
from app.main import app

@pytest.fixture
def client():
    """Test client fixture"""
    with TestClient(app) as c:
        yield c


class TestStartProjectEndpoint:
    """Tests for POST /api/orchestration/{project_id}/start"""

    @patch('app.routers.tasks.start_project_task')
    def test_start_project_returns_task_id(self, mock_task, client):
        """Test that starting a project returns a task ID"""
        # Arrange
        project_id = 1
        task_id = "abc123-task-id"

        # Mock Celery task
        mock_result = MagicMock()
        mock_result.id = task_id
        mock_task.delay.return_value = mock_result

        # Act
        response = client.post(f"/api/orchestration/{project_id}/start")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "pending"
        assert "Poll /api/task-status" in data["message"]
        mock_task.delay.assert_called_once_with(project_id)


class TestStopProjectEndpoint:
    """Tests for POST /api/orchestration/{project_id}/stop"""

    @patch('app.routers.tasks.stop_project_task')
    def test_stop_project_returns_task_id(self, mock_task, client):
        """Test that stopping a project returns a task ID"""
        # Arrange
        project_id = 1
        task_id = "xyz789-task-id"

        # Mock Celery task
        mock_result = MagicMock()
        mock_result.id = task_id
        mock_task.delay.return_value = mock_result

        # Act
        response = client.post(f"/api/orchestration/{project_id}/stop")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["status"] == "pending"
        mock_task.delay.assert_called_once_with(project_id)


class TestTaskStatusEndpoint:
    """Tests for GET /api/task-status/{task_id}"""

    @patch('app.routers.tasks.AsyncResult')
    def test_task_status_pending(self, mock_async_result, client):
        """Test task status when task is pending"""
        # Arrange
        task_id = "pending-task"
        mock_task = MagicMock()
        mock_task.state = 'PENDING'
        mock_task.ready.return_value = False
        mock_task.info = None
        mock_async_result.return_value = mock_task

        # Act
        response = client.get(f"/api/task-status/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["state"] == "PENDING"
        assert data["ready"] is False
        assert data["progress"] == 0

    @patch('app.routers.tasks.AsyncResult')
    def test_task_status_building(self, mock_async_result, client):
        """Test task status when task is building"""
        # Arrange
        task_id = "building-task"
        mock_task = MagicMock()
        mock_task.state = 'BUILDING'
        mock_task.ready.return_value = False
        mock_task.info = {'step': 'Building containers...', 'progress': 50}
        mock_async_result.return_value = mock_task

        # Act
        response = client.get(f"/api/task-status/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["state"] == "BUILDING"
        assert data["progress"] == 50
        assert "Building containers" in data["status"]

    @patch('app.routers.tasks.AsyncResult')
    def test_task_status_success(self, mock_async_result, client):
        """Test task status when task succeeds"""
        # Arrange
        task_id = "success-task"
        expected_result = {"ports": [8010, 3010], "status": "running"}
        mock_task = MagicMock()
        mock_task.state = 'SUCCESS'
        mock_task.ready.return_value = True
        mock_task.result = expected_result
        mock_task.info = None
        mock_async_result.return_value = mock_task

        # Act
        response = client.get(f"/api/task-status/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["state"] == "SUCCESS"
        assert data["ready"] is True
        assert data["progress"] == 100
        assert data["result"] == expected_result

    @patch('app.routers.tasks.AsyncResult')
    def test_task_status_failure(self, mock_async_result, client):
        """Test task status when task fails"""
        # Arrange
        task_id = "failed-task"
        error_msg = "Dagger build failed"
        mock_task = MagicMock()
        mock_task.state = 'FAILURE'
        mock_task.ready.return_value = True
        mock_task.info = error_msg
        mock_async_result.return_value = mock_task

        # Act
        response = client.get(f"/api/task-status/{task_id}")

        # Assert
        assert response.status_code == 200
        data = response.json()
        assert data["task_id"] == task_id
        assert data["state"] == "FAILURE"
        assert data["progress"] == 0
        assert data["error"] == error_msg
