"""
Tests for action execution endpoint (Phase 3, Task 3.4)

The action execution endpoint allows agents to execute affordances,
enabling agent parity with the UI.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status


class TestActionExecution:
    """Tests for the /actions/execute endpoint."""

    @pytest.mark.asyncio
    async def test_action_endpoint_exists(self, test_client_with_mocks):
        """Verify the action execution endpoint exists."""
        response = await test_client_with_mocks.post(
            "/api/v1/actions/execute",
            json={
                "action": "trigger_audit",
                "target": {"type": "symbol", "id": "123"},
                "description": "Run audit",
            },
        )
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_execute_trigger_audit(self, test_client_with_mocks):
        """Execute trigger_audit action."""
        response = await test_client_with_mocks.post(
            "/api/v1/actions/execute",
            json={
                "action": "trigger_audit",
                "target": {"type": "symbol", "id": "123"},
                "description": "Run security audit",
                "parameters": {"audit_type": "security"},
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["queued", "completed"]
        assert "job_id" in data

    @pytest.mark.asyncio
    async def test_execute_drill_down(self, test_client_with_mocks):
        """Execute drill_down action returns redirect query."""
        response = await test_client_with_mocks.post(
            "/api/v1/actions/execute",
            json={
                "action": "drill_down",
                "target": {"type": "symbol", "id": "456"},
                "description": "View details",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert "redirect_query" in data
        assert data["redirect_query"]["entities"][0]["type"] == "symbol"

    @pytest.mark.asyncio
    async def test_execute_view_dependencies(self, test_client_with_mocks):
        """Execute view_dependencies action returns dependency query."""
        response = await test_client_with_mocks.post(
            "/api/v1/actions/execute",
            json={
                "action": "view_dependencies",
                "target": {"type": "symbol", "id": "789"},
                "description": "View dependencies",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert "redirect_query" in data
        # Check relationships are included for dependency viewing
        assert len(data["redirect_query"].get("relationships", [])) > 0

    @pytest.mark.asyncio
    async def test_execute_view_callers(self, test_client_with_mocks):
        """Execute view_callers action returns caller query."""
        response = await test_client_with_mocks.post(
            "/api/v1/actions/execute",
            json={
                "action": "view_callers",
                "target": {"type": "symbol", "id": "101"},
                "description": "View callers",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] == "completed"
        assert "redirect_query" in data

    @pytest.mark.asyncio
    async def test_execute_create_task(self, test_client_with_mocks):
        """Execute create_task action."""
        response = await test_client_with_mocks.post(
            "/api/v1/actions/execute",
            json={
                "action": "create_task",
                "target": {"type": "symbol", "id": "202"},
                "description": "Create task",
                "parameters": {"title": "Review this function"},
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["queued", "completed"]

    @pytest.mark.asyncio
    async def test_execute_run_indexer(self, test_client_with_mocks):
        """Execute run_indexer action."""
        response = await test_client_with_mocks.post(
            "/api/v1/actions/execute",
            json={
                "action": "run_indexer",
                "target": {"type": "repo", "id": "303"},
                "description": "Re-index repo",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["status"] in ["queued", "completed"]

    @pytest.mark.asyncio
    async def test_execute_action_includes_message(self, test_client_with_mocks):
        """Action response includes descriptive message."""
        response = await test_client_with_mocks.post(
            "/api/v1/actions/execute",
            json={
                "action": "trigger_audit",
                "target": {"type": "file", "id": "404"},
                "description": "Run audit",
            },
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "message" in data
        assert len(data["message"]) > 0


# Fixtures


@pytest.fixture
async def test_client_with_mocks():
    """Create an async test client with database mocks."""
    from httpx import ASGITransport, AsyncClient

    from app.auth.project_context import get_current_project_id
    from app.database import get_db
    from app.main import app

    # Create mock database session
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar.return_value = 0
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def override_get_db():
        yield mock_session

    async def override_get_project_id():
        return 1

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_project_id] = override_get_project_id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()
