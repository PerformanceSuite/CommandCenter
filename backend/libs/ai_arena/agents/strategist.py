"""
Strategist Agent - GPT-based strategic advisory

Focuses on practical implementation, execution, and actionable outcomes.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .base import BaseAgent

if TYPE_CHECKING:
    from libs.llm_gateway import LLMGateway


# Load prompt template
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "strategist.md"


def _load_prompt() -> str:
    """Load the strategist prompt template."""
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text()
    # Fallback if file not found
    return """You are a Strategic Advisor. Provide actionable, pragmatic perspectives.
Focus on practical implementation, resource constraints, and execution.
Respond with JSON containing: answer, reasoning, confidence (0-100), evidence (list)."""


class StrategistAgent(BaseAgent):
    """
    Strategic Advisor agent powered by GPT.

    Specializes in:
    - Practical implementation planning
    - Resource and constraint analysis
    - Trade-off evaluation
    - Stakeholder alignment
    - Action-oriented recommendations
    """

    DEFAULT_PROVIDER = "gpt"

    def __init__(
        self,
        gateway: LLMGateway,
        name: str = "Strategist",
        provider: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize the Strategist agent.

        Args:
            gateway: LLMGateway instance for making API calls
            name: Agent name (default: "Strategist")
            provider: LLM provider override (default: gpt)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        super().__init__(
            name=name,
            role="strategist",
            provider=provider or self.DEFAULT_PROVIDER,
            gateway=gateway,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._prompt = _load_prompt()

    def get_system_prompt(self) -> str:
        """Return the strategist system prompt."""
        return self._prompt

    def _build_question_prompt(self, question: str, context: str | None) -> str:
        """Build strategist-specific question prompt."""
        prompt = ""

        if context:
            prompt += f"## Context\n\n{context}\n\n"

        prompt += f"## Strategic Question\n\n{question}\n\n"

        prompt += """## Your Task

Approach this question from a strategic execution perspective. Consider:
- How would this be practically implemented?
- What resources, capabilities, and timeline are needed?
- What are the key trade-offs and decision points?
- What could go wrong and how would you adapt?

"""
        prompt += f"## Response Format\n\nRespond with a JSON object:\n```json\n{self.RESPONSE_SCHEMA}\n```"

        return prompt
