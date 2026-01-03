"""IMPROVE phase adapter - planning, coding, and fixing."""

from .base import BaseAdapter, LoopContext


class ImproveAdapter(BaseAdapter):
    """Handles the IMPROVE phase of The Loop."""

    def get_phase(self) -> str:
        return "improve"

    async def execute(self, context: LoopContext, **kwargs) -> LoopContext:
        """
        Execute IMPROVE phase:
        - mode="spec": Write spec document (spec/writer)
        - mode="plan": Create implementation plan (agents/planner)
        - mode="code": Implement subtasks (agents/coder)
        - mode="fix": Fix QA issues (qa/fixer)
        """
        mode = kwargs.get("mode", "plan")

        if mode == "spec":
            return await self._write_spec(context)
        elif mode == "plan":
            return await self._create_plan(context)
        elif mode == "code":
            return await self._implement(context)
        elif mode == "fix":
            return await self._fix_issues(context)

        return context

    async def _write_spec(self, context: LoopContext) -> LoopContext:
        """Use spec writer to create spec document."""
        try:
            from spec.writer import SpecWriter

            writer = SpecWriter(
                project_dir=str(context.project_dir),
                spec_dir=str(context.spec_dir),
            )

            spec = await writer.write(
                requirements=context.artifacts.get("requirements"),
                research=context.artifacts.get("research"),
            )
            context.artifacts["spec"] = spec

        except ImportError:
            # Fallback: Create basic spec from requirements
            requirements = context.artifacts.get("requirements", {})
            context.artifacts["spec"] = {
                "title": requirements.get("description", "Untitled"),
                "requirements": requirements,
                "written": False,
                "error": "Auto-Claude spec module not available",
            }

        return context.with_phase("validate")

    async def _create_plan(self, context: LoopContext) -> LoopContext:
        """Use planner agent to create implementation plan."""
        try:
            from agents.planner import PlannerAgent

            planner = PlannerAgent(
                project_dir=str(context.project_dir),
                spec_dir=str(context.spec_dir),
            )

            plan = await planner.create_plan(context.artifacts.get("spec"))
            context.artifacts["plan"] = plan

        except ImportError:
            # Fallback: Create basic plan
            spec = context.artifacts.get("spec", {})
            context.artifacts["plan"] = {
                "title": spec.get("title", "Implementation Plan"),
                "subtasks": [{"task": "Implement feature", "status": "pending"}],
                "planned": False,
                "error": "Auto-Claude agents module not available",
            }

        return context

    async def _implement(self, context: LoopContext) -> LoopContext:
        """Use coder agent to implement subtasks."""
        try:
            from agents.coder import CoderAgent

            coder = CoderAgent(
                project_dir=str(context.project_dir),
                spec_dir=str(context.spec_dir),
                sandbox_id=context.sandbox_id,
            )

            implementation = await coder.implement(context.artifacts.get("plan"))
            context.artifacts["implementation"] = implementation

        except ImportError:
            context.artifacts["implementation"] = {
                "implemented": False,
                "error": "Auto-Claude agents module not available",
            }

        return context.with_phase("validate")

    async def _fix_issues(self, context: LoopContext) -> LoopContext:
        """Use qa_fixer agent to fix issues."""
        try:
            from qa.fixer import QAFixer

            fixer = QAFixer(
                project_dir=str(context.project_dir),
                spec_dir=str(context.spec_dir),
                sandbox_id=context.sandbox_id,
            )

            fix_result = await fixer.fix(context.artifacts.get("qa_result"))
            context.artifacts["fix_result"] = fix_result

        except ImportError:
            context.artifacts["fix_result"] = {
                "fixed": False,
                "error": "Auto-Claude qa module not available",
            }

        return context.with_phase("validate")
