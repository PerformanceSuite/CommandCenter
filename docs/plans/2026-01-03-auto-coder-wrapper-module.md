# AutoCoder Module - Composable Design (v2)

**Date**: 2026-01-03
**Status**: Ready for Execution
**Revision**: v2 - Composable Architecture
**Supersedes**: Previous monolithic wrapper design

## Design Principles

This design follows CommandCenter's composability mindset:

1. **Everything is a building block** - Each capability is independently usable
2. **Agents are primary consumers** - MCP tools first, human UI second
3. **Intent crystallizes over time** - Start vague, refine iteratively
4. **Skills API integration** - Capabilities are discoverable, not hardcoded
5. **Loose coupling** - Interfaces over implementations
6. **The Loop is optional** - Agents can use full orchestration OR pick individual tools

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        MCP Tool Layer                               │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ gather_reqs │ │ research    │ │ write_spec  │ │ critique    │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐ ┌─────────────┐   │
│  │ plan_impl   │ │ code_task   │ │ review_qa   │ │ fix_issues  │   │
│  └─────────────┘ └─────────────┘ └─────────────┘ └─────────────┘   │
└─────────────────────────────────────────────────────────────────────┘
                              ↑
                    Agents pick what they need
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                      Skills Registry                                │
│  GET /api/skills?category=coding → returns available capabilities   │
│  Each skill has: id, description, inputs, outputs, examples         │
└─────────────────────────────────────────────────────────────────────┘
                              ↑
                    Optional orchestration
                              ↓
┌─────────────────────────────────────────────────────────────────────┐
│                    Loop Orchestrator (Optional)                     │
│  Agents CAN use this for full DISCOVER→VALIDATE→IMPROVE flow       │
│  Or they can compose individual tools themselves                    │
└─────────────────────────────────────────────────────────────────────┘
```

## Module Structure

```
hub/modules/auto-coder/
├── README.md
├── pyproject.toml
├── SKILL.md                        # Skill manifest for discovery
│
├── src/
│   ├── __init__.py
│   ├── config.py
│   │
│   ├── skills/                     # Individual composable skills
│   │   ├── __init__.py
│   │   ├── base.py                 # Skill base class + registry
│   │   ├── gather_requirements.py  # DISCOVER: Gather reqs
│   │   ├── research_approach.py    # DISCOVER: Research solutions
│   │   ├── write_spec.py           # IMPROVE: Write spec doc
│   │   ├── critique_spec.py        # VALIDATE: Self-critique
│   │   ├── plan_implementation.py  # IMPROVE: Create plan
│   │   ├── code_subtask.py         # IMPROVE: Implement code
│   │   ├── review_qa.py            # VALIDATE: QA review
│   │   └── fix_issues.py           # IMPROVE: Fix QA issues
│   │
│   ├── mcp/                        # MCP tool provider
│   │   ├── __init__.py
│   │   ├── provider.py             # Exposes skills as MCP tools
│   │   └── schemas.py              # Tool input/output schemas
│   │
│   ├── orchestrator/               # OPTIONAL Loop orchestration
│   │   ├── __init__.py
│   │   ├── loop_runner.py          # Full Loop automation
│   │   └── context.py              # Shared context between skills
│   │
│   ├── api/                        # REST API (wraps MCP for HTTP)
│   │   ├── __init__.py
│   │   └── routes.py
│   │
│   └── bridges/                    # Integration bridges
│       ├── __init__.py
│       ├── sandbox.py              # E2B sandbox bridge
│       ├── memory.py               # KnowledgeBeast/Graphiti bridge
│       └── auto_claude.py          # Auto-Claude core bridge
│
├── prompts/                        # Prompt templates (queryable)
│   ├── gather_requirements.md
│   ├── research_approach.md
│   ├── write_spec.md
│   ├── critique_spec.md
│   ├── plan_implementation.md
│   ├── code_subtask.md
│   ├── review_qa.md
│   └── fix_issues.md
│
└── tests/
    └── ...
```

## Key Difference: Skills as Building Blocks

### Skill Base Class

```python
# src/skills/base.py
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, TypeVar, Generic
from pydantic import BaseModel

T_Input = TypeVar("T_Input", bound=BaseModel)
T_Output = TypeVar("T_Output", bound=BaseModel)


