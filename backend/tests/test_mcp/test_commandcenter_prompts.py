"""Comprehensive tests for CommandCenter Prompt Provider."""

import pytest

from app.mcp.providers.base import Prompt, PromptMessage, PromptResult
from app.mcp.providers.commandcenter_prompts import CommandCenterPromptProvider
from app.mcp.utils import InvalidParamsError, PromptNotFoundError


@pytest.fixture
def prompt_provider():
    """Create prompt provider."""
    return CommandCenterPromptProvider()


class TestPromptProviderInitialization:
    """Tests for provider initialization."""

    def test_provider_creation(self, prompt_provider):
        """Test creating prompt provider."""
        assert prompt_provider.name == "commandcenter_prompts"

    @pytest.mark.asyncio
    async def test_provider_initialize(self, prompt_provider):
        """Test provider initialization."""
        await prompt_provider.initialize()
        assert prompt_provider.is_initialized

    @pytest.mark.asyncio
    async def test_provider_shutdown(self, prompt_provider):
        """Test provider shutdown."""
        await prompt_provider.initialize()
        await prompt_provider.shutdown()
        assert not prompt_provider.is_initialized


class TestListPrompts:
    """Tests for listing available prompts."""

    @pytest.mark.asyncio
    async def test_list_prompts_returns_all_7_types(self, prompt_provider):
        """Test that list_prompts returns all 7 prompt types."""
        prompts = await prompt_provider.list_prompts()

        assert len(prompts) == 7
        assert all(isinstance(p, Prompt) for p in prompts)

    @pytest.mark.asyncio
    async def test_list_prompts_names(self, prompt_provider):
        """Test all prompt names."""
        prompts = await prompt_provider.list_prompts()

        prompt_names = [p.name for p in prompts]
        expected_names = [
            "analyze_project",
            "evaluate_technology",
            "plan_research",
            "review_code",
            "generate_report",
            "prioritize_tasks",
            "architecture_review",
        ]

        assert set(prompt_names) == set(expected_names)

    @pytest.mark.asyncio
    async def test_all_prompts_have_required_fields(self, prompt_provider):
        """Test all prompts have name, description, and parameters."""
        prompts = await prompt_provider.list_prompts()

        for prompt in prompts:
            assert prompt.name
            assert prompt.description
            assert prompt.parameters is not None

    @pytest.mark.asyncio
    async def test_all_prompts_have_descriptions(self, prompt_provider):
        """Test all prompts have meaningful descriptions."""
        prompts = await prompt_provider.list_prompts()

        for prompt in prompts:
            assert len(prompt.description) > 20
            assert prompt.description[0].isupper()


class TestAnalyzeProjectPrompt:
    """Tests for analyze_project prompt."""

    @pytest.mark.asyncio
    async def test_get_analyze_project_prompt(self, prompt_provider):
        """Test getting analyze_project prompt."""
        arguments = {
            "project_name": "CommandCenter",
            "focus_area": "technologies",
        }

        result = await prompt_provider.get_prompt("analyze_project", arguments)

        assert isinstance(result, PromptResult)
        assert len(result.messages) == 2
        assert result.messages[0].role == "system"
        assert result.messages[1].role == "user"

    @pytest.mark.asyncio
    async def test_analyze_project_contains_project_name(self, prompt_provider):
        """Test prompt contains the project name."""
        arguments = {"project_name": "TestProject"}

        result = await prompt_provider.get_prompt("analyze_project", arguments)

        assert "TestProject" in result.messages[1].content

    @pytest.mark.asyncio
    async def test_analyze_project_with_default_focus(self, prompt_provider):
        """Test prompt with default focus area."""
        arguments = {"project_name": "TestProject"}

        result = await prompt_provider.get_prompt("analyze_project", arguments)

        assert "all" in result.messages[1].content.lower()

    @pytest.mark.asyncio
    async def test_analyze_project_missing_project_name(self, prompt_provider):
        """Test prompt fails without project_name."""
        arguments = {}

        with pytest.raises(InvalidParamsError):
            await prompt_provider.get_prompt("analyze_project", arguments)

    @pytest.mark.asyncio
    async def test_analyze_project_system_message(self, prompt_provider):
        """Test system message content."""
        arguments = {"project_name": "Test"}

        result = await prompt_provider.get_prompt("analyze_project", arguments)

        system_msg = result.messages[0].content
        assert "project analyst" in system_msg.lower()
        assert "commandcenter" in system_msg.lower()


