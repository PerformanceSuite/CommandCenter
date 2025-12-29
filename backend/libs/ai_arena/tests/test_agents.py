"""Tests for AI Arena agents"""

import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from libs.ai_arena.agents import (
    AgentConfig,
    AgentResponse,
    AnalystAgent,
    CriticAgent,
    ResearcherAgent,
    StrategistAgent,
)


class TestAgentResponse:
    """Tests for AgentResponse dataclass"""

    def test_create_response(self):
        """Should create a valid AgentResponse"""
        response = AgentResponse(
            answer="The market size is $10B",
            reasoning="Based on industry reports...",
            confidence=85,
            evidence=["Source A", "Source B"],
            agent_name="Analyst",
            model="anthropic/claude-sonnet-4",
        )

        assert response.answer == "The market size is $10B"
        assert response.confidence == 85
        assert len(response.evidence) == 2
        assert response.agent_name == "Analyst"

    def test_to_dict(self):
        """Should convert response to dictionary"""
        response = AgentResponse(
            answer="Yes",
            reasoning="Because...",
            confidence=70,
            evidence=["Evidence"],
            agent_name="Test",
            model="test-model",
        )

        data = response.to_dict()

        assert data["answer"] == "Yes"
        assert data["confidence"] == 70
        assert data["agent_name"] == "Test"

    def test_from_dict(self):
        """Should create response from dictionary"""
        data = {
            "answer": "No",
            "reasoning": "Reasons...",
            "confidence": 60,
            "evidence": ["A", "B"],
            "agent_name": "Agent",
            "model": "model",
        }

        response = AgentResponse.from_dict(data)

        assert response.answer == "No"
        assert response.confidence == 60
        assert len(response.evidence) == 2


class TestAnalystAgent:
    """Tests for AnalystAgent"""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway"""
        gateway = MagicMock()
        gateway.complete = AsyncMock()
        return gateway

    def test_init_default_provider(self, mock_gateway):
        """Analyst should default to Claude provider"""
        agent = AnalystAgent(gateway=mock_gateway)

        assert agent.provider == "claude"
        assert agent.role == "analyst"
        assert agent.name == "Analyst"

    def test_init_custom_provider(self, mock_gateway):
        """Analyst should accept custom provider"""
        agent = AnalystAgent(gateway=mock_gateway, provider="gpt")

        assert agent.provider == "gpt"

    def test_get_system_prompt(self, mock_gateway):
        """Analyst should have system prompt"""
        agent = AnalystAgent(gateway=mock_gateway)
        prompt = agent.get_system_prompt()

        assert "Analyst" in prompt or "analyst" in prompt.lower()
        assert len(prompt) > 100

    @pytest.mark.asyncio
    async def test_respond_success(self, mock_gateway):
        """Should parse valid JSON response"""
        mock_gateway.complete.return_value = {
            "content": json.dumps(
                {
                    "answer": "Market is growing at 15% CAGR",
                    "reasoning": "Based on industry data...",
                    "confidence": 82,
                    "evidence": ["Report A", "Report B"],
                }
            ),
            "model": "anthropic/claude-sonnet-4",
        }

        agent = AnalystAgent(gateway=mock_gateway)
        response = await agent.respond("What is the market growth rate?")

        assert response.answer == "Market is growing at 15% CAGR"
        assert response.confidence == 82
        assert response.agent_name == "Analyst"

    @pytest.mark.asyncio
    async def test_respond_with_markdown_json(self, mock_gateway):
        """Should extract JSON from markdown code block"""
        mock_gateway.complete.return_value = {
            "content": """Here's my analysis:

```json
{
    "answer": "The answer is 42",
    "reasoning": "Complex calculation",
    "confidence": 95,
    "evidence": ["Math"]
}
```

That's my conclusion.""",
            "model": "anthropic/claude-sonnet-4",
        }

        agent = AnalystAgent(gateway=mock_gateway)
        response = await agent.respond("What is the answer?")

        assert response.answer == "The answer is 42"
        assert response.confidence == 95

    @pytest.mark.asyncio
    async def test_respond_fallback_on_parse_error(self, mock_gateway):
        """Should return fallback response on parse error"""
        mock_gateway.complete.return_value = {
            "content": "This is not JSON at all",
            "model": "anthropic/claude-sonnet-4",
        }

        agent = AnalystAgent(gateway=mock_gateway)
        response = await agent.respond("Question?")

        assert response.answer == "This is not JSON at all"
        assert response.confidence == 50  # Default fallback confidence


