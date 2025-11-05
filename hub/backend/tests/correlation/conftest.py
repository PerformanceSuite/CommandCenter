"""Pytest configuration for correlation tests.

These tests don't require database access, so we provide a minimal conftest
to avoid loading database dependencies from the root conftest.
"""
import pytest


@pytest.fixture(autouse=True)
def cleanup_correlation_context():
    """Ensure correlation context is clean for each test."""
    # Import here to avoid circular dependency and ensure modules exist
    try:
        from app.correlation.context import clear_correlation_id
        clear_correlation_id()
        yield
        clear_correlation_id()
    except ImportError:
        # Module doesn't exist yet - this is expected in RED phase
        yield
