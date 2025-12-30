"""Tests for LLM Gateway providers configuration"""

import pytest
from libs.llm_gateway.providers import (
    COSTS,
    PROVIDERS,
    PROVIDER_CONFIGS,
    DynamicProviderRegistry,
    ProviderConfig,
    ProviderCost,
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

    def test_registry_initialization_without_db(self):
        """Registry should initialize without database"""
        registry = DynamicProviderRegistry()
        assert registry.db is None
        assert registry._cache == {}

    def test_registry_initialization_with_db(self):
        """Registry should accept database session"""
        mock_db = "mock_session"  # In real tests, would be AsyncSession mock
        registry = DynamicProviderRegistry(db=mock_db)
        assert registry.db == mock_db
        assert registry._cache == {}

    def test_get_config_static_provider(self):
        """get_config should return static provider config"""
        registry = DynamicProviderRegistry()
        config = registry.get_config("claude")
        
        assert isinstance(config, ProviderConfig)
        assert config.model_id == "anthropic/claude-sonnet-4-20250514"
        assert config.api_base is None
        assert config.api_key_env is None

    def test_get_config_with_api_base(self):
        """get_config should return config with custom api_base"""
        registry = DynamicProviderRegistry()
        config = registry.get_config("zai")
        
        assert isinstance(config, ProviderConfig)
        assert config.model_id == "openai/glm-4.7"
        assert config.api_base == "https://api.z.ai/api/paas/v4"
        assert config.api_key_env == "ZAI_API_KEY"

    def test_get_config_caching(self):
        """get_config should cache configurations"""
        registry = DynamicProviderRegistry()
        
        # First call
        config1 = registry.get_config("claude")
        assert "claude" in registry._cache
        
        # Second call should return cached value
        config2 = registry.get_config("claude")
        assert config1 is config2  # Same object reference

    def test_get_config_invalid_provider(self):
        """get_config should raise KeyError for unknown provider"""
        registry = DynamicProviderRegistry()
        
        with pytest.raises(KeyError) as exc_info:
            registry.get_config("nonexistent-provider")
        
        assert "Unknown provider" in str(exc_info.value)
        assert "nonexistent-provider" in str(exc_info.value)

    def test_list_providers_without_db(self):
        """list_providers should return static providers when no DB"""
        registry = DynamicProviderRegistry()
        providers = registry.list_providers()
        
        assert isinstance(providers, list)
        assert set(providers) == {"claude", "gemini", "gpt", "gpt-mini", "zai", "zai-flash"}
        assert providers == sorted(providers)  # Should be sorted

    def test_list_providers_with_db_placeholder(self):
        """list_providers should work with DB session (Phase 1 integration point)"""
        mock_db = "mock_session"
        registry = DynamicProviderRegistry(db=mock_db)
        providers = registry.list_providers()
        
        # Currently returns static providers; will include DB providers after Phase 1
        assert isinstance(providers, list)
        assert set(providers) == {"claude", "gemini", "gpt", "gpt-mini", "zai", "zai-flash"}

    def test_clear_cache(self):
        """clear_cache should empty the configuration cache"""
        registry = DynamicProviderRegistry()
        
        # Populate cache
        registry.get_config("claude")
        registry.get_config("gpt")
        assert len(registry._cache) == 2
        
        # Clear cache
        registry.clear_cache()
        assert len(registry._cache) == 0
        
        # Can still get configs after clearing
        config = registry.get_config("claude")
        assert config is not None
        assert len(registry._cache) == 1

    def test_all_static_providers_accessible(self):
        """All static providers should be accessible via registry"""
        registry = DynamicProviderRegistry()
        
        for alias in PROVIDER_CONFIGS.keys():
            config = registry.get_config(alias)
            assert config is not None
            assert config.model_id == PROVIDER_CONFIGS[alias].model_id

    def test_config_immutability(self):
        """ProviderConfig should be immutable (frozen dataclass)"""
        config = ProviderConfig(model_id="test/model")
        
        with pytest.raises(AttributeError):
            config.model_id = "different/model"

    def test_registry_db_integration_point(self):
        """Registry should have placeholder for Phase 1 DB integration"""
        # This test documents the integration point for Phase 1
        # When Phase 1 is complete, the registry should query the database
        mock_db = "mock_session"
        registry = DynamicProviderRegistry(db=mock_db)
        
        # Currently falls back to static config
        config = registry.get_config("claude")
        assert config is not None
        
        # TODO: After Phase 1, this should query database:
        # - Check if provider exists in DB
        # - Return DB config if found
        # - Fall back to static config otherwise
