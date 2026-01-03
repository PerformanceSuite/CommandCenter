# AutoCoder Module - Wrapper Design

**Date**: 2026-01-03
**Status**: Ready for Execution
**Depends On**: `docs/plans/2026-01-03-auto-claude-integration.md` (extraction complete)

## Objective

Create a CommandCenter-native module that wraps Auto-Claude's agent intelligence to:
1. Participate in The Loop (DISCOVER → VALIDATE → IMPROVE)
2. Integrate with existing E2B sandbox infrastructure (`tools/agent-sandboxes/`)
3. Expose via API, CLI, and VISLZR interfaces
4. Enable autonomous coding on CommandCenter itself (dogfooding)

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         VISLZR                                  │
│                    (Mind Map UI Node)                           │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                   hub/modules/auto-coder/                       │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐             │
│  │   Adapter   │  │   Adapter   │  │   Adapter   │             │
│  │  (Discover) │  │  (Validate) │  │  (Improve)  │             │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘             │
└─────────┼────────────────┼────────────────┼─────────────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────────────┐
│              integrations/auto-claude-core/                     │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ spec_agents/ │  │   agents/    │  │   agents/    │          │
│  │  gatherer    │  │  qa_reviewer │  │   planner    │          │
│  │  researcher  │  │    critic    │  │    coder     │          │
│  └──────────────┘  └──────────────┘  │   qa_fixer   │          │
│                                      └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
          │                │                │
┌─────────▼────────────────▼────────────────▼─────────────────────┐
│                tools/agent-sandboxes/                           │
│              (E2B Sandbox Execution)                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │  obox: Parallel agents in isolated cloud sandboxes      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
```

## The Loop Mapping

| Loop Phase | Auto-Claude Component | AutoCoder Adapter |
|------------|----------------------|-------------------|
| **DISCOVER** | `spec_agents/gatherer.py` | `discover.py` - Gathers requirements, explores codebase |
| **DISCOVER** | `spec_agents/researcher.py` | `discover.py` - Validates external deps, researches approaches |
| **VALIDATE** | `spec_agents/critic.py` | `validate.py` - Self-critique specs with ultrathink |
| **VALIDATE** | `agents/qa_reviewer.py` | `validate.py` - Validates implementation against acceptance criteria |
| **IMPROVE** | `spec_agents/writer.py` | `improve.py` - Creates spec.md documents |
| **IMPROVE** | `agents/planner.py` | `improve.py` - Creates subtask-based implementation plan |
| **IMPROVE** | `agents/coder.py` | `improve.py` - Implements subtasks |
| **IMPROVE** | `agents/qa_fixer.py` | `improve.py` - Fixes QA-reported issues |

## Module Structure

```
hub/modules/auto-coder/
├── README.md                    # Module documentation
├── pyproject.toml              # Python package config
├── src/
│   ├── __init__.py
│   ├── config.py               # Module configuration
│   │
│   ├── adapters/               # The Loop adapters
│   │   ├── __init__.py
│   │   ├── base.py             # Base adapter class
│   │   ├── discover.py         # DISCOVER phase (gatherer, researcher)
│   │   ├── validate.py         # VALIDATE phase (critic, qa_reviewer)
│   │   └── improve.py          # IMPROVE phase (writer, planner, coder, fixer)
│   │
│   ├── orchestrator/           # Task orchestration
│   │   ├── __init__.py
│   │   ├── task_manager.py     # Manages coding tasks through The Loop
│   │   ├── sandbox_bridge.py   # Bridge to E2B/obox infrastructure
│   │   └── memory_bridge.py    # Bridge to KnowledgeBeast/Graphiti
│   │
│   ├── api/                    # REST API endpoints
│   │   ├── __init__.py
│   │   ├── routes.py           # FastAPI routes
│   │   └── schemas.py          # Pydantic models
│   │
│   └── cli/                    # CLI commands
│       ├── __init__.py
│       └── commands.py         # Click commands
│
├── prompts/                    # CommandCenter-adapted prompts
│   ├── discover_gatherer.md
│   ├── discover_researcher.md
│   ├── validate_critic.md
│   ├── validate_qa.md
│   ├── improve_planner.md
│   ├── improve_coder.md
│   └── improve_fixer.md
│
└── tests/
    ├── __init__.py
    ├── test_adapters.py
    └── test_orchestrator.py
