"""Integration tests for correlation ID flow through app."""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4

from app.main import app


@pytest.fixture
def client():
    """Create test client for main app."""
    return TestClient(app)


def test_correlation_id_flows_through_health_endpoint(client):
    """Test correlation ID is added to health check."""
    response = client.get("/health")

    assert response.status_code == 200
    assert "X-Correlation-ID" in response.headers


def test_correlation_id_flows_through_projects_endpoint(client):
    """Test correlation ID flows through projects API."""
    test_id = str(uuid4())

    response = client.get(
        "/api/projects",
        headers={"X-Correlation-ID": test_id}
    )

    # Should preserve correlation ID
    assert "X-Correlation-ID" in response.headers
    assert response.headers["X-Correlation-ID"] == test_id


def test_multiple_requests_have_different_correlation_ids(client):
    """Test each request gets unique correlation ID."""
    response1 = client.get("/health")
    response2 = client.get("/health")

    id1 = response1.headers["X-Correlation-ID"]
    id2 = response2.headers["X-Correlation-ID"]

    assert id1 != id2
