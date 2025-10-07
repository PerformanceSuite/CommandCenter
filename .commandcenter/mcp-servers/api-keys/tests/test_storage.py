"""
Tests for API key storage
"""

import pytest
import os
import tempfile
import json
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.storage import APIKeyStorage


@pytest.fixture
def temp_storage_file():
    """Create temporary storage file"""
    fd, path = tempfile.mkstemp(suffix='.enc')
    os.close(fd)
    yield Path(path)
    # Cleanup
    if os.path.exists(path):
        os.remove(path)


@pytest.fixture
def storage(temp_storage_file, monkeypatch):
    """Create storage instance with temp file"""
    # Mock the KEYS_FILE constant
    import tools.storage as storage_module
    monkeypatch.setattr(storage_module, 'KEYS_FILE', temp_storage_file)
    monkeypatch.setattr(storage_module, 'ENCRYPT_KEYS', False)  # Disable encryption for tests
    return APIKeyStorage()


class TestAPIKeyStorage:
    """Test API key storage functionality"""

    def test_add_key(self, storage):
        """Test adding an API key"""
        result = storage.add_key("test_provider", "test-api-key-123")
        assert result is True

        # Verify key was stored
        assert "test_provider" in storage.keys_data["keys"]

    def test_get_key(self, storage):
        """Test retrieving an API key"""
        storage.add_key("test_provider", "test-api-key-123")
        key = storage.get_key("test_provider")
        assert key == "test-api-key-123"

    def test_get_nonexistent_key(self, storage):
        """Test retrieving a key that doesn't exist"""
        key = storage.get_key("nonexistent")
        assert key is None

    def test_remove_key(self, storage):
        """Test removing an API key"""
        storage.add_key("test_provider", "test-api-key-123")
        result = storage.remove_key("test_provider")
        assert result is True

        # Verify key was removed
        assert storage.get_key("test_provider") is None

    def test_remove_nonexistent_key(self, storage):
        """Test removing a key that doesn't exist"""
        result = storage.remove_key("nonexistent")
        assert result is False

    def test_rotate_key(self, storage):
        """Test rotating an API key"""
        storage.add_key("test_provider", "old-key-123")
        result = storage.rotate_key("test_provider", "new-key-456")
        assert result is True

        # Verify new key
        key = storage.get_key("test_provider")
        assert key == "new-key-456"

        # Check rotation metadata
        metadata = storage.get_metadata("test_provider")
        assert metadata["rotation_count"] == 1

    def test_list_providers(self, storage):
        """Test listing providers"""
        storage.add_key("provider1", "key1")
        storage.add_key("provider2", "key2")

        providers = storage.list_providers()
        assert len(providers) == 2
        assert "provider1" in providers
        assert "provider2" in providers

    def test_key_metadata(self, storage):
        """Test key metadata storage"""
        metadata = {
            "description": "Test key",
            "expiration_date": "2025-12-31"
        }
        storage.add_key("test_provider", "test-key", metadata)

        retrieved_metadata = storage.get_metadata("test_provider")
        assert retrieved_metadata["description"] == "Test key"
        assert retrieved_metadata["expiration_date"] == "2025-12-31"
        assert "created_at" in retrieved_metadata
        assert "last_updated" in retrieved_metadata

    def test_audit_log(self, storage):
        """Test audit logging"""
        storage.add_key("test_provider", "test-key")
        storage.get_key("test_provider")
        storage.remove_key("test_provider")

        logs = storage.get_audit_log()
        assert len(logs) >= 3

        # Check log entries
        actions = [log["action"] for log in logs]
        assert "add_key" in actions
        assert "get_key" in actions
        assert "remove_key" in actions

    def test_audit_log_filter(self, storage):
        """Test audit log filtering by provider"""
        storage.add_key("provider1", "key1")
        storage.add_key("provider2", "key2")

        logs = storage.get_audit_log(provider="provider1")
        assert all(log["provider"] == "provider1" for log in logs)

    def test_validate_key_format_anthropic(self, storage):
        """Test Anthropic key validation"""
        is_valid, msg = storage.validate_key_format("anthropic", "sk-ant-api-key-123")
        assert is_valid is True

        is_valid, msg = storage.validate_key_format("anthropic", "invalid-key")
        assert is_valid is False

    def test_validate_key_format_openai(self, storage):
        """Test OpenAI key validation"""
        is_valid, msg = storage.validate_key_format("openai", "sk-api-key-123")
        assert is_valid is True

        is_valid, msg = storage.validate_key_format("openai", "invalid-key")
        assert is_valid is False

    def test_validate_key_format_google(self, storage):
        """Test Google key validation"""
        is_valid, msg = storage.validate_key_format("google", "a" * 25)
        assert is_valid is True

        is_valid, msg = storage.validate_key_format("google", "short")
        assert is_valid is False

    def test_empty_key_validation(self, storage):
        """Test that empty keys are rejected"""
        with pytest.raises(ValueError, match="API key cannot be empty"):
            storage.add_key("test_provider", "")

    def test_persistence(self, storage, temp_storage_file):
        """Test that keys persist across instances"""
        storage.add_key("test_provider", "test-key-123")

        # Create new instance with same file
        import tools.storage as storage_module
        storage_module.KEYS_FILE = temp_storage_file
        new_storage = APIKeyStorage()

        key = new_storage.get_key("test_provider")
        assert key == "test-key-123"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
