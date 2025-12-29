"""
Base Agent for AI Arena

Provides the foundation for all AI agents participating in debates.
Each agent has a role, provider preference, and confidence scoring.
"""

from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import structlog

if TYPE_CHECKING:
    from libs.llm_gateway import LLMGateway

logger = structlog.get_logger(__name__)


@dataclass
class AgentResponse:
    """Structured response from an agent in a debate."""

    answer: str
    reasoning: str
    confidence: int  # 0-100
    evidence: list[str]
    agent_name: str
    model: str
    raw_content: str = ""

    def to_dict(self) -> dict[str, Any]:
        """Convert response to dictionary."""
        return {
            "answer": self.answer,
            "reasoning": self.reasoning,
            "confidence": self.confidence,
            "evidence": self.evidence,
            "agent_name": self.agent_name,
            "model": self.model,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AgentResponse:
        """Create response from dictionary."""
        return cls(
            answer=data["answer"],
            reasoning=data["reasoning"],
            confidence=data["confidence"],
            evidence=data.get("evidence", []),
            agent_name=data["agent_name"],
            model=data["model"],
            raw_content=data.get("raw_content", ""),
        )


@dataclass
class AgentConfig:
    """Configuration for an agent."""

    name: str
    role: str
    provider: str
    system_prompt: str
    temperature: float = 0.7
    max_tokens: int = 4096
    metadata: dict[str, Any] = field(default_factory=dict)


class BaseAgent(ABC):
    """
    Base class for all AI Arena agents.

    Each agent represents a distinct perspective in a debate,
    powered by a specific LLM provider.

    Subclasses should implement:
    - get_system_prompt(): Return the agent's system prompt
    - _build_question_prompt(): Customize how questions are presented
    """

    # Expected JSON structure for agent responses
    RESPONSE_SCHEMA = """
{
    "answer": "Your direct answer to the question",
    "reasoning": "Step-by-step explanation of your reasoning",
    "confidence": 85,  // Integer 0-100
    "evidence": ["Evidence point 1", "Evidence point 2"]
}
"""

    def __init__(
        self,
        name: str,
        role: str,
        provider: str,
        gateway: LLMGateway,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize an agent.

        Args:
            name: Unique identifier for this agent
            role: The role this agent plays (e.g., "analyst", "critic")
            provider: LLM provider alias (e.g., "claude", "gpt")
            gateway: LLMGateway instance for making API calls
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
        """
        self.name = name
        self.role = role
        self.provider = provider
        self.gateway = gateway
        self.temperature = temperature
        self.max_tokens = max_tokens

    @abstractmethod
    def get_system_prompt(self) -> str:
        """
        Return the system prompt that defines this agent's behavior.

        This should include:
        - The agent's role and perspective
        - Guidelines for response format
        - Any domain-specific instructions
        """
        pass

    async def respond(
        self,
        question: str,
        context: str | None = None,
        previous_responses: list[AgentResponse] | None = None,
    ) -> AgentResponse:
        """
        Generate a response to a question.

        Args:
            question: The question or topic to respond to
            context: Optional additional context
            previous_responses: Responses from other agents in prior rounds

        Returns:
            Structured AgentResponse with answer, reasoning, and confidence
        """
        messages = self._build_messages(question, context, previous_responses)

        logger.info(
            "agent_responding",
            agent=self.name,
            provider=self.provider,
            question_preview=question[:100],
        )

        response = await self.gateway.complete(
            provider=self.provider,
            messages=messages,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

        content = response["content"]

        try:
            parsed = self._parse_response(content)
            parsed.agent_name = self.name
            parsed.model = response["model"]
            parsed.raw_content = content
            return parsed
        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(
                "agent_response_parse_failed",
                agent=self.name,
                error=str(e),
                content_preview=content[:200],
            )
            # Return a fallback response
            return AgentResponse(
                answer=content,
                reasoning="(Response could not be parsed into structured format)",
                confidence=50,
                evidence=[],
                agent_name=self.name,
                model=response["model"],
                raw_content=content,
            )

    def _build_messages(
        self,
        question: str,
        context: str | None,
        previous_responses: list[AgentResponse] | None,
    ) -> list[dict[str, str]]:
        """Build the message list for the LLM call."""
        messages = [
            {"role": "system", "content": self.get_system_prompt()},
        ]

        # Build user message with question and context
        user_content = self._build_question_prompt(question, context)

        # Add previous responses if this is a follow-up round
        if previous_responses:
            user_content += "\n\n## Previous Responses from Other Agents\n\n"
            for resp in previous_responses:
                user_content += f"### {resp.agent_name} (Confidence: {resp.confidence}%)\n"
                user_content += f"**Answer:** {resp.answer}\n"
                user_content += f"**Reasoning:** {resp.reasoning}\n\n"

            user_content += (
                "\nConsider these perspectives and either reinforce your position "
                "or adjust based on compelling arguments. Update your confidence accordingly."
            )

        messages.append({"role": "user", "content": user_content})

        return messages

    def _build_question_prompt(self, question: str, context: str | None) -> str:
        """
        Build the question prompt.

        Override in subclasses to customize how questions are presented.
        """
        prompt = f"## Question\n\n{question}"

        if context:
            prompt = f"## Context\n\n{context}\n\n{prompt}"

        prompt += f"\n\n## Response Format\n\nRespond with a JSON object:\n```json\n{self.RESPONSE_SCHEMA}\n```"

        return prompt

    def _parse_response(self, content: str) -> AgentResponse:
        """Parse LLM response into structured AgentResponse."""
        # Try to extract JSON from the response
        json_match = re.search(r"```(?:json)?\s*([\s\S]*?)```", content)
        if json_match:
            json_str = json_match.group(1).strip()
        else:
            # Try to parse the entire content as JSON
            json_str = content.strip()

        data = json.loads(json_str)

        # Validate confidence is in range
        confidence = data.get("confidence", 50)
        confidence = max(0, min(100, int(confidence)))

        return AgentResponse(
            answer=data.get("answer", ""),
            reasoning=data.get("reasoning", ""),
            confidence=confidence,
            evidence=data.get("evidence", []),
            agent_name="",  # Will be set by caller
            model="",  # Will be set by caller
        )

    def get_config(self) -> AgentConfig:
        """Get the current configuration of this agent."""
        return AgentConfig(
            name=self.name,
            role=self.role,
            provider=self.provider,
            system_prompt=self.get_system_prompt(),
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(name={self.name!r}, role={self.role!r}, provider={self.provider!r})"