```

## Key Components

### 1. Base Adapter (`adapters/base.py`)

```python
from abc import ABC, abstractmethod
from typing import Any
from dataclasses import dataclass

@dataclass
class LoopContext:
    """Context passed through The Loop"""
    task_id: str
    project_dir: str
    spec_dir: str
    phase: str  # discover, validate, improve
    memory: dict  # From KnowledgeBeast/Graphiti
    sandbox_id: str | None = None

class BaseAdapter(ABC):
    """Base class for Loop phase adapters"""

    def __init__(self, auto_claude_path: str):
        self.auto_claude_path = auto_claude_path
        # Import from integrations/auto-claude-core/

    @abstractmethod
    async def execute(self, context: LoopContext, **kwargs) -> dict[str, Any]:
        """Execute the adapter's phase logic"""
        pass

    @abstractmethod
    def get_phase(self) -> str:
        """Return the Loop phase this adapter handles"""
        pass
```

### 2. Task Manager (`orchestrator/task_manager.py`)

```python
class AutoCoderTaskManager:
    """Orchestrates coding tasks through The Loop"""

    def __init__(self):
        self.discover_adapter = DiscoverAdapter()
        self.validate_adapter = ValidateAdapter()
        self.improve_adapter = ImproveAdapter()
        self.sandbox_bridge = SandboxBridge()
        self.memory_bridge = MemoryBridge()

    async def run_task(self, task: CodingTask) -> TaskResult:
        """Run a coding task through The Loop"""

        context = LoopContext(
            task_id=task.id,
            project_dir=task.project_dir,
            spec_dir=self._create_spec_dir(task),
            phase="discover",
            memory=await self.memory_bridge.get_context(task)
        )

        # DISCOVER: Gather requirements, research
        context = await self.discover_adapter.execute(context, task=task)

        # VALIDATE: Critique spec
        context = await self.validate_adapter.execute(context, mode="spec")

        # IMPROVE: Plan and implement
        context = await self.improve_adapter.execute(context, mode="plan")
        context = await self.improve_adapter.execute(context, mode="code")

        # VALIDATE: QA review
        qa_result = await self.validate_adapter.execute(context, mode="qa")

        # Loop if issues found
        while not qa_result.passed and qa_result.attempts < 3:
            context = await self.improve_adapter.execute(context, mode="fix")
            qa_result = await self.validate_adapter.execute(context, mode="qa")

        return TaskResult(context=context, qa_result=qa_result)
```

### 3. Sandbox Bridge (`orchestrator/sandbox_bridge.py`)

```python
class SandboxBridge:
    """Bridge to tools/agent-sandboxes infrastructure"""

    def __init__(self):
        # Connect to existing obox infrastructure
        self.obox_path = Path("tools/agent-sandboxes/apps/sandbox_workflows")

    async def create_sandbox(self, repo_url: str, branch: str) -> str:
        """Create an E2B sandbox for the task"""
        # Uses existing obox infrastructure
        pass

    async def run_agent_in_sandbox(
        self,
        sandbox_id: str,
        agent_type: str,  # planner, coder, qa_reviewer, qa_fixer
        prompt: str
    ) -> AgentResult:
        """Run an Auto-Claude agent in the sandbox"""
        pass

    async def get_sandbox_files(self, sandbox_id: str) -> list[str]:
        """Get files from sandbox for review"""
        pass
```

### 4. API Routes (`api/routes.py`)

```python
from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

