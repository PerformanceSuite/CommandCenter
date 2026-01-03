"""Bridge to Auto-Claude core components."""
import sys
from pathlib import Path

# Add auto-claude-core to path
AUTO_CLAUDE_PATH = Path(__file__).parents[4] / "integrations" / "auto-claude-core"
if AUTO_CLAUDE_PATH.exists():
    sys.path.insert(0, str(AUTO_CLAUDE_PATH))


class AutoClaudeBridge:
    """
    Bridge to Auto-Claude core components.

    Provides a stable interface even if Auto-Claude internals change.
    Falls back to stub implementations if Auto-Claude not available.
    """

    def __init__(self):
        self.auto_claude_available = AUTO_CLAUDE_PATH.exists()

    async def gather_requirements(self, task_description: str, project_dir: str) -> dict:
        """Gather requirements using Auto-Claude's gatherer."""
        if self.auto_claude_available:
            try:
                from spec_agents.gatherer import SpecGatherer
                gatherer = SpecGatherer(project_dir=project_dir)
                return await gatherer.gather(task_description)
            except ImportError:
                pass

        # Fallback: basic extraction
        return {
            "requirements": [task_description],
            "user_stories": [],
            "acceptance_criteria": [],
            "complexity_estimate": "standard",
        }

    async def code_subtask(
        self,
        subtask: str,
        project_dir: str,
        spec: dict | None = None,
        plan: dict | None = None,
    ) -> dict:
        """Code a subtask using Auto-Claude's coder."""
        if self.auto_claude_available:
            try:
                from agents.coder import CoderAgent
                coder = CoderAgent(project_dir=project_dir)
                return await coder.implement_subtask(subtask, spec=spec, plan=plan)
            except ImportError:
                pass

        # Fallback: return placeholder
        return {
            "success": False,
            "files_changed": [],
            "files_created": [],
            "implementation_notes": "Auto-Claude core not available",
        }
