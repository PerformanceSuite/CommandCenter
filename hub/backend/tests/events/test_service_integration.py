"""Integration tests for EventService with real NATS server."""
import pytest
import pytest_asyncio
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4

from app.events.service import EventService
from app.config import get_nats_url
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.models import Base


@pytest_asyncio.fixture
async def db_session():
    """Create in-memory database for testing."""
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        yield session

    await engine.dispose()


@pytest_asyncio.fixture
async def event_service(db_session):
    """Create EventService connected to real NATS."""
    service = EventService(
        nats_url=get_nats_url(),
        db_session=db_session
    )

    try:
        await service.connect()
        yield service
    finally:
        await service.disconnect()


@pytest.mark.integration
@pytest.mark.asyncio
async def test_publish_and_subscribe_integration(event_service):
    """Should publish event and receive via subscription."""
    received_events = []
    event_received = asyncio.Event()

    async def handler(subject: str, data: dict):
        received_events.append((subject, data))
        event_received.set()

    # Subscribe first
    await event_service.subscribe("hub.test.*", handler)

    # Publish event
    test_payload = {"test": "integration", "value": 123}
    event_id = await event_service.publish(
        subject="hub.test.integration",
        payload=test_payload
    )

    # Wait for event (with timeout)
    try:
        await asyncio.wait_for(event_received.wait(), timeout=2.0)
    except asyncio.TimeoutError:
        pytest.fail("Event not received within timeout")

    # Verify
    assert len(received_events) == 1
    subject, data = received_events[0]
    assert subject == "hub.test.integration"
    assert data["payload"] == test_payload


@pytest.mark.integration
@pytest.mark.asyncio
async def test_replay_integration(event_service):
    """Should replay events from database."""
    # Publish multiple events
    correlation_id = uuid4()
    for i in range(5):
        await event_service.publish(
            subject=f"hub.test.replay.{i}",
            payload={"index": i},
            correlation_id=correlation_id
        )

    # Replay all test events
    events = await event_service.replay(subject_filter="hub.test.replay.%")

    assert len(events) == 5
    assert events[0].payload["index"] == 0
    assert events[4].payload["index"] == 4

    # Replay by correlation ID
    correlated_events = await event_service.replay(correlation_id=correlation_id)
    assert len(correlated_events) == 5
