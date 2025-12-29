"""
Researcher Agent - Gemini-based research synthesis

Focuses on comprehensive research, cross-domain synthesis, and source quality.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from .base import BaseAgent

if TYPE_CHECKING:
    from libs.llm_gateway import LLMGateway


# Load prompt template
PROMPT_PATH = Path(__file__).parent.parent / "prompts" / "researcher.md"


def _load_prompt() -> str:
    """Load the researcher prompt template."""
    if PROMPT_PATH.exists():
        return PROMPT_PATH.read_text()
    # Fallback if file not found
    return """You are a Research Specialist. Provide deep, well-sourced perspectives.
Focus on comprehensive research, cross-domain synthesis, and emerging trends.
Respond with JSON containing: answer, reasoning, confidence (0-100), evidence (list)."""


class ResearcherAgent(BaseAgent):
    """
    Research Specialist agent powered by Gemini.

    Specializes in:
    - Comprehensive research and synthesis
    - Cross-domain connections and insights
    - Academic and industry source evaluation
    - Emerging trends and paradigm identification
    """

    DEFAULT_PROVIDER = "gemini"

    def __init__(
        self,
        gateway: LLMGateway,
        name: str = "Researcher",
        provider: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ):
        """
        Initialize the Researcher agent.

        Args:
            gateway: LLMGateway instance for making API calls
            name: Agent name (default: "Researcher")
            provider: LLM provider override (default: gemini)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
        """
        super().__init__(
            name=name,
            role="researcher",
            provider=provider or self.DEFAULT_PROVIDER,
            gateway=gateway,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        self._prompt = _load_prompt()

    def get_system_prompt(self) -> str:
        """Return the researcher system prompt."""
        return self._prompt

    def _build_question_prompt(self, question: str, context: str | None) -> str:
        """Build researcher-specific question prompt."""
        prompt = ""

        if context:
            prompt += f"## Context\n\n{context}\n\n"

        prompt += f"## Research Question\n\n{question}\n\n"

        prompt += """## Your Task

Research this question comprehensively. Consider:
- What does current academic and industry research say?
- Are there competing theories or schools of thought?
- What insights can be drawn from adjacent domains?
- What are the emerging trends in this area?

"""
        prompt += f"## Response Format\n\nRespond with a JSON object:\n```json\n{self.RESPONSE_SCHEMA}\n```"

        return prompt
