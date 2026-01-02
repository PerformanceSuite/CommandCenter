"""Tests for skill_retriever module."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from libs.agent_framework.skill_retriever import (
    RetrievedSkill,
    SkillRetriever,
    format_skills_for_prompt,
)


@pytest.fixture
def sample_skill():
    return RetrievedSkill(
        slug="websocket-subscription-pattern",
        name="WebSocket Subscription Pattern",
        category="pattern",
        description="Pattern for real-time updates via WebSocket",
        content="# WebSocket Pattern\n\nUse ConnectionManager for session tracking...",
        effectiveness_score=0.85,
    )


class TestRetrievedSkill:
    def test_to_prompt_section(self, sample_skill):
        section = sample_skill.to_prompt_section()

        assert "### WebSocket Subscription Pattern" in section
        assert "**Category:** pattern" in section
        assert "ConnectionManager" in section


class TestFormatSkillsForPrompt:
    def test_empty_skills(self):
        result = format_skills_for_prompt([])
        assert result == ""

    def test_formats_multiple_skills(self, sample_skill):
        skills = [sample_skill, sample_skill]
        result = format_skills_for_prompt(skills)

        assert "## Relevant Skills & Patterns" in result
        assert result.count("### WebSocket Subscription Pattern") == 2


class TestSkillRetriever:
    @pytest.mark.asyncio
    async def test_find_relevant_success(self):
        retriever = SkillRetriever(api_base="http://test:8000/api/v1")

        # Use MagicMock for the response since httpx.Response methods like .json() are sync
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                "slug": "test-skill",
                "name": "Test Skill",
                "category": "pattern",
                "description": "A test skill",
                "content": "# Test\nContent here",
                "effectiveness_score": 0.9,
            }
        ]

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            skills = await retriever.find_relevant("implement websocket")

            assert len(skills) == 1
            assert skills[0].slug == "test-skill"

    @pytest.mark.asyncio
    async def test_find_relevant_handles_timeout(self):
        import httpx

        retriever = SkillRetriever(api_base="http://test:8000/api/v1")

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=httpx.TimeoutException("timeout")
            )

            skills = await retriever.find_relevant("implement websocket")

            assert skills == []

    @pytest.mark.asyncio
    async def test_get_for_persona_coding(self):
        retriever = SkillRetriever()

        # Just verify the mapping works
        result = await retriever.get_for_persona("coding", limit=0)
        assert isinstance(result, list)
