"""
Tests for API key management
"""

import pytest
import os
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.manage import APIKeyManager
from tools.storage import APIKeyStorage


@pytest.fixture
def temp_files(monkeypatch):
    """Create temporary files for testing"""
    import tools.storage as storage_module
    import config as config_module

    # Create temp directory
    temp_dir = tempfile.mkdtemp()
    temp_dir_path = Path(temp_dir)

    # Mock file paths
    keys_file = temp_dir_path / ".keys.enc"
    usage_file = temp_dir_path / "usage.json"
    routing_file = temp_dir_path / "routing_config.json"

    monkeypatch.setattr(storage_module, 'KEYS_FILE', keys_file)
    monkeypatch.setattr(storage_module, 'ENCRYPT_KEYS', False)
    monkeypatch.setattr(config_module, 'KEYS_FILE', keys_file)
    monkeypatch.setattr(config_module, 'USAGE_FILE', usage_file)
    monkeypatch.setattr(config_module, 'ROUTING_CONFIG_FILE', routing_file)

    yield temp_dir_path

    # Cleanup
    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def manager(temp_files):
    """Create manager instance"""
    # Reset singleton
    import tools.manage as manage_module
    manage_module._manager = None
    import tools.storage as storage_module
    storage_module._storage = None

    # Initialize config files
    from config import ensure_files_exist
    ensure_files_exist()

    return APIKeyManager()


class TestAPIKeyManager:
    """Test API key manager functionality"""

    def test_add_key_success(self, manager):
        """Test adding a valid API key"""
        result = manager.add_key(
            provider="anthropic",
            api_key="sk-ant-test-key-123456789012345678901234567890"
        )
        assert result["success"] is True
        assert result["provider"] == "anthropic"

    def test_add_key_invalid_provider(self, manager):
        """Test adding key for unknown provider"""
        result = manager.add_key(
            provider="unknown_provider",
            api_key="test-key"
        )
        assert result["success"] is False
        assert "Unknown provider" in result["error"]

    def test_add_key_invalid_format(self, manager):
        """Test adding key with invalid format"""
        result = manager.add_key(
            provider="anthropic",
            api_key="invalid-format"
        )
        assert result["success"] is False
        assert "Invalid API key format" in result["error"]

    def test_add_key_from_env_var(self, manager, monkeypatch):
        """Test adding key from environment variable"""
        monkeypatch.setenv("TEST_API_KEY", "sk-ant-test-key-123456789012345678901234567890")

        result = manager.add_key(
            provider="anthropic",
            env_var="TEST_API_KEY"
        )
        assert result["success"] is True

    def test_add_key_missing_env_var(self, manager):
        """Test adding key from non-existent env var"""
        result = manager.add_key(
            provider="anthropic",
            env_var="NONEXISTENT_VAR"
        )
        assert result["success"] is False
        assert "not found" in result["error"]

    def test_remove_key_success(self, manager):
        """Test removing an existing key"""
        manager.add_key(
            provider="anthropic",
            api_key="sk-ant-test-key-123456789012345678901234567890"
        )

        result = manager.remove_key("anthropic")
        assert result["success"] is True

    def test_remove_key_not_found(self, manager):
        """Test removing a non-existent key"""
        result = manager.remove_key("anthropic")
        assert result["success"] is False

    def test_rotate_key(self, manager):
        """Test rotating an API key"""
        # Add initial key
        manager.add_key(
            provider="anthropic",
            api_key="sk-ant-old-key-123456789012345678901234567890"
        )

        # Rotate to new key
        result = manager.rotate_key(
            provider="anthropic",
            new_api_key="sk-ant-new-key-123456789012345678901234567890"
        )
        assert result["success"] is True

    def test_list_keys(self, manager):
        """Test listing keys"""
        manager.add_key(
            provider="anthropic",
            api_key="sk-ant-test-key-123456789012345678901234567890"
        )
        manager.add_key(
            provider="openai",
            api_key="sk-test-key-123456789012345678901234567890"
        )

        result = manager.list_keys()
        assert result["total_count"] == 2
        assert len(result["providers"]) == 2

        provider_names = [p["name"] for p in result["providers"]]
        assert "anthropic" in provider_names
        assert "openai" in provider_names

    def test_get_key_info(self, manager):
        """Test getting key information"""
        manager.add_key(
            provider="anthropic",
            api_key="sk-ant-test-key-123456789012345678901234567890",
            description="Test key"
        )

        result = manager.get_key_info("anthropic")
        assert result["success"] is True
        assert result["provider"] == "anthropic"
        assert result["has_key"] is True
        assert "metadata" in result

    def test_get_key_info_not_found(self, manager):
        """Test getting info for non-existent key"""
        result = manager.get_key_info("anthropic")
        assert result["success"] is False

    def test_update_provider_config(self, manager):
        """Test updating provider configuration"""
        result = manager.update_provider_config(
            provider="anthropic",
            enabled=False
        )
        assert result["success"] is True
        assert result["config"]["enabled"] is False

    def test_update_unknown_provider_config(self, manager):
        """Test updating config for unknown provider"""
        result = manager.update_provider_config(
            provider="unknown",
            enabled=True
        )
        assert result["success"] is False

    def test_get_audit_log(self, manager):
        """Test retrieving audit log"""
        manager.add_key(
            provider="anthropic",
            api_key="sk-ant-test-key-123456789012345678901234567890"
        )

        result = manager.get_audit_log()
        assert result["success"] is True
        assert len(result["entries"]) > 0

    def test_get_audit_log_filtered(self, manager):
        """Test retrieving filtered audit log"""
        manager.add_key(
            provider="anthropic",
            api_key="sk-ant-test-key-123456789012345678901234567890"
        )
        manager.add_key(
            provider="openai",
            api_key="sk-test-key-123456789012345678901234567890"
        )

        result = manager.get_audit_log(provider="anthropic")
        assert result["success"] is True
        assert result["provider_filter"] == "anthropic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
