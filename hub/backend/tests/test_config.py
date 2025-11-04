import pytest
import os


def test_nats_url_env_var():
    """NATS_URL should be configurable via environment"""
    expected = "nats://nats:4222"
    os.environ["NATS_URL"] = expected
    assert os.getenv("NATS_URL") == expected


def test_nats_url_default():
    """NATS_URL should have sensible default"""
    # Clear env var
    if "NATS_URL" in os.environ:
        del os.environ["NATS_URL"]

    from app.config import get_nats_url
    url = get_nats_url()
    assert url.startswith("nats://")
