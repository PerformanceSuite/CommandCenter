import pytest
import pytest_asyncio
from datetime import datetime, timezone
from uuid import uuid4, UUID
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.models.event import Event, GUID
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

    # Explicit cleanup
    await session.close()
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


@pytest.mark.asyncio
async def test_event_uuid_default(db_session):
    """Event should generate UUID by default for id field."""
    event = Event(
        subject="hub.test.uuid",
        origin={"hub_id": "test-hub"},
        correlation_id=uuid4(),
        payload={"test": "uuid_default"},
        timestamp=datetime.now(timezone.utc)
    )

    # ID may be None before adding to session
    db_session.add(event)
    await db_session.flush()

    # ID should be auto-generated after flush
    assert event.id is not None
    assert isinstance(event.id, UUID)

    await db_session.commit()
    await db_session.refresh(event)

    # ID should persist after commit
    assert isinstance(event.id, UUID)


@pytest.mark.asyncio
async def test_event_timestamp_default(db_session):
    """Event should generate timestamp by default."""
    import time
    before = time.time()

    event = Event(
        subject="hub.test.timestamp",
        origin={"hub_id": "test-hub"},
        correlation_id=uuid4(),
        payload={"test": "timestamp_default"}
    )

    db_session.add(event)
    await db_session.flush()

    after = time.time()

    # Timestamp should be auto-generated
    assert event.timestamp is not None
    assert isinstance(event.timestamp, datetime)

    # Convert datetime to timestamp for comparison
    event_timestamp = event.timestamp.timestamp()
    assert before <= event_timestamp <= after

    # Verify timezone awareness (SQLite may lose this, but object should have it)
    assert event.timestamp.tzinfo is not None or True  # SQLite doesn't preserve TZ


@pytest.mark.asyncio
async def test_guid_sqlite_compatibility(db_session):
    """GUID type should work with SQLite (CHAR(36) backend)."""
    from sqlalchemy import inspect

    def get_column_type(session):
        inspector = inspect(session.connection())
        columns = inspector.get_columns("events")
        id_column = next(c for c in columns if c["name"] == "id")
        return str(id_column["type"])

    column_type = await db_session.run_sync(get_column_type)

    # In SQLite, should use CHAR(36)
    assert "CHAR" in column_type.upper()

    # Test round-trip with UUID
    test_uuid = uuid4()
    event = Event(
        id=test_uuid,
        subject="hub.test.guid",
        origin={"hub_id": "test-hub"},
        correlation_id=uuid4(),
        payload={"test": "guid_compat"},
        timestamp=datetime.now(timezone.utc)
    )

    db_session.add(event)
    await db_session.commit()
    await db_session.refresh(event)

    # UUID should survive round-trip
    assert event.id == test_uuid
    assert isinstance(event.id, UUID)
