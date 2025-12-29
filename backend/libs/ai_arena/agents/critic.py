"""
Critic Agent - Claude-based devil's advocate

Focuses on finding flaws, challenging assumptions, and stress-testing ideas.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .base import BaseAgent

if TYPE_CHECKING:
    from libs.llm_gateway import LLMGateway


# Load prompt template
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "critic.md"


def _load_prompt() -> str:
    """Load the critic prompt template."""
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text()
    # Fallback if file not found
    return """You are a Critical Evaluator (Devil's Advocate). Stress-test ideas by finding weaknesses.
Focus on identifying flaws, blind spots, and potential failure modes.
Respond with JSON containing: answer, reasoning, confidence (0-100), evidence (list).
Your confidence represents how likely the hypothesis is to be WRONG."""


class CriticAgent(BaseAgent):
    """
    Critical Evaluator (Devil's Advocate) agent powered by Claude.

    Specializes in:
    - Identifying weaknesses and blind spots
    - Challenging assumptions
    - Exploring failure modes
    - Stress-testing ideas
    - Surfacing uncomfortable truths
    """

    DEFAULT_PROVIDER = "claude"

    def __init__(
        self,
        gateway: LLMGateway,
        name: str = "Critic",
        provider: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize the Critic agent.

        Args:
            gateway: LLMGateway instance for making API calls
            name: Agent name (default: "Critic")
            provider: LLM provider override (default: claude)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        super().__init__(
            name=name,
            role="critic",
            provider=provider or self.DEFAULT_PROVIDER,
            gateway=gateway,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._prompt = _load_prompt()

    def get_system_prompt(self) -> str:
        """Return the critic system prompt."""
        return self._prompt

    def _build_question_prompt(self, question: str, context: str | None) -> str:
        """Build critic-specific question prompt."""
        prompt = ""

        if context:
            prompt += f"## Context\n\n{context}\n\n"

        prompt += f"## Hypothesis/Claim to Critique\n\n{question}\n\n"

        prompt += """## Your Task

Critically evaluate this hypothesis or claim. Your job is to find flaws, not to agree.
Consider:
- What assumptions does this rely on? Are they valid?
- What evidence would disprove this?
- What similar ideas have failed in the past and why?
- What are we not seeing because of our biases?
- Who has incentives to make this fail?

**Note**: Your confidence score represents how likely this hypothesis is to be WRONG or FLAWED.
A high confidence (90%+) means you found serious, fundamental flaws.
A low confidence (30% or less) means the hypothesis appears robust.

"""
        prompt += f"## Response Format\n\nRespond with a JSON object:\n```json\n{self.RESPONSE_SCHEMA}\n```"

        return prompt
