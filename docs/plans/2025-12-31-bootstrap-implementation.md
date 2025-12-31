# Bootstrap Implementation Plan: Agent Self-Build Foundation

**Created**: 2025-12-31
**Status**: 🟢 Active Sprint
**Goal**: Build minimum infrastructure so coding agents can build the rest

---

## Philosophy

> Build just enough that the agents can build the rest.

We are NOT building:
- Full UI
- Complete workflows
- Perfect abstractions

We ARE building:
- Working Prompt Improver
- Persona storage (file-based, simple)
- AgentExecutor that can run E2B sandboxes
- CLI to trigger agent workflows

**Success Criteria**: We can run a command that spawns coding agents to build the Persona Management UI, and they produce a working PR.

---

## The Four Bootstrap Components

```
┌────────────────────────────────────────────────────────────────────┐
│  BOOTSTRAP COMPONENTS (Human-Built)                                │
│                                                                    │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐  ┌────────┐ │
│  │   Prompt     │  │   Persona    │  │    Agent     │  │  CLI   │ │
│  │  Improver    │→ │    Store     │→ │   Executor   │→ │ Runner │ │
│  └──────────────┘  └──────────────┘  └──────────────┘  └────────┘ │
│                                                                    │
│  "Make prompts    "Store agent     "Run agents in   "Trigger     │
│   good"            definitions"     E2B sandboxes"   workflows"   │
└────────────────────────────────────────────────────────────────────┘
```

---

## Component 1: Prompt Improver

**Time**: 2 hours
**Files**:
- `backend/libs/agent_framework/prompt_improver.py`
- `backend/app/routers/prompts.py`

### Implementation

```python
# backend/libs/agent_framework/prompt_improver.py

"""
Minimal Prompt Improver - analyzes and improves agent prompts.
"""

from dataclasses import dataclass
from typing import Optional
import json
import os

# Use LLMGateway if available, else direct API call
try:
    from libs.llm_gateway import LLMGateway
except ImportError:
    LLMGateway = None


@dataclass
class PromptAnalysis:
    original: str
    issues: list[dict]
    scores: dict[str, int]
    improved: Optional[str] = None


ANALYZE_PROMPT = '''Analyze this agent prompt for issues:

```
{prompt}
```

Return JSON:
```json
{{
    "issues": [
        {{"type": "conflict|ambiguity|missing_output|verbosity", "severity": "high|medium|low", "description": "...", "fix": "..."}}
    ],
    "scores": {{"clarity": 0-100, "structure": 0-100, "completeness": 0-100}},
    "improved_prompt": "Full improved version if score < 80, else null"
}}
```'''


class PromptImprover:
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("ANTHROPIC_API_KEY")

    async def analyze(self, prompt: str) -> PromptAnalysis:
        """Analyze prompt and optionally improve it."""
        import anthropic

        client = anthropic.AsyncAnthropic(api_key=self.api_key)

        response = await client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[{"role": "user", "content": ANALYZE_PROMPT.format(prompt=prompt)}]
        )

        content = response.content[0].text

        # Parse JSON from response
        try:
            start = content.find("{")
            end = content.rfind("}") + 1
            data = json.loads(content[start:end])
        except:
            data = {"issues": [], "scores": {"clarity": 50, "structure": 50, "completeness": 50}}

        return PromptAnalysis(
            original=prompt,
            issues=data.get("issues", []),
            scores=data.get("scores", {}),
            improved=data.get("improved_prompt"),
        )

    def quick_check(self, prompt: str) -> dict:
        """Fast local check, no API call."""
        prompt_lower = prompt.lower()

        return {
            "has_role": any(k in prompt_lower for k in ["you are", "your role", "act as"]),
            "has_output_format": any(k in prompt_lower for k in ["output", "respond with", "return", "json"]),
            "has_constraints": any(k in prompt_lower for k in ["do not", "never", "always", "must"]),
            "word_count": len(prompt.split()),
            "suggestions": self._quick_suggestions(prompt_lower),
        }

    def _quick_suggestions(self, prompt_lower: str) -> list[str]:
        suggestions = []
        if "you are" not in prompt_lower and "your role" not in prompt_lower:
            suggestions.append("Add role definition at start")
        if "output" not in prompt_lower and "json" not in prompt_lower:
            suggestions.append("Specify output format")
        if len(prompt_lower.split()) > 1500:
            suggestions.append("Consider condensing - very long prompt")
        return suggestions
```