class TestEvaluateTechnologyPrompt:
    """Tests for evaluate_technology prompt."""

    @pytest.mark.asyncio
    async def test_get_evaluate_technology_prompt(self, prompt_provider):
        """Test getting evaluate_technology prompt."""
        arguments = {
            "technology_name": "Kubernetes",
            "use_case": "Container orchestration",
        }

        result = await prompt_provider.get_prompt("evaluate_technology", arguments)

        assert isinstance(result, PromptResult)
        assert len(result.messages) == 2

    @pytest.mark.asyncio
    async def test_evaluate_technology_contains_tech_name(self, prompt_provider):
        """Test prompt contains technology name."""
        arguments = {"technology_name": "Docker"}

        result = await prompt_provider.get_prompt("evaluate_technology", arguments)

        assert "Docker" in result.messages[1].content

    @pytest.mark.asyncio
    async def test_evaluate_technology_contains_radar_framework(self, prompt_provider):
        """Test prompt mentions Technology Radar framework."""
        arguments = {"technology_name": "FastAPI"}

        result = await prompt_provider.get_prompt("evaluate_technology", arguments)

        content = result.messages[0].content + result.messages[1].content
        assert "Technology Radar" in content or "Adopt" in content
        assert "Trial" in content
        assert "Assess" in content
        assert "Hold" in content

    @pytest.mark.asyncio
    async def test_evaluate_technology_missing_name(self, prompt_provider):
        """Test prompt fails without technology_name."""
        arguments = {}

        with pytest.raises(InvalidParamsError):
            await prompt_provider.get_prompt("evaluate_technology", arguments)

    @pytest.mark.asyncio
    async def test_evaluate_technology_with_use_case(self, prompt_provider):
        """Test prompt includes use case."""
        arguments = {
            "technology_name": "PostgreSQL",
            "use_case": "Primary database for analytics",
        }

        result = await prompt_provider.get_prompt("evaluate_technology", arguments)

        assert "analytics" in result.messages[1].content.lower()


class TestPlanResearchPrompt:
    """Tests for plan_research prompt."""

    @pytest.mark.asyncio
    async def test_get_plan_research_prompt(self, prompt_provider):
        """Test getting plan_research prompt."""
        arguments = {
            "topic": "Microservices patterns",
            "duration": "3 weeks",
        }

        result = await prompt_provider.get_prompt("plan_research", arguments)

        assert isinstance(result, PromptResult)
        assert len(result.messages) == 2

    @pytest.mark.asyncio
    async def test_plan_research_contains_topic(self, prompt_provider):
        """Test prompt contains research topic."""
        arguments = {"topic": "GraphQL adoption"}

        result = await prompt_provider.get_prompt("plan_research", arguments)

        assert "GraphQL adoption" in result.messages[1].content

    @pytest.mark.asyncio
    async def test_plan_research_with_default_duration(self, prompt_provider):
        """Test prompt with default duration."""
        arguments = {"topic": "Test topic"}

        result = await prompt_provider.get_prompt("plan_research", arguments)

        assert "2 weeks" in result.messages[1].content

    @pytest.mark.asyncio
    async def test_plan_research_missing_topic(self, prompt_provider):
        """Test prompt fails without topic."""
        arguments = {}

        with pytest.raises(InvalidParamsError):
            await prompt_provider.get_prompt("plan_research", arguments)

    @pytest.mark.asyncio
    async def test_plan_research_contains_structure(self, prompt_provider):
        """Test prompt contains research plan structure."""
        arguments = {"topic": "Test"}

        result = await prompt_provider.get_prompt("plan_research", arguments)

        content = result.messages[1].content
        assert "Objectives" in content
        assert "Methodology" in content
        assert "Timeline" in content
        assert "Tasks" in content


