"""Tests for LLM Gateway providers configuration"""

import pytest
from libs.llm_gateway.providers import (
    COSTS,
    PROVIDERS,
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
        assert set(providers) == {"claude", "gemini", "gpt", "gpt-mini"}


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
