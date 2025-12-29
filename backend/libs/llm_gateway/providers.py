"""
LLM Provider Configurations for AI Arena

Defines provider model mappings and cost structures for multi-model debate system.
Uses LiteLLM model naming conventions.
"""

from dataclasses import dataclass
from typing import Dict, Optional


@dataclass(frozen=True)
class ProviderCost:
    """Cost per 1M tokens for a provider"""

    input: float  # Cost per 1M input tokens
    output: float  # Cost per 1M output tokens


@dataclass(frozen=True)
class ProviderConfig:
    """Configuration for an LLM provider"""

    model_id: str  # LiteLLM model identifier
    api_base: Optional[str] = None  # Custom API base URL (for OpenAI-compatible providers)
    api_key_env: Optional[str] = None  # Environment variable name for API key


# Provider aliases to configuration
# For OpenAI-compatible APIs (like Z.AI), use openai/ prefix with custom api_base
PROVIDER_CONFIGS: Dict[str, ProviderConfig] = {
    "claude": ProviderConfig(model_id="anthropic/claude-sonnet-4-20250514"),
    "gemini": ProviderConfig(model_id="gemini/gemini-2.5-flash"),
    "gpt": ProviderConfig(model_id="openai/gpt-4o"),
    "gpt-mini": ProviderConfig(model_id="openai/gpt-4o-mini"),
    "zai": ProviderConfig(
        model_id="openai/glm-4.7",
        api_base="https://api.z.ai/api/paas/v4",
        api_key_env="ZAI_API_KEY",
    ),
    "zai-flash": ProviderConfig(
        model_id="openai/glm-4.5-flash",
        api_base="https://api.z.ai/api/paas/v4",
        api_key_env="ZAI_API_KEY",
    ),
}

# Legacy: Simple provider aliases to LiteLLM model identifiers
PROVIDERS: Dict[str, str] = {k: v.model_id for k, v in PROVIDER_CONFIGS.items()}


# Cost per 1M tokens by provider alias
# Updated December 2025 based on provider pricing pages
COSTS: Dict[str, ProviderCost] = {
    "claude": ProviderCost(input=3.0, output=15.0),
    "gemini": ProviderCost(input=0.15, output=0.60),
    "gpt": ProviderCost(input=2.50, output=10.0),
    "gpt-mini": ProviderCost(input=0.15, output=0.60),
    "zai": ProviderCost(input=0.50, output=2.0),  # GLM-4.7 pricing
    "zai-flash": ProviderCost(input=0.05, output=0.20),  # GLM-4.5-flash pricing
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
    "zai": {
        "temperature": 0.7,
        "max_tokens": 4096,
    },
    "zai-flash": {
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


def get_provider_config(provider_alias: str) -> ProviderConfig:
    """
    Get full configuration for a provider.

    Args:
        provider_alias: Short alias like 'claude', 'gpt', 'zai'

    Returns:
        ProviderConfig with model_id, api_base, and api_key_env

    Raises:
        KeyError: If provider alias is not recognized
    """
    if provider_alias not in PROVIDER_CONFIGS:
        raise KeyError(
            f"Unknown provider: {provider_alias}. " f"Available: {list(PROVIDER_CONFIGS.keys())}"
        )
    return PROVIDER_CONFIGS[provider_alias]


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
