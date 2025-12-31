#!/usr/bin/env python3
"""
CommandCenter Agent CLI

Run coding agents to execute tasks on repositories.

Usage:
    python -m cli.cc_agent run backend-coder --task "Build the personas API endpoint"
    python -m cli.cc_agent run backend-coder frontend-coder --task "Build feature X" --parallel
    python -m cli.cc_agent list-personas
    python -m cli.cc_agent improve-prompt --file prompt.txt
"""

import argparse
import asyncio
import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(
        description="CommandCenter Agent CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List available personas
  python -m cli.cc_agent list-personas

  # Run a single agent
  python -m cli.cc_agent run backend-coder --task "Fix the bug in auth.py"

  # Run multiple agents in parallel
  python -m cli.cc_agent run backend-coder frontend-coder --task "Build X" --parallel

  # Analyze and improve a prompt
  python -m cli.cc_agent improve-prompt --file my-prompt.txt
""",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run command
    run_parser = subparsers.add_parser("run", help="Run agent(s) on a task")
    run_parser.add_argument("personas", nargs="+", help="Persona name(s) to run")
    run_parser.add_argument("--task", "-t", required=True, help="Task description")
    run_parser.add_argument(
        "--repo",
        "-r",
        default="https://github.com/PerformanceSuite/CommandCenter",
        help="Repository URL",
    )
    run_parser.add_argument("--branch", "-b", default="main", help="Git branch")
    run_parser.add_argument("--create-pr", action="store_true", help="Create PR with changes")
    run_parser.add_argument("--parallel", action="store_true", help="Run personas in parallel")
    run_parser.add_argument("--max-turns", type=int, default=50, help="Maximum conversation turns")

    # list-personas command
    list_parser = subparsers.add_parser("list-personas", help="List available personas")
    list_parser.add_argument("--category", "-c", help="Filter by category")

    # show-persona command
    show_parser = subparsers.add_parser("show-persona", help="Show persona details")
    show_parser.add_argument("name", help="Persona name")

    # improve-prompt command
    improve_parser = subparsers.add_parser("improve-prompt", help="Analyze and improve a prompt")
    improve_parser.add_argument("--file", "-f", help="Read prompt from file")
    improve_parser.add_argument("--text", "-t", help="Prompt text directly")
    improve_parser.add_argument(
        "--quick", action="store_true", help="Quick check only (no API call)"
    )

    args = parser.parse_args()

    if args.command == "run":
        asyncio.run(cmd_run(args))
    elif args.command == "list-personas":
        cmd_list_personas(args)
    elif args.command == "show-persona":
        cmd_show_persona(args)
    elif args.command == "improve-prompt":
        asyncio.run(cmd_improve_prompt(args))


async def cmd_run(args):
    """Run agent(s) with task."""
    from libs.agent_framework.executor import AgentExecutor

    print(f"🤖 Running agent(s): {', '.join(args.personas)}")
    print(f"📋 Task: {args.task}")
    print(f"📦 Repo: {args.repo} ({args.branch})")
    if args.create_pr:
        print("🔀 Will create PR with changes")
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
    print("\n" + "=" * 60)
    print("RESULTS")
    print("=" * 60)

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
            print(f"   Note: {r.sandbox_result.error}")


def cmd_list_personas(args):
    """List available personas."""
    from libs.agent_framework.persona_store import PersonaStore

    store = PersonaStore()
    personas = store.list(category=args.category)

    if not personas:
        print("No personas found.")
        return

    print(f"\n{'Name':<20} {'Category':<15} {'Description'}")
    print("-" * 70)
    for p in personas:
        desc = p.description[:35] + "..." if len(p.description) > 35 else p.description
        print(f"{p.name:<20} {p.category:<15} {desc}")
    print()


def cmd_show_persona(args):
    """Show persona details."""
    from libs.agent_framework.persona_store import PersonaStore

    store = PersonaStore()
    try:
        p = store.get(args.name)
    except FileNotFoundError:
        print(f"❌ Persona not found: {args.name}")
        return

    print(f"\n🤖 {p.display_name}")
    print(f"   Name: {p.name}")
    print(f"   Category: {p.category}")
    print(f"   Model: {p.model}")
    print(f"   Temperature: {p.temperature}")
    print(f"   Requires Sandbox: {p.requires_sandbox}")
    print(f"   Tags: {', '.join(p.tags)}")
    print(f"\n📝 Description:\n   {p.description}")
    print(f"\n💬 System Prompt:\n{'-'*40}")
    print(p.system_prompt)
    print("-" * 40)


async def cmd_improve_prompt(args):
    """Analyze and improve a prompt."""
    from libs.agent_framework.prompt_improver import PromptImprover

    # Get prompt text
    if args.file:
        with open(args.file) as f:
            prompt = f.read()
    elif args.text:
        prompt = args.text
    else:
        print("Reading prompt from stdin (Ctrl+D when done)...")
        prompt = sys.stdin.read()

    improver = PromptImprover()

    if args.quick:
        # Quick check only
        result = improver.quick_check(prompt)
        print("\n📊 Quick Check Results:")
        print(f"   Has role definition: {'✅' if result['has_role'] else '❌'}")
        print(f"   Has output format: {'✅' if result['has_output_format'] else '❌'}")
        print(f"   Has constraints: {'✅' if result['has_constraints'] else '❌'}")
        print(f"   Word count: {result['word_count']}")

        if result["suggestions"]:
            print("\n💡 Suggestions:")
            for s in result["suggestions"]:
                print(f"   • {s}")

        if result["potential_conflicts"]:
            print("\n⚠️  Potential Conflicts:")
            for c in result["potential_conflicts"]:
                print(f"   • {c}")
        return

    # Full analysis
    print("🔍 Analyzing prompt...")
    result = await improver.analyze(prompt)

    print("\n📊 Scores:")
    for k, v in result.scores.items():
        bar = "█" * (v // 10) + "░" * (10 - (v // 10))
        print(f"   {k:<15} {bar} {v}")

    if result.issues:
        print(f"\n⚠️  Issues ({len(result.issues)}):")
        for issue in result.issues:
            sev_icon = {"high": "🔴", "medium": "🟡", "low": "🟢"}.get(issue.severity, "⚪")
            print(f"   {sev_icon} [{issue.type}] {issue.description}")
            print(f"      💡 {issue.suggestion}")

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
                print(f"✅ Saved to {args.file}")


if __name__ == "__main__":
    main()
