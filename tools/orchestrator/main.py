#!/usr/bin/env python3
"""
Long-Running Agent Orchestrator

The main entry point for overnight autonomous development.

Usage:
    python main.py                    # Run continuously (overnight mode)
    python main.py --mode once        # Process one task and exit
    python main.py --mode batch       # Process all pending tasks
    python main.py --mode status      # Show queue and budget status
"""

from __future__ import annotations

import argparse
import asyncio
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

from task_queue import Task, TaskQueue
from skills_store import SkillsStore, SkillUpdate
from cost_budget import CostBudget


class AgentOrchestrator:
    """
    Long-running process that:
    1. Monitors task queue for ready tasks
    2. Spawns E2B sandboxes for each task
    3. Tracks costs against daily budget
    4. Writes learned patterns back to skills
    5. Triggers dependent tasks on completion
    """

    def __init__(
        self,
        tasks_dir: str = "tasks",
        skills_dir: str = "~/.claude/skills",
        daily_budget: float = 50.0,
    ):
        self.task_queue = TaskQueue(tasks_dir)
        self.skills = SkillsStore(skills_dir)
        self.budget = CostBudget(daily_limit=daily_budget)

        # E2B sandbox workflow location
        self.obox_dir = Path("~/Projects/CommandCenter/tools/agent-sandboxes/apps/sandbox_workflows").expanduser()

        # Check required API keys
        self._check_api_keys()

    def _check_api_keys(self):
        """Verify required API keys are set"""
        required = ["ANTHROPIC_API_KEY", "E2B_API_KEY", "GITHUB_TOKEN"]
        missing = [k for k in required if not os.environ.get(k)]

        if missing:
            print(f"⚠️  Missing API keys: {', '.join(missing)}")
            print("   Set them in your environment or ~/.config/api-keys/.env.api-keys")

    async def run(self, mode: str = "continuous"):
        """
        Run the orchestrator.

        Modes:
        - continuous: Run forever (overnight mode)
        - once: Process one task and exit
        - batch: Process all pending tasks
        - status: Show current status
        """
        if mode == "status":
            self._show_status()
            return
        elif mode == "once":
            await self._process_one_task()
        elif mode == "batch":
            await self._process_all_tasks()
        else:
            await self._run_continuous()

    def _show_status(self):
        """Display current queue and budget status"""
        print("\n" + "=" * 60)
        print("🤖 AGENT ORCHESTRATOR STATUS")
        print("=" * 60)

        # Queue status
        status = self.task_queue.status()
        print(f"\n📋 Task Queue:")
        print(f"   Pending:   {status['pending']}")
        print(f"   Running:   {status['running']}")
        print(f"   Completed: {status['completed']}")
        print(f"   Failed:    {status['failed']}")

        # Budget status
        print(f"\n{self.budget}")

        # Pending tasks
        pending = self.task_queue.load_pending()
        if pending:
            print(f"\n📌 Pending Tasks:")
            for task in sorted(pending, key=lambda t: t.priority):
                deps = f" (waiting: {', '.join(task.depends_on)})" if task.depends_on else ""
                print(f"   [{task.priority}] {task.id}: {task.title}{deps}")

        # Learned skills
        learned = self.skills.list_learned()
        if learned:
            print(f"\n📚 Learned Skills: {', '.join(learned)}")

        # Pending skill reviews
        pending_skills = self.skills.list_pending()
        if pending_skills:
            print(f"\n📝 Skills Pending Review: {len(pending_skills)}")
            for s in pending_skills[:5]:
                print(f"   - {s}")

        print("\n" + "=" * 60)

    async def _run_continuous(self):
        """Main overnight loop"""
        print(f"\n🤖 Orchestrator starting at {datetime.now()}")
        print(f"💰 Daily budget: ${self.budget.daily_limit:.2f}")
        print(f"📂 Tasks directory: {self.task_queue.base_dir}")
        print("\nPress Ctrl+C to stop\n")

        while True:
            try:
                # Check cost budget
                if self.budget.exhausted():
                    reset_time = self.budget.reset_time()
                    print(f"💸 Budget exhausted. Sleeping until {reset_time}")
                    await self._sleep_until(reset_time)
                    continue

                # Get next task
                task = self.task_queue.get_next()

                if not task:
                    print("📭 No tasks ready. Sleeping 60s...")
                    await asyncio.sleep(60)
                    continue

                # Check if we can afford it
                if not self.budget.can_afford(task.agent_config.max_cost_usd):
                    print(f"💸 Cannot afford task {task.id} (${task.agent_config.max_cost_usd:.2f})")
                    # Put it back
                    self.task_queue.add_task(task)
                    await asyncio.sleep(60)
                    continue

                # Execute
                print(f"\n🚀 Starting task: {task.title}")
                await self._execute_task(task)

            except KeyboardInterrupt:
                print("\n🛑 Orchestrator stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                import traceback
                traceback.print_exc()
                await asyncio.sleep(60)

    async def _process_one_task(self):
        """Process single task and exit"""
        task = self.task_queue.get_next()

        if not task:
            print("📭 No tasks ready")
            return

        print(f"🚀 Processing: {task.title}")
        await self._execute_task(task)

    async def _process_all_tasks(self):
        """Process all pending tasks"""
        count = 0

        while True:
            task = self.task_queue.get_next()

            if not task:
                break

            if self.budget.exhausted():
                print(f"💸 Budget exhausted after {count} tasks")
                # Put task back
                self.task_queue.add_task(task)
                break

            print(f"\n🚀 Task {count + 1}: {task.title}")
            await self._execute_task(task)
            count += 1

        print(f"\n✅ Processed {count} tasks")

    async def _execute_task(self, task: Task):
        """Execute a single task in an E2B sandbox"""
        start_time = datetime.utcnow()

        try:
            # Load relevant skills for context
            skills_context = self.skills.load(task.skills_required)

            # Build the agent prompt
            prompt = self._build_prompt(task, skills_context)

            # Write prompt to temp file
            prompt_file = Path(f"/tmp/task-{task.id}-prompt.md")
            prompt_file.write_text(prompt)

            # Execute via obox
            result = await self._run_obox(
                repo_url=task.context.repo,
                branch=task.context.branch,
                prompt_file=str(prompt_file),
                model=task.agent_config.model,
                max_turns=task.agent_config.max_turns,
            )

            # Estimate cost (rough: $0.003 per 1k input, $0.015 per 1k output for Sonnet)
            estimated_cost = min(
                task.agent_config.max_cost_usd,
                2.0  # Assume $2 average for now
            )

            if result.returncode == 0:
                # Success!
                self.budget.record_cost(estimated_cost, task.id)
                self.task_queue.complete(task, cost_usd=estimated_cost)

                # Trigger dependent tasks
                for next_id in task.on_completion.trigger_next:
                    print(f"  → Unblocked: {next_id}")

                # Optional: Extract and write skill learnings
                if task.on_completion.update_skill:
                    await self._extract_learnings(task, result.stdout)

                duration = (datetime.utcnow() - start_time).total_seconds()
                print(f"✅ Task completed in {duration:.1f}s (${estimated_cost:.2f})")

            else:
                # Failed
                error = result.stderr or "Unknown error"
                self.task_queue.fail(task, error[:500])
                print(f"❌ Task failed: {error[:200]}")

        except Exception as e:
            self.task_queue.fail(task, str(e))
            print(f"❌ Task exception: {e}")

    def _build_prompt(self, task: Task, skills_context: str) -> str:
        """Build the full prompt for the agent"""
        parts = []

        # Header
        parts.append(f"# Task: {task.title}")
        parts.append(f"\n**Task ID:** {task.id}")
        parts.append(f"**Branch:** {task.context.branch}")

        # Plan file reference
        if task.context.plan_file:
            parts.append(f"\n## Implementation Plan")
            parts.append(f"See: {task.context.plan_file}")

        # Skills context
        if skills_context:
            parts.append(f"\n## Relevant Skills\n\n{skills_context}")

        # Git authentication
        parts.append("""
## CRITICAL: Git Authentication

Before any git push operations, configure authentication:

```bash
git remote set-url origin https://${GITHUB_TOKEN}@github.com/PerformanceSuite/CommandCenter.git
git remote -v  # Verify
```

**You MUST do this before attempting to push.**
""")

        # Task instructions
        parts.append(f"""
## Your Mission

Complete the task described above.

### Workflow

1. Review the plan file if provided
2. Implement the changes on branch: `{task.context.branch}`
3. Write tests if applicable
4. Commit with clear, descriptive messages
5. Push and create a PR

### Commit Messages

Use conventional commits:
- feat(scope): Add new feature
- fix(scope): Fix bug
- docs(scope): Update documentation
- test(scope): Add tests
- refactor(scope): Code refactoring

### On Completion

Create a pull request with:
- Clear title summarizing the change
- Description of what was implemented
- Any notes for reviewers
""")

        return "\n".join(parts)

    async def _run_obox(
        self,
        repo_url: str,
        branch: str,
        prompt_file: str,
        model: str = "sonnet",
        max_turns: int = 100,
    ) -> subprocess.CompletedProcess:
        """Run obox command to execute agent in sandbox"""

        cmd = [
            "uv", "run", "obox",
            repo_url,
            "-p", prompt_file,
            "-b", branch,
            "-m", model,
            "-t", str(max_turns),
        ]

        print(f"  Running: {' '.join(cmd[:6])}...")

        # Run in obox directory
        result = subprocess.run(
            cmd,
            cwd=str(self.obox_dir),
            capture_output=True,
            text=True,
            env={**os.environ},
        )

        return result

    async def _extract_learnings(self, task: Task, output: str):
        """Extract learnings from agent output and update skills"""
        if task.on_completion.update_skill:
            update = SkillUpdate(
                domain=task.on_completion.update_skill,
                patterns=[f"Pattern from task {task.id}"],
                confidence=0.6,  # Low confidence = goes to pending
                source_task=task.id,
            )
            self.skills.write(update)

    async def _sleep_until(self, target: datetime):
        """Sleep until target time"""
        now = datetime.utcnow()
        if target > now:
            sleep_seconds = (target - now).total_seconds()
            print(f"💤 Sleeping for {sleep_seconds / 3600:.1f} hours")
            await asyncio.sleep(sleep_seconds)


def main():
    parser = argparse.ArgumentParser(
        description="Long-Running Agent Orchestrator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s                    Run continuously (overnight mode)
    %(prog)s --mode once        Process one task and exit
    %(prog)s --mode batch       Process all pending tasks
    %(prog)s --mode status      Show queue and budget status
        """
    )

    parser.add_argument(
        "--mode",
        choices=["continuous", "once", "batch", "status"],
        default="continuous",
        help="Execution mode (default: continuous)"
    )

    parser.add_argument(
        "--budget",
        type=float,
        default=50.0,
        help="Daily budget in USD (default: 50.0)"
    )

    parser.add_argument(
        "--tasks-dir",
        default="tasks",
        help="Tasks directory (default: tasks)"
    )

    args = parser.parse_args()

    orchestrator = AgentOrchestrator(
        tasks_dir=args.tasks_dir,
        daily_budget=args.budget,
    )

    asyncio.run(orchestrator.run(mode=args.mode))


if __name__ == "__main__":
    main()
