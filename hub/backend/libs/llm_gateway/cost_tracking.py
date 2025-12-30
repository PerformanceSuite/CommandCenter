"""
Cost Tracking for LLM Gateway

Calculates request costs based on token usage and provider pricing.
Integrates with structured logging and Prometheus metrics.
"""

from typing import TypedDict

import structlog

from .metrics import record_cost, record_tokens
from .providers import COSTS, ProviderCost

logger = structlog.get_logger(__name__)


class UsageInfo(TypedDict):
    """Token usage information from LLM response"""

    prompt_tokens: int
    completion_tokens: int
    total_tokens: int


def calculate_cost(provider: str, usage: UsageInfo) -> float:
    """
    Calculate the cost of an LLM request based on token usage.

    Args:
        provider: Provider alias (e.g., 'claude', 'gpt', 'gemini')
        usage: Token usage dict with prompt_tokens and completion_tokens

    Returns:
        Cost in US dollars

    Note:
        Returns 0.0 if provider is not in COSTS (unknown provider)
    """
    cost_info: ProviderCost | None = COSTS.get(provider)
    if cost_info is None:
        logger.warning("unknown_provider_for_cost", provider=provider)
        return 0.0

    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)

    # Costs are per 1M tokens
    input_cost = (input_tokens / 1_000_000) * cost_info.input
    output_cost = (output_tokens / 1_000_000) * cost_info.output
    total_cost = input_cost + output_cost

    return total_cost


def track_usage(
    provider: str,
    model: str,
    usage: UsageInfo,
    cost: float,
) -> None:
    """
    Track LLM usage with structured logging and Prometheus metrics.

    Args:
        provider: Provider alias (e.g., 'claude', 'gpt')
        model: Full model identifier
        usage: Token usage information
        cost: Calculated cost in dollars
    """
    input_tokens = usage.get("prompt_tokens", 0)
    output_tokens = usage.get("completion_tokens", 0)

    # Emit Prometheus metrics
    record_tokens(provider, input_tokens, output_tokens)
    record_cost(provider, cost)

    # Structured logging
    logger.info(
        "llm_request_completed",
        provider=provider,
        model=model,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        total_tokens=usage.get("total_tokens", input_tokens + output_tokens),
        cost_usd=round(cost, 6),
    )
