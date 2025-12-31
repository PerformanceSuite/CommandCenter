"""
Agent Sandbox - Run Claude Code agents in E2B sandboxes.

Provides isolated execution environments for coding agents.

## API Key Setup

Keys should be in `~/.config/api-keys/.env.api-keys`:
```bash
ANTHROPIC_API_KEY=sk-ant-...
E2B_API_KEY=e2b_...
GITHUB_TOKEN=ghp_...  # Must be classic PAT with 'repo' scope
```

Or in `~/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows/.env`

See skill: ~/.claude/skills/agent-sandboxes/SKILL.md for full setup guide.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import structlog

logger = structlog.get_logger(__name__)


# Standard locations for API keys (in order of precedence)
API_KEY_LOCATIONS = [
    # 1. Environment variables (already set)
    None,  # Placeholder - we check os.environ first
    # 2. Centralized API keys file
    Path.home() / ".config" / "api-keys" / ".env.api-keys",
    # 3. Sandbox workflows .env
    Path.home() / "Projects" / "CommandCenter" / "tools" / "agent-sandboxes" / "apps" / "sandbox_workflows" / ".env",
    # 4. Backend .env
    Path.home() / "Projects" / "CommandCenter" / "backend" / ".env",
    # 5. Project root .env
    Path.home() / "Projects" / "CommandCenter" / ".env",
]


def _load_key_from_file(filepath: Path, key_name: str) -> Optional[str]:
    """Load a specific key from an env file."""
    if not filepath.exists():
        return None
    
    try:
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key_name}="):
                    value = line.split("=", 1)[1].strip()
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    if value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    # Skip export prefix
                    if value.startswith("export "):
                        value = value[7:]
                    return value if value else None
    except Exception:
        pass
    return None


def find_api_key(key_name: str) -> Optional[str]:
    """
    Find an API key by searching standard locations.
    
    Order:
    1. Environment variable
    2. ~/.config/api-keys/.env.api-keys
    3. sandbox_workflows/.env
    4. backend/.env
    5. Project root .env
    
    Returns the first non-empty value found.
    """
    # 1. Check environment first
    value = os.environ.get(key_name)
    if value:
        return value
    
    # 2. Check file locations
    for filepath in API_KEY_LOCATIONS[1:]:  # Skip None placeholder
        value = _load_key_from_file(filepath, key_name)
        if value:
            logger.debug("api_key_found", key=key_name, source=str(filepath))
            return value
    
    return None


def get_key_setup_instructions(key_name: str) -> str:
    """Get setup instructions for a missing API key."""
    instructions = {
        "E2B_API_KEY": """
E2B API Key Not Found!

Get your key:
  1. Sign up at https://e2b.dev
  2. Go to Dashboard → API Keys
  3. Copy your key (starts with 'e2b_')

Add to your config:
  echo 'E2B_API_KEY=e2b_your_key_here' >> ~/.config/api-keys/.env.api-keys
  source ~/.zshrc

Or add to sandbox workflows:
  echo 'E2B_API_KEY=e2b_your_key_here' >> ~/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows/.env

Full setup guide: ~/.claude/skills/agent-sandboxes/SKILL.md
""",
        "ANTHROPIC_API_KEY": """
Anthropic API Key Not Found!

Get your key:
  1. Go to https://console.anthropic.com
  2. Create an API key
  3. Copy it (starts with 'sk-ant-')

Add to your config:
  echo 'ANTHROPIC_API_KEY=sk-ant-...' >> ~/.config/api-keys/.env.api-keys
  source ~/.zshrc
""",
        "GITHUB_TOKEN": """
GitHub Token Not Found!

Get your token:
  1. Go to https://github.com/settings/tokens
  2. Generate new token (classic) - NOT fine-grained!
  3. Select 'repo' scope
  4. Copy it (starts with 'ghp_')

IMPORTANT: Use classic PATs (ghp_), not OAuth tokens (gho_)!
OAuth tokens expire and cause push failures.

Add to your config:
  echo 'GITHUB_TOKEN=ghp_...' >> ~/.config/api-keys/.env.api-keys
  source ~/.zshrc
