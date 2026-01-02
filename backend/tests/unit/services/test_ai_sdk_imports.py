"""
Smoke tests for AI provider SDK imports.

Ensures all required AI provider SDKs are installed and importable.
This prevents runtime errors when AIRouter tries to initialize provider clients.
"""

import pytest


def _sdk_available(module_name: str, from_module: str = None, attr: str = None) -> bool:
    """Check if an SDK module is available."""
    try:
        if from_module:
            mod = __import__(from_module, fromlist=[module_name])
            getattr(mod, module_name)
        else:
            __import__(module_name)
        return True
    except (ImportError, AttributeError):
        return False


def test_openai_sdk_importable():
    """Verify OpenAI SDK can be imported"""
    try:
        import openai
        from openai import AsyncOpenAI

        assert openai.__version__ is not None
        assert AsyncOpenAI is not None
    except ImportError as e:
        pytest.fail(f"OpenAI SDK not installed or not importable: {e}")


def test_anthropic_sdk_importable():
    """Verify Anthropic SDK can be imported"""
    try:
        import anthropic
        from anthropic import AsyncAnthropic

        assert anthropic.__version__ is not None
        assert AsyncAnthropic is not None
    except ImportError as e:
        pytest.fail(f"Anthropic SDK not installed or not importable: {e}")


@pytest.mark.skipif(
    not _sdk_available("genai", from_module="google"),
    reason="Google Gen AI SDK (google-genai) not installed",
)
def test_google_ai_sdk_importable():
    """Verify Google Gen AI SDK can be imported (new SDK as of May 2025)"""
    from google import genai

    # New SDK (google-genai) replaced google-generativeai in May 2025
    assert genai is not None


@pytest.mark.skipif(
    not _sdk_available("litellm"),
    reason="LiteLLM SDK not installed",
)
def test_litellm_importable():
    """Verify LiteLLM SDK can be imported"""
    import litellm

    # Check module is importable - __version__ attribute may not exist in all versions
    assert litellm is not None


@pytest.mark.skipif(
    not (_sdk_available("genai", from_module="google") and _sdk_available("litellm")),
    reason="One or more optional AI provider SDKs not installed",
)
def test_all_provider_sdks_importable():
    """Integration test: verify all AI provider SDKs can be imported together"""
    import anthropic
    import litellm
    import openai
    from google import genai

    # Verify all imports succeeded
    assert openai is not None
    assert anthropic is not None
    assert genai is not None
    assert litellm is not None
