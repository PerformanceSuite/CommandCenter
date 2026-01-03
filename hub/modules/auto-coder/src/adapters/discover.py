"""DISCOVER phase adapter - requirements gathering and research."""

from .base import BaseAdapter, LoopContext


class DiscoverAdapter(BaseAdapter):
    """Handles the DISCOVER phase of The Loop."""

    def get_phase(self) -> str:
        return "discover"

    async def execute(self, context: LoopContext, **kwargs) -> LoopContext:
        """
        Execute DISCOVER phase:
        1. Gather requirements (spec/gatherer)
        2. Research approaches (spec/researcher)
        """
        task = kwargs.get("task")

        # Phase 1: Gather requirements
        context = await self._gather_requirements(context, task)

        # Phase 2: Research (for standard/complex tasks)
        if task and task.complexity in ("standard", "complex"):
            context = await self._research_approaches(context, task)

        return context.with_phase("validate")

    async def _gather_requirements(self, context: LoopContext, task) -> LoopContext:
        """Use spec gatherer to collect requirements."""
        try:
            # Import from auto-claude-core
            from spec.discovery import SpecDiscovery

            discovery = SpecDiscovery(
                project_dir=str(context.project_dir),
                spec_dir=str(context.spec_dir),
            )

            requirements = await discovery.gather(task.description if task else "")
            context.artifacts["requirements"] = requirements

        except ImportError:
            # Fallback: Create basic requirements from task description
            context.artifacts["requirements"] = {
                "description": task.description if task else "",
                "gathered": False,
                "error": "Auto-Claude spec module not available",
            }

        return context

    async def _research_approaches(self, context: LoopContext, task) -> LoopContext:
        """Use spec researcher to validate external dependencies."""
        try:
            from spec.discovery import SpecDiscovery

            discovery = SpecDiscovery(
                project_dir=str(context.project_dir),
                spec_dir=str(context.spec_dir),
            )

            research = await discovery.research(context.artifacts.get("requirements", {}))
            context.artifacts["research"] = research

        except ImportError:
            context.artifacts["research"] = {
                "researched": False,
                "error": "Auto-Claude spec module not available",
            }

        return context
