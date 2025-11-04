"""Tests for natural language time parsing."""
import pytest
from datetime import datetime, timezone, timedelta
from app.cli.utils.time_parser import parse_time


def test_parse_relative_hours():
    """Test parsing relative hours (1h, 2h)."""
    result = parse_time("1h")
    expected = datetime.now(timezone.utc) - timedelta(hours=1)

    # Within 1 second tolerance
    assert abs((result - expected).total_seconds()) < 1


def test_parse_relative_minutes():
    """Test parsing relative minutes (30m, 5m)."""
    result = parse_time("30m")
    expected = datetime.now(timezone.utc) - timedelta(minutes=30)

    assert abs((result - expected).total_seconds()) < 1


def test_parse_relative_days():
    """Test parsing relative days (1d, 7d)."""
    result = parse_time("7d")
    expected = datetime.now(timezone.utc) - timedelta(days=7)

    assert abs((result - expected).total_seconds()) < 1


def test_parse_natural_language():
    """Test natural language parsing (yesterday, last Monday)."""
    result = parse_time("yesterday")
    expected = datetime.now(timezone.utc) - timedelta(days=1)

    # Should be roughly 24 hours ago (within 1 hour tolerance)
    assert abs((result - expected).total_seconds()) < 3600


def test_parse_iso_format():
    """Test ISO 8601 datetime parsing."""
    iso_string = "2025-11-04T10:30:00Z"
    result = parse_time(iso_string)

    expected = datetime(2025, 11, 4, 10, 30, 0, tzinfo=timezone.utc)
    assert result == expected


def test_parse_none_returns_none():
    """Test None input returns None."""
    result = parse_time(None)
    assert result is None


def test_parse_empty_string_returns_none():
    """Test empty string returns None."""
    result = parse_time("")
    assert result is None


def test_parse_invalid_raises_error():
    """Test invalid time string raises ValueError."""
    with pytest.raises(ValueError):
        parse_time("not-a-time")
