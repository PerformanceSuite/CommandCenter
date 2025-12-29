"""
Analyst Agent - Claude-based data-driven analysis

Focuses on quantitative evidence, market data, trends, and analytical frameworks.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .base import BaseAgent

if TYPE_CHECKING:
    from libs.llm_gateway import LLMGateway


# Load prompt template
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "analyst.md"


def _load_prompt() -> str:
    """Load the analyst prompt template."""
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text()
    # Fallback if file not found
    return """You are a Strategic Analyst. Provide data-driven, analytical perspectives.
Focus on quantitative evidence, market data, and measurable outcomes.
Respond with JSON containing: answer, reasoning, confidence (0-100), evidence (list)."""


class AnalystAgent(BaseAgent):
    """
    Strategic Analyst agent powered by Claude.

    Specializes in:
    - Quantitative analysis and data interpretation
    - Market sizing and trend analysis
    - Risk assessment and opportunity identification
    - Framework-based strategic analysis (SWOT, Porter's, etc.)
    """

    DEFAULT_PROVIDER = "claude"

    def __init__(
        self,
        gateway: LLMGateway,
        name: str = "Analyst",
        provider: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize the Analyst agent.

        Args:
            gateway: LLMGateway instance for making API calls
            name: Agent name (default: "Analyst")
            provider: LLM provider override (default: claude)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        super().__init__(
            name=name,
            role="analyst",
            provider=provider or self.DEFAULT_PROVIDER,
            gateway=gateway,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._prompt = _load_prompt()

    def get_system_prompt(self) -> str:
        """Return the analyst system prompt."""
        return self._prompt

    def _build_question_prompt(self, question: str, context: str | None) -> str:
        """Build analyst-specific question prompt."""
        prompt = ""

        if context:
            prompt += f"## Context\n\n{context}\n\n"

        prompt += f"## Question for Analysis\n\n{question}\n\n"

        prompt += """## Your Task

Analyze this question from a data-driven perspective. Consider:
- What quantitative evidence is relevant?
- What market data or trends apply?
- What frameworks help structure the analysis?
- What are the key metrics and how do they compare?

"""
        prompt += f"## Response Format\n\nRespond with a JSON object:\n```json\n{self.RESPONSE_SCHEMA}\n```"

        return prompt
