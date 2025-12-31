"""
Agent Executor - Orchestrates agent execution with personas.

Loads personas and runs them in sandboxes or locally.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Optional

import structlog

from .persona_store import Persona, PersonaStore
from .sandbox import AgentSandbox, SandboxResult

logger = structlog.get_logger(__name__)


@dataclass
class ExecutionResult:
    """Result from executing an agent."""

    persona: str
    task: str
    sandbox_result: SandboxResult

    def to_dict(self) -> dict:
        return {
            "persona": self.persona,
            "task": self.task,
            "result": self.sandbox_result.to_dict(),
        }


class AgentExecutor:
    """
    Executes agents based on personas.

    Example:
        executor = AgentExecutor(repo_url="https://github.com/org/repo")

        result = await executor.run(
            persona="backend-coder",
            task="Implement the /api/v1/personas endpoint",
            create_pr=True,
        )

        print(f"Success: {result.sandbox_result.success}")
        print(f"Changed: {result.sandbox_result.files_changed}")
    """

    def __init__(
        self,
        repo_url: str,
        branch: str = "main",
        persona_store: Optional[PersonaStore] = None,
    ):
        """
        Initialize executor for a repository.

        Args:
            repo_url: Git repository URL
            branch: Default branch to work on
            persona_store: Persona store instance (defaults to standard store)
        """
        self.repo_url = repo_url
        self.branch = branch
        self.personas = persona_store or PersonaStore()

    async def run(
        self,
        persona: str,
        task: str,
        branch: Optional[str] = None,
        create_pr: bool = False,
        pr_title: Optional[str] = None,
        max_turns: int = 50,
    ) -> ExecutionResult:
        """
        Run a single agent with the given task.

        Args:
            persona: Name of the persona to use
            task: Task description for the agent
            branch: Git branch (defaults to executor's default)
            create_pr: Whether to create a PR with changes
            pr_title: Title for the PR
            max_turns: Maximum conversation turns

        Returns:
            ExecutionResult with persona info and sandbox result
        """
        # Load persona
        p = self.personas.get(persona)

        logger.info(
            "agent_execution_started",
            persona=persona,
            task_preview=task[:100],
            branch=branch or self.branch,
            create_pr=create_pr,
        )

        # Build full prompt
        full_prompt = self._build_prompt(p, task)

        # Create sandbox and run
        sandbox = AgentSandbox(
            repo_url=self.repo_url,
            branch=branch or self.branch,
        )

        # Extract model name (e.g., "claude-sonnet-4-20250514" -> "sonnet")
        model = self._extract_model_name(p.model)

        result = await sandbox.run(
            prompt=full_prompt,
            model=model,
            max_turns=max_turns,
            create_pr=create_pr,
            pr_title=pr_title or f"[{persona}] {task[:50]}",
        )

        logger.info(
            "agent_execution_completed",
            persona=persona,
            success=result.success,
            files_changed=len(result.files_changed),
            duration=result.duration_seconds,
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
        branch: Optional[str] = None,
        max_concurrent: int = 3,
    ) -> list[ExecutionResult]:
        """
        Run multiple agents in parallel on the same task.

        Args:
            personas: List of persona names to run
            task: Task description for all agents
            branch: Git branch
            max_concurrent: Maximum concurrent executions

        Returns:
            List of ExecutionResults, one per persona
        """
        logger.info(
            "parallel_execution_started",
            personas=personas,
            task_preview=task[:100],
            max_concurrent=max_concurrent,
        )

        semaphore = asyncio.Semaphore(max_concurrent)

        async def run_with_limit(persona: str) -> ExecutionResult:
            async with semaphore:
                return await self.run(persona, task, branch=branch)

        results = await asyncio.gather(
            *[run_with_limit(p) for p in personas],
            return_exceptions=True,
        )

        # Convert exceptions to failed results
        processed = []
        for i, r in enumerate(results):
            if isinstance(r, Exception):
                logger.error(
                    "parallel_agent_failed",
                    persona=personas[i],
                    error=str(r),
                )
                processed.append(
                    ExecutionResult(
                        persona=personas[i],
                        task=task,
                        sandbox_result=SandboxResult(
                            success=False,
                            output="",
                            exit_code=1,
                            cost_usd=0.0,
                            duration_seconds=0.0,
                            error=str(r),
                        ),
                    )
                )
            else:
                processed.append(r)

        logger.info(
            "parallel_execution_completed",
            total=len(personas),
            succeeded=sum(1 for r in processed if r.sandbox_result.success),
            failed=sum(1 for r in processed if not r.sandbox_result.success),
        )

        return processed

    def _build_prompt(self, persona: Persona, task: str) -> str:
        """Build the full prompt from persona and task."""
        return f"""{persona.system_prompt}

---

## Current Task

{task}

---

Remember to:
1. Read existing code first to understand patterns
2. Make focused, minimal changes
3. Run tests before committing
4. Use clear commit messages
"""

    def _extract_model_name(self, model: str) -> str:
        """Extract short model name from full model string."""
        # "claude-sonnet-4-20250514" -> "sonnet"
        # "claude" -> "sonnet" (default)
        if "opus" in model.lower():
            return "opus"
        elif "haiku" in model.lower():
            return "haiku"
        elif "sonnet" in model.lower():
            return "sonnet"
        else:
            return "sonnet"  # Default to sonnet
