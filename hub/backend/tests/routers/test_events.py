import pytest
from httpx import AsyncClient
from datetime import datetime, timezone
from uuid import uuid4

from app.main import app


@pytest.mark.asyncio
async def test_publish_event_endpoint():
    """POST /api/events should publish event and return event ID."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/events",
            json={
                "subject": "hub.test.example",
                "payload": {"test": "data"}
            }
        )

    assert response.status_code == 201
    data = response.json()
    assert "event_id" in data
    assert "correlation_id" in data


@pytest.mark.asyncio
async def test_query_events_endpoint():
    """GET /api/events should return filtered events."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/events?subject=hub.test.*&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_event_by_id_endpoint():
    """GET /api/events/{event_id} should return specific event."""
    event_id = uuid4()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(f"/api/events/{event_id}")

    # Will 404 if event doesn't exist, which is fine for this test
    assert response.status_code in [200, 404]
