"""
LLM Gateway - Unified Multi-Provider Interface

Provides a single async interface for calling multiple LLM providers
(Claude, Gemini, GPT) via LiteLLM with automatic retry, cost tracking,
and Prometheus metrics.
"""

import time
from typing import Any, TypedDict

import litellm
import structlog
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

from .cost_tracking import calculate_cost, track_usage
from .metrics import record_request_failure, record_request_success
from .providers import DEFAULT_PARAMS, get_model_id, list_providers

logger = structlog.get_logger(__name__)


class LLMResponse(TypedDict):
    """Response from LLM completion"""

    content: str
    model: str
    usage: dict
    cost: float


class LLMGatewayError(Exception):
    """Base exception for LLM Gateway errors"""

    pass


class ProviderError(LLMGatewayError):
    """Error from LLM provider (e.g., API error, rate limit)"""

    pass


class LLMGateway:
    """
    Unified async interface for multiple LLM providers.

    Uses LiteLLM as the underlying gateway for provider abstraction.
    Includes automatic retry with exponential backoff, cost tracking,
    and Prometheus metrics.

    Example:
        gateway = LLMGateway()

        response = await gateway.complete(
            provider="claude",
            messages=[{"role": "user", "content": "Hello!"}],
        )
        print(response["content"])
        print(f"Cost: ${response['cost']:.6f}")
    """

    def __init__(self) -> None:
        """Initialize LLM Gateway."""
        # Disable LiteLLM's verbose logging
        litellm.set_verbose = False
        logger.info("llm_gateway_initialized", providers=list_providers())

    async def complete(
        self,
        provider: str,
        messages: list[dict[str, str]],
        temperature: float | None = None,
        max_tokens: int | None = None,
        **kwargs: Any,
    ) -> LLMResponse:
        """
        Send completion request to specified provider.

        Args:
            provider: Provider alias ('claude', 'gpt', 'gemini', 'gpt-mini')
            messages: List of message dicts with 'role' and 'content' keys
            temperature: Sampling temperature (0-1). Uses provider default if None.
            max_tokens: Maximum tokens to generate. Uses provider default if None.
            **kwargs: Additional parameters passed to LiteLLM

        Returns:
            LLMResponse with content, model, usage, and cost

        Raises:
            ProviderError: If the provider request fails after retries
            KeyError: If provider alias is not recognized

        Example:
            response = await gateway.complete(
                provider="claude",
                messages=[
                    {"role": "system", "content": "You are helpful."},
                    {"role": "user", "content": "What is 2+2?"},
                ],
                temperature=0.3,
            )
        """
        model_id = get_model_id(provider)
        defaults = DEFAULT_PARAMS.get(provider, {})

        # Use provided values or fall back to defaults
        temp = temperature if temperature is not None else defaults.get("temperature", 0.7)
        tokens = max_tokens if max_tokens is not None else defaults.get("max_tokens", 4096)

        start_time = time.perf_counter()

        try:
            response = await self._call_with_retry(
                model=model_id,
                messages=messages,
                temperature=temp,
                max_tokens=tokens,
                **kwargs,
            )
            duration = time.perf_counter() - start_time

            # Extract usage info
            usage = {
                "prompt_tokens": response.usage.prompt_tokens,
                "completion_tokens": response.usage.completion_tokens,
                "total_tokens": response.usage.total_tokens,
            }

            # Calculate cost
            cost = calculate_cost(provider, usage)

            # Track metrics
            record_request_success(provider, duration)
            track_usage(provider, model_id, usage, cost)

            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model,
                usage=usage,
                cost=cost,
            )

        except Exception as e:
            duration = time.perf_counter() - start_time
            record_request_failure(provider, duration)
            logger.error(
                "llm_request_failed",
                provider=provider,
                model=model_id,
                error=str(e),
                duration_seconds=round(duration, 3),
            )
            raise ProviderError(f"Provider {provider} failed: {e}") from e

    @retry(
        retry=retry_if_exception_type((litellm.RateLimitError, litellm.ServiceUnavailableError)),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def _call_with_retry(
        self,
        model: str,
        messages: list[dict[str, str]],
        temperature: float,
        max_tokens: int,
        **kwargs: Any,
    ):
        """
        Make LiteLLM call with automatic retry on transient failures.

        Retries on:
        - Rate limit errors (429)
        - Service unavailable (503)

        Uses exponential backoff: 1s, 2s, 4s (max 3 attempts)
        """
        return await litellm.acompletion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            **kwargs,
        )

    def available_providers(self) -> list[str]:
        """
        Get list of available provider aliases.

        Returns:
            List of provider aliases like ['claude', 'gpt', 'gemini', 'gpt-mini']
        """
        return list_providers()