@dataclass
class SkillMetadata:
    """Metadata for skill discovery."""
    id: str
    name: str
    description: str
    category: str  # discover, validate, improve
    phase: str     # The Loop phase
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    examples: list[dict] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)  # Other skill IDs


class Skill(ABC, Generic[T_Input, T_Output]):
    """Base class for composable coding skills."""

    @classmethod
    @abstractmethod
    def metadata(cls) -> SkillMetadata:
        """Return skill metadata for discovery."""
        pass

    @abstractmethod
    async def execute(self, input: T_Input, context: dict | None = None) -> T_Output:
        """Execute the skill."""
        pass

    def get_prompt(self) -> str:
        """Get the prompt template for this skill."""
        prompt_path = Path(__file__).parents[2] / "prompts" / f"{self.metadata().id}.md"
        return prompt_path.read_text() if prompt_path.exists() else ""


# Global skill registry
_SKILL_REGISTRY: dict[str, type[Skill]] = {}


def register_skill(skill_cls: type[Skill]) -> type[Skill]:
    """Decorator to register a skill."""
    metadata = skill_cls.metadata()
    _SKILL_REGISTRY[metadata.id] = skill_cls
    return skill_cls


def get_skill(skill_id: str) -> type[Skill] | None:
    """Get a skill by ID."""
    return _SKILL_REGISTRY.get(skill_id)


def list_skills(category: str | None = None) -> list[SkillMetadata]:
    """List all registered skills, optionally filtered by category."""
    skills = [cls.metadata() for cls in _SKILL_REGISTRY.values()]
    if category:
        skills = [s for s in skills if s.category == category]
    return skills
```

### Example Skill: Gather Requirements

```python
# src/skills/gather_requirements.py
from pydantic import BaseModel
from .base import Skill, SkillMetadata, register_skill


class GatherRequirementsInput(BaseModel):
    """Input for requirements gathering."""
    task_description: str
    project_dir: str
    context: dict | None = None  # Optional context from previous skills


class GatherRequirementsOutput(BaseModel):
    """Output from requirements gathering."""
    requirements: list[str]
    user_stories: list[dict]
    acceptance_criteria: list[str]
    complexity_estimate: str  # simple, standard, complex
    suggested_next_skills: list[str]  # Composability hint


@register_skill
class GatherRequirementsSkill(Skill[GatherRequirementsInput, GatherRequirementsOutput]):
    """Gather and structure requirements from a task description."""

    @classmethod
    def metadata(cls) -> SkillMetadata:
        return SkillMetadata(
            id="gather_requirements",
            name="Gather Requirements",
            description="Analyze a task description and extract structured requirements",
            category="discover",
            phase="DISCOVER",
            input_schema=GatherRequirementsInput,
            output_schema=GatherRequirementsOutput,
            examples=[
                {
                    "input": {"task_description": "Add user authentication", "project_dir": "."},
                    "output": {"requirements": ["User login", "User logout", "Password reset"], "complexity_estimate": "standard"}
                }
            ],
            depends_on=[],  # No dependencies - can be used standalone
        )

    async def execute(
        self,
        input: GatherRequirementsInput,
        context: dict | None = None
    ) -> GatherRequirementsOutput:
        """Execute requirements gathering."""
        # Bridge to Auto-Claude's gatherer
        from ..bridges.auto_claude import get_gatherer

        gatherer = get_gatherer(input.project_dir)
        result = await gatherer.gather(input.task_description)

        return GatherRequirementsOutput(
            requirements=result.get("requirements", []),
            user_stories=result.get("user_stories", []),
            acceptance_criteria=result.get("acceptance_criteria", []),
            complexity_estimate=result.get("complexity", "standard"),
            suggested_next_skills=["research_approach", "write_spec"],  # Hint for agents
        )
```

## MCP Tool Provider

```python
# src/mcp/provider.py
"""Expose skills as MCP tools for agent consumption."""
from mcp import Tool, ToolProvider
from ..skills.base import list_skills, get_skill