class TestResearcherAgent:
    """Tests for ResearcherAgent"""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway"""
        gateway = MagicMock()
        gateway.complete = AsyncMock()
        return gateway

    def test_init_default_provider(self, mock_gateway):
        """Researcher should default to Gemini provider"""
        agent = ResearcherAgent(gateway=mock_gateway)

        assert agent.provider == "gemini"
        assert agent.role == "researcher"

    def test_get_config(self, mock_gateway):
        """Should return agent configuration"""
        agent = ResearcherAgent(gateway=mock_gateway, temperature=0.5)
        config = agent.get_config()

        assert isinstance(config, AgentConfig)
        assert config.role == "researcher"
        assert config.provider == "gemini"
        assert config.temperature == 0.5


class TestStrategistAgent:
    """Tests for StrategistAgent"""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway"""
        gateway = MagicMock()
        gateway.complete = AsyncMock()
        return gateway

    def test_init_default_provider(self, mock_gateway):
        """Strategist should default to GPT provider"""
        agent = StrategistAgent(gateway=mock_gateway)

        assert agent.provider == "gpt"
        assert agent.role == "strategist"


class TestCriticAgent:
    """Tests for CriticAgent"""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway"""
        gateway = MagicMock()
        gateway.complete = AsyncMock()
        return gateway

    def test_init_default_provider(self, mock_gateway):
        """Critic should default to Claude provider"""
        agent = CriticAgent(gateway=mock_gateway)

        assert agent.provider == "claude"
        assert agent.role == "critic"

    @pytest.mark.asyncio
    async def test_respond_with_previous_responses(self, mock_gateway):
        """Should include previous responses in prompt"""
        mock_gateway.complete.return_value = {
            "content": json.dumps(
                {
                    "answer": "I disagree because...",
                    "reasoning": "The assumptions are flawed",
                    "confidence": 75,
                    "evidence": ["Counter-evidence"],
                }
            ),
            "model": "anthropic/claude-sonnet-4",
        }

        previous = [
            AgentResponse(
                answer="Previous answer",
                reasoning="Previous reasoning",
                confidence=80,
                evidence=[],
                agent_name="Analyst",
                model="claude",
            )
        ]

        agent = CriticAgent(gateway=mock_gateway)
        response = await agent.respond(
            "Is this hypothesis valid?",
            previous_responses=previous,
        )

        # Check that the call included previous responses
        call_args = mock_gateway.complete.call_args
        messages = call_args.kwargs["messages"]
        user_message = messages[-1]["content"]

        assert "Analyst" in user_message
        assert "Previous answer" in user_message
        assert response.confidence == 75


class TestAgentParsing:
    """Tests for response parsing edge cases"""

    @pytest.fixture
    def mock_gateway(self):
        """Create mock gateway"""
        gateway = MagicMock()
        gateway.complete = AsyncMock()
        return gateway

    @pytest.mark.asyncio
    async def test_confidence_clamped_to_range(self, mock_gateway):
        """Confidence should be clamped to 0-100"""
        mock_gateway.complete.return_value = {
            "content": json.dumps(
                {
                    "answer": "Answer",
                    "reasoning": "Reasoning",
                    "confidence": 150,  # Over 100
                    "evidence": [],
                }
            ),
            "model": "test",
        }

        agent = AnalystAgent(gateway=mock_gateway)
        response = await agent.respond("Question?")

        assert response.confidence == 100  # Clamped to max

    @pytest.mark.asyncio
    async def test_confidence_min_zero(self, mock_gateway):
        """Confidence should not go below 0"""
        mock_gateway.complete.return_value = {
            "content": json.dumps(
                {
                    "answer": "Answer",
                    "reasoning": "Reasoning",
                    "confidence": -10,  # Below 0
                    "evidence": [],
                }
            ),
            "model": "test",
        }

        agent = AnalystAgent(gateway=mock_gateway)
        response = await agent.respond("Question?")

        assert response.confidence == 0  # Clamped to min
