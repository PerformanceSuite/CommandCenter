"""
Task Queue for Long-Running Agent Orchestrator

File-based task queue using YAML files for persistence.
Tasks move between directories: pending → running → completed/failed
"""

from __future__ import annotations

import yaml
import shutil
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Optional


@dataclass
class TaskConfig:
    """Agent execution configuration"""
    model: str = "sonnet"
    max_turns: int = 100
    max_cost_usd: float = 10.0


@dataclass
class TaskContext:
    """Context for task execution"""
    plan_file: Optional[str] = None
    repo: str = ""
    branch: str = ""


@dataclass
class TaskCompletion:
    """What to do on task completion"""
    create_pr: bool = True
    update_skill: Optional[str] = None
    trigger_next: list[str] = field(default_factory=list)


@dataclass
class Task:
    """A task for the orchestrator to execute"""
    id: str
    title: str
    type: str = "implementation"
    priority: int = 5  # 1 = highest
    depends_on: list[str] = field(default_factory=list)

    context: TaskContext = field(default_factory=TaskContext)
    skills_required: list[str] = field(default_factory=list)
    agent_config: TaskConfig = field(default_factory=TaskConfig)
    on_completion: TaskCompletion = field(default_factory=TaskCompletion)

    # Execution state
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    cost_usd: float = 0.0
    error: Optional[str] = None

    @classmethod
    def from_yaml(cls, path: Path) -> "Task":
        """Load task from YAML file"""
        data = yaml.safe_load(path.read_text())

        # Parse nested objects
        context = TaskContext(**data.get("context", {}))
        agent_config = TaskConfig(**data.get("agent_config", {}))
        on_completion = TaskCompletion(**data.get("on_completion", {}))

        return cls(
            id=data["id"],
            title=data["title"],
            type=data.get("type", "implementation"),
            priority=data.get("priority", 5),
            depends_on=data.get("depends_on", []),
            context=context,
            skills_required=data.get("skills_required", []),
            agent_config=agent_config,
            on_completion=on_completion,
        )

    def to_yaml(self) -> str:
        """Serialize task to YAML"""
        data = {
            "id": self.id,
            "title": self.title,
            "type": self.type,
            "priority": self.priority,
            "depends_on": self.depends_on,
            "context": {
                "plan_file": self.context.plan_file,
                "repo": self.context.repo,
                "branch": self.context.branch,
            },
            "skills_required": self.skills_required,
            "agent_config": {
                "model": self.agent_config.model,
                "max_turns": self.agent_config.max_turns,
                "max_cost_usd": self.agent_config.max_cost_usd,
            },
            "on_completion": {
                "create_pr": self.on_completion.create_pr,
                "update_skill": self.on_completion.update_skill,
                "trigger_next": self.on_completion.trigger_next,
            },
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "cost_usd": self.cost_usd,
            "error": self.error,
        }
        return yaml.dump(data, default_flow_style=False, sort_keys=False)


class TaskQueue:
    """
    File-based task queue.

    Tasks are YAML files that move between directories:
    - pending/   : Tasks waiting to run
    - running/   : Currently executing (should only be 1-N)
    - completed/ : Successfully finished
    - failed/    : Failed tasks (for review)
    """

    def __init__(self, base_dir: str | Path = "tasks"):
        self.base_dir = Path(base_dir)
        self.pending_dir = self.base_dir / "pending"
        self.running_dir = self.base_dir / "running"
        self.completed_dir = self.base_dir / "completed"
        self.failed_dir = self.base_dir / "failed"

        # Ensure directories exist
        for d in [self.pending_dir, self.running_dir, self.completed_dir, self.failed_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def load_pending(self) -> list[Task]:
        """Load all pending tasks"""
        tasks = []
        for path in self.pending_dir.glob("*.yaml"):
            try:
                tasks.append(Task.from_yaml(path))
            except Exception as e:
                print(f"⚠️ Failed to load {path}: {e}")
        return tasks

    def load_completed(self) -> set[str]:
        """Get IDs of completed tasks"""
        return {p.stem.split("-")[0] for p in self.completed_dir.glob("*.yaml")}

    def get_next(self) -> Optional[Task]:
        """
        Get the highest priority task with satisfied dependencies.

        Returns None if no tasks are ready.
        """
        tasks = self.load_pending()
        completed_ids = self.load_completed()

        # Sort by priority (lower = higher priority)
        tasks.sort(key=lambda t: t.priority)

        for task in tasks:
            # Check dependencies
            if all(dep in completed_ids for dep in task.depends_on):
                # Move to running
                self._move_task(task.id, self.pending_dir, self.running_dir)
                task.started_at = datetime.utcnow().isoformat()
                return task

        return None

    def complete(self, task: Task, cost_usd: float = 0.0):
        """Mark task as completed"""
        task.completed_at = datetime.utcnow().isoformat()
        task.cost_usd = cost_usd

        # Write updated task
        dest = self.completed_dir / f"{task.id}.yaml"
        dest.write_text(task.to_yaml())

        # Remove from running
        running_path = self.running_dir / f"{task.id}.yaml"
        if running_path.exists():
            running_path.unlink()

        print(f"✅ Task completed: {task.id} (${cost_usd:.2f})")

    def fail(self, task: Task, error: str):
        """Mark task as failed"""
        task.completed_at = datetime.utcnow().isoformat()
        task.error = error

        # Write to failed
        dest = self.failed_dir / f"{task.id}.yaml"
        dest.write_text(task.to_yaml())

        # Remove from running
        running_path = self.running_dir / f"{task.id}.yaml"
        if running_path.exists():
            running_path.unlink()

        print(f"❌ Task failed: {task.id} - {error}")

    def retry(self, task_id: str):
        """Move failed task back to pending"""
        src = self.failed_dir / f"{task_id}.yaml"
        if src.exists():
            task = Task.from_yaml(src)
            task.started_at = None
            task.completed_at = None
            task.error = None

            dest = self.pending_dir / f"{task_id}.yaml"
            dest.write_text(task.to_yaml())
            src.unlink()

            print(f"🔄 Task retried: {task_id}")

    def add_task(self, task: Task):
        """Add a new task to pending"""
        path = self.pending_dir / f"{task.id}.yaml"
        path.write_text(task.to_yaml())
        print(f"📋 Task added: {task.id}")

    def status(self) -> dict[str, int]:
        """Get queue status"""
        return {
            "pending": len(list(self.pending_dir.glob("*.yaml"))),
            "running": len(list(self.running_dir.glob("*.yaml"))),
            "completed": len(list(self.completed_dir.glob("*.yaml"))),
            "failed": len(list(self.failed_dir.glob("*.yaml"))),
        }

    def _move_task(self, task_id: str, from_dir: Path, to_dir: Path):
        """Move task file between directories"""
        src = from_dir / f"{task_id}.yaml"
        dest = to_dir / f"{task_id}.yaml"
        if src.exists():
            shutil.move(str(src), str(dest))


if __name__ == "__main__":
    # Test the queue
    queue = TaskQueue("test_tasks")

    # Create a test task
    task = Task(
        id="test-001",
        title="Test Task",
        priority=1,
        context=TaskContext(
            repo="https://github.com/test/repo",
            branch="feature/test",
        ),
    )

    queue.add_task(task)
    print(f"Status: {queue.status()}")

    # Get next
    next_task = queue.get_next()
    print(f"Next task: {next_task.title if next_task else 'None'}")
    print(f"Status: {queue.status()}")

    # Complete
    if next_task:
        queue.complete(next_task, cost_usd=1.50)
    print(f"Status: {queue.status()}")