class AutoCoderMCPProvider(ToolProvider):
    """MCP provider that exposes all registered skills as tools."""

    def list_tools(self) -> list[Tool]:
        """List all available tools (one per skill)."""
        tools = []
        for skill_meta in list_skills():
            tools.append(Tool(
                name=f"auto_coder_{skill_meta.id}",
                description=skill_meta.description,
                input_schema=skill_meta.input_schema.model_json_schema(),
            ))
        return tools

    async def call_tool(self, name: str, arguments: dict) -> dict:
        """Execute a skill by tool name."""
        # Extract skill ID from tool name
        skill_id = name.replace("auto_coder_", "")
        skill_cls = get_skill(skill_id)

        if not skill_cls:
            return {"error": f"Unknown skill: {skill_id}"}

        skill = skill_cls()
        input_model = skill_cls.metadata().input_schema

        try:
            input_data = input_model(**arguments)
            result = await skill.execute(input_data)
            return result.model_dump()
        except Exception as e:
            return {"error": str(e)}


# Also expose via Skills API
def register_with_skills_api():
    """Register all skills with CommandCenter's Skills API."""
    from commandcenter.skills import register_skill_provider

    for skill_meta in list_skills():
        register_skill_provider(
            skill_id=f"auto-coder/{skill_meta.id}",
            category="coding",
            metadata={
                "name": skill_meta.name,
                "description": skill_meta.description,
                "phase": skill_meta.phase,
                "input_schema": skill_meta.input_schema.model_json_schema(),
                "output_schema": skill_meta.output_schema.model_json_schema(),
                "examples": skill_meta.examples,
                "depends_on": skill_meta.depends_on,
            }
        )
```

## SKILL.md Manifest

```markdown
# AutoCoder Skills

Composable coding skills for CommandCenter agents.

## Available Skills

### DISCOVER Phase
- `gather_requirements` - Extract structured requirements from task description
- `research_approach` - Research technical approaches and validate dependencies

### VALIDATE Phase
- `critique_spec` - Self-critique specification with ultrathink
- `review_qa` - QA review of implementation against acceptance criteria

### IMPROVE Phase
- `write_spec` - Write structured specification document
- `plan_implementation` - Create subtask-based implementation plan
- `code_subtask` - Implement a single subtask
- `fix_issues` - Fix QA-reported issues

## Usage

### As MCP Tools
```
Agent: Use tool auto_coder_gather_requirements with {"task_description": "Add auth", "project_dir": "."}
```

### Via Skills API
```
GET /api/skills?category=coding
→ Returns all auto-coder skills with schemas

POST /api/skills/auto-coder/gather_requirements/execute
→ Executes the skill
```

### Composing Skills
Agents can chain skills however they want:
```
1. gather_requirements → get structured reqs
2. write_spec → create spec (skip research for simple tasks)
3. plan_implementation → get subtasks
4. code_subtask (parallel) → implement each subtask
5. review_qa → validate
6. fix_issues (if needed) → iterate
```

### Full Loop Orchestration (Optional)
For agents that want the full DISCOVER→VALIDATE→IMPROVE loop:
```
POST /api/auto-coder/orchestrate
{"task": "Add auth", "mode": "full_loop"}
```

## Skill Dependencies

```
gather_requirements ──┬──→ research_approach ──┬──→ write_spec
                      └─────────────────────────┘        ↓
                                                   critique_spec
                                                         ↓
                                                 plan_implementation
                                                         ↓
                                                   code_subtask
                                                         ↓
                                                    review_qa
                                                         ↓
                                                   fix_issues (if needed)
```

Skills advertise `suggested_next_skills` in their output for agent guidance.
```

## Optional Loop Orchestrator

The orchestrator is **optional** - agents can use it for convenience or compose skills themselves:

```python
# src/orchestrator/loop_runner.py
"""Optional Loop orchestrator - agents can use this OR compose skills directly."""
from ..skills.base import get_skill
from .context import LoopContext


class LoopRunner:
    """
    Runs the full DISCOVER→VALIDATE→IMPROVE loop.

    This is OPTIONAL - agents can also:
    - Call individual skills via MCP tools
    - Compose skills in their own order
    - Skip phases they don't need
    """

    async def run_full_loop(self, task_description: str, project_dir: str) -> dict:
        """Run the complete loop. Convenience method for agents that want automation."""
        context = LoopContext(task_description=task_description, project_dir=project_dir)

        # DISCOVER
        gather = get_skill("gather_requirements")()
        context.requirements = await gather.execute(GatherRequirementsInput(
            task_description=task_description,
            project_dir=project_dir,
        ))

        # ... rest of loop

        return context.to_dict()

    async def run_phase(self, phase: str, context: LoopContext) -> LoopContext:
        """Run a single phase. Agents can call this for partial automation."""
        if phase == "discover":
            # Run discover skills
            pass
        elif phase == "validate":
            # Run validate skills
            pass
        elif phase == "improve":
            # Run improve skills
            pass
        return context
