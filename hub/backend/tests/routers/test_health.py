import pytest
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_health_check():
    """GET /health should return service status."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health")

    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "nats" in data
    assert "database" in data


@pytest.mark.asyncio
async def test_nats_health():
    """GET /health/nats should return NATS connection status."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/health/nats")

    assert response.status_code == 200
    data = response.json()
    assert "connected" in data
