"""DISCOVER skill: Gather and structure requirements."""
from pydantic import BaseModel, Field, field_validator
from .base import Skill, SkillMetadata, register_skill
from .validators import validate_project_dir


class GatherRequirementsInput(BaseModel):
    """Input for requirements gathering."""
    task_description: str = Field(..., description="Natural language task description")
    project_dir: str = Field(default=".", description="Project directory path")
    context: dict | None = Field(default=None, description="Optional context from previous skills")

    @field_validator('project_dir')
    @classmethod
    def check_project_dir(cls, v: str) -> str:
        """Validate project_dir is within allowed boundaries."""
        return validate_project_dir(v)


class GatherRequirementsOutput(BaseModel):
    """Structured requirements output."""
    requirements: list[str] = Field(..., description="List of requirements")
    user_stories: list[dict] = Field(default_factory=list, description="User stories")
    acceptance_criteria: list[str] = Field(default_factory=list, description="Acceptance criteria")
    complexity_estimate: str = Field(default="standard", description="simple|standard|complex")
    suggested_next_skills: list[str] = Field(
        default_factory=lambda: ["research_approach", "write_spec"],
        description="Suggested skills to run next (composability hint)"
    )


@register_skill
class GatherRequirementsSkill(Skill[GatherRequirementsInput, GatherRequirementsOutput]):
    """
    Gather and structure requirements from a task description.

    This is a DISCOVER phase skill that can be used:
    - Standalone for requirements analysis
    - As first step in full Loop orchestration
    - Combined with research_approach for deeper analysis
    """

    @classmethod
    def metadata(cls) -> SkillMetadata:
        return SkillMetadata(
            id="gather_requirements",
            name="Gather Requirements",
            description="Analyze a task description and extract structured requirements, user stories, and acceptance criteria",
            category="discover",
            phase="DISCOVER",
            input_schema=GatherRequirementsInput,
            output_schema=GatherRequirementsOutput,
            examples=[
                {
                    "input": {
                        "task_description": "Add user authentication with email/password",
                        "project_dir": "."
                    },
                    "output": {
                        "requirements": [
                            "User registration with email/password",
                            "User login with email/password",
                            "Password reset via email",
                            "Session management"
                        ],
                        "complexity_estimate": "standard",
                        "suggested_next_skills": ["research_approach", "write_spec"]
                    }
                }
            ],
            depends_on=[],  # No dependencies - can be entry point
        )

    async def execute(
        self,
        input: GatherRequirementsInput,
        context: dict | None = None
    ) -> GatherRequirementsOutput:
        """Execute requirements gathering."""
        # Bridge to Auto-Claude's gatherer (when available)
        # For now, return structured placeholder
        from ..bridges.auto_claude import AutoClaudeBridge

        bridge = AutoClaudeBridge()
        result = await bridge.gather_requirements(
            task_description=input.task_description,
            project_dir=input.project_dir,
        )

        return GatherRequirementsOutput(**result)