### API Endpoint

```python
# backend/app/routers/prompts.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/api/v1/prompts", tags=["prompts"])


class PromptRequest(BaseModel):
    prompt: str


@router.post("/quick-check")
async def quick_check(request: PromptRequest):
    """Fast local prompt check - no API call."""
    from libs.agent_framework.prompt_improver import PromptImprover
    improver = PromptImprover()
    return improver.quick_check(request.prompt)


@router.post("/analyze")
async def analyze(request: PromptRequest):
    """Full AI-powered analysis."""
    from libs.agent_framework.prompt_improver import PromptImprover
    improver = PromptImprover()
    result = await improver.analyze(request.prompt)
    return {
        "issues": result.issues,
        "scores": result.scores,
        "improved": result.improved,
    }
```

### Done When
- [ ] `POST /api/v1/prompts/quick-check` returns instant feedback
- [ ] `POST /api/v1/prompts/analyze` returns issues + improved prompt
- [ ] Can improve a bad prompt and get measurably better output

---

## Component 2: Persona Store

**Time**: 1 hour
**Files**:
- `backend/libs/agent_framework/personas/` (directory)
- `backend/libs/agent_framework/persona_store.py`

### Implementation

File-based storage. No database needed for bootstrap. Each persona is a YAML file.

```
backend/libs/agent_framework/personas/
├── _index.yaml           # Registry of all personas
├── backend-coder.yaml
├── frontend-coder.yaml
├── reviewer.yaml
├── challenger.yaml
└── arbiter.yaml
```

```python
# backend/libs/agent_framework/persona_store.py

"""
Simple file-based persona storage.
Personas are YAML files - easy to edit, version control, improve.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional
import yaml


@dataclass
class Persona:
    name: str
    display_name: str
    description: str
    system_prompt: str
    category: str = "custom"  # assessment, verification, coding, synthesis
    model: str = "claude-sonnet-4-20250514"
    temperature: float = 0.7
    requires_sandbox: bool = False
    tags: list[str] = field(default_factory=list)


PERSONAS_DIR = Path(__file__).parent / "personas"


class PersonaStore:
    def __init__(self, personas_dir: Optional[Path] = None):
        self.dir = personas_dir or PERSONAS_DIR
        self.dir.mkdir(parents=True, exist_ok=True)

    def list(self, category: Optional[str] = None) -> list[Persona]:
        """List all personas, optionally filtered by category."""
        personas = []
        for f in self.dir.glob("*.yaml"):
            if f.name.startswith("_"):
                continue
            try:
                personas.append(self.get(f.stem))
            except:
                pass

        if category:
            personas = [p for p in personas if p.category == category]

        return sorted(personas, key=lambda p: p.name)

    def get(self, name: str) -> Persona:
        """Get persona by name."""
        path = self.dir / f"{name}.yaml"
        if not path.exists():
            raise FileNotFoundError(f"Persona not found: {name}")

        with open(path) as f:
            data = yaml.safe_load(f)

        return Persona(**data)

    def save(self, persona: Persona) -> None:
        """Save persona to file."""
        path = self.dir / f"{persona.name}.yaml"

        data = {
            "name": persona.name,
            "display_name": persona.display_name,
            "description": persona.description,
            "category": persona.category,
            "model": persona.model,
            "temperature": persona.temperature,
            "requires_sandbox": persona.requires_sandbox,
            "tags": persona.tags,
            "system_prompt": persona.system_prompt,
        }

        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)

    def delete(self, name: str) -> None:
        """Delete persona."""
        path = self.dir / f"{name}.yaml"
        if path.exists():
            path.unlink()
```

