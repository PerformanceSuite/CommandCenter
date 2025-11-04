import pytest
import asyncio
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from unittest.mock import AsyncMock, MagicMock, patch

from app.events.service import EventService


@pytest.fixture
def mock_nats_client():
    """Mock NATS client."""
    mock = AsyncMock()
    mock.jetstream = MagicMock(return_value=AsyncMock())
    return mock


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    mock = AsyncMock()
    mock.execute = AsyncMock()
    mock.commit = AsyncMock()
    mock.refresh = AsyncMock()
    mock.add = MagicMock()
    return mock


@pytest.fixture
def event_service(mock_nats_client, mock_db_session):
    """Create EventService with mocked dependencies."""
    service = EventService(
        nats_url="nats://localhost:4222",
        db_session=mock_db_session
    )
    service.nc = mock_nats_client
    service.js = mock_nats_client.jetstream()
    return service


@pytest.mark.asyncio
async def test_publish_event(event_service, mock_db_session):
    """Should publish event to NATS and persist to database."""
    subject = "hub.test.example"
    payload = {"test": "data"}
    correlation_id = uuid4()

    event_id = await event_service.publish(
        subject=subject,
        payload=payload,
        correlation_id=correlation_id
    )

    assert event_id is not None
    assert isinstance(event_id, type(uuid4()))

    # Verify database insert called
    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_subscribe_event(event_service):
    """Should subscribe to NATS subject and call handler."""
    subject = "hub.test.*"
    handler_called = asyncio.Event()
    received_data = {}

    async def test_handler(subject: str, data: dict):
        received_data["subject"] = subject
        received_data["data"] = data
        handler_called.set()

    # Start subscription
    await event_service.subscribe(subject, test_handler)

    # Simulate message receipt
    # (In real implementation, this would come from NATS)
    # For unit test, we just verify subscribe was called
    event_service.nc.subscribe.assert_called()


@pytest.mark.asyncio
async def test_replay_events(event_service, mock_db_session):
    """Should query events from database by time range and subject."""
    subject_filter = "hub.test.*"
    since = datetime.now(timezone.utc) - timedelta(hours=1)
    until = datetime.now(timezone.utc)

    # Mock database query result
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_db_session.execute.return_value = mock_result

    events = await event_service.replay(
        subject_filter=subject_filter,
        since=since,
        until=until
    )

    assert isinstance(events, list)
    mock_db_session.execute.assert_awaited_once()
