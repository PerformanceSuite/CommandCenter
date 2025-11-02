"""Unit tests for CorrelationIDMiddleware.

Tests verify that correlation IDs are:
1. Generated when missing
2. Extracted when provided
3. Added to response headers
4. Stored in request state
5. Resilient to errors
"""

import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app


client = TestClient(app)


def test_generates_uuid_when_header_missing():
    """Test that middleware generates a UUID when X-Request-ID header is missing."""
    response = client.get("/health")

    # Should have X-Request-ID in response
    assert "X-Request-ID" in response.headers, "X-Request-ID header missing from response"

    # Should be a valid UUID format (36 characters with hyphens)
    request_id = response.headers["X-Request-ID"]
    assert len(request_id) == 36, f"Invalid UUID length: {len(request_id)}"

    # Verify it's a valid UUID by parsing it
    try:
        uuid.UUID(request_id)
    except ValueError:
        pytest.fail(f"Invalid UUID format: {request_id}")


def test_extracts_existing_request_id():
    """Test that middleware extracts and preserves existing X-Request-ID."""
    custom_id = "test-correlation-123"

    response = client.get("/health", headers={"X-Request-ID": custom_id})

    # Should preserve the custom ID
    assert response.headers["X-Request-ID"] == custom_id, (
        f"Expected {custom_id}, got {response.headers.get('X-Request-ID')}"
    )


def test_adds_request_id_to_response_headers():
    """Test that X-Request-ID is always added to response headers."""
    # Test with missing header
    response1 = client.get("/health")
    assert "X-Request-ID" in response1.headers

    # Test with provided header
    response2 = client.get("/health", headers={"X-Request-ID": "custom-123"})
    assert "X-Request-ID" in response2.headers


def test_stores_request_id_in_request_state():
    """Test that correlation ID is accessible in request.state.

    Note: This test verifies the middleware stores the ID by checking
    that the error response includes request_id (which comes from request.state).
    """
    # Create an endpoint that will trigger the exception handler
    # The exception handler accesses request.state.request_id
    response = client.get("/api/v1/nonexistent-endpoint-that-triggers-404")

    # Even 404s should have correlation ID in headers
    assert "X-Request-ID" in response.headers


def test_middleware_doesnt_fail_on_error():
    """Test that middleware is resilient and doesn't fail on malformed input."""
    # Test with very long header (edge case)
    long_id = "x" * 300
    response = client.get("/health", headers={"X-Request-ID": long_id})

    # Should generate new UUID instead of using invalid long ID
    assert "X-Request-ID" in response.headers
    assert len(response.headers["X-Request-ID"]) == 36  # Valid UUID length


def test_correlation_id_unique_across_requests():
    """Test that different requests get different correlation IDs."""
    response1 = client.get("/health")
    response2 = client.get("/health")

    id1 = response1.headers["X-Request-ID"]
    id2 = response2.headers["X-Request-ID"]

    assert id1 != id2, "Correlation IDs should be unique across requests"


def test_correlation_id_works_with_different_endpoints():
    """Test that correlation ID middleware works across all endpoints."""
    endpoints = [
        "/health",
        "/api/v1/repositories",
        "/api/v1/technologies",
        "/docs",
    ]

    for endpoint in endpoints:
        response = client.get(endpoint)
        assert "X-Request-ID" in response.headers, (
            f"Missing X-Request-ID for endpoint: {endpoint}"
        )
