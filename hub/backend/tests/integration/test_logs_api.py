import pytest
from unittest.mock import patch, AsyncMock


@pytest.mark.asyncio
async def test_get_logs_endpoint_returns_service_logs(test_client, sample_project):
    """Test GET /api/projects/{id}/logs/{service} returns logs"""
    # Mock the orchestration service
    with patch("app.routers.logs.OrchestrationService") as mock_orch:
        mock_instance = AsyncMock()
        mock_instance.get_project_logs = AsyncMock(return_value="Log line 1\nLog line 2")
        mock_orch.return_value = mock_instance

        response = test_client.get(
            f"/api/v1/projects/{sample_project.id}/logs/backend",
            params={"tail": 50}
        )

    assert response.status_code == 200
    data = response.json()
    assert "logs" in data
    assert "service" in data
    assert data["service"] == "backend"


@pytest.mark.asyncio
async def test_get_logs_endpoint_validates_service_name(test_client, sample_project):
    """Test that invalid service names return 400"""
    response = test_client.get(
        f"/api/v1/projects/{sample_project.id}/logs/invalid_service"
    )

    assert response.status_code == 400
    assert "invalid service" in response.json()["detail"].lower()


@pytest.mark.asyncio
async def test_get_logs_endpoint_handles_project_not_found(test_client):
    """Test 404 for non-existent project"""
    response = test_client.get("/api/v1/projects/99999/logs/backend")

    assert response.status_code == 404