router = APIRouter(prefix="/api/auto-coder", tags=["auto-coder"])

class CodingTaskRequest(BaseModel):
    description: str
    project_dir: str
    complexity: str = "standard"  # simple, standard, complex
    parallel_agents: int = 1

class TaskStatus(BaseModel):
    task_id: str
    phase: str
    status: str
    progress: float
    current_agent: str | None

@router.post("/tasks")
async def create_task(request: CodingTaskRequest, background_tasks: BackgroundTasks):
    """Create a new autonomous coding task"""
    task = await task_manager.create_task(request)
    background_tasks.add_task(task_manager.run_task, task)
    return {"task_id": task.id, "status": "started"}

@router.get("/tasks/{task_id}")
async def get_task_status(task_id: str) -> TaskStatus:
    """Get status of a coding task"""
    return await task_manager.get_status(task_id)

@router.get("/tasks/{task_id}/spec")
async def get_task_spec(task_id: str):
    """Get the generated spec for a task"""
    return await task_manager.get_spec(task_id)

@router.post("/tasks/{task_id}/approve")
async def approve_task(task_id: str):
    """Approve and merge the task's changes"""
    return await task_manager.approve_and_merge(task_id)

@router.post("/tasks/{task_id}/reject")
async def reject_task(task_id: str, feedback: str):
    """Reject task with feedback for revision"""
    return await task_manager.reject_with_feedback(task_id, feedback)
```

### 5. CLI Commands (`cli/commands.py`)

```python
import click
from rich.console import Console

console = Console()

@click.group()
def auto_coder():
    """AutoCoder - Autonomous coding through The Loop"""
    pass

@auto_coder.command()
@click.argument("description")
@click.option("--project", "-p", default=".", help="Project directory")
@click.option("--complexity", "-c", type=click.Choice(["simple", "standard", "complex"]), default="standard")
@click.option("--parallel", "-n", default=1, help="Number of parallel agents")
def create(description: str, project: str, complexity: str, parallel: int):
    """Create a new coding task"""
    console.print(f"[bold blue]Creating task:[/] {description}")
    # ... implementation

@auto_coder.command()
@click.argument("task_id")
def status(task_id: str):
    """Check task status"""
    # ... implementation

@auto_coder.command()
@click.argument("task_id")
def approve(task_id: str):
    """Approve and merge task changes"""
    # ... implementation

@auto_coder.command()
def list():
    """List all tasks"""
    # ... implementation
```

## VISLZR Integration

The AutoCoder module appears in VISLZR as an interactive node:

```yaml
# VISLZR node configuration
node:
  id: auto-coder
  type: module
  label: AutoCoder
  icon: robot

  # Contextual actions (action ring)
  actions:
    - id: new-task
      label: New Coding Task
      icon: plus
      action: open_modal
      modal: auto-coder-new-task

    - id: view-tasks
      label: View Tasks
      icon: list
      action: navigate
      target: /auto-coder/tasks

    - id: run-on-self
      label: Improve CommandCenter
      icon: refresh
      action: open_modal
      modal: auto-coder-self-improve

  # Child nodes (active tasks)
  children:
    dynamic: true
    source: /api/auto-coder/tasks?status=active
    nodeType: task
```

## Integration Points

### With KnowledgeBeast
```python
# Memory bridge fetches context from KB
context = await kb_client.query(
    f"relevant code patterns for: {task.description}",
    filters={"project": task.project_dir}
)
```

### With Existing E2B Infrastructure
```python
# Reuse obox for sandbox execution
from tools.agent_sandboxes.apps.sandbox_workflows.src.modules import obox

result = await obox.run(
    repo_url=task.repo_url,
    branch=f"auto-coder/{task.id}",
    prompt=agent_prompt,
    model="sonnet",
    turns=10
)
```

### With Graphiti (from Auto-Claude)
```python
# Use Auto-Claude's memory system for cross-session context
from integrations.auto_claude_core.integrations.graphiti.memory import get_graphiti_memory

