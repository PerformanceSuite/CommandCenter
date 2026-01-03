"""IMPROVE skill: Implement a single coding subtask."""
from pydantic import BaseModel, Field
from .base import Skill, SkillMetadata, register_skill


class CodeSubtaskInput(BaseModel):
    """Input for coding a subtask."""
    subtask: str = Field(..., description="Subtask description")
    project_dir: str = Field(default=".", description="Project directory")
    spec: dict | None = Field(default=None, description="Spec context if available")
    plan: dict | None = Field(default=None, description="Implementation plan if available")
    sandbox_id: str | None = Field(default=None, description="E2B sandbox ID for isolated execution")


class CodeSubtaskOutput(BaseModel):
    """Output from coding subtask."""
    success: bool
    files_changed: list[str] = Field(default_factory=list)
    files_created: list[str] = Field(default_factory=list)
    implementation_notes: str = Field(default="")
    suggested_next_skills: list[str] = Field(
        default_factory=lambda: ["review_qa"],
        description="Usually QA review after coding"
    )


@register_skill
class CodeSubtaskSkill(Skill[CodeSubtaskInput, CodeSubtaskOutput]):
    """
    Implement a single coding subtask.

    This is an IMPROVE phase skill that can be used:
    - Standalone for quick fixes
    - In parallel for multiple subtasks
    - After plan_implementation for structured work
    """

    @classmethod
    def metadata(cls) -> SkillMetadata:
        return SkillMetadata(
            id="code_subtask",
            name="Code Subtask",
            description="Implement a single coding subtask with optional sandbox isolation",
            category="improve",
            phase="IMPROVE",
            input_schema=CodeSubtaskInput,
            output_schema=CodeSubtaskOutput,
            examples=[
                {
                    "input": {
                        "subtask": "Add login endpoint to auth.py",
                        "project_dir": "."
                    },
                    "output": {
                        "success": True,
                        "files_changed": ["src/auth.py"],
                        "files_created": ["src/auth_test.py"],
                        "suggested_next_skills": ["review_qa"]
                    }
                }
            ],
            depends_on=[],  # Can run standalone
        )

    async def execute(
        self,
        input: CodeSubtaskInput,
        context: dict | None = None
    ) -> CodeSubtaskOutput:
        """Execute subtask implementation."""
        from ..bridges.auto_claude import AutoClaudeBridge
        from ..bridges.sandbox import SandboxBridge

        # Use sandbox if provided
        if input.sandbox_id:
            sandbox = SandboxBridge()
            result = await sandbox.run_coder(
                sandbox_id=input.sandbox_id,
                subtask=input.subtask,
                context=context,
            )
        else:
            bridge = AutoClaudeBridge()
            result = await bridge.code_subtask(
                subtask=input.subtask,
                project_dir=input.project_dir,
                spec=input.spec,
                plan=input.plan,
            )

        return CodeSubtaskOutput(**result)
