"""Test that required dependencies are available."""
import pytest


def test_knowledgebeast_available():
    """Test that KnowledgeBeast can be imported."""
    try:
        from knowledgebeast.backends.postgres import PostgresBackend

        assert PostgresBackend is not None
    except ImportError as e:
        pytest.fail(f"KnowledgeBeast not available: {e}")


def test_dagger_available():
    """Test that Dagger can be imported."""
    try:
        import dagger

        assert dagger is not None
    except ImportError as e:
        pytest.fail(f"Dagger not available: {e}")


def test_asyncpg_available():
    """Test that asyncpg can be imported."""
    try:
        import asyncpg

        assert asyncpg is not None
    except ImportError as e:
        pytest.fail(f"asyncpg not available: {e}")