class TestReviewCodePrompt:
    """Tests for review_code prompt."""

    @pytest.mark.asyncio
    async def test_get_review_code_prompt(self, prompt_provider):
        """Test getting review_code prompt."""
        arguments = {
            "repository_name": "backend",
            "review_type": "security",
        }

        result = await prompt_provider.get_prompt("review_code", arguments)

        assert isinstance(result, PromptResult)
        assert len(result.messages) == 2

    @pytest.mark.asyncio
    async def test_review_code_contains_repo_name(self, prompt_provider):
        """Test prompt contains repository name."""
        arguments = {"repository_name": "frontend"}

        result = await prompt_provider.get_prompt("review_code", arguments)

        assert "frontend" in result.messages[1].content

    @pytest.mark.asyncio
    async def test_review_code_security_focus(self, prompt_provider):
        """Test security review has appropriate content."""
        arguments = {
            "repository_name": "api",
            "review_type": "security",
        }

        result = await prompt_provider.get_prompt("review_code", arguments)

        content = result.messages[1].content
        assert "security" in content.lower()
        # Should mention security-specific items
        assert any(
            term in content.lower()
            for term in ["authentication", "authorization", "vulnerability", "injection"]
        )

    @pytest.mark.asyncio
    async def test_review_code_performance_focus(self, prompt_provider):
        """Test performance review has appropriate content."""
        arguments = {
            "repository_name": "api",
            "review_type": "performance",
        }

        result = await prompt_provider.get_prompt("review_code", arguments)

        content = result.messages[1].content
        assert "performance" in content.lower()
        assert any(term in content.lower() for term in ["optimization", "caching", "query"])

    @pytest.mark.asyncio
    async def test_review_code_architecture_focus(self, prompt_provider):
        """Test architecture review has appropriate content."""
        arguments = {
            "repository_name": "api",
            "review_type": "architecture",
        }

        result = await prompt_provider.get_prompt("review_code", arguments)

        content = result.messages[1].content
        assert "architecture" in content.lower()
        assert any(
            term in content.lower() for term in ["solid", "pattern", "scalability", "design"]
        )

    @pytest.mark.asyncio
    async def test_review_code_with_default_type(self, prompt_provider):
        """Test review with default type."""
        arguments = {"repository_name": "test-repo"}

        result = await prompt_provider.get_prompt("review_code", arguments)

        assert "general" in result.messages[1].content.lower()

    @pytest.mark.asyncio
    async def test_review_code_missing_repo_name(self, prompt_provider):
        """Test prompt fails without repository_name."""
        arguments = {}

        with pytest.raises(InvalidParamsError):
            await prompt_provider.get_prompt("review_code", arguments)


class TestGenerateReportPrompt:
    """Tests for generate_report prompt."""

    @pytest.mark.asyncio
    async def test_get_generate_report_prompt(self, prompt_provider):
        """Test getting generate_report prompt."""
        arguments = {
            "report_type": "project_summary",
            "period": "Q1 2025",
        }

        result = await prompt_provider.get_prompt("generate_report", arguments)

        assert isinstance(result, PromptResult)
        assert len(result.messages) == 2

    @pytest.mark.asyncio
    async def test_generate_report_contains_type(self, prompt_provider):
        """Test prompt contains report type."""
        arguments = {"report_type": "technology_radar"}

        result = await prompt_provider.get_prompt("generate_report", arguments)

        assert "technology_radar" in result.messages[1].content

    @pytest.mark.asyncio
    async def test_generate_report_with_period(self, prompt_provider):
        """Test prompt includes reporting period."""
        arguments = {
            "report_type": "research_findings",
            "period": "January 2025",
        }

        result = await prompt_provider.get_prompt("generate_report", arguments)

        assert "January 2025" in result.messages[1].content

    @pytest.mark.asyncio
    async def test_generate_report_missing_type(self, prompt_provider):
        """Test prompt fails without report_type."""
        arguments = {}

        with pytest.raises(InvalidParamsError):
            await prompt_provider.get_prompt("generate_report", arguments)

    @pytest.mark.asyncio
    async def test_generate_report_structure(self, prompt_provider):
        """Test prompt contains report structure."""
        arguments = {"report_type": "project_summary"}

        result = await prompt_provider.get_prompt("generate_report", arguments)

        content = result.messages[1].content
        assert "Executive Summary" in content
        assert "Findings" in content
        assert "Recommendations" in content


