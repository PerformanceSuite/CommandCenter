"""
Tests for CLI configuration management.
"""

import pytest
from pathlib import Path
import tempfile
from cli.config import Config


def test_config_defaults():
    """Test default configuration values."""
    config = Config()

    assert config.api.url == "http://localhost:8000"
    assert config.api.timeout == 30
    assert config.api.verify_ssl is True
    assert config.auth.token is None
    assert config.output.format == "table"
    assert config.output.verbose is False
    assert config.analysis.cache is True
    assert config.agents.max_concurrent == 3


def test_config_load_creates_default():
    """Test loading config creates default if not exists."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"
        config = Config.load(config_path)

        assert config_path.exists()
        assert config.api.url == "http://localhost:8000"


def test_config_save_and_load():
    """Test saving and loading configuration."""
    with tempfile.TemporaryDirectory() as tmpdir:
        config_path = Path(tmpdir) / "config.yaml"

        # Create and save config
        config = Config()
        config.api.url = "http://example.com:9000"
        config.auth.token = "test-token"
        config.save(config_path)

        # Load and verify
        loaded = Config.load(config_path)
        assert loaded.api.url == "http://example.com:9000"
        assert loaded.auth.token == "test-token"


def test_config_get_nested():
    """Test getting nested config values."""
    config = Config()
    config.api.url = "http://test.com"

    assert config.get("api.url") == "http://test.com"
    assert config.get("api.timeout") == 30
    assert config.get("output.format") == "table"


def test_config_set_nested():
    """Test setting nested config values."""
    config = Config()

    config.set("api.url", "http://new.com")
    assert config.api.url == "http://new.com"

    config.set("api.timeout", 60)
    assert config.api.timeout == 60

    config.set("output.verbose", True)
    assert config.output.verbose is True


def test_config_get_invalid_key():
    """Test getting invalid config key raises error."""
    config = Config()

    with pytest.raises(AttributeError):
        config.get("invalid.key")


def test_config_set_invalid_key():
    """Test setting invalid config key raises error."""
    config = Config()

    with pytest.raises(AttributeError):
        config.set("invalid.key", "value")


def test_get_default_config_path():
    """Test getting default config path."""
    path = Config.get_default_config_path()

    assert path == Path.home() / ".commandcenter" / "config.yaml"
    assert isinstance(path, Path)
