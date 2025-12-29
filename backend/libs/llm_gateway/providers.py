"""
LLM Provider Configurations for AI Arena

Defines provider model mappings and cost structures for multi-model debate system.
Uses LiteLLM model naming conventions.
"""

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class ProviderCost:
    """Cost per 1M tokens for a provider"""

    input: float  # Cost per 1M input tokens
    output: float  # Cost per 1M output tokens


# Provider aliases to LiteLLM model identifiers
# Format: "alias" -> "provider/model-name"
PROVIDERS: Dict[str, str] = {
    "claude": "anthropic/claude-sonnet-4-20250514",
    "gemini": "gemini/gemini-2.5-flash",
    "gpt": "openai/gpt-4o",
    "gpt-mini": "openai/gpt-4o-mini",
}


# Cost per 1M tokens by provider alias
# Updated December 2025 based on provider pricing pages
COSTS: Dict[str, ProviderCost] = {
    "claude": ProviderCost(input=3.0, output=15.0),
    "gemini": ProviderCost(input=0.15, output=0.60),
    "gpt": ProviderCost(input=2.50, output=10.0),
    "gpt-mini": ProviderCost(input=0.15, output=0.60),
}


# Default parameters for each provider
DEFAULT_PARAMS: Dict[str, Dict] = {
    "claude": {
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "gemini": {
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "gpt": {
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "gpt-mini": {
        "temperature": 0.7,
        "max_tokens": 4096,
    },
}


def get_model_id(provider_alias: str) -> str:
    """
    Get LiteLLM model identifier from provider alias.

    Args:
        provider_alias: Short alias like 'claude', 'gpt', 'gemini'

    Returns:
        Full LiteLLM model identifier

    Raises:
        KeyError: If provider alias is not recognized
    """
    if provider_alias not in PROVIDERS:
        raise KeyError(
            f"Unknown provider: {provider_alias}. " f"Available: {list(PROVIDERS.keys())}"
        )
    return PROVIDERS[provider_alias]


def get_provider_cost(provider_alias: str) -> ProviderCost:
    """
    Get cost structure for a provider.

    Args:
        provider_alias: Short alias like 'claude', 'gpt', 'gemini'

    Returns:
        ProviderCost with input/output costs per 1M tokens

    Raises:
        KeyError: If provider alias is not recognized
    """
    if provider_alias not in COSTS:
        raise KeyError(f"Unknown provider: {provider_alias}. " f"Available: {list(COSTS.keys())}")
    return COSTS[provider_alias]


def list_providers() -> list[str]:
    """List all available provider aliases."""
    return list(PROVIDERS.keys())
