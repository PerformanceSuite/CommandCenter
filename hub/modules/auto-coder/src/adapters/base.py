"""Base adapter class for Loop phase integration."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any
import sys

# Add auto-claude-core to path
AUTO_CLAUDE_PATH = Path(__file__).parents[4] / "integrations" / "auto-claude-core"
sys.path.insert(0, str(AUTO_CLAUDE_PATH))


@dataclass
class LoopContext:
    """Context passed through The Loop."""

    task_id: str
    project_dir: Path
    spec_dir: Path
    phase: str  # discover, validate, improve
    memory: dict = field(default_factory=dict)
    sandbox_id: str | None = None
    artifacts: dict = field(default_factory=dict)

    def with_phase(self, phase: str) -> "LoopContext":
        """Return new context with updated phase."""
        return LoopContext(
            task_id=self.task_id,
            project_dir=self.project_dir,
            spec_dir=self.spec_dir,
            phase=phase,
            memory=self.memory,
            sandbox_id=self.sandbox_id,
            artifacts=self.artifacts.copy(),
        )


class BaseAdapter(ABC):
    """Base class for Loop phase adapters."""

    def __init__(self):
        self.auto_claude_path = AUTO_CLAUDE_PATH

    @abstractmethod
    async def execute(self, context: LoopContext, **kwargs) -> LoopContext:
        """Execute the adapter's phase logic."""
        pass

    @abstractmethod
    def get_phase(self) -> str:
        """Return the Loop phase this adapter handles."""
        pass

    def _load_prompt(self, prompt_name: str) -> str:
        """Load a prompt template."""
        prompt_path = Path(__file__).parents[2] / "prompts" / f"{prompt_name}.md"
        if prompt_path.exists():
            return prompt_path.read_text()

        # Fall back to Auto-Claude prompts
        auto_prompt = self.auto_claude_path / "prompts" / f"{prompt_name}.md"
        if auto_prompt.exists():
            return auto_prompt.read_text()

        raise FileNotFoundError(f"Prompt not found: {prompt_name}")
