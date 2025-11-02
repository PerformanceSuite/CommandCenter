"""
CommandCenter Prompt Provider for MCP.

Exposes prompt templates for AI assistants to guide interactions with CommandCenter.
Provides context-aware prompts for analysis, research, and project management tasks.
"""

import logging
from typing import List, Dict, Any, Optional

from app.mcp.providers.base import (
    Prompt,
    PromptParameter,
    PromptProvider,
    PromptResult,
    PromptMessage,
)
from app.mcp.utils import PromptNotFoundError, InvalidParamsError


logger = logging.getLogger(__name__)


class CommandCenterPromptProvider(PromptProvider):
    """
    Prompt provider for CommandCenter interactions.

    Provides templates for:
    - Project analysis and assessment
    - Research task planning
    - Technology evaluation
    - Code review guidance
    - Report generation
    """

    def __init__(self):
        """Initialize CommandCenter prompt provider."""
        super().__init__("commandcenter_prompts")

    async def list_prompts(self) -> List[Prompt]:
        """
        List all available CommandCenter prompts.

        Returns:
            List of Prompt objects
        """
        prompts = [
            Prompt(
                name="analyze_project",
                description="Analyze a project's current state, technologies, and research tasks",
                parameters=[
                    PromptParameter(
                        name="project_name",
                        description="Name of the project to analyze",
                        required=True,
                    ),
                    PromptParameter(
                        name="focus_area",
                        description="Specific area to focus on (technologies, research, repositories)",
                        required=False,
                        default="all",
                    ),
                ],
            ),
            Prompt(
                name="evaluate_technology",
                description="Evaluate a technology for adoption, providing structured assessment",
                parameters=[
                    PromptParameter(
                        name="technology_name",
                        description="Name of the technology to evaluate",
                        required=True,
                    ),
                    PromptParameter(
                        name="use_case",
                        description="Intended use case or problem to solve",
                        required=False,
                    ),
                ],
            ),
            Prompt(
                name="plan_research",
                description="Create a research plan for investigating a technology or problem",
                parameters=[
                    PromptParameter(
                        name="topic",
                        description="Research topic or question",
                        required=True,
                    ),
                    PromptParameter(
                        name="duration",
                        description="Expected research duration (e.g., '2 weeks', '1 month')",
                        required=False,
                    ),
                ],
            ),
            Prompt(
                name="review_code",
                description="Guide code review for a repository with CommandCenter best practices",
                parameters=[
                    PromptParameter(
                        name="repository_name",
                        description="Name of the repository to review",
                        required=True,
                    ),
                    PromptParameter(
                        name="review_type",
                        description="Type of review (security, performance, architecture, general)",
                        required=False,
                        default="general",
                    ),
                ],
            ),
            Prompt(
                name="generate_report",
                description="Generate a comprehensive project or research report",
                parameters=[
                    PromptParameter(
                        name="report_type",
                        description="Type of report (project_summary, technology_radar, research_findings)",
                        required=True,
                    ),
                    PromptParameter(
                        name="period",
                        description="Reporting period (e.g., 'Q1 2025', 'January 2025')",
                        required=False,
                    ),
                ],
            ),
            Prompt(
                name="prioritize_tasks",
                description="Help prioritize research tasks based on various criteria",
                parameters=[
                    PromptParameter(
                        name="criteria",
                        description="Prioritization criteria (urgency, impact, dependencies)",
                        required=False,
                        default="impact",
                    ),
                ],
            ),
            Prompt(
                name="architecture_review",
                description="Conduct an architecture review with CommandCenter patterns",
                parameters=[
                    PromptParameter(
                        name="system_name",
                        description="Name of the system or component to review",
                        required=True,
                    ),
                    PromptParameter(
                        name="focus",
                        description="Review focus (scalability, maintainability, security)",
                        required=False,
                    ),
                ],
            ),
        ]

        return prompts

    async def get_prompt(
        self, name: str, arguments: Optional[Dict[str, Any]] = None
    ) -> PromptResult:
        """
        Get rendered prompt with arguments filled in.

        Args:
            name: Prompt name
            arguments: Template arguments

        Returns:
            PromptResult with rendered messages

        Raises:
            PromptNotFoundError: If prompt doesn't exist
            InvalidParamsError: If required arguments are missing
        """
        arguments = arguments or {}

        # Route to appropriate handler
        if name == "analyze_project":
            return await self._prompt_analyze_project(arguments)
        elif name == "evaluate_technology":
            return await self._prompt_evaluate_technology(arguments)
        elif name == "plan_research":
            return await self._prompt_plan_research(arguments)
        elif name == "review_code":
            return await self._prompt_review_code(arguments)
        elif name == "generate_report":
            return await self._prompt_generate_report(arguments)
        elif name == "prioritize_tasks":
            return await self._prompt_prioritize_tasks(arguments)
        elif name == "architecture_review":
            return await self._prompt_architecture_review(arguments)
        else:
            raise PromptNotFoundError(name)

    # Prompt handlers
    async def _prompt_analyze_project(self, arguments: Dict[str, Any]) -> PromptResult:
        """Generate project analysis prompt."""
        if "project_name" not in arguments:
            raise InvalidParamsError("project_name is required")

        project_name = arguments["project_name"]
        focus_area = arguments.get("focus_area", "all")

        messages = [
            PromptMessage(
                role="system",
                content="""You are a project analyst for CommandCenter, an R&D management system.
Your role is to provide insightful analysis of projects, identifying strengths, gaps, and opportunities.""",
            ),
            PromptMessage(
                role="user",
                content=f"""Analyze the project "{project_name}" focusing on {focus_area}.

Please provide:

1. **Current State Assessment**
   - Active technologies and their status
   - Research tasks in progress
   - Repository health and activity

2. **Technology Stack Analysis**
   - Current technology choices and rationale
   - Potential gaps or redundancies
   - Recommendations for adoption/retirement

3. **Research Progress**
   - Active research initiatives
   - Task completion rates
   - Priority alignment

4. **Recommendations**
   - Immediate action items
   - Medium-term improvements
   - Long-term strategic considerations

Use the CommandCenter resources (commandcenter://projects/{project_name}) to gather data.""",
            ),
        ]

        return PromptResult(messages=messages)

    async def _prompt_evaluate_technology(self, arguments: Dict[str, Any]) -> PromptResult:
        """Generate technology evaluation prompt."""
        if "technology_name" not in arguments:
            raise InvalidParamsError("technology_name is required")

        technology_name = arguments["technology_name"]
        use_case = arguments.get("use_case", "general evaluation")

        messages = [
            PromptMessage(
                role="system",
                content="""You are a technology evaluator for CommandCenter.
Provide structured, evidence-based assessments of technologies using the Technology Radar framework (Adopt, Trial, Assess, Hold).""",
            ),
            PromptMessage(
                role="user",
                content=f"""Evaluate "{technology_name}" for use case: {use_case}

Provide a comprehensive evaluation covering:

1. **Technology Overview**
   - Purpose and key capabilities
   - Maturity and ecosystem
   - Community and support

2. **Suitability Assessment**
   - Fit for stated use case
   - Technical capabilities
   - Integration complexity

3. **Risk Analysis**
   - Vendor lock-in risk
   - Long-term viability
   - Security considerations
   - Learning curve

4. **Recommendation**
   - Technology Radar status (Adopt/Trial/Assess/Hold)
   - Rationale for recommendation
   - Implementation timeline
   - Success metrics

5. **Alternatives**
   - Comparable technologies
   - Trade-offs comparison

Base your evaluation on current CommandCenter technologies (commandcenter://technologies) to identify overlaps and gaps.""",
            ),
        ]

        return PromptResult(messages=messages)

    async def _prompt_plan_research(self, arguments: Dict[str, Any]) -> PromptResult:
        """Generate research planning prompt."""
        if "topic" not in arguments:
            raise InvalidParamsError("topic is required")

        topic = arguments["topic"]
        duration = arguments.get("duration", "2 weeks")

        messages = [
            PromptMessage(
                role="system",
                content="""You are a research planner for CommandCenter.
Create structured, actionable research plans with clear objectives, milestones, and deliverables.""",
            ),
            PromptMessage(
                role="user",
                content=f"""Create a research plan for: "{topic}"
Expected duration: {duration}

Structure the plan with:

1. **Research Objectives**
   - Primary questions to answer
   - Success criteria
   - Expected outcomes

2. **Methodology**
   - Research approach (literature review, POC, comparative analysis)
   - Data sources and resources
   - Tools and technologies needed

3. **Timeline & Milestones**
   - Phase breakdown
   - Key deliverables per phase
   - Checkpoints and reviews

4. **Tasks Breakdown**
   - Specific actionable tasks
   - Priority levels
   - Dependencies
   - Estimated effort per task

5. **Risk Mitigation**
   - Potential blockers
   - Contingency plans
   - Escalation criteria

Format as actionable tasks that can be created in CommandCenter using the create_research_task tool.""",
            ),
        ]

        return PromptResult(messages=messages)

    async def _prompt_review_code(self, arguments: Dict[str, Any]) -> PromptResult:
        """Generate code review prompt."""
        if "repository_name" not in arguments:
            raise InvalidParamsError("repository_name is required")

        repository_name = arguments["repository_name"]
        review_type = arguments.get("review_type", "general")

        messages = [
            PromptMessage(
                role="system",
                content=f"""You are conducting a {review_type} code review for CommandCenter.
Apply software engineering best practices and provide constructive, actionable feedback.""",
            ),
            PromptMessage(
                role="user",
                content=f"""Review the repository: "{repository_name}"
Review type: {review_type}

Focus areas for {review_type} review:

"""
                + (
                    """
**Security Review:**
- Input validation and sanitization
- Authentication and authorization
- Secrets management
- Dependency vulnerabilities
- SQL injection risks
- XSS prevention
"""
                    if review_type == "security"
                    else ""
                )
                + (
                    """
**Performance Review:**
- Database query optimization
- Caching strategies
- Algorithm efficiency
- Resource utilization
- Load handling capabilities
"""
                    if review_type == "performance"
                    else ""
                )
                + (
                    """
**Architecture Review:**
- Separation of concerns
- SOLID principles
- Design patterns usage
- Scalability considerations
- Maintainability
"""
                    if review_type == "architecture"
                    else ""
                )
                + (
                    """
**General Review:**
- Code quality and readability
- Test coverage
- Documentation
- Error handling
- Best practices adherence
"""
                    if review_type == "general"
                    else ""
                )
                + f"""

Provide:
1. **Strengths** - What's done well
2. **Issues** - Problems found with severity levels
3. **Recommendations** - Specific improvements
4. **Action Items** - Priority-ordered tasks

Access repository data via commandcenter://repositories/{repository_name}""",
            ),
        ]

        return PromptResult(messages=messages)

    async def _prompt_generate_report(self, arguments: Dict[str, Any]) -> PromptResult:
        """Generate report generation prompt."""
        if "report_type" not in arguments:
            raise InvalidParamsError("report_type is required")

        report_type = arguments["report_type"]
        period = arguments.get("period", "current period")

        messages = [
            PromptMessage(
                role="system",
                content="""You are a report generator for CommandCenter.
Create comprehensive, data-driven reports with clear insights and actionable recommendations.""",
            ),
            PromptMessage(
                role="user",
                content=f"""Generate a {report_type} report for {period}

Report structure:

1. **Executive Summary**
   - Key highlights
   - Major achievements
   - Critical issues

2. **Detailed Findings**
   - Quantitative metrics
   - Qualitative analysis
   - Trends and patterns

3. **Insights & Analysis**
   - What the data reveals
   - Unexpected findings
   - Root cause analysis

4. **Recommendations**
   - Immediate actions
   - Strategic initiatives
   - Resource needs

5. **Appendix**
   - Data tables
   - Detailed metrics
   - Supporting evidence

Gather data from CommandCenter resources (commandcenter://overview, commandcenter://projects, commandcenter://technologies, commandcenter://research/tasks)""",
            ),
        ]

        return PromptResult(messages=messages)

    async def _prompt_prioritize_tasks(self, arguments: Dict[str, Any]) -> PromptResult:
        """Generate task prioritization prompt."""
        criteria = arguments.get("criteria", "impact")

        messages = [
            PromptMessage(
                role="system",
                content="""You are a task prioritization specialist for CommandCenter.
Help teams prioritize research tasks effectively using structured frameworks.""",
            ),
            PromptMessage(
                role="user",
                content=f"""Prioritize research tasks based on {criteria}

Use the following framework:

1. **Assessment Criteria**
   - Impact: Business value and strategic alignment
   - Urgency: Time sensitivity and deadlines
   - Effort: Required resources and time
   - Dependencies: Blocking or blocked by other tasks
   - Risk: Probability and impact of failure

2. **Prioritization Matrix**
   - High Impact + Low Effort = Do First
   - High Impact + High Effort = Plan & Schedule
   - Low Impact + Low Effort = Quick Wins
   - Low Impact + High Effort = Reconsider

3. **Recommendations**
   - Ranked task list with rationale
   - Suggested order of execution
   - Resource allocation advice

Retrieve current tasks from commandcenter://research/tasks and provide a prioritized action plan.""",
            ),
        ]

        return PromptResult(messages=messages)

    async def _prompt_architecture_review(self, arguments: Dict[str, Any]) -> PromptResult:
        """Generate architecture review prompt."""
        if "system_name" not in arguments:
            raise InvalidParamsError("system_name is required")

        system_name = arguments["system_name"]
        focus = arguments.get("focus", "comprehensive")

        messages = [
            PromptMessage(
                role="system",
                content="""You are a software architect conducting architecture reviews for CommandCenter.
Evaluate system designs against best practices, scalability, and maintainability.""",
            ),
            PromptMessage(
                role="user",
                content=f"""Conduct an architecture review of: "{system_name}"
Focus area: {focus}

Review aspects:

1. **Architecture Patterns**
   - Pattern selection appropriateness
   - Implementation quality
   - Adherence to principles (SOLID, DRY, KISS)

2. **Component Design**
   - Service boundaries
   - Data flow
   - API design
   - Error handling strategy

3. **Scalability**
   - Horizontal scaling capability
   - Performance bottlenecks
   - Resource utilization
   - Caching strategies

4. **Maintainability**
   - Code organization
   - Documentation quality
   - Testing approach
   - Deployment complexity

5. **Security & Reliability**
   - Authentication/authorization
   - Data protection
   - Fault tolerance
   - Disaster recovery

6. **Recommendations**
   - Architecture improvements
   - Refactoring priorities
   - Technical debt items
   - Long-term evolution path

Use CommandCenter resources to understand current technologies and patterns.""",
            ),
        ]

        return PromptResult(messages=messages)
