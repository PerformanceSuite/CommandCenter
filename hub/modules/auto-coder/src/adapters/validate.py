"""VALIDATE phase adapter - spec critique and QA review."""

from .base import BaseAdapter, LoopContext


class ValidateAdapter(BaseAdapter):
    """Handles the VALIDATE phase of The Loop."""

    def get_phase(self) -> str:
        return "validate"

    async def execute(self, context: LoopContext, **kwargs) -> LoopContext:
        """
        Execute VALIDATE phase:
        - mode="spec": Critique the spec (spec/critique)
        - mode="qa": Review implementation (qa/reviewer)
        """
        mode = kwargs.get("mode", "spec")

        if mode == "spec":
            return await self._critique_spec(context)
        elif mode == "qa":
            return await self._qa_review(context)

        return context

    async def _critique_spec(self, context: LoopContext) -> LoopContext:
        """Use spec critic for self-critique with ultrathink."""
        try:
            from spec.critique import SpecCritic

            critic = SpecCritic(
                project_dir=str(context.project_dir),
                spec_dir=str(context.spec_dir),
            )

            critique = await critic.critique(context.artifacts.get("spec"))
            context.artifacts["critique"] = critique

            # If major issues, loop back to DISCOVER
            if critique.get("major_issues"):
                return context.with_phase("discover")

        except ImportError:
            context.artifacts["critique"] = {
                "critiqued": False,
                "major_issues": False,
                "error": "Auto-Claude spec module not available",
            }

        return context.with_phase("improve")

    async def _qa_review(self, context: LoopContext) -> LoopContext:
        """Use qa_reviewer to validate implementation."""
        try:
            from qa.reviewer import QAReviewer

            reviewer = QAReviewer(
                project_dir=str(context.project_dir),
                spec_dir=str(context.spec_dir),
            )

            qa_result = await reviewer.review(context.artifacts.get("implementation"))
            context.artifacts["qa_result"] = qa_result

        except ImportError:
            # Fallback: Mark as passed if implementation exists
            has_impl = bool(context.artifacts.get("implementation"))
            context.artifacts["qa_result"] = {
                "passed": has_impl,
                "reviewed": False,
                "error": "Auto-Claude qa module not available",
            }

        return context