```

## Composability Benefits

| Scenario | Monolithic Design | Composable Design |
|----------|-------------------|-------------------|
| Simple fix | Must run full pipeline | Agent calls `code_subtask` directly |
| Research only | Can't isolate | Agent calls `research_approach` only |
| Custom flow | Stuck with TaskManager | Agent composes skills in any order |
| Parallel coding | Hidden inside orchestrator | Agent spawns N `code_subtask` calls |
| Partial context | Must have full LoopContext | Each skill takes minimal input |
| Discovery | Hidden implementation | `GET /api/skills?category=coding` |

## Agent Consumption Example

An agent discovering and using AutoCoder skills:

```
Agent: What coding skills are available?
→ GET /api/skills?category=coding
← [gather_requirements, research_approach, write_spec, ...]

Agent: I have a simple bug fix, I'll skip discovery and just code it.
→ Use tool auto_coder_code_subtask with {
    "subtask": "Fix null pointer in auth.py line 42",
    "project_dir": ".",
    "context": {"file": "auth.py", "line": 42}
  }
← {"implementation": "...", "files_changed": ["auth.py"]}

Agent: Now let me verify it works.
→ Use tool auto_coder_review_qa with {
    "implementation": "...",
    "acceptance_criteria": ["No null pointer exception"]
  }
← {"passed": true, "notes": "Fix verified"}
```

---

## Claude Code Prompt

Copy everything below the line and paste into Claude Code:

---

```
# AutoCoder Composable Module Creation

## Context
Creating the AutoCoder module with a composable architecture where each capability is an independent skill that agents can discover and use via MCP tools or Skills API.

## Task
Create the composable AutoCoder module structure:

### Step 1: Create Directory Structure
```bash
mkdir -p /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/{src/{skills,mcp,orchestrator,api,bridges},prompts,tests}
```

### Step 2: Create pyproject.toml
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/pyproject.toml`:

```toml
[project]
name = "commandcenter-auto-coder"
version = "0.1.0"
description = "Composable autonomous coding skills for CommandCenter"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "pydantic>=2.5.0",
    "fastapi>=0.109.0",
    "httpx>=0.26.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

### Step 3: Create Skill Base Class
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/skills/base.py`:

```python
"""Base classes for composable coding skills."""
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, TypeVar, Generic
from pydantic import BaseModel

T_Input = TypeVar("T_Input", bound=BaseModel)
T_Output = TypeVar("T_Output", bound=BaseModel)


@dataclass
class SkillMetadata:
    """Metadata for skill discovery via Skills API."""
    id: str
    name: str
    description: str
    category: str  # discover, validate, improve
    phase: str     # The Loop phase
    input_schema: type[BaseModel]
    output_schema: type[BaseModel]
    examples: list[dict] = field(default_factory=list)
    depends_on: list[str] = field(default_factory=list)


class Skill(ABC, Generic[T_Input, T_Output]):
    """
    Base class for composable coding skills.

    Each skill is:
    - Independently usable (no required orchestration)
    - Discoverable via Skills API
    - Callable via MCP tools
    - Composable with other skills
    """

    @classmethod
    @abstractmethod
    def metadata(cls) -> SkillMetadata:
        """Return skill metadata for discovery."""
        pass

    @abstractmethod
    async def execute(self, input: T_Input, context: dict | None = None) -> T_Output:
        """
        Execute the skill.

        Args:
            input: Validated input data
            context: Optional context from previous skills (loose coupling)

        Returns:
            Skill output with suggested_next_skills for composability hints
        """
        pass

    def get_prompt(self) -> str:
        """Get the prompt template for this skill."""
        prompt_path = Path(__file__).parents[2] / "prompts" / f"{self.metadata().id}.md"
        return prompt_path.read_text() if prompt_path.exists() else ""


# ============================================================================
# Skill Registry - enables discovery
# ============================================================================