class TestPrioritizeTasksPrompt:
    """Tests for prioritize_tasks prompt."""

    @pytest.mark.asyncio
    async def test_get_prioritize_tasks_prompt(self, prompt_provider):
        """Test getting prioritize_tasks prompt."""
        arguments = {"criteria": "urgency"}

        result = await prompt_provider.get_prompt("prioritize_tasks", arguments)

        assert isinstance(result, PromptResult)
        assert len(result.messages) == 2

    @pytest.mark.asyncio
    async def test_prioritize_tasks_with_criteria(self, prompt_provider):
        """Test prompt includes criteria."""
        arguments = {"criteria": "impact"}

        result = await prompt_provider.get_prompt("prioritize_tasks", arguments)

        assert "impact" in result.messages[1].content.lower()

    @pytest.mark.asyncio
    async def test_prioritize_tasks_with_default_criteria(self, prompt_provider):
        """Test prompt with default criteria."""
        arguments = {}

        result = await prompt_provider.get_prompt("prioritize_tasks", arguments)

        assert "impact" in result.messages[1].content.lower()

    @pytest.mark.asyncio
    async def test_prioritize_tasks_contains_framework(self, prompt_provider):
        """Test prompt contains prioritization framework."""
        arguments = {"criteria": "urgency"}

        result = await prompt_provider.get_prompt("prioritize_tasks", arguments)

        content = result.messages[1].content
        assert "Impact" in content
        assert "Effort" in content
        assert "Matrix" in content


class TestArchitectureReviewPrompt:
    """Tests for architecture_review prompt."""

    @pytest.mark.asyncio
    async def test_get_architecture_review_prompt(self, prompt_provider):
        """Test getting architecture_review prompt."""
        arguments = {
            "system_name": "API Gateway",
            "focus": "scalability",
        }

        result = await prompt_provider.get_prompt("architecture_review", arguments)

        assert isinstance(result, PromptResult)
        assert len(result.messages) == 2

    @pytest.mark.asyncio
    async def test_architecture_review_contains_system_name(self, prompt_provider):
        """Test prompt contains system name."""
        arguments = {"system_name": "Payment Service"}

        result = await prompt_provider.get_prompt("architecture_review", arguments)

        assert "Payment Service" in result.messages[1].content

    @pytest.mark.asyncio
    async def test_architecture_review_with_focus(self, prompt_provider):
        """Test prompt includes focus area."""
        arguments = {
            "system_name": "Service",
            "focus": "security",
        }

        result = await prompt_provider.get_prompt("architecture_review", arguments)

        assert "security" in result.messages[1].content.lower()

    @pytest.mark.asyncio
    async def test_architecture_review_missing_system_name(self, prompt_provider):
        """Test prompt fails without system_name."""
        arguments = {}

        with pytest.raises(PromptNotFoundError):
            # This will fail at routing, not parameter validation
            pass

        with pytest.raises(InvalidParamsError):
            await prompt_provider.get_prompt("architecture_review", arguments)

    @pytest.mark.asyncio
    async def test_architecture_review_contains_aspects(self, prompt_provider):
        """Test prompt contains review aspects."""
        arguments = {"system_name": "Test System"}

        result = await prompt_provider.get_prompt("architecture_review", arguments)

        content = result.messages[1].content
        assert "Architecture Patterns" in content
        assert "Scalability" in content
        assert "Maintainability" in content
        assert "Security" in content


