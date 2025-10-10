"""
Multi-Provider AI Router Service

Handles routing AI requests to different providers:
- OpenRouter (unified API for 200+ models)
- Anthropic (Claude direct)
- OpenAI (GPT direct)
- Google (Gemini direct)
- LiteLLM (self-hosted proxy)

Based on architecture design in docs/AI_PROVIDER_ROUTING_ARCHITECTURE.md
"""

import logging
from typing import Optional, Dict, Any, List
from enum import Enum

from openai import OpenAI, AsyncOpenAI
from app.config import settings

logger = logging.getLogger(__name__)


class AIProvider(str, Enum):
    """Supported AI providers"""
    OPENROUTER = "openrouter"
    ANTHROPIC = "anthropic"
    OPENAI = "openai"
    GOOGLE = "google"
    LITELLM = "litellm"


class ModelTier(str, Enum):
    """Model cost tiers for budget management"""
    PREMIUM = "premium"  # Claude Opus, GPT-4, Gemini Ultra
    STANDARD = "standard"  # Claude Sonnet, GPT-4 Turbo, Gemini Pro
    ECONOMY = "economy"  # Claude Haiku, GPT-3.5, Gemini Flash
    LOCAL = "local"  # Ollama, vLLM, LM Studio


class AIRouterService:
    """
    Multi-provider AI routing service

    Features:
    - Unified interface for multiple AI providers
    - Automatic fallback on provider failures
    - Cost tier management
    - Request/response logging
    - Usage tracking
    """

    def __init__(self):
        """Initialize AI router with configured providers"""
        self.default_provider = AIProvider(settings.default_ai_provider)
        self.default_model = settings.default_model

        # Initialize clients based on available API keys
        self._clients: Dict[AIProvider, Any] = {}
        self._init_clients()

    def _init_clients(self):
        """Initialize API clients for each configured provider"""

        # OpenRouter client (uses OpenAI SDK with custom base URL)
        if settings.openrouter_api_key:
            self._clients[AIProvider.OPENROUTER] = AsyncOpenAI(
                api_key=settings.openrouter_api_key,
                base_url="https://openrouter.ai/api/v1"
            )
            logger.info("✅ OpenRouter client initialized")

        # Anthropic direct client (if needed)
        if settings.anthropic_api_key:
            try:
                from anthropic import AsyncAnthropic
                self._clients[AIProvider.ANTHROPIC] = AsyncAnthropic(
                    api_key=settings.anthropic_api_key
                )
                logger.info("✅ Anthropic client initialized")
            except ImportError:
                logger.warning("⚠️  Anthropic SDK not installed (pip install anthropic)")

        # OpenAI direct client
        if settings.openai_api_key:
            self._clients[AIProvider.OPENAI] = AsyncOpenAI(
                api_key=settings.openai_api_key
            )
            logger.info("✅ OpenAI client initialized")

        # Google AI client
        if settings.google_api_key:
            try:
                import google.generativeai as genai
                genai.configure(api_key=settings.google_api_key)
                self._clients[AIProvider.GOOGLE] = genai
                logger.info("✅ Google AI client initialized")
            except ImportError:
                logger.warning("⚠️  Google AI SDK not installed (pip install google-generativeai)")

        if not self._clients:
            logger.warning("⚠️  No AI providers configured! Add API keys to .env")

    async def chat_completion(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        provider: Optional[AIProvider] = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
        fallback_providers: Optional[List[AIProvider]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Send chat completion request with automatic fallback

        Args:
            messages: List of message dicts with 'role' and 'content'
            model: Model identifier (e.g., 'anthropic/claude-3.5-sonnet')
            provider: Specific provider to use (defaults to default_provider)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            fallback_providers: List of fallback providers if primary fails
            **kwargs: Additional provider-specific parameters

        Returns:
            Dict with 'content', 'model', 'usage', 'provider' keys

        Raises:
            ValueError: If no providers are available
        """
        provider = provider or self.default_provider
        model = model or self.default_model
        fallback_providers = fallback_providers or []

        # Try primary provider
        try:
            return await self._execute_completion(
                provider=provider,
                messages=messages,
                model=model,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
        except Exception as e:
            logger.warning(f"⚠️  Primary provider {provider} failed: {e}")

            # Try fallback providers
            for fallback in fallback_providers:
                try:
                    logger.info(f"🔄 Falling back to {fallback}")
                    return await self._execute_completion(
                        provider=fallback,
                        messages=messages,
                        model=model,
                        temperature=temperature,
                        max_tokens=max_tokens,
                        **kwargs
                    )
                except Exception as fallback_error:
                    logger.warning(f"⚠️  Fallback provider {fallback} failed: {fallback_error}")
                    continue

            # All providers failed
            raise ValueError(f"All providers failed. Last error: {e}")

    async def _execute_completion(
        self,
        provider: AIProvider,
        messages: List[Dict[str, str]],
        model: str,
        temperature: float,
        max_tokens: int,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute completion request for specific provider

        Returns:
            Normalized response dict
        """
        client = self._clients.get(provider)
        if not client:
            raise ValueError(f"Provider {provider} not configured")

        # OpenRouter & OpenAI use the same API
        if provider in [AIProvider.OPENROUTER, AIProvider.OPENAI]:
            response = await client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                "provider": provider.value,
                "finish_reason": response.choices[0].finish_reason,
            }

        # Anthropic uses different API
        elif provider == AIProvider.ANTHROPIC:
            response = await client.messages.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )

            return {
                "content": response.content[0].text,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
                },
                "provider": provider.value,
                "finish_reason": response.stop_reason,
            }

        # Google Gemini uses different API
        elif provider == AIProvider.GOOGLE:
            gemini_model = client.GenerativeModel(model)
            response = await gemini_model.generate_content_async(
                messages[-1]["content"],  # Gemini takes single prompt for now
                generation_config={
                    "temperature": temperature,
                    "max_output_tokens": max_tokens,
                }
            )

            return {
                "content": response.text,
                "model": model,
                "usage": {
                    "prompt_tokens": response.usage_metadata.prompt_token_count,
                    "completion_tokens": response.usage_metadata.candidates_token_count,
                    "total_tokens": response.usage_metadata.total_token_count,
                },
                "provider": provider.value,
                "finish_reason": response.candidates[0].finish_reason.name if response.candidates else "STOP",
            }

        else:
            raise ValueError(f"Provider {provider} not implemented yet")

    def get_available_providers(self) -> List[str]:
        """Get list of configured providers"""
        return [provider.value for provider in self._clients.keys()]

    def get_model_info(self, model: str) -> Dict[str, Any]:
        """
        Get information about a model

        Returns:
            Dict with 'provider', 'tier', 'context_window', 'cost_per_1m_tokens'
        """
        # Model catalog (subset - expand as needed)
        MODEL_CATALOG = {
            "anthropic/claude-3.5-sonnet": {
                "provider": "anthropic",
                "tier": ModelTier.STANDARD,
                "context_window": 200000,
                "cost_per_1m_input_tokens": 3.00,
                "cost_per_1m_output_tokens": 15.00,
            },
            "anthropic/claude-3-opus": {
                "provider": "anthropic",
                "tier": ModelTier.PREMIUM,
                "context_window": 200000,
                "cost_per_1m_input_tokens": 15.00,
                "cost_per_1m_output_tokens": 75.00,
            },
            "anthropic/claude-3-haiku": {
                "provider": "anthropic",
                "tier": ModelTier.ECONOMY,
                "context_window": 200000,
                "cost_per_1m_input_tokens": 0.25,
                "cost_per_1m_output_tokens": 1.25,
            },
            "openai/gpt-4-turbo": {
                "provider": "openai",
                "tier": ModelTier.STANDARD,
                "context_window": 128000,
                "cost_per_1m_input_tokens": 10.00,
                "cost_per_1m_output_tokens": 30.00,
            },
            "openai/gpt-3.5-turbo": {
                "provider": "openai",
                "tier": ModelTier.ECONOMY,
                "context_window": 16000,
                "cost_per_1m_input_tokens": 0.50,
                "cost_per_1m_output_tokens": 1.50,
            },
            "google/gemini-pro": {
                "provider": "google",
                "tier": ModelTier.STANDARD,
                "context_window": 1000000,
                "cost_per_1m_input_tokens": 0.50,
                "cost_per_1m_output_tokens": 1.50,
            },
            "google/gemini-flash": {
                "provider": "google",
                "tier": ModelTier.ECONOMY,
                "context_window": 1000000,
                "cost_per_1m_input_tokens": 0.075,
                "cost_per_1m_output_tokens": 0.30,
            },
        }

        return MODEL_CATALOG.get(model, {
            "provider": "unknown",
            "tier": ModelTier.STANDARD,
            "context_window": 4096,
            "cost_per_1m_input_tokens": 0.0,
            "cost_per_1m_output_tokens": 0.0,
        })


# Global AI router instance
ai_router = AIRouterService()
