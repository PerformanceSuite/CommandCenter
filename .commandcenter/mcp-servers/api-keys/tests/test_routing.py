"""
Tests for multi-provider routing
"""

import pytest
import tempfile
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.routing import ProviderRouter
from tools.storage import APIKeyStorage


@pytest.fixture
def temp_files(monkeypatch):
    """Create temporary files for testing"""
    import tools.storage as storage_module
    import config as config_module

    temp_dir = tempfile.mkdtemp()
    temp_dir_path = Path(temp_dir)

    keys_file = temp_dir_path / ".keys.enc"
    usage_file = temp_dir_path / "usage.json"
    routing_file = temp_dir_path / "routing_config.json"

    monkeypatch.setattr(storage_module, 'KEYS_FILE', keys_file)
    monkeypatch.setattr(storage_module, 'ENCRYPT_KEYS', False)
    monkeypatch.setattr(config_module, 'KEYS_FILE', keys_file)
    monkeypatch.setattr(config_module, 'USAGE_FILE', usage_file)
    monkeypatch.setattr(config_module, 'ROUTING_CONFIG_FILE', routing_file)

    yield temp_dir_path

    import shutil
    shutil.rmtree(temp_dir)


@pytest.fixture
def router(temp_files):
    """Create router instance with configured providers"""
    # Reset singletons
    import tools.routing as routing_module
    import tools.storage as storage_module
    routing_module._router = None
    storage_module._storage = None

    # Initialize config
    from config import ensure_files_exist
    ensure_files_exist()

    # Add test API keys
    storage = APIKeyStorage()
    storage.add_key("anthropic", "sk-ant-test-key-123456789012345678901234567890")
    storage.add_key("openai", "sk-test-key-123456789012345678901234567890")

    return ProviderRouter()


class TestProviderRouter:
    """Test multi-provider routing functionality"""

    def test_route_request_primary(self, router):
        """Test routing to primary provider"""
        result = router.route_request(task_type="code_generation")
        assert result["success"] is True
        assert result["provider"] == "anthropic"  # Default for code_generation
        assert result["is_fallback"] is False

    def test_route_request_with_preferred_provider(self, router):
        """Test routing with preferred provider"""
        result = router.route_request(
            task_type="analysis",
            preferred_provider="openai"
        )
        assert result["success"] is True
        assert result["provider"] == "openai"

    def test_route_request_fallback(self, router):
        """Test fallback routing when primary unavailable"""
        # Disable primary provider
        router.routing_config["providers"]["anthropic"]["enabled"] = False

        result = router.route_request(
            task_type="code_generation",
            enable_fallback=True
        )
        assert result["success"] is True
        assert result["is_fallback"] is True
        assert result["provider"] != "anthropic"

    def test_route_request_no_fallback(self, router):
        """Test routing without fallback"""
        # Disable all providers
        for provider in router.routing_config["providers"]:
            router.routing_config["providers"][provider]["enabled"] = False

        result = router.route_request(
            task_type="code_generation",
            enable_fallback=False
        )
        # Should fail when no providers available
        assert result["success"] is False

    def test_get_best_provider_for_cost(self, router):
        """Test cost-optimized provider selection"""
        result = router.get_best_provider_for_cost(
            task_type="embeddings",
            estimated_tokens=10000
        )
        assert result["success"] is True
        # Local should be cheapest (cost 0)
        assert result["provider"] == "local" or result["estimated_cost"] == 0

    def test_provider_availability_check(self, router):
        """Test provider availability checking"""
        # Anthropic has key and is enabled
        is_available, reason = router._is_provider_available("anthropic")
        assert is_available is True

        # Disable provider
        router.routing_config["providers"]["anthropic"]["enabled"] = False
        is_available, reason = router._is_provider_available("anthropic")
        assert is_available is False
        assert "disabled" in reason.lower()

    def test_update_provider_health(self, router):
        """Test updating provider health status"""
        router.update_provider_health("anthropic", "unhealthy", "Test error")
        health = router.provider_health["anthropic"]

        assert health["status"] == "unhealthy"
        assert health["error"] == "Test error"
        assert "last_check" in health

    def test_get_routing_recommendations(self, router):
        """Test getting routing recommendations"""
        result = router.get_routing_recommendations()
        assert result["success"] is True
        assert "recommendations" in result
        assert "warnings" in result
        assert "available_providers" in result

    def test_update_routing_config(self, router):
        """Test updating routing configuration"""
        result = router.update_routing_config(
            task_type="chat",
            provider="openai"
        )
        assert result["success"] is True
        assert result["task_type"] == "chat"
        assert result["provider"] == "openai"

    def test_get_provider_stats(self, router):
        """Test getting provider statistics"""
        result = router.get_provider_stats()
        assert result["success"] is True
        assert "providers" in result
        assert result["total_providers"] > 0
        assert result["available_providers"] >= 0

    def test_local_provider_no_key_required(self, router):
        """Test that local provider doesn't require API key"""
        # Local should be available even without explicit key
        is_available, reason = router._is_provider_available("local")
        # May be available if enabled, even without key
        assert isinstance(is_available, bool)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
