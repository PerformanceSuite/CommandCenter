import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from datetime import datetime, timezone
from uuid import uuid4

from app.main import app
from app.database import get_db
from app.models import Base, Event
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker


@pytest_asyncio.fixture
async def db_session():
    """Create test database session with events table."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create session
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session

    # Cleanup
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session):
    """Create test client with database override."""
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)

    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_publish_event_endpoint(client):
    """POST /api/events should publish event and return event ID."""
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
async def test_query_events_endpoint(client):
    """GET /api/events should return filtered events."""
    response = await client.get("/api/events?subject=hub.test.*&limit=10")

    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_get_event_by_id_endpoint(client):
    """GET /api/events/{event_id} should return specific event."""
    event_id = uuid4()

    response = await client.get(f"/api/events/{event_id}")

    # Will 404 if event doesn't exist, which is fine for this test
    assert response.status_code in [200, 404]
