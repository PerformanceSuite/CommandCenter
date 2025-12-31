"""
Agent Sandbox - Run Claude Code agents in E2B sandboxes.

Provides isolated execution environments for coding agents.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


@dataclass
class SandboxResult:
    """Result from running an agent in a sandbox."""

    success: bool
    output: str
    exit_code: int
    cost_usd: float
    duration_seconds: float
    files_changed: list[str] = field(default_factory=list)
    pr_url: Optional[str] = None
    error: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "success": self.success,
            "output": self.output,
            "exit_code": self.exit_code,
            "cost_usd": self.cost_usd,
            "duration_seconds": self.duration_seconds,
            "files_changed": self.files_changed,
            "pr_url": self.pr_url,
            "error": self.error,
        }


class AgentSandbox:
    """
    Runs a Claude Code agent in an E2B sandbox.

    Example:
        sandbox = AgentSandbox(
            repo_url="https://github.com/org/repo",
            branch="main",
        )

        result = await sandbox.run(
            prompt="Fix the bug in auth.py",
            create_pr=True,
        )

        print(f"Changed files: {result.files_changed}")
        print(f"PR: {result.pr_url}")
    """

    def __init__(
        self,
        repo_url: str,
        branch: str = "main",
        github_token: Optional[str] = None,
    ):
        """
        Initialize sandbox for a repository.

        Args:
            repo_url: Git repository URL
            branch: Branch to work on
            github_token: GitHub token for pushing (defaults to GITHUB_TOKEN env)
        """
        self.repo_url = repo_url
        self.branch = branch
        self.github_token = github_token or os.environ.get("GITHUB_TOKEN")
        self.e2b_api_key = os.environ.get("E2B_API_KEY")

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

        Args:
            prompt: Task prompt for the agent
            model: Claude model to use (sonnet, opus, haiku)
            max_turns: Maximum conversation turns
            timeout_minutes: Sandbox timeout
            create_pr: Whether to create a PR with changes
            pr_title: Title for the PR

        Returns:
            SandboxResult with output, changed files, and PR URL
        """
        start = time.perf_counter()

        # Check for E2B API key
        if not self.e2b_api_key:
            logger.warning("E2B_API_KEY not set, running in local mode")
            return await self._run_local(prompt, model, max_turns)

        try:
            return await self._run_e2b(
                prompt=prompt,
                model=model,
                max_turns=max_turns,
                timeout_minutes=timeout_minutes,
                create_pr=create_pr,
                pr_title=pr_title,
                start_time=start,
            )
        except ImportError:
            logger.warning("e2b package not installed, running in local mode")
            return await self._run_local(prompt, model, max_turns)
        except Exception as e:
            logger.error("sandbox_run_failed", error=str(e))
            return SandboxResult(
                success=False,
                output="",
                exit_code=1,
                cost_usd=0.0,
                duration_seconds=time.perf_counter() - start,
                error=str(e),
            )

    async def _run_e2b(
        self,
        prompt: str,
        model: str,
        max_turns: int,
        timeout_minutes: int,
        create_pr: bool,
        pr_title: Optional[str],
        start_time: float,
    ) -> SandboxResult:
        """Run agent in E2B sandbox."""
        from e2b_code_interpreter import Sandbox

        sandbox = Sandbox(
            api_key=self.e2b_api_key,
            timeout=timeout_minutes * 60,
        )

        try:
            # Setup: clone repo, configure git
            setup_script = f"""
git clone {self.repo_url} /home/user/repo
cd /home/user/repo
git checkout {self.branch}
git config user.email "agent@commandcenter.ai"
git config user.name "CC Agent"
"""
            if self.github_token:
                # Configure git credentials for pushing
                repo_url_with_token = self.repo_url.replace(
                    "https://", f"https://x-access-token:{self.github_token}@"
                )
                setup_script += f"""
git remote set-url origin {repo_url_with_token}
"""

            sandbox.run_code(setup_script)

            # Write prompt to file
            sandbox.files.write("/home/user/task.md", prompt)

            # Run Claude Code
            claude_cmd = f"""
cd /home/user/repo && claude \\
    --print \\
    --model {model} \\
    --max-turns {max_turns} \\
    --prompt "$(cat /home/user/task.md)" \\
    2>&1 | tee /home/user/output.log

echo "EXIT_CODE:$?"
"""

            result = sandbox.run_code(claude_cmd)
            output = result.text if hasattr(result, "text") else str(result)

            # Parse exit code
            exit_code = 0
            if "EXIT_CODE:" in output:
                try:
                    exit_code = int(output.split("EXIT_CODE:")[-1].strip().split()[0])
                except (ValueError, IndexError):
                    pass

            # Get changed files
            diff_result = sandbox.run_code("cd /home/user/repo && git diff --name-only HEAD")
            files_changed = [f.strip() for f in (diff_result.text or "").split("\n") if f.strip()]

            # Create PR if requested
            pr_url = None
            if create_pr and files_changed:
                pr_url = await self._create_pr_e2b(sandbox, pr_title or "Agent changes")

            duration = time.perf_counter() - start_time

            return SandboxResult(
                success=exit_code == 0,
                output=output,
                exit_code=exit_code,
                cost_usd=0.0,  # TODO: track from Claude API
                duration_seconds=duration,
                files_changed=files_changed,
                pr_url=pr_url,
            )

        finally:
            sandbox.kill()

    async def _create_pr_e2b(self, sandbox, title: str) -> Optional[str]:
        """Commit changes and create PR in E2B sandbox."""
        branch_name = f"agent/{title.lower().replace(' ', '-')[:30]}-{int(time.time())}"

        pr_script = f"""
cd /home/user/repo
git checkout -b {branch_name}
git add -A
git commit -m "{title}"
git push -u origin {branch_name}

# Create PR using gh CLI if available
if command -v gh &> /dev/null; then
    gh pr create --title "{title}" --body "Automated changes by CC Agent" --head {branch_name}
fi
"""

        result = sandbox.run_code(pr_script)
        output = result.text or ""

        # Try to extract PR URL from output
        if "github.com" in output and "/pull/" in output:
            for line in output.split("\n"):
                if "github.com" in line and "/pull/" in line:
                    return line.strip()

        return None

    async def _run_local(
        self,
        prompt: str,
        model: str,
        max_turns: int,
    ) -> SandboxResult:
        """
        Run agent locally (fallback when E2B not available).

        This is a simplified local execution - it won't actually run Claude Code,
        but allows testing the workflow without E2B.
        """
        import asyncio

        start = time.perf_counter()

        logger.info(
            "local_execution_mode",
            prompt_preview=prompt[:100],
            model=model,
            max_turns=max_turns,
        )

        # In local mode, we just simulate the execution
        await asyncio.sleep(0.1)  # Simulate some work

        return SandboxResult(
            success=True,
            output=f"[LOCAL MODE] Would execute with model={model}, max_turns={max_turns}\n\nPrompt:\n{prompt[:500]}...",
            exit_code=0,
            cost_usd=0.0,
            duration_seconds=time.perf_counter() - start,
            files_changed=[],
            error="Local mode - E2B not configured",
        )
