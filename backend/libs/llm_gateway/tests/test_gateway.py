"""Tests for LLM Gateway"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from libs.llm_gateway import LLMGateway, ProviderError
from libs.llm_gateway.cost_tracking import calculate_cost
from libs.llm_gateway.providers import DynamicProviderRegistry, ProviderConfig


class TestCostCalculation:
    """Tests for cost calculation accuracy"""

    def test_claude_cost_calculation(self):
        """Claude costs should be calculated correctly"""
        usage = {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_tokens": 1500,
        }
        cost = calculate_cost("claude", usage)
        # Input: 1000/1M * $3.00 = $0.003
        # Output: 500/1M * $15.00 = $0.0075
        # Total: $0.0105
        expected = (1000 / 1_000_000) * 3.0 + (500 / 1_000_000) * 15.0
        assert abs(cost - expected) < 0.0001

    def test_gpt_cost_calculation(self):
        """GPT costs should be calculated correctly"""
        usage = {
            "prompt_tokens": 2000,
            "completion_tokens": 1000,
            "total_tokens": 3000,
        }
        cost = calculate_cost("gpt", usage)
        expected = (2000 / 1_000_000) * 2.50 + (1000 / 1_000_000) * 10.0
        assert abs(cost - expected) < 0.0001

    def test_gemini_cost_calculation(self):
        """Gemini costs should be calculated correctly"""
        usage = {
            "prompt_tokens": 5000,
            "completion_tokens": 2000,
            "total_tokens": 7000,
        }
        cost = calculate_cost("gemini", usage)
        expected = (5000 / 1_000_000) * 0.15 + (2000 / 1_000_000) * 0.60
        assert abs(cost - expected) < 0.0001

    def test_unknown_provider_returns_zero(self):
        """Unknown provider should return zero cost"""
        usage = {
            "prompt_tokens": 1000,
            "completion_tokens": 500,
            "total_tokens": 1500,
        }
        cost = calculate_cost("unknown", usage)
        assert cost == 0.0

    def test_cost_within_one_percent(self):
        """Cost calculation should be accurate within 1%"""
        # Test with 1M tokens
        usage = {
            "prompt_tokens": 500_000,
            "completion_tokens": 500_000,
            "total_tokens": 1_000_000,
        }

        # Claude: 0.5 * $3 + 0.5 * $15 = $9
        claude_cost = calculate_cost("claude", usage)
        expected_claude = 9.0
        assert abs(claude_cost - expected_claude) / expected_claude < 0.01


class TestLLMGateway:
    """Tests for LLMGateway class"""

    @pytest.fixture
    def gateway(self):
        """Create gateway instance"""
        return LLMGateway()

    def test_available_providers(self, gateway):
        """Gateway should list available providers"""
        providers = gateway.available_providers()
        assert "claude" in providers
        assert "gpt" in providers
        assert "gemini" in providers
        assert "gpt-mini" in providers

    @pytest.mark.asyncio
    async def test_complete_success(self, gateway):
        """Successful completion should return response with cost"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello, world!"
        mock_response.model = "anthropic/claude-sonnet-4-20250514"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch("libs.llm_gateway.gateway.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            response = await gateway.complete(
                provider="claude",
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert response["content"] == "Hello, world!"
            assert response["model"] == "anthropic/claude-sonnet-4-20250514"
            assert response["usage"]["prompt_tokens"] == 10
            assert response["usage"]["completion_tokens"] == 5
            assert response["cost"] > 0

    @pytest.mark.asyncio
    async def test_complete_with_custom_params(self, gateway):
        """Completion should pass custom temperature and max_tokens"""
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test"
        mock_response.model = "openai/gpt-4o"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 5
        mock_response.usage.completion_tokens = 2
        mock_response.usage.total_tokens = 7

        with patch("libs.llm_gateway.gateway.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            await gateway.complete(
                provider="gpt",
                messages=[{"role": "user", "content": "Hi"}],
                temperature=0.3,
                max_tokens=100,
            )

            # Verify parameters were passed
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["temperature"] == 0.3
            assert call_kwargs["max_tokens"] == 100

    @pytest.mark.asyncio
    async def test_complete_unknown_provider_raises(self, gateway):
        """Unknown provider should raise KeyError"""
        with pytest.raises(KeyError) as exc_info:
            await gateway.complete(
                provider="unknown",
                messages=[{"role": "user", "content": "Hello"}],
            )
        assert "Unknown provider" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_complete_failure_raises_provider_error(self, gateway):
        """Failed request should raise ProviderError"""
        with patch("libs.llm_gateway.gateway.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.side_effect = Exception("API Error")

            with pytest.raises(ProviderError) as exc_info:
                await gateway.complete(
                    provider="claude",
                    messages=[{"role": "user", "content": "Hello"}],
                )

            assert "claude" in str(exc_info.value)
            assert "API Error" in str(exc_info.value)


class TestRetryBehavior:
    """Tests for retry behavior on transient failures"""

    @pytest.fixture
    def gateway(self):
        """Create gateway instance"""
        return LLMGateway()

    @pytest.mark.asyncio
    async def test_retry_on_rate_limit(self, gateway):
        """Should retry on rate limit errors"""
        import litellm

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Success after retry"
        mock_response.model = "anthropic/claude-sonnet-4-20250514"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        call_count = 0

        async def mock_completion(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise litellm.RateLimitError(
                    message="Rate limited",
                    llm_provider="anthropic",
                    model="claude",
                    response=MagicMock(),
                )
            return mock_response

        with patch("libs.llm_gateway.gateway.litellm.acompletion", side_effect=mock_completion):
            response = await gateway.complete(
                provider="claude",
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert response["content"] == "Success after retry"
            assert call_count == 2


class TestDynamicProviderRegistryIntegration:
    """Tests for LLMGateway integration with DynamicProviderRegistry"""

    @pytest.fixture
    def mock_registry(self):
        """Create a mock registry with custom provider"""
        registry = DynamicProviderRegistry()
        # Add a custom provider to the cache for testing
        registry._cache["custom-provider"] = ProviderConfig(
            model_id="openai/gpt-3.5-turbo",
            api_base="https://custom-api.example.com",
            api_key_env="CUSTOM_API_KEY",
        )
        return registry

    def test_gateway_initialization_with_registry(self, mock_registry):
        """Gateway should accept and store a registry"""
        gateway = LLMGateway(registry=mock_registry)
        assert gateway.registry is mock_registry

    def test_gateway_initialization_without_registry(self):
        """Gateway should work without a registry"""
        gateway = LLMGateway()
        assert gateway.registry is None

    def test_available_providers_uses_registry(self, mock_registry):
        """available_providers should use registry when provided"""
        gateway = LLMGateway(registry=mock_registry)
        providers = gateway.available_providers()
        
        # Should include static providers
        assert "claude" in providers
        assert "gpt" in providers

    def test_available_providers_without_registry(self):
        """available_providers should use static list without registry"""
        gateway = LLMGateway()
        providers = gateway.available_providers()
        
        assert isinstance(providers, list)
        assert "claude" in providers
        assert "gpt" in providers

    @pytest.mark.asyncio
    async def test_complete_uses_registry_config(self, mock_registry):
        """complete should use registry to get provider config"""
        gateway = LLMGateway(registry=mock_registry)
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Custom provider response"
        mock_response.model = "openai/gpt-3.5-turbo"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch("libs.llm_gateway.gateway.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            response = await gateway.complete(
                provider="custom-provider",
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert response["content"] == "Custom provider response"
            # Verify custom api_base was passed
            call_kwargs = mock.call_args.kwargs
            assert call_kwargs["api_base"] == "https://custom-api.example.com"

    @pytest.mark.asyncio
    async def test_complete_static_provider_with_registry(self, mock_registry):
        """complete should work with static providers when using registry"""
        gateway = LLMGateway(registry=mock_registry)
        
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Hello!"
        mock_response.model = "anthropic/claude-sonnet-4-20250514"
        mock_response.usage = MagicMock()
        mock_response.usage.prompt_tokens = 10
        mock_response.usage.completion_tokens = 5
        mock_response.usage.total_tokens = 15

        with patch("libs.llm_gateway.gateway.litellm.acompletion", new_callable=AsyncMock) as mock:
            mock.return_value = mock_response

            response = await gateway.complete(
                provider="claude",
                messages=[{"role": "user", "content": "Hello"}],
            )

            assert response["content"] == "Hello!"

    def test_is_provider_configured_with_registry(self, mock_registry):
        """is_provider_configured should use registry config"""
        gateway = LLMGateway(registry=mock_registry)
        
        # Test with custom provider that has api_key_env
        # (won't be configured unless env var is set, but should not error)
        try:
            result = gateway.is_provider_configured("custom-provider")
            assert isinstance(result, bool)
        except KeyError:
            pytest.fail("Should not raise KeyError for providers in registry")

    def test_is_provider_configured_without_registry(self):
        """is_provider_configured should work without registry"""
        gateway = LLMGateway()
        
        # Should work with static providers
        result = gateway.is_provider_configured("claude")
        assert isinstance(result, bool)
