"""
Smoke tests for AI provider SDK imports.

Ensures all required AI provider SDKs are installed and importable.
This prevents runtime errors when AIRouter tries to initialize provider clients.
"""

import pytest


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


def test_google_ai_sdk_importable():
    """Verify Google Gen AI SDK can be imported (new SDK as of May 2025)"""
    try:
        from google import genai
        # New SDK (google-genai) replaced google-generativeai in May 2025
        assert genai is not None
    except ImportError as e:
        pytest.fail(f"Google Gen AI SDK not installed or not importable: {e}")


def test_litellm_importable():
    """Verify LiteLLM SDK can be imported"""
    try:
        import litellm
        assert litellm.__version__ is not None
    except ImportError as e:
        pytest.fail(f"LiteLLM SDK not installed or not importable: {e}")


def test_all_provider_sdks_importable():
    """Integration test: verify all AI provider SDKs can be imported together"""
    try:
        import openai
        import anthropic
        from google import genai
        import litellm

        # Verify all imports succeeded
        assert openai is not None
        assert anthropic is not None
        assert genai is not None
        assert litellm is not None

    except ImportError as e:
        pytest.fail(f"One or more AI provider SDKs failed to import: {e}")