### Bootstrap Personas

```yaml
# backend/libs/agent_framework/personas/backend-coder.yaml

name: backend-coder
display_name: Backend Coder
description: Expert Python/FastAPI developer for backend implementation
category: coding
model: claude-sonnet-4-20250514
temperature: 0.3
requires_sandbox: true
tags: [coding, backend, python, fastapi]

system_prompt: |
  You are an expert Backend Developer specializing in Python and FastAPI.

  ## Your Expertise
  - Python 3.11+ with type hints
  - FastAPI with async/await patterns
  - SQLAlchemy 2.0 with async sessions
  - Pydantic v2 for validation
  - Clean architecture and SOLID principles

  ## Your Task
  When given a coding task:
  1. Read the relevant existing code first
  2. Follow existing patterns and conventions
  3. Write clean, typed, tested code
  4. Create or update tests for your changes
  5. Commit with conventional commit messages

  ## Output
  - Create/modify files directly
  - Run tests to verify changes work
  - Create a PR when complete

  ## Constraints
  - Never break existing tests
  - Follow the project's existing patterns
  - Keep changes focused and minimal
  - Add docstrings to public functions
```

```yaml
# backend/libs/agent_framework/personas/frontend-coder.yaml

name: frontend-coder
display_name: Frontend Coder
description: Expert React/TypeScript developer for frontend implementation
category: coding
model: claude-sonnet-4-20250514
temperature: 0.3
requires_sandbox: true
tags: [coding, frontend, react, typescript]

system_prompt: |
  You are an expert Frontend Developer specializing in React and TypeScript.

  ## Your Expertise
  - React 18+ with hooks
  - TypeScript with strict mode
  - Tailwind CSS for styling
  - React Query for data fetching
  - Component composition patterns

  ## Your Task
  When given a coding task:
  1. Read existing components for patterns
  2. Follow the project's component structure
  3. Write typed, accessible components
  4. Use existing UI patterns (buttons, cards, etc.)
  5. Test in the browser before committing

  ## Output
  - Create/modify files directly
  - Ensure no TypeScript errors
  - Create a PR when complete

  ## Constraints
  - Match existing styling patterns
  - Keep components focused and reusable
  - Use semantic HTML
  - Ensure responsive design
```

```yaml
# backend/libs/agent_framework/personas/reviewer.yaml

name: reviewer
display_name: Code Reviewer
description: Reviews code for quality, bugs, and improvements
category: verification
model: claude-sonnet-4-20250514
temperature: 0.5
requires_sandbox: true
tags: [review, quality, verification]

system_prompt: |
  You are an expert Code Reviewer.

  ## Your Task
  Review the code changes and provide feedback on:
  1. Correctness - Does it work? Any bugs?
  2. Style - Does it follow project conventions?
  3. Security - Any vulnerabilities?
  4. Performance - Any obvious issues?
  5. Tests - Adequate coverage?

  ## Process
  1. Read the diff/changes carefully
  2. Check out the branch and run tests
  3. Look for edge cases
  4. Provide specific, actionable feedback

  ## Output Format
  ```json
  {
    "verdict": "approve|request_changes|comment",
    "summary": "Overall assessment",
    "issues": [
      {"severity": "high|medium|low", "file": "...", "line": N, "issue": "...", "suggestion": "..."}
    ],
    "praise": ["Things done well"]
  }
  ```

  ## Constraints
  - Be constructive, not harsh
  - Focus on important issues first
  - Acknowledge good patterns
  - Suggest specific fixes, not vague criticism
```

### Done When
- [ ] `PersonaStore().list()` returns all personas
- [ ] `PersonaStore().get("backend-coder")` returns the persona
- [ ] At least 3 coding personas defined (backend, frontend, reviewer)
- [ ] Personas can be edited as YAML files

---

## Component 3: Agent Executor + E2B

