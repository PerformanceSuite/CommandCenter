#!/usr/bin/env python3
"""
CommandCenter CLI - Run agents from the command line.

Usage:
    python cli/cc.py personas           # List all personas
    python cli/cc.py skills <query>     # Search skills
    python cli/cc.py run -p coder -t "Task" -r ~/Projects/repo
"""

import asyncio
import sys
from pathlib import Path

import click

# Add backend to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "backend"))

from libs.agent_framework import PersonaStore, SkillRetriever, AgentExecutor


@click.group()
@click.version_option(version="0.1.0", prog_name="cc")
def cli():
    """CommandCenter CLI - Run agents with personas and skills."""
    pass


@cli.command()
@click.option("--category", "-c", help="Filter by category (coding, verification, synthesis)")
def personas(category: str | None):
    """List available agent personas."""
    store = PersonaStore()
    persona_list = store.list(category=category)

    if not persona_list:
        click.echo("No personas found.")
        return

    click.echo(f"\n{'Name':<20} {'Category':<15} {'Description'}")
    click.echo("-" * 70)

    for p in persona_list:
        desc = p.description[:40] + "..." if len(p.description) > 40 else p.description
        click.echo(f"{p.name:<20} {p.category:<15} {desc}")

    click.echo(f"\nTotal: {len(persona_list)} personas")


@cli.command()
@click.argument("query")
@click.option("--limit", "-n", default=5, help="Number of results")
def skills(query: str, limit: int):
    """Search for relevant skills."""

    async def _search():
        retriever = SkillRetriever()
        try:
            results = await retriever.find_relevant(task=query, limit=limit)
            return results
        except Exception as e:
            click.echo(f"Error searching skills: {e}", err=True)
            return []

    results = asyncio.run(_search())

    if not results:
        click.echo(f"No skills found for: {query}")
        return

    click.echo(f"\nSkills matching '{query}':\n")
    for skill in results:
        click.echo(f"  • {skill.slug}")
        if skill.description:
            click.echo(f"    {skill.description[:60]}...")
        click.echo()


@cli.command()
@click.option("--persona", "-p", required=True, help="Persona to use")
@click.option("--task", "-t", required=True, help="Task description")
@click.option("--repo", "-r", required=True, help="Repository URL or local path")
@click.option("--branch", "-b", default="main", help="Git branch")
@click.option("--pr", is_flag=True, help="Create PR with changes")
@click.option("--max-turns", default=50, help="Maximum conversation turns")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def run(persona: str, task: str, repo: str, branch: str, pr: bool, max_turns: int, verbose: bool):
    """Run an agent with a specific task."""

    # Expand local paths
    if repo.startswith("~") or repo.startswith("/") or repo.startswith("."):
        repo_path = Path(repo).expanduser().resolve()
        if repo_path.exists():
            repo = f"file://{repo_path}"

    click.echo(f"🤖 Persona: {persona}")
    click.echo(f"📋 Task: {task}")
    click.echo(f"📁 Repo: {repo}")
    click.echo(f"🌿 Branch: {branch}")
    click.echo("-" * 50)

    async def _run():
        executor = AgentExecutor(
            repo_url=repo,
            branch=branch,
        )

        # Load persona to show info
        store = PersonaStore()
        try:
            p = store.get(persona)
            if verbose:
                click.echo(f"📝 {p.display_name}: {p.description}")
        except FileNotFoundError:
            click.echo(f"❌ Persona not found: {persona}", err=True)
            click.echo("Run 'cc personas' to see available personas.", err=True)
            return None

        result = await executor.run(
            persona=persona,
            task=task,
            branch=branch,
            create_pr=pr,
            max_turns=max_turns,
        )

        return result

    try:
        result = asyncio.run(_run())

        if result is None:
            sys.exit(1)

        click.echo("-" * 50)

        if result.sandbox_result.success:
            click.echo("✅ Success!")
            if result.sandbox_result.files_changed:
                click.echo(f"📝 Files changed: {', '.join(result.sandbox_result.files_changed)}")
            if result.sandbox_result.pr_url:
                click.echo(f"🔗 PR: {result.sandbox_result.pr_url}")
        else:
            click.echo("❌ Failed")
            if result.sandbox_result.error:
                click.echo(f"Error: {result.sandbox_result.error}")

        click.echo(f"⏱️  Duration: {result.sandbox_result.duration_seconds:.1f}s")
        click.echo(f"💰 Cost: ${result.sandbox_result.cost_usd:.4f}")

    except Exception as e:
        click.echo(f"❌ Error: {e}", err=True)
        if verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument("name")
def show(name: str):
    """Show details for a specific persona."""
    store = PersonaStore()

    try:
        p = store.get(name)
    except FileNotFoundError:
        click.echo(f"Persona not found: {name}", err=True)
        sys.exit(1)

    click.echo(f"\n{p.display_name}")
    click.echo("=" * len(p.display_name))
    click.echo(f"\nCategory: {p.category}")
    click.echo(f"Model: {p.model}")
    click.echo(f"Temperature: {p.temperature}")
    click.echo(f"Requires sandbox: {p.requires_sandbox}")

    if p.tags:
        click.echo(f"Tags: {', '.join(p.tags)}")

    click.echo(f"\nDescription:\n{p.description}")
    click.echo(f"\nSystem Prompt:\n{'-' * 40}\n{p.system_prompt[:500]}...")


if __name__ == "__main__":
    cli()
