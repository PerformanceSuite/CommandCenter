"""
LLM Gateway - Unified Multi-Provider LLM Interface

A unified async interface for calling multiple LLM providers
(Claude, Gemini, GPT) via LiteLLM with cost tracking and metrics.

Example:
    from libs.llm_gateway import LLMGateway

    gateway = LLMGateway()

    response = await gateway.complete(
        provider="claude",
        messages=[{"role": "user", "content": "Hello!"}],
    )
    print(response["content"])
    print(f"Cost: ${response['cost']:.6f}")
"""

from .gateway import LLMGateway, LLMGatewayError, LLMResponse, ProviderError
from .providers import COSTS, PROVIDERS, get_model_id, get_provider_cost, list_providers

__all__ = [
    # Main gateway
    "LLMGateway",
    # Types
    "LLMResponse",
    # Exceptions
    "LLMGatewayError",
    "ProviderError",
    # Provider utilities
    "PROVIDERS",
    "COSTS",
    "get_model_id",
    "get_provider_cost",
    "list_providers",
]
