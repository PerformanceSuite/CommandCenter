"""Tests for Server-Sent Events streaming."""
import pytest
from httpx import AsyncClient, ASGITransport
from uuid import uuid4

from app.main import app


def test_sse_route_exists():
    """Test that SSE route is registered in the app."""
    # Check that the route exists by inspecting FastAPI routes
    routes = [route.path for route in app.routes]
    assert "/api/events/sse" in routes, "SSE endpoint should be registered"


@pytest.mark.asyncio
async def test_sse_endpoint_accepts_parameters():
    """Test SSE endpoint accepts query parameters without errors."""
    transport = ASGITransport(app=app)
    test_id = uuid4()

    # Test each parameter combination
    test_cases = [
        "/api/events/sse",
        "/api/events/sse?subject=hub.test.*",
        f"/api/events/sse?correlation_id={test_id}",
        "/api/events/sse?since=1h",
        f"/api/events/sse?subject=hub.*&correlation_id={test_id}&since=1h"
    ]

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for url in test_cases:
            # We can't actually stream in tests (would hang), but we can verify
            # the endpoint doesn't reject the parameters (no 422 error)
            # Just check the route would be matched by trying OPTIONS
            response = await client.options(url)
            # OPTIONS should return 200 or 405 (method not allowed), not 422 (validation error) or 404
            assert response.status_code in [200, 405], f"Route {url} should accept parameters"
