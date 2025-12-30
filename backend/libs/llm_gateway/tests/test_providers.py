"""Tests for LLM Gateway providers configuration"""

import pytest
from libs.llm_gateway.providers import (
    COSTS,
    PROVIDERS,
    PROVIDER_CONFIGS,
    ProviderCost,
    ProviderConfig,
    DynamicProviderRegistry,
    get_model_id,
    get_provider_cost,
    list_providers,
)


class TestProviders:
    """Tests for provider configuration"""

    def test_providers_contains_claude(self):
        """Claude provider should be configured"""
        assert "claude" in PROVIDERS
        assert "anthropic/" in PROVIDERS["claude"]

    def test_providers_contains_gemini(self):
        """Gemini provider should be configured"""
        assert "gemini" in PROVIDERS
        assert "gemini/" in PROVIDERS["gemini"]

    def test_providers_contains_gpt(self):
        """GPT provider should be configured"""
        assert "gpt" in PROVIDERS
        assert "openai/" in PROVIDERS["gpt"]

    def test_providers_contains_gpt_mini(self):
        """GPT-mini provider should be configured"""
        assert "gpt-mini" in PROVIDERS
        assert "openai/" in PROVIDERS["gpt-mini"]

    def test_providers_contains_zai(self):
        """Z.AI provider should be configured"""
        assert "zai" in PROVIDERS
        assert "openai/" in PROVIDERS["zai"]  # Uses OpenAI-compatible API

    def test_providers_contains_zai_flash(self):
        """Z.AI Flash provider should be configured"""
        assert "zai-flash" in PROVIDERS
        assert "openai/" in PROVIDERS["zai-flash"]

    def test_get_model_id_valid(self):
        """get_model_id returns correct model for valid provider"""
        assert get_model_id("claude") == PROVIDERS["claude"]
        assert get_model_id("gpt") == PROVIDERS["gpt"]
        assert get_model_id("gemini") == PROVIDERS["gemini"]

    def test_get_model_id_invalid_raises(self):
        """get_model_id raises KeyError for unknown provider"""
        with pytest.raises(KeyError) as exc_info:
            get_model_id("unknown_provider")
        assert "Unknown provider" in str(exc_info.value)

    def test_list_providers_returns_all(self):
        """list_providers returns all configured providers"""
        providers = list_providers()
        assert set(providers) == {"claude", "gemini", "gpt", "gpt-mini", "zai", "zai-flash"}


class TestCosts:
    """Tests for cost configuration"""

    def test_costs_contains_all_providers(self):
        """Every provider should have cost info"""
        for provider in PROVIDERS:
            assert provider in COSTS

    def test_cost_structure(self):
        """Cost should have input and output fields"""
        for provider, cost in COSTS.items():
            assert isinstance(cost, ProviderCost)
            assert isinstance(cost.input, (int, float))
            assert isinstance(cost.output, (int, float))
            assert cost.input >= 0
            assert cost.output >= 0

    def test_get_provider_cost_valid(self):
        """get_provider_cost returns correct cost for valid provider"""
        cost = get_provider_cost("claude")
        assert cost.input == 3.0
        assert cost.output == 15.0

    def test_get_provider_cost_invalid_raises(self):
        """get_provider_cost raises KeyError for unknown provider"""
        with pytest.raises(KeyError) as exc_info:
            get_provider_cost("unknown_provider")
        assert "Unknown provider" in str(exc_info.value)

    def test_gpt_mini_cheaper_than_gpt(self):
        """GPT-mini should be cheaper than GPT"""
        gpt_cost = get_provider_cost("gpt")
        mini_cost = get_provider_cost("gpt-mini")
        assert mini_cost.input < gpt_cost.input
        assert mini_cost.output < gpt_cost.output

    def test_gemini_is_economical(self):
        """Gemini should have low costs"""
        gemini = get_provider_cost("gemini")
        claude = get_provider_cost("claude")
        assert gemini.input < claude.input
        assert gemini.output < claude.output


class TestDynamicProviderRegistry:
    """Tests for DynamicProviderRegistry"""

    def test_init_without_db(self):
        """Registry can be initialized without a database"""
        registry = DynamicProviderRegistry()
        assert registry.db is None
        assert registry._cache == {}

    def test_init_with_db(self):
        """Registry can be initialized with a database session"""
        mock_db = object()  # Simple mock
        registry = DynamicProviderRegistry(db=mock_db)
        assert registry.db is mock_db
        assert registry._cache == {}

    def test_get_config_from_static_defaults(self):
        """get_config falls back to static defaults when no DB"""
        registry = DynamicProviderRegistry()
        
        config = registry.get_config("claude")
        assert isinstance(config, ProviderConfig)
        assert config.model_id == "anthropic/claude-sonnet-4-20250514"
        
        config = registry.get_config("gpt")
        assert config.model_id == "openai/gpt-4o"

    def test_get_config_invalid_alias_raises(self):
        """get_config raises KeyError for unknown provider"""
        registry = DynamicProviderRegistry()
        
        with pytest.raises(KeyError) as exc_info:
            registry.get_config("unknown_provider")
        assert "Unknown provider" in str(exc_info.value)

    def test_get_config_uses_cache(self):
        """get_config uses cached values for performance"""
        registry = DynamicProviderRegistry()
        
        # First call
        config1 = registry.get_config("claude")
        
        # Second call should use cache
        config2 = registry.get_config("claude")
        
        # Should be the same object from cache
        assert config1 is config2
        assert "claude" in registry._cache

    def test_list_providers_without_db(self):
        """list_providers returns static providers when no DB"""
        registry = DynamicProviderRegistry()
        
        providers = registry.list_providers()
        assert set(providers) == {"claude", "gemini", "gpt", "gpt-mini", "zai", "zai-flash"}

    def test_list_providers_returns_sorted(self):
        """list_providers returns providers in sorted order"""
        registry = DynamicProviderRegistry()
        
        providers = registry.list_providers()
        assert providers == sorted(providers)

    def test_clear_cache(self):
        """clear_cache empties the cache"""
        registry = DynamicProviderRegistry()
        
        # Populate cache
        registry.get_config("claude")
        registry.get_config("gpt")
        assert len(registry._cache) == 2
        
        # Clear cache
        registry.clear_cache()
        assert registry._cache == {}

    def test_cache_per_instance(self):
        """Each registry instance has its own cache"""
        registry1 = DynamicProviderRegistry()
        registry2 = DynamicProviderRegistry()
        
        registry1.get_config("claude")
        
        assert "claude" in registry1._cache
        assert "claude" not in registry2._cache

    def test_get_config_with_custom_api_base(self):
        """get_config returns configs with custom API base"""
        registry = DynamicProviderRegistry()
        
        config = registry.get_config("zai")
        assert config.api_base == "https://api.z.ai/api/paas/v4"
        assert config.api_key_env == "ZAI_API_KEY"

    def test_all_static_providers_accessible(self):
        """All static PROVIDER_CONFIGS are accessible through registry"""
        registry = DynamicProviderRegistry()
        
        for alias in PROVIDER_CONFIGS.keys():
            config = registry.get_config(alias)
            assert isinstance(config, ProviderConfig)
            assert config.model_id == PROVIDER_CONFIGS[alias].model_id
