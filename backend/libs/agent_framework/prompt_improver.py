"""
Prompt Improver - Analyzes and improves agent prompts.

Provides:
- quick_check: Fast local analysis (no API call)
- analyze: Full AI-powered analysis with scores and improvement suggestions
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class PromptIssue:
    """A single issue found in a prompt."""

    type: str  # conflict, ambiguity, missing_output, missing_constraints, verbosity, structure
    severity: str  # high, medium, low
    description: str
    suggestion: str

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "severity": self.severity,
            "description": self.description,
            "suggestion": self.suggestion,
        }


@dataclass
class PromptAnalysis:
    """Complete analysis of a prompt."""

    original: str
    issues: list[PromptIssue] = field(default_factory=list)
    scores: dict[str, int] = field(default_factory=dict)
    improved: Optional[str] = None
    summary: str = ""

    def to_dict(self) -> dict:
        return {
            "issues": [i.to_dict() for i in self.issues],
            "scores": self.scores,
            "improved": self.improved,
            "summary": self.summary,
        }


ANALYZE_PROMPT = """You are a Prompt Engineering Expert. Analyze this agent prompt for issues.

## Prompt to Analyze

```
{prompt}
```

## Analysis Tasks

1. **Conflict Detection**: Find contradictory instructions
   - Example: "Be concise" vs "Provide detailed explanations"
   - Example: "Never ask questions" vs "Clarify unclear requests"

2. **Ambiguity Check**: Find vague or unclear instructions
   - Example: "Do a good job" (what defines good?)
   - Example: "Handle edge cases" (which ones?)

3. **Structure Review**: Check organization
   - Is there a clear role definition?
   - Are responsibilities clearly listed?
   - Is there an output format specification?
   - Are there constraints/guardrails?

4. **Completeness Check**: What's missing?
   - Error handling instructions?
   - Edge case guidance?
   - Output format specification?
   - Success criteria?

5. **Verbosity Check**: Can anything be more concise?

## Output Format

