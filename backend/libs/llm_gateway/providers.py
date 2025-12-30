"""
LLM Provider Configurations for AI Arena

Defines provider model mappings and cost structures for multi-model debate system.
Uses LiteLLM model naming conventions.
"""

from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, Optional

if TYPE_CHECKING:
    from sqlalchemy.orm import Session


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


@dataclass
class ModelInfo:
    """Information about an available model"""

    id: str  # LiteLLM model identifier (e.g., "anthropic/claude-sonnet-4-20250514")
    name: str  # Human-readable name (e.g., "Claude Sonnet 4")
    cost_input: float  # Cost per 1M input tokens
    cost_output: float  # Cost per 1M output tokens
    api_key_env: Optional[str] = None  # Environment variable for API key
    api_base: Optional[str] = None  # Custom API base URL


# Provider configuration for dynamic model fetching
PROVIDER_API_KEYS: Dict[str, str] = {
    "anthropic": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "zai": "ZAI_API_KEY",
}

# Custom API bases for non-standard providers
PROVIDER_API_BASES: Dict[str, str] = {
    "zai": "https://api.z.ai/api/paas/v4",
}

# Model prefixes to search for each provider in LiteLLM
PROVIDER_MODEL_PREFIXES: Dict[str, list[str]] = {
    "anthropic": ["claude-"],
    "openai": ["gpt-4o", "gpt-4-turbo", "o1", "o3", "o4"],
    "google": ["gemini/gemini-2", "gemini/gemini-1.5-pro", "gemini/gemini-1.5-flash"],
    "zai": [],  # Z.AI uses custom models not in LiteLLM
}

# Excluded model patterns (embeddings, deprecated, etc.)
EXCLUDED_PATTERNS = [
    "embed",
    "vision",
    "realtime",
    "audio",
    "transcribe",
    "instruct",
    "0301",
    "0314",
    "0613",
    "1106",
    "0125",
    "exp-",
    "preview",
    "latest",
]

# Z.AI custom models (not in LiteLLM)
ZAI_MODELS = [
    ModelInfo(
        id="openai/glm-4.7",
        name="GLM-4.7",
        cost_input=0.50,
        cost_output=2.0,
        api_key_env="ZAI_API_KEY",
        api_base="https://api.z.ai/api/paas/v4",
    ),
    ModelInfo(
        id="openai/glm-4.5-flash",
        name="GLM-4.5 Flash",
        cost_input=0.05,
        cost_output=0.20,
        api_key_env="ZAI_API_KEY",
        api_base="https://api.z.ai/api/paas/v4",
    ),
]


def get_available_models() -> Dict[str, list[ModelInfo]]:
    """
    Dynamically fetch available models from LiteLLM's model registry.

    Returns models grouped by provider with cost information.
    """
    import litellm

    result: Dict[str, list[ModelInfo]] = {}

    for provider, prefixes in PROVIDER_MODEL_PREFIXES.items():
        models: list[ModelInfo] = []
        seen_names: set[str] = set()

        if provider == "zai":
            # Z.AI uses custom models not in LiteLLM
            result[provider] = ZAI_MODELS
            continue

        for model_id, info in litellm.model_cost.items():
            # Check if model matches any of this provider's prefixes
            matches_prefix = any(model_id.startswith(prefix) for prefix in prefixes)
            if not matches_prefix:
                continue

            # Skip excluded patterns
            if any(pattern in model_id.lower() for pattern in EXCLUDED_PATTERNS):
                continue

            # Skip if not a chat model
            if info.get("mode") != "chat":
                continue

            # Get cost info (convert from per-token to per-1M tokens)
            input_cost = info.get("input_cost_per_token", 0) * 1_000_000
            output_cost = info.get("output_cost_per_token", 0) * 1_000_000

            # Create human-readable name
            name = model_id.replace("gemini/", "").replace("-", " ").title()

            # Skip duplicates by name
            if name in seen_names:
                continue
            seen_names.add(name)

            # Format model ID for LiteLLM
            if provider == "anthropic" and not model_id.startswith("anthropic/"):
                formatted_id = f"anthropic/{model_id}"
            elif provider == "openai" and not model_id.startswith("openai/"):
                formatted_id = f"openai/{model_id}"
            elif provider == "google" and not model_id.startswith("gemini/"):
                formatted_id = f"gemini/{model_id}"
            else:
                formatted_id = model_id

            models.append(
                ModelInfo(
                    id=formatted_id,
                    name=name,
                    cost_input=round(input_cost, 2),
                    cost_output=round(output_cost, 2),
                    api_key_env=PROVIDER_API_KEYS.get(provider),
                    api_base=PROVIDER_API_BASES.get(provider),
                )
            )

        # Sort by cost (cheapest first within each provider)
        models.sort(key=lambda m: (m.cost_input + m.cost_output))
        result[provider] = models

    return result