**Time**: 3 hours
**Files**:
- `backend/libs/agent_framework/executor.py`
- `backend/libs/agent_framework/sandbox.py`

### Implementation

Minimal executor that can:
1. Load a persona
2. Spawn an E2B sandbox
3. Run Claude Code with the persona's prompt
4. Return results

```python
# backend/libs/agent_framework/sandbox.py

"""
E2B Sandbox wrapper - runs Claude Code agents in isolated environments.
"""

import os
import json
import asyncio
from dataclasses import dataclass
from typing import Optional
from pathlib import Path


@dataclass
class SandboxResult:
    success: bool
    output: str
    exit_code: int
    cost_usd: float
    duration_seconds: float
    files_changed: list[str]
    pr_url: Optional[str] = None
    error: Optional[str] = None


class AgentSandbox:
    """Runs a Claude Code agent in an E2B sandbox."""

    def __init__(
        self,
        repo_url: str,
        branch: str = "main",
        github_token: Optional[str] = None,
    ):
        self.repo_url = repo_url
        self.branch = branch
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.e2b_api_key = os.environ.get("E2B_API_KEY")

        if not self.e2b_api_key:
            raise ValueError("E2B_API_KEY environment variable required")

    async def run(
        self,
        prompt: str,
        model: str = "sonnet",
        max_turns: int = 50,
        timeout_minutes: int = 30,
        create_pr: bool = False,
        pr_title: Optional[str] = None,
    ) -> SandboxResult:
        """
        Run Claude Code agent in sandbox with the given prompt.
        """
        from e2b_code_interpreter import Sandbox
        import time

        start = time.perf_counter()

        # Create sandbox
        sandbox = Sandbox(
            api_key=self.e2b_api_key,
            timeout=timeout_minutes * 60,
        )

        try:
            # Setup: clone repo, configure git
            setup_script = f'''
            git clone {self.repo_url} /home/user/repo
            cd /home/user/repo
            git checkout {self.branch}
            git config user.email "agent@commandcenter.ai"
            git config user.name "CC Agent"
            '''

            if self.github_token:
                # Configure git credentials for pushing
                setup_script += f'''
                git remote set-url origin https://x-access-token:{self.github_token}@{self.repo_url.replace('https://', '')}
                '''

            sandbox.run_code(setup_script)

            # Write prompt to file
            sandbox.files.write("/home/user/task.md", prompt)

            # Run Claude Code
            claude_cmd = f'''
            cd /home/user/repo && claude \\
                --print \\
                --model {model} \\
                --max-turns {max_turns} \\
                --prompt "$(cat /home/user/task.md)" \\
                2>&1 | tee /home/user/output.log

            echo "EXIT_CODE:$?"
            '''

            result = sandbox.run_code(claude_cmd)
            output = result.text if hasattr(result, 'text') else str(result)

            # Parse exit code
            exit_code = 0
            if "EXIT_CODE:" in output:
                try:
                    exit_code = int(output.split("EXIT_CODE:")[-1].strip().split()[0])
                except:
                    pass

            # Get changed files
            diff_result = sandbox.run_code("cd /home/user/repo && git diff --name-only HEAD")
            files_changed = [f.strip() for f in (diff_result.text or "").split("\n") if f.strip()]

            # Create PR if requested
            pr_url = None
            if create_pr and files_changed:
                pr_url = await self._create_pr(sandbox, pr_title or "Agent changes")

            duration = time.perf_counter() - start

            return SandboxResult(
                success=exit_code == 0,
                output=output,
                exit_code=exit_code,
                cost_usd=0.0,  # TODO: track from Claude API
                duration_seconds=duration,
                files_changed=files_changed,
                pr_url=pr_url,
            )

        except Exception as e:
            return SandboxResult(
                success=False,
                output="",
                exit_code=1,
                cost_usd=0.0,
                duration_seconds=time.perf_counter() - start,
                files_changed=[],
                error=str(e),
            )
        finally:
            sandbox.kill()

    async def _create_pr(self, sandbox, title: str) -> Optional[str]:
        """Commit changes and create PR."""
        branch_name = f"agent/{title.lower().replace(' ', '-')[:30]}-{int(time.time())}"

        pr_script = f'''
        cd /home/user/repo
        git checkout -b {branch_name}
        git add -A
        git commit -m "{title}"
        git push -u origin {branch_name}

        # Create PR using gh CLI if available
        if command -v gh &> /dev/null; then
            gh pr create --title "{title}" --body "Automated changes by CC Agent" --head {branch_name}
        fi
        '''

        result = sandbox.run_code(pr_script)

        # Try to extract PR URL from output
        output = result.text or ""
        if "github.com" in output and "/pull/" in output:
            for line in output.split("\n"):
                if "github.com" in line and "/pull/" in line:
                    return line.strip()

        return None
```