""",
    }
    return instructions.get(key_name, f"Set {key_name} in ~/.config/api-keys/.env.api-keys")


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

    API keys are automatically loaded from standard locations:
    1. Environment variables
    2. ~/.config/api-keys/.env.api-keys
    3. ~/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows/.env
    
    See ~/.claude/skills/agent-sandboxes/SKILL.md for full setup guide.

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
        e2b_api_key: Optional[str] = None,
    ):
        """
        Initialize sandbox for a repository.

        Args:
            repo_url: Git repository URL
            branch: Branch to work on
            github_token: GitHub token for pushing (auto-discovered if not provided)
            e2b_api_key: E2B API key (auto-discovered if not provided)
        """
        self.repo_url = repo_url
        self.branch = branch
        
        # Auto-discover keys from standard locations
        self.github_token = github_token or find_api_key("GITHUB_TOKEN")
        self.e2b_api_key = e2b_api_key or find_api_key("E2B_API_KEY")
        
        # Log what we found
        if self.e2b_api_key:
            logger.debug("e2b_key_found", key_preview=f"{self.e2b_api_key[:10]}...")
        if self.github_token:
            logger.debug("github_token_found", key_preview=f"{self.github_token[:10]}...")

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
            logger.info("setup_instructions", instructions=get_key_setup_instructions("E2B_API_KEY"))
            return await self._run_local(prompt, model, max_turns)

        # Warn if GitHub token missing and PR requested
        if create_pr and not self.github_token:
            logger.warning("GITHUB_TOKEN not set, PR creation will fail")
            logger.info("setup_instructions", instructions=get_key_setup_instructions("GITHUB_TOKEN"))

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
            logger.warning("e2b package not installed")
            logger.info("install_e2b", command="pip install e2b-code-interpreter")
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
        
        # Set E2B API key in environment (SDK reads from env)
        os.environ["E2B_API_KEY"] = self.e2b_api_key

        logger.info("starting_e2b_sandbox", timeout_minutes=timeout_minutes)
        
        # E2B SDK uses Sandbox.create() class method
        sandbox = Sandbox.create(timeout=timeout_minutes * 60)

        try:
            # Helper to run shell commands
            def run_shell(cmd: str) -> tuple[str, str, int]:
                """Run shell command and return (stdout, stderr, returncode)."""
                code = f'''
import subprocess
import sys
result = subprocess.run({repr(cmd)}, shell=True, capture_output=True, text=True)
sys.stdout.write("__STDOUT_START__")
sys.stdout.write(result.stdout)
sys.stdout.write("__STDOUT_END__")
sys.stdout.write("__STDERR_START__")
sys.stdout.write(result.stderr)
sys.stdout.write("__STDERR_END__")
sys.stdout.write(f"__RETCODE__{{result.returncode}}__")
'''
                result = sandbox.run_code(code)
                full_output = "".join(result.logs.stdout)
                
                # Parse stdout
                stdout = ""
                if "__STDOUT_START__" in full_output and "__STDOUT_END__" in full_output:
                    start = full_output.find("__STDOUT_START__") + len("__STDOUT_START__")
                    end = full_output.find("__STDOUT_END__")
                    stdout = full_output[start:end]
                
                # Parse stderr
                stderr = ""
                if "__STDERR_START__" in full_output and "__STDERR_END__" in full_output:
                    start = full_output.find("__STDERR_START__") + len("__STDERR_START__")
                    end = full_output.find("__STDERR_END__")
                    stderr = full_output[start:end]
                
                # Parse return code
                retcode = 1  # Default to error
                if "__RETCODE__" in full_output:
                    try:
                        start = full_output.find("__RETCODE__") + len("__RETCODE__")
                        end = full_output.find("__", start)
                        retcode = int(full_output[start:end])
                    except (ValueError, IndexError):
                        pass
                
                return stdout, stderr, retcode

            # Setup: clone repo, configure git
            logger.info("sandbox_setup", repo=self.repo_url, branch=self.branch)
            
            # Clone repo
            clone_url = self.repo_url
            if self.github_token:
                clone_url = self.repo_url.replace(
                    "https://", f"https://x-access-token:{self.github_token}@"
                )
            
            stdout, stderr, retcode = run_shell(f"git clone --depth 50 {clone_url} /home/user/repo")
            if retcode != 0:
                logger.error("clone_failed", stderr=stderr)
                raise RuntimeError(f"Failed to clone repo: {stderr}")
            
            # Configure git
            run_shell('cd /home/user/repo && git config user.email "agent@commandcenter.ai"')
            run_shell('cd /home/user/repo && git config user.name "CC Agent"')
            run_shell(f'cd /home/user/repo && git checkout {self.branch}')

            # Check if Claude Code is installed, install if not
            logger.info("checking_claude_code")
            which_out, _, retcode = run_shell('which claude')
            logger.info("claude_check", which_out=which_out, retcode=retcode)
            
            if retcode != 0 or not which_out.strip():
                logger.info("installing_claude_code")
                # Try to install Claude Code via npm (requires node)
                install_out, install_err, install_ret = run_shell('npm install -g @anthropic-ai/claude-code 2>&1')
                logger.info("npm_install_result", retcode=install_ret, out=install_out[:200] if install_out else "")
                
                # Verify installation
                which_out2, _, retcode2 = run_shell('which claude')
                if retcode2 != 0 or not which_out2.strip():
                    logger.warning("claude_code_not_available", msg="Claude Code not installed in sandbox, using API fallback")
                    # Fall back to direct API call
                    result = await self._run_api_fallback(prompt, model, sandbox, start_time)
                    sandbox.kill()
                    return result
            
            # Set ANTHROPIC_API_KEY in sandbox environment for Claude Code
            anthropic_key = find_api_key("ANTHROPIC_API_KEY")
            if anthropic_key:
                sandbox.run_code(f'''
import os
os.environ["ANTHROPIC_API_KEY"] = "{anthropic_key}"
''')

            # Write prompt to file
            prompt_escaped = prompt.replace('"', r'\"').replace("'", r"\'")
            sandbox.run_code(f'''
with open("/home/user/task.md", "w") as f:
    f.write("""{prompt}""")
''')

            # Run Claude Code as non-root user (required for --dangerously-skip-permissions)
            # Claude Code CLI: claude [options] <prompt>
            logger.info("running_claude_code", model=model, max_turns=max_turns)
            anthropic_key = find_api_key("ANTHROPIC_API_KEY")
            export_cmd = f"export ANTHROPIC_API_KEY={anthropic_key} && " if anthropic_key else ""
            # Create a non-root user and run claude as that user
            setup_user_cmd = '''useradd -m agent 2>/dev/null || true
chown -R agent:agent /home/user/repo
chmod -R 755 /home/user/repo
'''
            run_shell(setup_user_cmd)
            
            # Run as 'agent' user with su
            claude_cmd = f'{export_cmd}su - agent -c "cd /home/user/repo && claude --print --dangerously-skip-permissions --model {model} --max-turns {max_turns} \"$(cat /home/user/task.md)\"" 2>&1'
            stdout, stderr, exit_code = run_shell(claude_cmd)
            output = stdout + stderr
            
            logger.info("claude_completed", exit_code=exit_code, output_len=len(output), output_preview=output[:500] if output else "")

            # Get changed files (staged + unstaged + untracked)
            status_stdout, _, status_ret = run_shell("cd /home/user/repo && git status --porcelain")
            logger.info("git_status", stdout=status_stdout[:200] if status_stdout else "", retcode=status_ret)
            files_changed = []
            for line in status_stdout.split("\n"):
                line = line.strip()
                if line and len(line) > 2:
                    # Format: XY filename (where XY is status)
                    # Examples: "?? newfile.txt", "M  modified.txt", " M unstaged.txt"
                    files_changed.append(line[2:].strip())
            
            logger.info("sandbox_completed", exit_code=exit_code, files_changed=len(files_changed))

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

        logger.info("creating_pr", branch=branch_name, title=title)
        result = sandbox.run_code(pr_script)
        output = result.text or ""

        # Try to extract PR URL from output
        if "github.com" in output and "/pull/" in output:
            for line in output.split("\n"):
                if "github.com" in line and "/pull/" in line:
                    pr_url = line.strip()
                    logger.info("pr_created", url=pr_url)
                    return pr_url

        logger.warning("pr_url_not_found", output_preview=output[:200])
        return None

    async def _run_api_fallback(
        self,
        prompt: str,
        model: str,
        sandbox,
        start_time: float,
    ) -> SandboxResult:
        """
        Fallback when Claude Code CLI isn't available.
        Uses Anthropic API directly to execute coding tasks.
        """
        import anthropic
        
        anthropic_key = find_api_key("ANTHROPIC_API_KEY")
        if not anthropic_key:
            return SandboxResult(
                success=False,
                output="",
                exit_code=1,
                cost_usd=0.0,
                duration_seconds=time.perf_counter() - start_time,
                error="Neither Claude Code nor ANTHROPIC_API_KEY available",
            )
        
        client = anthropic.Anthropic(api_key=anthropic_key)
        
        # Helper to run shell in sandbox
        def run_shell(cmd: str) -> tuple[str, str, int]:
            code = f'''
import subprocess
result = subprocess.run({repr(cmd)}, shell=True, capture_output=True, text=True)
print("STDOUT:", result.stdout)
print("STDERR:", result.stderr)
print("RETCODE:", result.returncode)
'''
            result = sandbox.run_code(code)
            stdout_lines = []
            stderr_lines = []
            retcode = 0
            for line in result.logs.stdout:
                if line.startswith("STDOUT: "):
                    stdout_lines.append(line[8:])
                elif line.startswith("STDERR: "):
                    stderr_lines.append(line[8:])
                elif line.startswith("RETCODE: "):
                    try:
                        retcode = int(line[9:].strip())
                    except ValueError:
                        pass
            return "".join(stdout_lines), "".join(stderr_lines), retcode
        
        # Get repo structure for context
        ls_out, _, _ = run_shell("cd /home/user/repo && find . -type f -name '*.py' -o -name '*.md' | head -50")
        
        system_prompt = f"""You are an expert coding agent working in a git repository.