_SKILL_REGISTRY: dict[str, type[Skill]] = {}


def register_skill(skill_cls: type[Skill]) -> type[Skill]:
    """Decorator to register a skill for discovery."""
    metadata = skill_cls.metadata()
    _SKILL_REGISTRY[metadata.id] = skill_cls
    return skill_cls


def get_skill(skill_id: str) -> type[Skill] | None:
    """Get a skill class by ID."""
    return _SKILL_REGISTRY.get(skill_id)


def list_skills(category: str | None = None, phase: str | None = None) -> list[SkillMetadata]:
    """
    List all registered skills.

    Args:
        category: Filter by category (discover, validate, improve)
        phase: Filter by Loop phase (DISCOVER, VALIDATE, IMPROVE)
    """
    skills = [cls.metadata() for cls in _SKILL_REGISTRY.values()]

    if category:
        skills = [s for s in skills if s.category == category]
    if phase:
        skills = [s for s in skills if s.phase == phase]

    return skills


def get_skill_schema(skill_id: str) -> dict | None:
    """Get JSON schema for a skill's input/output."""
    skill_cls = get_skill(skill_id)
    if not skill_cls:
        return None

    meta = skill_cls.metadata()
    return {
        "id": meta.id,
        "input_schema": meta.input_schema.model_json_schema(),
        "output_schema": meta.output_schema.model_json_schema(),
    }
```

### Step 4: Create Example Skills
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/skills/gather_requirements.py`:

```python
"""DISCOVER skill: Gather and structure requirements."""
from pydantic import BaseModel, Field
from .base import Skill, SkillMetadata, register_skill


class GatherRequirementsInput(BaseModel):
    """Input for requirements gathering."""
    task_description: str = Field(..., description="Natural language task description")
    project_dir: str = Field(default=".", description="Project directory path")
    context: dict | None = Field(default=None, description="Optional context from previous skills")


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
```

Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/skills/code_subtask.py`:

```python
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
```

### Step 5: Create Skills __init__.py (auto-registers all skills)
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/skills/__init__.py`:

```python
"""
AutoCoder Skills - Composable coding capabilities.

Each skill is:
- Independently usable
- Discoverable via list_skills()
- Callable via MCP tools
- Composable with other skills

Usage:
    from auto_coder.skills import list_skills, get_skill

    # Discovery
    skills = list_skills(category="discover")

    # Get and use a skill
    skill_cls = get_skill("gather_requirements")
    skill = skill_cls()
    result = await skill.execute(input_data)
"""

from .base import (
    Skill,
    SkillMetadata,
    register_skill,
    get_skill,
    list_skills,
    get_skill_schema,
)

# Import all skills to trigger registration
from . import gather_requirements
from . import code_subtask
# Add more as they're created:
# from . import research_approach
# from . import write_spec
# from . import critique_spec
# from . import plan_implementation
# from . import review_qa
# from . import fix_issues

__all__ = [
    "Skill",
    "SkillMetadata",
    "register_skill",
    "get_skill",
    "list_skills",
    "get_skill_schema",
]
```

### Step 6: Create MCP Provider
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/mcp/provider.py`:

```python
"""MCP Tool Provider - exposes skills as MCP tools for agents."""
from typing import Any
from ..skills import list_skills, get_skill


class AutoCoderMCPProvider:
    """
    Exposes all registered skills as MCP tools.

    Each skill becomes a tool named: auto_coder_{skill_id}

    Agents can discover tools and call them directly without
    going through the Loop orchestrator.
    """

    def list_tools(self) -> list[dict]:
        """List all available tools (one per skill)."""
        tools = []
        for skill_meta in list_skills():
            tools.append({
                "name": f"auto_coder_{skill_meta.id}",
                "description": skill_meta.description,
                "input_schema": skill_meta.input_schema.model_json_schema(),
                "metadata": {
                    "category": skill_meta.category,
                    "phase": skill_meta.phase,
                    "depends_on": skill_meta.depends_on,
                    "examples": skill_meta.examples,
                }
            })
        return tools

    async def call_tool(self, name: str, arguments: dict) -> dict[str, Any]:
        """Execute a skill by tool name."""
        # Extract skill ID from tool name
        if not name.startswith("auto_coder_"):
            return {"error": f"Unknown tool format: {name}"}

        skill_id = name.replace("auto_coder_", "")
        skill_cls = get_skill(skill_id)

        if not skill_cls:
            available = [s.id for s in list_skills()]
            return {"error": f"Unknown skill: {skill_id}", "available": available}

        # Instantiate and execute
        skill = skill_cls()
        input_model = skill_cls.metadata().input_schema

        try:
            input_data = input_model(**arguments)
            result = await skill.execute(input_data)
            return {"success": True, "result": result.model_dump()}
        except Exception as e:
            return {"success": False, "error": str(e)}


