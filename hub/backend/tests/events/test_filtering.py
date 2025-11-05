"""Tests for EventService filtering methods."""
import pytest
import pytest_asyncio
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
    """Create EventService for testing."""
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
async def test_query_events_by_subject(event_service):
    """Test querying events by subject pattern."""
    # Publish test events
    await event_service.publish("hub.test.foo.created", {"data": 1})
    await event_service.publish("hub.test.bar.created", {"data": 2})
    await event_service.publish("hub.prod.foo.created", {"data": 3})

    # Query with wildcard
    events = await event_service.query_events(subject="hub.test.*")

    assert len(events) == 2
    assert all("hub.test" in e.subject for e in events)


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_events_by_time_range(event_service):
    """Test querying events by time range."""
    now = datetime.now(timezone.utc)
    one_hour_ago = now - timedelta(hours=1)

    # Publish events
    await event_service.publish("hub.test.created", {"data": 1})

    # Query since 1 hour ago
    events = await event_service.query_events(since=one_hour_ago)

    assert len(events) >= 1
    # Convert naive timestamps to UTC for comparison
    for e in events:
        ts = e.timestamp if e.timestamp.tzinfo else e.timestamp.replace(tzinfo=timezone.utc)
        assert ts >= one_hour_ago


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_events_by_correlation_id(event_service):
    """Test querying events by correlation ID."""
    test_correlation_id = uuid4()
    other_correlation_id = uuid4()

    # Publish with specific correlation ID
    await event_service.publish(
        "hub.test.created",
        {"data": 1},
        correlation_id=test_correlation_id
    )
    await event_service.publish(
        "hub.test.created",
        {"data": 2},
        correlation_id=other_correlation_id
    )

    # Query by correlation ID
    events = await event_service.query_events(
        correlation_id=test_correlation_id
    )

    assert len(events) == 1
    assert events[0].correlation_id == test_correlation_id


@pytest.mark.integration
@pytest.mark.asyncio
async def test_query_events_combined_filters(event_service):
    """Test combining multiple filters."""
    test_correlation_id = uuid4()
    one_hour_ago = datetime.now(timezone.utc) - timedelta(hours=1)

    await event_service.publish(
        "hub.test.foo.created",
        {"data": 1},
        correlation_id=test_correlation_id
    )

    # Combine subject, time, and correlation filters
    events = await event_service.query_events(
        subject="hub.test.*",
        since=one_hour_ago,
        correlation_id=test_correlation_id
    )

    assert len(events) == 1
    assert events[0].subject == "hub.test.foo.created"
    assert events[0].correlation_id == test_correlation_id