class TestInvalidPrompts:
    """Tests for invalid prompt calls."""

    @pytest.mark.asyncio
    async def test_get_nonexistent_prompt(self, prompt_provider):
        """Test getting non-existent prompt."""
        with pytest.raises(PromptNotFoundError):
            await prompt_provider.get_prompt("nonexistent_prompt", {})

    @pytest.mark.asyncio
    async def test_get_prompt_with_none_arguments(self, prompt_provider):
        """Test getting prompt with None arguments."""
        # Should use default empty dict
        result = await prompt_provider.get_prompt("prioritize_tasks", None)
        assert isinstance(result, PromptResult)


class TestPromptMessages:
    """Tests for prompt message format and structure."""

    @pytest.mark.asyncio
    async def test_all_prompts_have_system_and_user_messages(self, prompt_provider):
        """Test all prompts return both system and user messages."""
        prompts = await prompt_provider.list_prompts()

        for prompt in prompts:
            # Get prompt with minimal arguments
            args = {}
            for param in prompt.parameters:
                if param.required:
                    args[param.name] = f"test_{param.name}"

            result = await prompt_provider.get_prompt(prompt.name, args)

            assert len(result.messages) >= 2
            assert result.messages[0].role == "system"
            assert result.messages[1].role == "user"

    @pytest.mark.asyncio
    async def test_prompt_messages_have_content(self, prompt_provider):
        """Test all prompt messages have non-empty content."""
        arguments = {"project_name": "Test"}
        result = await prompt_provider.get_prompt("analyze_project", arguments)

        for message in result.messages:
            assert message.content
            assert len(message.content) > 10

    @pytest.mark.asyncio
    async def test_prompt_messages_are_proper_type(self, prompt_provider):
        """Test all messages are PromptMessage instances."""
        arguments = {"technology_name": "Test"}
        result = await prompt_provider.get_prompt("evaluate_technology", arguments)

        assert all(isinstance(msg, PromptMessage) for msg in result.messages)

    @pytest.mark.asyncio
    async def test_system_messages_set_context(self, prompt_provider):
        """Test system messages provide appropriate context."""
        arguments = {"topic": "Test"}
        result = await prompt_provider.get_prompt("plan_research", arguments)

        system_msg = result.messages[0].content
        assert "commandcenter" in system_msg.lower() or "research" in system_msg.lower()


class TestPromptParameters:
    """Tests for prompt parameter definitions."""

    @pytest.mark.asyncio
    async def test_all_prompts_document_parameters(self, prompt_provider):
        """Test all prompts have documented parameters."""
        prompts = await prompt_provider.list_prompts()

        for prompt in prompts:
            for param in prompt.parameters:
                assert param.name
                assert param.description
                assert isinstance(param.required, bool)

    @pytest.mark.asyncio
    async def test_required_parameters_enforced(self, prompt_provider):
        """Test required parameters are enforced."""
        prompts = await prompt_provider.list_prompts()

        # Test each prompt with missing required parameters
        for prompt in prompts:
            required_params = [p for p in prompt.parameters if p.required]
            if required_params:
                # Try with empty args - should fail
                with pytest.raises(InvalidParamsError):
                    await prompt_provider.get_prompt(prompt.name, {})

    @pytest.mark.asyncio
    async def test_default_parameters_work(self, prompt_provider):
        """Test default parameters are applied."""
        prompts = await prompt_provider.list_prompts()

        for prompt in prompts:
            # Build args with only required parameters
            args = {}
            for param in prompt.parameters:
                if param.required:
                    args[param.name] = f"test_{param.name}"

            # Should succeed with defaults for optional params
            result = await prompt_provider.get_prompt(prompt.name, args)
            assert isinstance(result, PromptResult)