You can execute shell commands by wrapping them in <shell>command</shell> tags.
You can create/edit files by using <file path="path/to/file">content</file> tags.

Repository structure (first 50 files):
{ls_out}

Execute the task and respond with the commands/files needed."""

        logger.info("api_fallback_calling_claude", model=model)
        
        response = client.messages.create(
            model=f"claude-3-5-{model}-latest" if model in ["sonnet", "haiku"] else model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}],
        )
        
        output = response.content[0].text
        logger.info("api_fallback_response", output_len=len(output))
        
        # Parse and execute shell commands
        import re
        shell_commands = re.findall(r'<shell>(.*?)</shell>', output, re.DOTALL)
        for cmd in shell_commands:
            logger.info("executing_shell", cmd=cmd[:50])
            run_shell(f"cd /home/user/repo && {cmd.strip()}")
        
        # Parse and create files
        file_matches = re.findall(r'<file path="([^"]+)">(.*?)</file>', output, re.DOTALL)
        for path, content in file_matches:
            logger.info("creating_file", path=path)
            # Write file via Python in sandbox
            escaped_content = content.replace('\\', '\\\\').replace("'''", "\\'''")
            sandbox.run_code(f'''
import os
os.makedirs(os.path.dirname("/home/user/repo/{path}") or ".", exist_ok=True)
with open("/home/user/repo/{path}", "w") as f:
    f.write(\'\'\'{escaped_content}\'\'\')
''')
        
        # Get changed files
        diff_stdout, _, _ = run_shell("cd /home/user/repo && git status --porcelain")
        files_changed = [line[3:].strip() for line in diff_stdout.split("\n") if line.strip()]
        
        duration = time.perf_counter() - start_time
        
        return SandboxResult(
            success=True,
            output=output,
            exit_code=0,
            cost_usd=0.0,
            duration_seconds=duration,
            files_changed=files_changed,
        )

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
            error="Local mode - E2B not configured. See: ~/.claude/skills/agent-sandboxes/SKILL.md",
        )
