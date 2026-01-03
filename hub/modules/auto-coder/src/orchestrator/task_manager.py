"""Task manager - orchestrates coding tasks through The Loop."""

from dataclasses import dataclass
from pathlib import Path
from typing import Literal
import uuid

from ..adapters.discover import DiscoverAdapter
from ..adapters.validate import ValidateAdapter
from ..adapters.improve import ImproveAdapter
from ..adapters.base import LoopContext


@dataclass
class CodingTask:
    """A coding task to be processed through The Loop."""

    id: str
    description: str
    project_dir: Path
    complexity: Literal["simple", "standard", "complex"] = "standard"
    status: str = "pending"
    parallel_agents: int = 1


@dataclass
class TaskResult:
    """Result of a coding task."""

    task_id: str
    success: bool
    context: LoopContext
    message: str


class AutoCoderTaskManager:
    """Orchestrates coding tasks through The Loop."""

    def __init__(self, base_dir: Path | None = None):
        self.base_dir = base_dir or Path.cwd()
        self.specs_dir = self.base_dir / ".auto-coder" / "specs"
        self.specs_dir.mkdir(parents=True, exist_ok=True)

        self.discover = DiscoverAdapter()
        self.validate = ValidateAdapter()
        self.improve = ImproveAdapter()

        self._tasks: dict[str, CodingTask] = {}

    async def create_task(self, description: str, **kwargs) -> CodingTask:
        """Create a new coding task."""
        task = CodingTask(
            id=str(uuid.uuid4())[:8],
            description=description,
            project_dir=kwargs.get("project_dir", self.base_dir),
            complexity=kwargs.get("complexity", "standard"),
            parallel_agents=kwargs.get("parallel_agents", 1),
        )
        self._tasks[task.id] = task
        return task

    async def run_task(self, task: CodingTask) -> TaskResult:
        """Run a coding task through The Loop."""
        task.status = "running"

        # Create spec directory
        spec_dir = self.specs_dir / f"{task.id}-{self._slugify(task.description)}"
        spec_dir.mkdir(parents=True, exist_ok=True)

        # Initialize context
        context = LoopContext(
            task_id=task.id,
            project_dir=task.project_dir,
            spec_dir=spec_dir,
            phase="discover",
        )

        try:
            # THE LOOP
            max_iterations = 5
            iteration = 0

            while iteration < max_iterations:
                iteration += 1

                # DISCOVER
                if context.phase == "discover":
                    context = await self.discover.execute(context, task=task)

                # Write spec after discover
                if context.phase == "validate" and "spec" not in context.artifacts:
                    context = await self.improve.execute(context, mode="spec")

                # VALIDATE spec
                if context.phase == "validate" and "plan" not in context.artifacts:
                    context = await self.validate.execute(context, mode="spec")

                # IMPROVE - plan and code
                if context.phase == "improve":
                    if "plan" not in context.artifacts:
                        context = await self.improve.execute(context, mode="plan")
                    context = await self.improve.execute(context, mode="code")

                # VALIDATE implementation
                if context.phase == "validate" and "implementation" in context.artifacts:
                    context = await self.validate.execute(context, mode="qa")

                    qa_result = context.artifacts.get("qa_result", {})
                    if qa_result.get("passed"):
                        task.status = "completed"
                        return TaskResult(
                            task_id=task.id,
                            success=True,
                            context=context,
                            message="Task completed successfully",
                        )

                    # Fix issues and loop
                    context = await self.improve.execute(context, mode="fix")
                    context = context.with_phase("validate")

            task.status = "max_iterations"
            return TaskResult(
                task_id=task.id,
                success=False,
                context=context,
                message=f"Max iterations ({max_iterations}) reached",
            )

        except Exception as e:
            task.status = "error"
            return TaskResult(
                task_id=task.id,
                success=False,
                context=context,
                message=str(e),
            )

    async def get_status(self, task_id: str) -> dict:
        """Get task status."""
        task = self._tasks.get(task_id)
        if not task:
            return {"error": "Task not found"}
        return {
            "task_id": task.id,
            "status": task.status,
            "description": task.description,
        }

    def list_tasks(self) -> list[dict]:
        """List all tasks."""
        return [
            {
                "task_id": t.id,
                "status": t.status,
                "description": t.description,
                "complexity": t.complexity,
            }
            for t in self._tasks.values()
        ]

    def _slugify(self, text: str) -> str:
        """Create a slug from text."""
        return "-".join(text.lower().split()[:5])
