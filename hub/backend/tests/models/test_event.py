import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.event import Event
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
        await session.rollback()

    await engine.dispose()


@pytest.mark.asyncio
async def test_event_model_creation(db_session):
    """Event should be creatable with required fields."""
    event = Event(
        id=uuid4(),
        subject="hub.test.example",
        origin={"hub_id": "test-hub", "service": "test"},
        correlation_id=uuid4(),
        payload={"test": "data"},
        timestamp=datetime.now(timezone.utc)
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    assert event.id is not None
    assert event.subject == "hub.test.example"
    assert event.origin["hub_id"] == "test-hub"
    assert event.payload["test"] == "data"


@pytest.mark.asyncio
async def test_event_model_indexes(db_session):
    """Event should have indexes on subject, correlation_id, timestamp."""
    from sqlalchemy import inspect

    def get_indexes(session):
        inspector = inspect(session.connection())
        return inspector.get_indexes("events")

    indexes = await db_session.run_sync(get_indexes)

    index_columns = {idx["column_names"][0] for idx in indexes if len(idx["column_names"]) == 1}

    assert "subject" in index_columns
    assert "correlation_id" in index_columns
    assert "timestamp" in index_columns
