"""Tests for CLI output formatters."""
import pytest
from datetime import datetime, timezone
from uuid import uuid4

from app.cli.utils.formatters import format_events_table, format_event_json
from app.models.event import Event


@pytest.fixture
def sample_events():
    """Create sample events for testing."""
    return [
        Event(
            id=uuid4(),
            subject="hub.test.project.created",
            origin={"hub_id": "local", "service": "hub-backend"},
            correlation_id=uuid4(),
            payload={"project_id": 1, "name": "Test Project"},
            timestamp=datetime(2025, 11, 4, 10, 30, 0, tzinfo=timezone.utc)
        ),
        Event(
            id=uuid4(),
            subject="hub.test.project.started",
            origin={"hub_id": "local", "service": "hub-backend"},
            correlation_id=uuid4(),
            payload={"project_id": 1},
            timestamp=datetime(2025, 11, 4, 10, 31, 0, tzinfo=timezone.utc)
        )
    ]


def test_format_events_table(sample_events):
    """Test table formatting."""
    output = format_events_table(sample_events)

    # Should contain table structure
    assert "Timestamp" in output
    assert "Subject" in output
    assert "Correlation ID" in output

    # Should contain event data
    assert "project.created" in output
    assert "project.started" in output


def test_format_events_table_truncates_long_subjects(sample_events):
    """Test long subjects are truncated."""
    sample_events[0].subject = "hub." + "x" * 100

    output = format_events_table(sample_events)

    # Should truncate to reasonable length
    assert len([line for line in output.split('\n') if 'xxx' in line][0]) < 200


def test_format_event_json(sample_events):
    """Test JSON formatting."""
    import json

    output = format_event_json(sample_events[0])

    # Should be valid JSON
    parsed = json.loads(output)

    assert parsed["subject"] == "hub.test.project.created"
    assert "timestamp" in parsed
    assert "payload" in parsed


def test_format_events_table_empty():
    """Test formatting empty event list."""
    output = format_events_table([])

    assert "No events" in output or output == ""


def test_format_events_table_with_limit(sample_events):
    """Test table respects limit parameter."""
    output = format_events_table(sample_events, limit=1)

    lines = output.split('\n')
    # Should only include 1 event (plus headers)
    assert 'project.created' in output
    assert 'project.started' not in output
