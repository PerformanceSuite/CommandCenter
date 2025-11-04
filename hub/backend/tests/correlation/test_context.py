"""Tests for correlation context management."""
import pytest
from uuid import uuid4
from app.correlation.context import (
    get_correlation_id,
    set_correlation_id,
    clear_correlation_id
)


def test_set_and_get_correlation_id():
    """Test setting and getting correlation ID."""
    test_id = str(uuid4())
    set_correlation_id(test_id)

    result = get_correlation_id()

    assert result == test_id


def test_get_correlation_id_default_none():
    """Test default value is None when not set."""
    clear_correlation_id()

    result = get_correlation_id()

    assert result is None


def test_correlation_id_isolation():
    """Test correlation IDs are isolated per context."""
    import asyncio
    from concurrent.futures import ThreadPoolExecutor

    def set_and_check(value: str) -> str:
        set_correlation_id(value)
        return get_correlation_id()

    # Run in separate threads
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(set_and_check, "id-1")
        future2 = executor.submit(set_and_check, "id-2")

        result1 = future1.result()
        result2 = future2.result()

    assert result1 == "id-1"
    assert result2 == "id-2"
