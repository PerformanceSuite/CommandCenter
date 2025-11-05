"""Tests for correlation middleware."""
import pytest
from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from uuid import uuid4, UUID

from app.correlation.middleware import correlation_middleware
from app.correlation.context import get_correlation_id


@pytest.fixture
def app():
    """Create test FastAPI app with correlation middleware."""
    app = FastAPI()
    app.middleware("http")(correlation_middleware)

    @app.get("/test")
    async def test_route(request: Request):
        return {
            "correlation_id": request.state.correlation_id,
            "context_id": get_correlation_id()
        }

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    with TestClient(app) as c:
        yield c


def test_middleware_generates_correlation_id(client):
    """Test middleware generates correlation ID if not provided."""
    response = client.get("/test")

    assert response.status_code == 200
    data = response.json()

    # Should have generated a UUID
    assert "correlation_id" in data
    assert UUID(data["correlation_id"])  # Valid UUID

    # Should be in response header
    assert "X-Correlation-ID" in response.headers
    assert response.headers["X-Correlation-ID"] == data["correlation_id"]


def test_middleware_preserves_provided_correlation_id(client):
    """Test middleware preserves correlation ID from request header."""
    test_id = str(uuid4())

    response = client.get("/test", headers={"X-Correlation-ID": test_id})

    assert response.status_code == 200
    data = response.json()

    # Should preserve provided ID
    assert data["correlation_id"] == test_id
    assert response.headers["X-Correlation-ID"] == test_id


def test_middleware_rejects_invalid_correlation_id(client):
    """Test middleware generates new ID if provided ID is invalid."""
    response = client.get("/test", headers={"X-Correlation-ID": "not-a-uuid"})

    assert response.status_code == 200
    data = response.json()

    # Should generate new UUID
    assert UUID(data["correlation_id"])
    assert data["correlation_id"] != "not-a-uuid"


def test_middleware_sets_context_variable(client):
    """Test middleware sets correlation ID in context variable."""
    response = client.get("/test")

    assert response.status_code == 200
    data = response.json()

    # Context variable should match request.state
    assert data["context_id"] == data["correlation_id"]
