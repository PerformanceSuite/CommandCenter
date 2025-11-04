import pytest
import os


def test_nats_url_env_var():
    """NATS_URL should be configurable via environment"""
    expected = "nats://nats:4222"
    original = os.environ.get("NATS_URL")
    try:
        os.environ["NATS_URL"] = expected
        assert os.getenv("NATS_URL") == expected
    finally:
        if original is None:
            os.environ.pop("NATS_URL", None)
        else:
            os.environ["NATS_URL"] = original


def test_nats_url_default():
    """NATS_URL should have sensible default"""
    # Clear env var
    if "NATS_URL" in os.environ:
        del os.environ["NATS_URL"]

    from app.config import get_nats_url
    url = get_nats_url()
    assert url.startswith("nats://")


def test_database_url_env_var():
    """DATABASE_URL should be configurable via environment"""
    expected = "postgresql://user:pass@db:5432/hubdb"
    original = os.environ.get("DATABASE_URL")
    try:
        os.environ["DATABASE_URL"] = expected
        # Clear the lru_cache to pick up the new env var
        from app.config import get_database_url
        get_database_url.cache_clear()
        assert get_database_url() == expected
    finally:
        if original is None:
            os.environ.pop("DATABASE_URL", None)
        else:
            os.environ["DATABASE_URL"] = original
        get_database_url.cache_clear()


def test_database_url_default():
    """DATABASE_URL should have sensible default for Docker"""
    original = os.environ.get("DATABASE_URL")
    try:
        # Clear env var
        if "DATABASE_URL" in os.environ:
            del os.environ["DATABASE_URL"]

        from app.config import get_database_url
        get_database_url.cache_clear()
        url = get_database_url()
        assert url.startswith("sqlite+aiosqlite://")
        assert "/app/data/hub.db" in url
    finally:
        if original is not None:
            os.environ["DATABASE_URL"] = original
        get_database_url.cache_clear()


def test_hub_id_env_var():
    """HUB_ID should be configurable via environment"""
    expected = "production-hub-01"
    original = os.environ.get("HUB_ID")
    try:
        os.environ["HUB_ID"] = expected
        # Clear the lru_cache to pick up the new env var
        from app.config import get_hub_id
        get_hub_id.cache_clear()
        assert get_hub_id() == expected
    finally:
        if original is None:
            os.environ.pop("HUB_ID", None)
        else:
            os.environ["HUB_ID"] = original
        get_hub_id.cache_clear()


def test_hub_id_default():
    """HUB_ID should have sensible default"""
    original = os.environ.get("HUB_ID")
    try:
        # Clear env var
        if "HUB_ID" in os.environ:
            del os.environ["HUB_ID"]

        from app.config import get_hub_id
        get_hub_id.cache_clear()
        hub_id = get_hub_id()
        assert hub_id == "local-hub"
    finally:
        if original is not None:
            os.environ["HUB_ID"] = original
        get_hub_id.cache_clear()