memory = get_graphiti_memory(spec_dir, project_dir)
insights = memory.get_context_for_session(task.description)
```

---

## Claude Code Prompt

Copy everything below the line and paste into Claude Code:

---

```
# AutoCoder Module Creation Task

## Context
I've extracted Auto-Claude core components to `integrations/auto-claude-core/`. Now I need to create a CommandCenter wrapper module that integrates these agents into The Loop.

## Task
Create the AutoCoder module structure at `hub/modules/auto-coder/`:

### Step 1: Create Directory Structure
```bash
mkdir -p /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/{src/{adapters,orchestrator,api,cli},prompts,tests}
```

### Step 2: Create pyproject.toml
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/pyproject.toml`:

```toml
[project]
name = "commandcenter-auto-coder"
version = "0.1.0"
description = "Autonomous coding module for CommandCenter - wraps Auto-Claude agents for The Loop"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.109.0",
    "uvicorn>=0.27.0",
    "pydantic>=2.5.0",
    "click>=8.1.0",
    "rich>=13.7.0",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[project.scripts]
auto-coder = "src.cli.commands:auto_coder"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Step 3: Create Base Adapter
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/adapters/base.py`:

```python
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
```

### Step 4: Create Discover Adapter
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/adapters/discover.py`:

```python
"""DISCOVER phase adapter - requirements gathering and research."""
from .base import BaseAdapter, LoopContext


class DiscoverAdapter(BaseAdapter):
    """Handles the DISCOVER phase of The Loop."""

    def get_phase(self) -> str:
        return "discover"

    async def execute(self, context: LoopContext, **kwargs) -> LoopContext:
        """
        Execute DISCOVER phase:
        1. Gather requirements (spec_agents/gatherer)
        2. Research approaches (spec_agents/researcher)
        """
        task = kwargs.get("task")

        # Phase 1: Gather requirements
        context = await self._gather_requirements(context, task)

        # Phase 2: Research (for standard/complex tasks)
        if task.complexity in ("standard", "complex"):
            context = await self._research_approaches(context, task)

        return context.with_phase("validate")

    async def _gather_requirements(self, context: LoopContext, task) -> LoopContext:
        """Use spec_gatherer to collect requirements."""
        # Import from auto-claude-core
        from spec_agents.gatherer import SpecGatherer

        gatherer = SpecGatherer(
            project_dir=str(context.project_dir),
            spec_dir=str(context.spec_dir),
        )

        requirements = await gatherer.gather(task.description)
        context.artifacts["requirements"] = requirements

        return context

    async def _research_approaches(self, context: LoopContext, task) -> LoopContext:
        """Use spec_researcher to validate external dependencies."""
        from spec_agents.researcher import SpecResearcher

        researcher = SpecResearcher(
            project_dir=str(context.project_dir),
            spec_dir=str(context.spec_dir),
        )

        research = await researcher.research(context.artifacts["requirements"])
        context.artifacts["research"] = research

        return context
```

### Step 5: Create Validate Adapter
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/adapters/validate.py`:

```python
"""VALIDATE phase adapter - spec critique and QA review."""
from .base import BaseAdapter, LoopContext