Return ONLY valid JSON (no markdown fences):
{{
    "issues": [
        {{
            "type": "conflict|ambiguity|missing_output|missing_constraints|verbosity|structure",
            "severity": "high|medium|low",
            "description": "What the issue is",
            "suggestion": "How to fix it"
        }}
    ],
    "scores": {{
        "clarity": 0-100,
        "structure": 0-100,
        "completeness": 0-100,
        "overall": 0-100
    }},
    "summary": "Brief summary of main improvements needed",
    "improved_prompt": "Full improved version if overall score < 80, else null"
}}"""


class PromptImprover:
    """
    Analyzes and improves agent prompts.

    Example:
        improver = PromptImprover()

        # Quick local check (no API call)
        quick = improver.quick_check(my_prompt)
        print(quick["suggestions"])

        # Full AI analysis
        analysis = await improver.analyze(my_prompt)
        print(f"Score: {analysis.scores['overall']}")
        if analysis.improved:
            print(f"Improved: {analysis.improved}")
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the prompt improver.

        Args:
            api_key: Anthropic API key. Defaults to ANTHROPIC_API_KEY env var.
        """
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    def quick_check(self, prompt: str) -> dict:
        """
        Fast local prompt check - no API call.

        Returns dict with:
        - has_role: bool
        - has_output_format: bool
        - has_constraints: bool
        - word_count: int
        - suggestions: list[str]
        - potential_conflicts: list[str]
        """
        prompt_lower = prompt.lower()

        # Check for key elements
        has_role = any(
            k in prompt_lower for k in ["you are", "your role", "act as", "you're a", "as a"]
        )
        has_output = any(
            k in prompt_lower
            for k in [
                "output format",
                "respond with",
                "return as",
                "output as",
                "json",
                "respond in",
                "format:",
                "```",
            ]
        )
        has_constraints = any(
            k in prompt_lower
            for k in ["do not", "don't", "never", "always", "must", "constraint", "rule", "avoid"]
        )

        # Build suggestions
        suggestions = []
        if not has_role:
            suggestions.append("Add a clear role definition at the start (e.g., 'You are a...')")
        if not has_output:
            suggestions.append("Specify the expected output format")
        if not has_constraints:
            suggestions.append("Add constraints or guardrails for the agent")

        word_count = len(prompt.split())
        if word_count > 1500:
            suggestions.append(f"Consider condensing - prompt is {word_count} words (very long)")
        elif word_count < 50:
            suggestions.append("Prompt may be too brief - consider adding more detail")

        # Check for potential conflicts
        conflicts = self._detect_conflicts(prompt_lower)

        return {
            "has_role": has_role,
            "has_output_format": has_output,
            "has_constraints": has_constraints,
            "word_count": word_count,
            "suggestions": suggestions,
            "potential_conflicts": conflicts,
        }

    def _detect_conflicts(self, prompt_lower: str) -> list[str]:
        """Detect potential conflicting instructions."""
        conflicts = []

        conflict_pairs = [
            ("concise", "detailed"),
            ("brief", "comprehensive"),
            ("short", "thorough"),
            ("never ask", "clarify"),
            ("don't explain", "explain your"),
            ("no questions", "ask for"),
            ("single", "multiple"),
            ("simple", "complex"),
        ]

        for a, b in conflict_pairs:
            if a in prompt_lower and b in prompt_lower:
                conflicts.append(f"Possible conflict: '{a}' vs '{b}'")

        return conflicts

    async def analyze(self, prompt: str) -> PromptAnalysis:
        """
        Full AI-powered prompt analysis.

        Returns PromptAnalysis with:
        - issues: List of identified problems
        - scores: Clarity, structure, completeness, overall (0-100)
        - improved: Improved version if score < 80
        - summary: Brief description of needed improvements
        """
        try:
            import anthropic
        except ImportError:
            logger.error("anthropic package not installed")
            return PromptAnalysis(
                original=prompt,
                scores={"clarity": 0, "structure": 0, "completeness": 0, "overall": 0},
                summary="Error: anthropic package not installed",
            )

        if not self.api_key:
            logger.error("No API key configured")
            return PromptAnalysis(
                original=prompt,
                scores={"clarity": 0, "structure": 0, "completeness": 0, "overall": 0},
                summary="Error: No API key configured",
            )

        client = anthropic.AsyncAnthropic(api_key=self.api_key)

        try:
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": ANALYZE_PROMPT.format(prompt=prompt)}],
            )

            content = response.content[0].text

            # Parse JSON from response
            data = self._parse_json_response(content)

            # Build issues list
            issues = []
            for issue_data in data.get("issues", []):
                issues.append(
                    PromptIssue(
                        type=issue_data.get("type", "unknown"),
                        severity=issue_data.get("severity", "medium"),
                        description=issue_data.get("description", ""),
                        suggestion=issue_data.get("suggestion", ""),
                    )
                )

            return PromptAnalysis(
                original=prompt,
                issues=issues,
                scores=data.get(
                    "scores", {"clarity": 50, "structure": 50, "completeness": 50, "overall": 50}
                ),
                improved=data.get("improved_prompt"),
                summary=data.get("summary", ""),
            )

        except Exception as e:
            logger.error("prompt_analysis_failed", error=str(e))
            return PromptAnalysis(
                original=prompt,
                scores={"clarity": 0, "structure": 0, "completeness": 0, "overall": 0},
                summary=f"Error: {str(e)}",
            )

    def _parse_json_response(self, content: str) -> dict:
        """Parse JSON from LLM response, handling various formats."""
        # Try direct parse first
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            pass

        # Try to extract JSON from markdown code block
        if "```json" in content:
            try:
                start = content.find("```json") + 7
                end = content.find("```", start)
                return json.loads(content[start:end])
            except (json.JSONDecodeError, ValueError):
                pass

        # Try to extract JSON from generic code block
        if "```" in content:
            try:
                start = content.find("```") + 3
                # Skip language identifier if present
                newline = content.find("\n", start)
                if newline != -1 and newline - start < 20:
                    start = newline + 1
                end = content.find("```", start)
                return json.loads(content[start:end])
            except (json.JSONDecodeError, ValueError):
                pass

        # Try to find JSON object in content
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(content[start:end])
        except json.JSONDecodeError:
            pass

        # Return empty dict if all parsing fails
        logger.warning("failed_to_parse_json_response", content_preview=content[:200])
        return {}

    async def improve(self, prompt: str) -> PromptAnalysis:
        """
        Analyze and return improved version.

        Convenience method that ensures improved version is generated.
        """
        analysis = await self.analyze(prompt)

        # If no improved version was generated but score is low, force improvement
        if not analysis.improved and analysis.scores.get("overall", 100) < 80:
            # Re-run with explicit improvement request
            analysis = await self._force_improvement(prompt, analysis)

        return analysis

    async def _force_improvement(self, prompt: str, analysis: PromptAnalysis) -> PromptAnalysis:
        """Force generation of improved prompt."""
        try:
            import anthropic
        except ImportError:
            return analysis

        if not self.api_key:
            return analysis

        client = anthropic.AsyncAnthropic(api_key=self.api_key)

        issues_text = "\n".join(
            [f"- {i.type}: {i.description} (Fix: {i.suggestion})" for i in analysis.issues]
        )

        improve_prompt = f"""Improve this prompt based on the identified issues.

## Original Prompt
```
{prompt}
```

## Issues to Fix
{issues_text}

## Instructions
- Fix all identified issues
- Keep the original intent
- Add missing structure (role, output format, constraints)
- Be concise but complete

Return ONLY the improved prompt, no explanation."""

        try:
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4000,
                messages=[{"role": "user", "content": improve_prompt}],
            )

            improved = response.content[0].text.strip()

            # Remove code fences if present
            if improved.startswith("```"):
                lines = improved.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                improved = "\n".join(lines)

            analysis.improved = improved
            return analysis

        except Exception as e:
            logger.error("force_improvement_failed", error=str(e))
            return analysis