```python
# backend/libs/agent_framework/executor.py

"""
Agent Executor - orchestrates agent execution.
"""

import asyncio
from dataclasses import dataclass
from typing import Optional
from .persona_store import PersonaStore, Persona
from .sandbox import AgentSandbox, SandboxResult


@dataclass
class ExecutionResult:
    persona: str
    task: str
    sandbox_result: SandboxResult


class AgentExecutor:
    """
    Executes agents based on personas.

    Usage:
        executor = AgentExecutor(repo_url="https://github.com/org/repo")

        result = await executor.run(
            persona="backend-coder",
            task="Implement the /api/v1/personas endpoint",
            create_pr=True,
        )
    """

    def __init__(
        self,
        repo_url: str,
        branch: str = "main",
        persona_store: Optional[PersonaStore] = None,
    ):
        self.repo_url = repo_url
        self.branch = branch
        self.personas = persona_store or PersonaStore()

    async def run(
        self,
        persona: str,
        task: str,
        create_pr: bool = False,
        pr_title: Optional[str] = None,
        max_turns: int = 50,
    ) -> ExecutionResult:
        """Run a single agent with the given task."""

        # Load persona
        p = self.personas.get(persona)

        # Build full prompt
        full_prompt = f"{p.system_prompt}\n\n---\n\n## Current Task\n\n{task}"

        # Create sandbox and run
        sandbox = AgentSandbox(
            repo_url=self.repo_url,
            branch=self.branch,
        )

        result = await sandbox.run(
            prompt=full_prompt,
            model=p.model.split("-")[1] if "-" in p.model else "sonnet",  # Extract model name
            max_turns=max_turns,
            create_pr=create_pr,
            pr_title=pr_title or f"[Agent] {task[:50]}",
        )

        return ExecutionResult(
            persona=persona,
            task=task,
            sandbox_result=result,
        )

    async def run_parallel(
        self,
        personas: list[str],
        task: str,
        max_concurrent: int = 3,
    ) -> list[ExecutionResult]:
        """Run multiple agents in parallel on the same task."""

        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_limit(persona: str) -> ExecutionResult:
            async with semaphore:
                return await self.run(persona, task)

        results = await asyncio.gather(
            *[run_with_limit(p) for p in personas],
            return_exceptions=True,
        )

        # Convert exceptions to failed results
        processed = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                processed.append(ExecutionResult(
                    persona=personas[i],
                    task=task,
                    sandbox_result=SandboxResult(
                        success=False,
                        output="",
                        exit_code=1,
                        cost_usd=0.0,
                        duration_seconds=0.0,
                        files_changed=[],
                        error=str(r),
                    ),
                ))
            else:
                processed.append(r)

        return processed
```

### Done When
- [ ] Can load a persona and run it in E2B sandbox
- [ ] Agent can clone repo, make changes, create PR
- [ ] Parallel execution works
- [ ] Results include changed files and PR URL

---

## Component 4: CLI Runner

**Time**: 1 hour
**Files**:
- `backend/cli/cc_agent.py`

### Implementation

Simple CLI using Click or just argparse.