# Cache for available models (refreshed on server restart)
_models_cache: Optional[Dict[str, list[ModelInfo]]] = None


def get_cached_models() -> Dict[str, list[ModelInfo]]:
    """Get cached models, fetching if not cached."""
    global _models_cache
    if _models_cache is None:
        _models_cache = get_available_models()
    return _models_cache


def refresh_models_cache() -> Dict[str, list[ModelInfo]]:
    """Force refresh the models cache."""
    global _models_cache
    _models_cache = get_available_models()
    return _models_cache


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


class DynamicProviderRegistry:
    """
    Dynamic provider registry that reads from database first, then falls back to static configs.

    This registry provides a unified interface for accessing provider configurations,
    with support for:
    - Database-backed provider configs (when Phase 1 is implemented)
    - Static fallback to PROVIDER_CONFIGS
    - Per-instance caching for performance

    Example:
        # Without database (falls back to static configs)
        registry = DynamicProviderRegistry()
        config = registry.get_config("claude")

        # With database session (future Phase 1 integration)
        registry = DynamicProviderRegistry(db=session)
        config = registry.get_config("custom-provider")
    """

    def __init__(self, db: Optional["Session"] = None):
        """
        Initialize the registry.

        Args:
            db: Optional database session for reading provider configs.
                If None, only static configs will be available.
        """
        self.db = db
        self._cache: Dict[str, ProviderConfig] = {}

    def get_config(self, alias: str) -> ProviderConfig:
        """
        Get provider configuration by alias.

        Checks in order:
        1. Instance cache
        2. Database (if available and Phase 1 is implemented)
        3. Static PROVIDER_CONFIGS

        Args:
            alias: Provider alias like 'claude', 'gpt', 'gemini'

        Returns:
            ProviderConfig with model_id, api_base, and api_key_env

        Raises:
            KeyError: If provider alias is not found in any source

        Example:
            config = registry.get_config("claude")
            print(config.model_id)  # "anthropic/claude-sonnet-4-20250514"
        """
        # Check cache first
        if alias in self._cache:
            return self._cache[alias]

        # TODO: Phase 1 - Query database for provider config if db is available
        # if self.db:
        #     from app.services.settings_service import SettingsService
        #     settings_service = SettingsService(self.db)
        #     db_provider = settings_service.get_provider(alias)
        #     if db_provider:
        #         config = ProviderConfig(
        #             model_id=db_provider.model_id,
        #             api_base=db_provider.api_base,
        #             api_key_env=db_provider.api_key_env,
        #         )
        #         self._cache[alias] = config
        #         return config

        # Fall back to static configs
        if alias not in PROVIDER_CONFIGS:
            raise KeyError(
                f"Unknown provider: {alias}. " f"Available: {list(PROVIDER_CONFIGS.keys())}"
            )

        config = PROVIDER_CONFIGS[alias]
        self._cache[alias] = config
        return config

    def list_providers(self) -> list[str]:
        """
        List all available provider aliases.

        Combines providers from:
        - Static PROVIDER_CONFIGS
        - Database (if available and Phase 1 is implemented)

        Returns:
            Sorted list of provider aliases

        Example:
            providers = registry.list_providers()
            # ['claude', 'gemini', 'gpt', 'gpt-mini', 'zai', 'zai-flash']
        """
        providers = set(PROVIDER_CONFIGS.keys())

        # TODO: Phase 1 - Add database providers if db is available
        # if self.db:
        #     from app.services.settings_service import SettingsService
        #     settings_service = SettingsService(self.db)
        #     db_providers = settings_service.list_providers()
        #     providers.update(db_providers)

        return sorted(list(providers))

    def clear_cache(self):
        """
        Clear the configuration cache.

        Call this when provider configs are updated in the database
        to force fresh reads on next access.

        Example:
            registry.clear_cache()  # Force reload from DB/static on next get_config()
        """
        self._cache.clear()


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