# Singleton for easy import
mcp_provider = AutoCoderMCPProvider()
```

### Step 7: Create Bridges
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/bridges/__init__.py`:

```python
"""Bridges to external systems."""
from .auto_claude import AutoClaudeBridge
from .sandbox import SandboxBridge

__all__ = ["AutoClaudeBridge", "SandboxBridge"]
```

Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/bridges/auto_claude.py`:

```python
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
```

Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/bridges/sandbox.py`:

```python
"""Bridge to E2B sandbox infrastructure."""
from pathlib import Path


class SandboxBridge:
    """
    Bridge to tools/agent-sandboxes infrastructure.

    Enables isolated code execution in E2B sandboxes.
    """

    def __init__(self):
        self.sandboxes_path = Path(__file__).parents[5] / "tools" / "agent-sandboxes"

    async def create_sandbox(self, repo_url: str, branch: str) -> str:
        """Create an E2B sandbox for isolated execution."""
        # Bridge to existing obox infrastructure
        # Returns sandbox_id
        pass

    async def run_coder(
        self,
        sandbox_id: str,
        subtask: str,
        context: dict | None = None,
    ) -> dict:
        """Run coder agent in sandbox."""
        # Execute in E2B sandbox
        pass

    async def get_files(self, sandbox_id: str, path: str = "/") -> list[str]:
        """Get files from sandbox."""
        pass

    async def destroy_sandbox(self, sandbox_id: str) -> bool:
        """Destroy a sandbox."""
        pass
```

### Step 8: Create remaining __init__ files
```bash
touch /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/__init__.py
touch /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/mcp/__init__.py
touch /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/orchestrator/__init__.py
touch /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/src/api/__init__.py
touch /Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/tests/__init__.py
```

### Step 9: Create SKILL.md manifest
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/SKILL.md`:

```markdown
# AutoCoder Skills

Composable autonomous coding capabilities for CommandCenter agents.

## Philosophy

Each skill is a **building block**, not a monolithic service:
- Independently callable via MCP tools
- Discoverable via Skills API
- Composable in any order
- Optional Loop orchestration

## Available Skills

### DISCOVER Phase
| Skill | Description | Depends On |
|-------|-------------|------------|
| `gather_requirements` | Extract structured requirements from task | - |
| `research_approach` | Research technical approaches | gather_requirements |

### VALIDATE Phase
| Skill | Description | Depends On |
|-------|-------------|------------|
| `critique_spec` | Self-critique with ultrathink | write_spec |
| `review_qa` | QA review against acceptance criteria | code_subtask |

### IMPROVE Phase
| Skill | Description | Depends On |
|-------|-------------|------------|
| `write_spec` | Create spec document | gather_requirements |
| `plan_implementation` | Create subtask plan | write_spec |
| `code_subtask` | Implement one subtask | - (can run standalone) |
| `fix_issues` | Fix QA-reported issues | review_qa |

## MCP Tools

Each skill is exposed as: `auto_coder_{skill_id}`

```
# List available tools
GET /mcp/tools

# Call a tool
POST /mcp/tools/auto_coder_gather_requirements
{"task_description": "Add auth", "project_dir": "."}
```

## Composability Patterns

### Quick Fix (skip discovery)
```
code_subtask → review_qa → [fix_issues if needed]
```

### Full Loop
```
gather_requirements → research_approach → write_spec → critique_spec
→ plan_implementation → code_subtask (parallel) → review_qa → fix_issues
```

### Research Only
```
gather_requirements → research_approach
```

## Output Hints