```python
#!/usr/bin/env python3
# backend/cli/cc_agent.py

"""
CommandCenter Agent CLI

Usage:
    cc-agent run backend-coder --task "Build the personas API endpoint"
    cc-agent run backend-coder frontend-coder --task "Build feature X" --parallel
    cc-agent list-personas
    cc-agent improve-prompt --file prompt.txt
"""

import asyncio
import argparse
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from libs.agent_framework.executor import AgentExecutor
from libs.agent_framework.persona_store import PersonaStore
from libs.agent_framework.prompt_improver import PromptImprover


def main():
    parser = argparse.ArgumentParser(description="CommandCenter Agent CLI")
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run command
    run_parser = subparsers.add_parser("run", help="Run agent(s)")
    run_parser.add_argument("personas", nargs="+", help="Persona name(s)")
    run_parser.add_argument("--task", "-t", required=True, help="Task description")
    run_parser.add_argument("--repo", "-r", default="https://github.com/PerformanceSuite/CommandCenter")
    run_parser.add_argument("--branch", "-b", default="main")
    run_parser.add_argument("--create-pr", action="store_true", help="Create PR with changes")
    run_parser.add_argument("--parallel", action="store_true", help="Run personas in parallel")
    run_parser.add_argument("--max-turns", type=int, default=50)

    # list-personas command
    list_parser = subparsers.add_parser("list-personas", help="List available personas")
    list_parser.add_argument("--category", "-c", help="Filter by category")

    # improve-prompt command
    improve_parser = subparsers.add_parser("improve-prompt", help="Improve a prompt")
    improve_parser.add_argument("--file", "-f", help="Read prompt from file")
    improve_parser.add_argument("--text", "-t", help="Prompt text directly")

    args = parser.parse_args()

    if args.command == "run":
        asyncio.run(cmd_run(args))
    elif args.command == "list-personas":
        cmd_list_personas(args)
    elif args.command == "improve-prompt":
        asyncio.run(cmd_improve_prompt(args))


async def cmd_run(args):
    """Run agent(s) with task."""
    print(f"🤖 Running agent(s): {', '.join(args.personas)}")
    print(f"📋 Task: {args.task}")
    print(f"📦 Repo: {args.repo} ({args.branch})")
    print()

    executor = AgentExecutor(
        repo_url=args.repo,
        branch=args.branch,
    )

    if args.parallel and len(args.personas) > 1:
        print(f"⚡ Running {len(args.personas)} agents in parallel...")
        results = await executor.run_parallel(
            personas=args.personas,
            task=args.task,
        )
    else:
        results = []
        for persona in args.personas:
            print(f"▶️  Running {persona}...")
            result = await executor.run(
                persona=persona,
                task=args.task,
                create_pr=args.create_pr,
                max_turns=args.max_turns,
            )
            results.append(result)

    # Print results
    print("\n" + "="*60)
    print("RESULTS")
    print("="*60)

    for r in results:
        status = "✅" if r.sandbox_result.success else "❌"
        print(f"\n{status} {r.persona}")
        print(f"   Duration: {r.sandbox_result.duration_seconds:.1f}s")
        print(f"   Files changed: {len(r.sandbox_result.files_changed)}")
        if r.sandbox_result.files_changed:
            for f in r.sandbox_result.files_changed[:5]:
                print(f"     - {f}")
            if len(r.sandbox_result.files_changed) > 5:
                print(f"     ... and {len(r.sandbox_result.files_changed) - 5} more")
        if r.sandbox_result.pr_url:
            print(f"   PR: {r.sandbox_result.pr_url}")
        if r.sandbox_result.error:
            print(f"   Error: {r.sandbox_result.error}")


def cmd_list_personas(args):
    """List available personas."""
    store = PersonaStore()
    personas = store.list(category=args.category)

    if not personas:
        print("No personas found.")
        return

    print(f"{'Name':<20} {'Category':<15} {'Description'}")
    print("-" * 70)
    for p in personas:
        print(f"{p.name:<20} {p.category:<15} {p.description[:35]}...")


async def cmd_improve_prompt(args):
    """Improve a prompt."""
    if args.file:
        with open(args.file) as f:
            prompt = f.read()
    elif args.text:
        prompt = args.text
    else:
        print("Reading prompt from stdin...")
        prompt = sys.stdin.read()

    improver = PromptImprover()

    print("🔍 Analyzing prompt...")
    result = await improver.analyze(prompt)

    print(f"\n📊 Scores:")
    for k, v in result.scores.items():
        bar = "█" * (v // 10) + "░" * (10 - v // 10)
        print(f"   {k:<15} {bar} {v}")

    if result.issues:
        print(f"\n⚠️  Issues ({len(result.issues)}):")
        for issue in result.issues:
            sev = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue.get("severity", ""), "")
            print(f"   {sev} {issue.get('type', '')}: {issue.get('description', '')}")
            print(f"      Fix: {issue.get('fix', '')}")

    if result.improved:
        print("\n✨ Improved Version:")
        print("-" * 40)
        print(result.improved)
        print("-" * 40)

        # Optionally save
        if args.file:
            save = input("\nSave improved version? [y/N] ")
            if save.lower() == "y":
                with open(args.file, "w") as f:
                    f.write(result.improved)
                print(f"Saved to {args.file}")


if __name__ == "__main__":
    main()
```

