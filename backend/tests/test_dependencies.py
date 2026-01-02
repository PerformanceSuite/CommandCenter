"""Test that required dependencies are available.

These tests check for optional dependencies that may not be installed
in all environments. They skip if the dependency is unavailable.
"""
import pytest


def _knowledgebeast_available():
    """Check if KnowledgeBeast is available."""
    try:
        from knowledgebeast.backends.postgres import PostgresBackend  # noqa: F401

        return True
    except ImportError:
        return False


def _dagger_available():
    """Check if Dagger is available."""
    try:
        import dagger  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.skipif(
    not _knowledgebeast_available(), reason="KnowledgeBeast not installed or has dependency issues"
)
def test_knowledgebeast_available():
    """Test that KnowledgeBeast can be imported when available."""
    from knowledgebeast.backends.postgres import PostgresBackend

    assert PostgresBackend is not None


@pytest.mark.skipif(not _dagger_available(), reason="Dagger not installed")
def test_dagger_available():
    """Test that Dagger can be imported when available."""
    import dagger

    assert dagger is not None


def test_asyncpg_available():
    """Test that asyncpg can be imported (required dependency)."""
    try:
        import asyncpg

        assert asyncpg is not None
    except ImportError as e:
        pytest.fail(f"asyncpg not available: {e}")
