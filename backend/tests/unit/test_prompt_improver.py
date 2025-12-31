"""
Tests for the Prompt Improver.
"""

import pytest
from libs.agent_framework.prompt_improver import PromptImprover


class TestQuickCheck:
    """Tests for the quick_check method (no API calls)."""

    def test_detects_missing_role(self):
        """Should detect missing role definition."""
        prompt = "Please analyze the code and find bugs."
        improver = PromptImprover()
        result = improver.quick_check(prompt)

        assert result["has_role"] is False
        assert any("role" in s.lower() for s in result["suggestions"])

    def test_detects_present_role(self):
        """Should detect present role definition."""
        prompt = "You are an expert code reviewer. Analyze the code."
        improver = PromptImprover()
        result = improver.quick_check(prompt)

        assert result["has_role"] is True

    def test_detects_missing_output_format(self):
        """Should detect missing output format."""
        prompt = "You are a code reviewer. Find all the bugs."
        improver = PromptImprover()
        result = improver.quick_check(prompt)

        assert result["has_output_format"] is False
        assert any("output" in s.lower() or "format" in s.lower() for s in result["suggestions"])

    def test_detects_present_output_format(self):
        """Should detect present output format."""
        prompt = "You are a reviewer. Return as JSON: {bugs: [], suggestions: []}"
        improver = PromptImprover()
        result = improver.quick_check(prompt)

        assert result["has_output_format"] is True

    def test_detects_missing_constraints(self):
        """Should detect missing constraints."""
        prompt = "You are a code reviewer. Find bugs."
        improver = PromptImprover()
        result = improver.quick_check(prompt)

        assert result["has_constraints"] is False

    def test_detects_present_constraints(self):
        """Should detect present constraints."""
        prompt = "You are a reviewer. Never suggest removing tests. Always be constructive."
        improver = PromptImprover()
        result = improver.quick_check(prompt)

        assert result["has_constraints"] is True

    def test_counts_words(self):
        """Should count words accurately."""
        prompt = "one two three four five"
        improver = PromptImprover()
        result = improver.quick_check(prompt)

        assert result["word_count"] == 5

    def test_detects_potential_conflict_concise_detailed(self):
        """Should detect concise vs detailed conflict."""
        prompt = "Be concise. Provide detailed explanations for each issue."
        improver = PromptImprover()
        result = improver.quick_check(prompt)

        assert len(result["potential_conflicts"]) > 0
        assert any(
            "concise" in c.lower() and "detailed" in c.lower()
            for c in result["potential_conflicts"]
        )

    def test_detects_potential_conflict_never_ask_clarify(self):
        """Should detect never ask vs clarify conflict."""
        prompt = "Never ask questions. Always clarify unclear requirements."
        improver = PromptImprover()
        result = improver.quick_check(prompt)

        assert len(result["potential_conflicts"]) > 0

    def test_no_conflicts_in_clean_prompt(self):
        """Should not detect conflicts in a clean prompt."""
        prompt = """You are an expert code reviewer.

Your task is to review code for:
- Bugs and errors
- Security issues
- Performance problems

Output as JSON:
{
  "issues": [],
  "suggestions": []
}

Constraints:
- Do not suggest removing tests
- Always be constructive
"""
        improver = PromptImprover()
        result = improver.quick_check(prompt)

        assert len(result["potential_conflicts"]) == 0
        assert result["has_role"] is True
        assert result["has_output_format"] is True
        assert result["has_constraints"] is True

    def test_warns_about_very_long_prompts(self):
        """Should warn about very long prompts."""
        prompt = "word " * 2000
        improver = PromptImprover()
        result = improver.quick_check(prompt)

        assert any("condensing" in s.lower() or "long" in s.lower() for s in result["suggestions"])

    def test_warns_about_very_short_prompts(self):
        """Should warn about very short prompts."""
        prompt = "Do the thing."
        improver = PromptImprover()
        result = improver.quick_check(prompt)

        assert any("brief" in s.lower() or "detail" in s.lower() for s in result["suggestions"])


class TestAnalyze:
    """Tests for the analyze method (requires API key)."""

    @pytest.mark.asyncio
    async def test_analyze_returns_scores(self):
        """Should return scores from analysis."""
        import os

        try:
            import anthropic  # noqa: F401
        except ImportError:
            pytest.skip("anthropic package not installed")

        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        prompt = "Do stuff."
        improver = PromptImprover()
        result = await improver.analyze(prompt)

        assert "clarity" in result.scores
        assert "structure" in result.scores
        assert "completeness" in result.scores
        assert "overall" in result.scores
        assert all(0 <= v <= 100 for v in result.scores.values())

    @pytest.mark.asyncio
    async def test_analyze_finds_issues_in_bad_prompt(self):
        """Should find issues in a bad prompt."""
        import os

        try:
            import anthropic  # noqa: F401
        except ImportError:
            pytest.skip("anthropic package not installed")

        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        prompt = "Do the thing good. Be brief but comprehensive."
        improver = PromptImprover()
        result = await improver.analyze(prompt)

        # Should find at least one issue
        assert len(result.issues) > 0

    @pytest.mark.asyncio
    async def test_analyze_generates_improved_version_for_bad_prompt(self):
        """Should generate improved version for low-scoring prompt."""
        import os

        try:
            import anthropic  # noqa: F401
        except ImportError:
            pytest.skip("anthropic package not installed")

        if not os.environ.get("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not set")

        prompt = "Fix bugs."
        improver = PromptImprover()
        result = await improver.improve(prompt)

        # Should generate an improved version
        assert result.improved is not None
        # Improved version should be longer and more detailed
        assert len(result.improved) > len(prompt)
