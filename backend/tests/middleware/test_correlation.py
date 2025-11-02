"""Unit tests for Correlation ID Middleware.

Tests cover:
1. UUID generation when X-Request-ID header missing
2. Header extraction when X-Request-ID present
3. Propagation to response headers
4. Storage in request.state
5. Error handling (middleware shouldn't fail requests)
"""

import uuid
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.middleware.correlation import CorrelationIDMiddleware


# Create test app with middleware
@pytest.fixture
def test_app():
    """Create a test FastAPI app with correlation middleware."""
    app = FastAPI()
    app.add_middleware(CorrelationIDMiddleware)

    @app.get("/test")
    async def test_endpoint():
        return {"message": "test"}

    @app.get("/test-state")
    async def test_state_endpoint(request):
        # Return the request_id from state for verification
        return {"request_id": getattr(request.state, "request_id", None)}

    return app


@pytest.fixture
def client(test_app):
    """Create a test client."""
    return TestClient(test_app)


def test_generates_uuid_when_header_missing(client):
    """Test that middleware generates UUID when X-Request-ID header is missing."""
    response = client.get("/test")

    # Check response has X-Request-ID header
    assert "X-Request-ID" in response.headers

    # Check it's a valid UUID
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 36  # UUID string length

    # Verify it's a valid UUID format
    try:
        uuid.UUID(request_id)
    except ValueError:
        pytest.fail(f"Invalid UUID format: {request_id}")


def test_extracts_existing_request_id(client):
    """Test that middleware extracts existing X-Request-ID from headers."""
    test_id = "test-request-123"

    response = client.get("/test", headers={"X-Request-ID": test_id})

    # Check response has same request ID
    assert response.headers["X-Request-ID"] == test_id


def test_adds_request_id_to_response_headers(client):
    """Test that middleware adds X-Request-ID to response headers."""
    response = client.get("/test")

    # Verify header exists
    assert "X-Request-ID" in response.headers

    # Verify it's not empty
    assert len(response.headers["X-Request-ID"]) > 0


def test_stores_request_id_in_request_state(client):
    """Test that middleware stores request_id in request.state."""
    test_id = "state-test-456"

    response = client.get("/test-state", headers={"X-Request-ID": test_id})

    # Check the endpoint could access request_id from state
    assert response.json()["request_id"] == test_id


def test_middleware_doesnt_fail_on_error(client):
    """Test that middleware doesn't break requests even if something goes wrong."""
    # Test with various edge cases
    edge_cases = [
        "",  # Empty string
        " ",  # Whitespace
        "a" * 1000,  # Very long string
    ]

    for test_id in edge_cases:
        response = client.get("/test", headers={"X-Request-ID": test_id})

        # Request should still succeed
        assert response.status_code == 200

        # Response should have some request ID
        assert "X-Request-ID" in response.headers


def test_strips_whitespace_from_header(client):
    """Test that middleware strips whitespace from provided request ID."""
    test_id = "  whitespace-test-789  "

    response = client.get("/test", headers={"X-Request-ID": test_id})

    # Should strip whitespace
    assert response.headers["X-Request-ID"] == test_id.strip()


def test_multiple_requests_get_different_ids(client):
    """Test that different requests get different UUIDs."""
    response1 = client.get("/test")
    response2 = client.get("/test")

    id1 = response1.headers["X-Request-ID"]
    id2 = response2.headers["X-Request-ID"]

    # IDs should be different
    assert id1 != id2


def test_uuid_format_validity(client):
    """Test that generated UUIDs are valid UUID format."""
    response = client.get("/test")
    request_id = response.headers["X-Request-ID"]

    # Should be parseable as UUID
    parsed_uuid = uuid.UUID(request_id)

    # Should be UUID version 4 (random)
    assert parsed_uuid.version == 4


def test_preserves_client_provided_uuid(client):
    """Test that client-provided UUIDs are preserved exactly."""
    client_uuid = str(uuid.uuid4())

    response = client.get("/test", headers={"X-Request-ID": client_uuid})

    # Should match exactly
    assert response.headers["X-Request-ID"] == client_uuid