Each skill output includes `suggested_next_skills` to guide composition:
```json
{
  "requirements": [...],
  "suggested_next_skills": ["research_approach", "write_spec"]
}
```
```

### Step 10: Create README
Create `/Users/danielconnolly/Projects/CommandCenter/hub/modules/auto-coder/README.md`:

```markdown
# AutoCoder Module

**Composable Autonomous Coding for CommandCenter**

AutoCoder provides coding capabilities as composable skills that agents can discover, call, and chain together.

## Design Principles

1. **Everything is a building block** - Each skill is independently usable
2. **Agents are primary consumers** - MCP tools first, human UI second
3. **Intent crystallizes over time** - Start with one skill, add more as needed
4. **Discovery over configuration** - Skills API exposes all capabilities
5. **The Loop is optional** - Use full orchestration OR pick individual skills

## Quick Start

```python
from auto_coder.skills import list_skills, get_skill

# Discover available skills
skills = list_skills(category="discover")
print([s.id for s in skills])  # ['gather_requirements', 'research_approach']

# Use a skill directly
skill = get_skill("gather_requirements")()
result = await skill.execute(GatherRequirementsInput(
    task_description="Add user authentication",
    project_dir="."
))

print(result.requirements)
print(result.suggested_next_skills)  # ['research_approach', 'write_spec']
```

## For Agents (MCP Tools)

```
Agent: What coding tools are available?
→ Lists auto_coder_* tools

Agent: Use auto_coder_gather_requirements with {
    "task_description": "Fix the login bug",
    "project_dir": "."
}
← Returns structured requirements + suggested next skills

Agent: Use auto_coder_code_subtask with {
    "subtask": "Fix null check in auth.py",
    "project_dir": "."
}
← Returns implementation result
```

## Skill Categories

| Phase | Skills |
|-------|--------|
| **DISCOVER** | gather_requirements, research_approach |
| **VALIDATE** | critique_spec, review_qa |
| **IMPROVE** | write_spec, plan_implementation, code_subtask, fix_issues |

## Architecture

```
┌─────────────────────────────────────────────┐
│            MCP Tool Layer                   │
│  auto_coder_* tools (one per skill)         │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│           Skills Registry                   │
│  list_skills(), get_skill(), schemas        │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│              Bridges                        │
│  auto_claude.py (agent logic)               │
│  sandbox.py (E2B isolation)                 │
└─────────────────────────────────────────────┘
```

## Integration Points

- **Auto-Claude Core**: `integrations/auto-claude-core/`
- **E2B Sandboxes**: `tools/agent-sandboxes/`
- **KnowledgeBeast**: Context for coding tasks
- **Skills API**: Registered for discovery

---

*Part of CommandCenter - The AI Operating System for Knowledge Work*
```

### Step 11: Git Add
```bash
cd /Users/danielconnolly/Projects/CommandCenter
git add hub/modules/auto-coder/
git status
```

## Success Criteria
- [ ] Directory structure with skills/, mcp/, bridges/
- [ ] Skill base class with registry pattern
- [ ] Example skills (gather_requirements, code_subtask)
- [ ] MCP provider exposing skills as tools
- [ ] Bridges to Auto-Claude and E2B
- [ ] SKILL.md manifest for discovery
- [ ] README with composability docs
- [ ] Files staged for commit

## Files Created
- hub/modules/auto-coder/pyproject.toml
- hub/modules/auto-coder/SKILL.md
- hub/modules/auto-coder/README.md
- hub/modules/auto-coder/src/skills/base.py
- hub/modules/auto-coder/src/skills/gather_requirements.py
- hub/modules/auto-coder/src/skills/code_subtask.py
- hub/modules/auto-coder/src/skills/__init__.py
- hub/modules/auto-coder/src/mcp/provider.py
- hub/modules/auto-coder/src/bridges/auto_claude.py
- hub/modules/auto-coder/src/bridges/sandbox.py
```

---

## Summary: Composable vs Monolithic

| Aspect | Previous (Monolithic) | New (Composable) |
|--------|----------------------|------------------|
| Unit of work | Task (full pipeline) | Skill (single capability) |
| Discovery | None | Skills API + MCP tools |
| Agent usage | "Create task, wait for completion" | "Pick skills, compose freely" |
| Flexibility | Rigid phases | Any order, skip phases |
| Loop | Required | Optional convenience |
| Coupling | Tight (TaskManager owns all) | Loose (skills are independent) |
