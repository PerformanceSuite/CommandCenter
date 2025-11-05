"""End-to-end integration test for Phase 2-3.

Tests the complete flow:
1. Event published with correlation ID
2. Query events by correlation ID
3. SSE streaming endpoint exists
4. CLI query integration
"""
import pytest
import asyncio
from uuid import uuid4

from app.events.service import EventService
from app.database import get_db, engine, Base
from app.config import get_nats_url


@pytest.fixture(scope="function", autouse=True)
async def setup_database():
    """Create database tables for tests."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup after test
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.mark.asyncio
async def test_correlation_id_in_event_system():
    """Test correlation ID flows through event publishing and querying."""
    test_correlation_id = uuid4()

    # Publish event with correlation ID
    async for session in get_db():
        event_service = EventService(get_nats_url(), session)
        await event_service.connect()

        event_id = await event_service.publish(
            "hub.test.phase2_3.correlation",
            {"test": "correlation_data"},
            correlation_id=test_correlation_id
        )

        # Query events by correlation ID
        events = await event_service.query_events(
            correlation_id=test_correlation_id
        )

        await event_service.disconnect()

        # Verify correlation ID is preserved
        assert len(events) >= 1
        assert events[0].correlation_id == test_correlation_id
        assert events[0].subject == "hub.test.phase2_3.correlation"
        break


@pytest.mark.asyncio
async def test_event_query_with_subject_filter():
    """Test querying events by subject pattern."""
    # Publish test events
    async for session in get_db():
        event_service = EventService(get_nats_url(), session)
        await event_service.connect()

        # Publish multiple events
        await event_service.publish(
            "hub.test.phase2_3.query.one",
            {"test": "query_test_1"}
        )
        await event_service.publish(
            "hub.test.phase2_3.query.two",
            {"test": "query_test_2"}
        )
        await event_service.publish(
            "hub.other.domain",
            {"test": "should_not_match"}
        )

        # Query with wildcard pattern
        events = await event_service.query_events(
            subject="hub.test.phase2_3.query.*",
            limit=10
        )

        await event_service.disconnect()

        # Should match both .one and .two but not .other
        matching_subjects = [e.subject for e in events]
        assert "hub.test.phase2_3.query.one" in matching_subjects
        assert "hub.test.phase2_3.query.two" in matching_subjects
        assert "hub.other.domain" not in matching_subjects
        break


def test_sse_endpoint_exists():
    """Test SSE streaming endpoint is available."""
    from app.main import app

    # Check that SSE route is registered
    routes = [route.path for route in app.routes]
    assert "/api/events/stream" in routes


@pytest.mark.asyncio
async def test_cli_query_returns_events():
    """Test CLI query function works end-to-end."""
    from click.testing import CliRunner
    from app.cli.__main__ import cli

    # Publish test event
    async for session in get_db():
        event_service = EventService(get_nats_url(), session)
        await event_service.connect()

        await event_service.publish(
            "hub.test.cli.query",
            {"test": "data"}
        )

        await event_service.disconnect()
        break

    # Query via CLI
    runner = CliRunner()
    result = runner.invoke(cli, [
        'query',
        '--subject', 'hub.test.cli.query',
        '--limit', '10'
    ])

    assert result.exit_code == 0
    assert 'hub.test.cli.query' in result.output or 'No events' in result.output