class ValidateAdapter(BaseAdapter):
    """Handles the VALIDATE phase of The Loop."""

    def get_phase(self) -> str:
        return "validate"

    async def execute(self, context: LoopContext, **kwargs) -> LoopContext:
        """
        Execute VALIDATE phase:
        - mode="spec": Critique the spec (spec_agents/critic)
        - mode="qa": Review implementation (agents/qa_reviewer)
        """
        mode = kwargs.get("mode", "spec")

        if mode == "spec":
            return await self._critique_spec(context)
        elif mode == "qa":
            return await self._qa_review(context)

        return context

    async def _critique_spec(self, context: LoopContext) -> LoopContext:
        """Use spec_critic for self-critique with ultrathink."""
        from spec_agents.critic import SpecCritic

        critic = SpecCritic(
            project_dir=str(context.project_dir),
            spec_dir=str(context.spec_dir),
        )

        critique = await critic.critique(context.artifacts.get("spec"))
        context.artifacts["critique"] = critique

        # If major issues, loop back to DISCOVER
        if critique.get("major_issues"):
            return context.with_phase("discover")

        return context.with_phase("improve")

    async def _qa_review(self, context: LoopContext) -> LoopContext:
        """Use qa_reviewer to validate implementation."""
        from agents.qa_reviewer import QAReviewer

        reviewer = QAReviewer(
            project_dir=str(context.project_dir),
            spec_dir=str(context.spec_dir),
        )

        qa_result = await reviewer.review(context.artifacts.get("implementation"))
        context.artifacts["qa_result"] = qa_result

        return context
```

### Step 6: Create Improve Adapter
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/adapters/improve.py`:

```python
"""IMPROVE phase adapter - planning, coding, and fixing."""
from .base import BaseAdapter, LoopContext


class ImproveAdapter(BaseAdapter):
    """Handles the IMPROVE phase of The Loop."""

    def get_phase(self) -> str:
        return "improve"

    async def execute(self, context: LoopContext, **kwargs) -> LoopContext:
        """
        Execute IMPROVE phase:
        - mode="spec": Write spec document (spec_agents/writer)
        - mode="plan": Create implementation plan (agents/planner)
        - mode="code": Implement subtasks (agents/coder)
        - mode="fix": Fix QA issues (agents/qa_fixer)
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
        """Use spec_writer to create spec document."""
        from spec_agents.writer import SpecWriter

        writer = SpecWriter(
            project_dir=str(context.project_dir),
            spec_dir=str(context.spec_dir),
        )

        spec = await writer.write(
            requirements=context.artifacts.get("requirements"),
            research=context.artifacts.get("research"),
        )
        context.artifacts["spec"] = spec

        return context.with_phase("validate")

    async def _create_plan(self, context: LoopContext) -> LoopContext:
        """Use planner agent to create implementation plan."""
        from agents.planner import PlannerAgent

        planner = PlannerAgent(
            project_dir=str(context.project_dir),
            spec_dir=str(context.spec_dir),
        )

        plan = await planner.create_plan(context.artifacts.get("spec"))
        context.artifacts["plan"] = plan

        return context

    async def _implement(self, context: LoopContext) -> LoopContext:
        """Use coder agent to implement subtasks."""
        from agents.coder import CoderAgent

        coder = CoderAgent(
            project_dir=str(context.project_dir),
            spec_dir=str(context.spec_dir),
            sandbox_id=context.sandbox_id,
        )

        implementation = await coder.implement(context.artifacts.get("plan"))
        context.artifacts["implementation"] = implementation

        return context.with_phase("validate")

    async def _fix_issues(self, context: LoopContext) -> LoopContext:
        """Use qa_fixer agent to fix issues."""
        from agents.qa_fixer import QAFixerAgent

        fixer = QAFixerAgent(
            project_dir=str(context.project_dir),
            spec_dir=str(context.spec_dir),
            sandbox_id=context.sandbox_id,
        )

        fix_result = await fixer.fix(context.artifacts.get("qa_result"))
        context.artifacts["fix_result"] = fix_result

        return context.with_phase("validate")
```

### Step 7: Create Task Manager
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/orchestrator/task_manager.py`:

```python
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

    def _slugify(self, text: str) -> str:
        """Create a slug from text."""
        return "-".join(text.lower().split()[:5])
```

### Step 8: Create init files
```bash
touch /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/__init__.py
touch /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/adapters/__init__.py
touch /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/orchestrator/__init__.py
touch /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/api/__init__.py
touch /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/cli/__init__.py
touch /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/tests/__init__.py
```

### Step 9: Create README
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/README.md`:

```markdown
# AutoCoder Module

**Autonomous Coding through The Loop**

AutoCoder wraps Auto-Claude's multi-agent coding framework for CommandCenter, enabling autonomous software development that participates in The Loop.

## Overview

```
DISCOVER → VALIDATE → IMPROVE → DISCOVER...
    ↓          ↓          ↓
 Gatherer   Critic    Planner
 Researcher   QA      Coder
                      Fixer
```

## Quick Start

```bash
# From hub/modules/auto-coder/
uv sync

# Create a coding task
uv run auto-coder create "Add user authentication to the API"

# Check status
uv run auto-coder status <task-id>

# Approve and merge
uv run auto-coder approve <task-id>
```

## API

```bash
# Create task
curl -X POST http://localhost:8000/api/auto-coder/tasks \
  -H "Content-Type: application/json" \
  -d '{"description": "Add rate limiting", "complexity": "standard"}'

# Check status
curl http://localhost:8000/api/auto-coder/tasks/<task-id>
```

## Architecture

### The Loop Adapters

| Adapter | Phase | Auto-Claude Agents |
|---------|-------|-------------------|
| `DiscoverAdapter` | DISCOVER | gatherer, researcher |
| `ValidateAdapter` | VALIDATE | critic, qa_reviewer |
| `ImproveAdapter` | IMPROVE | writer, planner, coder, qa_fixer |

### Integration Points

- **E2B Sandboxes**: Uses `tools/agent-sandboxes/` for isolated execution
- **KnowledgeBeast**: Fetches context for coding tasks
- **Graphiti Memory**: Cross-session insights from Auto-Claude

## Configuration

```bash
# Required
ANTHROPIC_API_KEY=your-key
E2B_API_KEY=your-key

# Optional
GRAPHITI_ENABLED=true
AUTO_CODER_MODEL=claude-sonnet-4-5-20250929
```

## Dogfooding

Use AutoCoder to improve CommandCenter itself:

```bash
uv run auto-coder create "Implement VISLZR Sprint 3 mind map nodes" \
  --project /Users/danielconnolly/Projects/CommandCenter \
  --complexity complex \
  --parallel 3
```

## Dependencies

- `integrations/auto-claude-core/` - Auto-Claude agent intelligence
- `tools/agent-sandboxes/` - E2B sandbox infrastructure
- `backend/` - CommandCenter API integration

---

*Part of CommandCenter - The AI Operating System for Knowledge Work*
```

### Step 10: Git Add
```bash
cd /Users/danielconnolly/Projects/CommandCenter
git add hub/modules/auto-coder/
git status
```

## Success Criteria
- [ ] Directory structure created
- [ ] pyproject.toml with dependencies
- [ ] Base adapter with LoopContext
- [ ] Three phase adapters (discover, validate, improve)
- [ ] Task manager orchestrating The Loop
- [ ] README with usage docs
- [ ] Files staged for commit

## What's Next (Don't Do Yet)
After I verify the module structure:
1. Add API routes (FastAPI)
2. Add CLI commands (Click)
3. Create sandbox bridge to E2B
4. Add tests
5. Dogfood by running on CommandCenter itself
```

---

## Next Steps After Module Creation

1. **Wire up API routes** - Expose through CommandCenter's main API
2. **Create sandbox bridge** - Connect to existing E2B infrastructure
3. **Add VISLZR node config** - Make it visible in the mind map
4. **Dogfood** - Use AutoCoder to build VISLZR Sprint 3

---

## Synergy Points

| CommandCenter | AutoCoder Uses |
|---------------|----------------|
| KnowledgeBeast | Context for coding tasks |
| E2B Sandboxes (obox) | Isolated execution |
| VISLZR | Task creation UI, progress visualization |
| Graphiti (via Auto-Claude) | Cross-session memory |
| The Loop | Orchestration pattern |