### Setup

```bash
# Add to pyproject.toml or setup.py
[project.scripts]
cc-agent = "cli.cc_agent:main"

# Or just run directly
python backend/cli/cc_agent.py run backend-coder --task "Build X"
```

### Done When
- [ ] `cc-agent list-personas` shows available agents
- [ ] `cc-agent improve-prompt --file x.txt` improves a prompt
- [ ] `cc-agent run backend-coder --task "..." --create-pr` creates a PR
- [ ] `cc-agent run backend-coder frontend-coder --task "..." --parallel` works

---

## Bootstrap Test: First Agent Task

Once all components are working, run this:

```bash
cc-agent run backend-coder --task "
Read the plan at docs/plans/2025-12-31-verification-workflows-agent-management.md

Implement Part 2: Agent/Persona Management API

Specifically:
1. Create the database migration for agent_personas and workflow_templates tables
2. Create the API endpoints in backend/app/routers/agents.py:
   - GET /api/v1/agents/personas
   - GET /api/v1/agents/personas/{name}
   - POST /api/v1/agents/personas
   - PUT /api/v1/agents/personas/{name}

Follow existing patterns in the codebase. Run tests before committing.
" --create-pr --repo https://github.com/PerformanceSuite/CommandCenter --branch main
```

**If this produces a working PR, bootstrap is complete.**

---

## Timeline

| Component | Est. Time | Dependencies |
|-----------|-----------|--------------|
| Prompt Improver | 2 hrs | None |
| Persona Store | 1 hr | None |
| Agent Executor + E2B | 3 hrs | Persona Store |
| CLI Runner | 1 hr | All above |
| **Total** | **7 hrs** | |

## Definition of Done

Bootstrap is complete when:

1. ✅ `cc-agent improve-prompt` can analyze and improve prompts
2. ✅ `cc-agent list-personas` shows backend-coder, frontend-coder, reviewer
3. ✅ `cc-agent run backend-coder --task "..." --create-pr` creates a working PR
4. ✅ The PR passes CI (if configured)
5. ✅ We can give agents tasks to build remaining features

---

## What Agents Build Next

After bootstrap, agents handle:

1. **Persona Management UI** - React components for CRUD
2. **Workflow Builder UI** - Visual workflow editor
3. **Full Verification Workflow** - Assess → Challenge → Arbitrate → Learn
4. **KB Integration** - Store verified facts
5. **Skills Auto-Update** - Methodology improvements
6. **Prompt Improver UI** - Web interface for prompt analysis
7. **Dashboard** - Workflow history, costs, results

Each becomes a task for the coding agents we just bootstrapped.
