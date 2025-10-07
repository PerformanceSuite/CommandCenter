"""
Providers resource - lists available AI providers
"""

from typing import Dict, Any
import json

from ..tools.routing import get_router
from ..tools.storage import get_storage
from ..config import load_routing_config


def get_providers_resource() -> str:
    """
    Get providers resource content

    Returns:
        JSON string with providers information
    """
    router = get_router()
    storage = get_storage()
    config = load_routing_config()

    providers_info = []

    for provider, provider_config in config["providers"].items():
        has_key = provider in storage.list_providers() or provider == "local"
        is_available, reason = router._is_provider_available(provider)

        provider_info = {
            "name": provider,
            "enabled": provider_config.get("enabled", False),
            "available": is_available,
            "availability_reason": reason if not is_available else "Available",
            "has_api_key": has_key,
            "models": provider_config.get("models", []),
            "rate_limit": provider_config.get("rate_limit", 0),
            "pricing": {
                "input_per_1k_tokens": provider_config.get("cost_per_1k_input_tokens", 0.0),
                "output_per_1k_tokens": provider_config.get("cost_per_1k_output_tokens", 0.0)
            },
            "max_tokens": provider_config.get("max_tokens", 0),
            "endpoint": provider_config.get("endpoint") if provider == "local" else None
        }

        providers_info.append(provider_info)

    routing_config = config.get("routing", {})
    fallback_order = config.get("fallback_order", [])

    result = {
        "providers": providers_info,
        "total_providers": len(providers_info),
        "enabled_providers": sum(1 for p in providers_info if p["enabled"]),
        "available_providers": sum(1 for p in providers_info if p["available"]),
        "routing_configuration": routing_config,
        "fallback_order": fallback_order,
        "budget_configuration": config.get("budget", {})
    }

    return json.dumps(result, indent=2)
