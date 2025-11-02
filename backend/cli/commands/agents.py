"""
Agent orchestration commands for CommandCenter CLI.

Commands for managing and monitoring agent workflows.
"""

import time

import click
from cli.api_client import APIClient, APIError
from cli.output import (
    create_progress_bar,
    display_error,
    display_logs,
    display_orchestration_status,
    display_orchestrations_list,
    display_success,
)
from rich.console import Console
from rich.live import Live

console = Console()


@click.group()
def agents():
    """Manage and orchestrate agents"""
    pass


@agents.command("launch")
@click.option(
    "--workflow",
    type=click.Choice(["full", "analyze-only", "custom"]),
    default="full",
    help="Workflow to execute",
)
@click.option(
    "--max-concurrent",
    type=int,
    default=None,
    help="Maximum concurrent agents",
)
@click.option(
    "--no-watch",
    is_flag=True,
    help="Don't watch orchestration progress",
)
@click.pass_context
def launch(ctx, workflow, max_concurrent, no_watch):
    """
    Launch agent orchestration workflow.

    Examples:
      commandcenter agents launch
      commandcenter agents launch --workflow analyze-only
      commandcenter agents launch --max-concurrent 5
    """
    config = ctx.obj["config"]
    max_concurrent = max_concurrent or config.agents.max_concurrent

    try:
        with APIClient(config.api.url, config.auth.token, config.api.timeout) as api:
            console.print(f"[bold]Launching {workflow} workflow...[/bold]")

            orchestration = api.launch_agents(workflow=workflow, max_concurrent=max_concurrent)

            orch_id = orchestration.get("id")
            display_success(f"Orchestration started: {orch_id}")

            if no_watch:
                console.print(f"\nUse 'commandcenter agents status {orch_id}' to check progress")
                return

            # Live status updates
            console.print("\n[bold]Monitoring progress...[/bold]\n")
            with Live(console=console, refresh_per_second=2) as live:
                while True:
                    orchestration = api.get_orchestration_status(orch_id)
                    display_orchestration_status(orchestration)
                    live.update(display_orchestration_status(orchestration))

                    # Check if complete
                    status = orchestration.get("status")
                    if status in ["completed", "failed", "cancelled"]:
                        break

                    time.sleep(2)

            # Final status
            if orchestration.get("status") == "completed":
                console.print("\n[bold green]Orchestration complete![/bold green]")
            else:
                status = orchestration.get("status")
                console.print(
                    f"\n[bold yellow]Orchestration ended with " f"status: {status}[/bold yellow]"
                )

    except APIError as e:
        display_error(f"Orchestration failed: {e.message}")
        raise click.Abort()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise click.Abort()
    except Exception as e:
        display_error(f"Unexpected error: {e}")
        if config.output.verbose:
            raise
        raise click.Abort()


@agents.command("status")
@click.argument("orchestration_id", required=False)
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    help="Watch status updates in real-time",
)
@click.pass_context
def status(ctx, orchestration_id, watch):
    """
    Show agent orchestration status.

    Examples:
      commandcenter agents status
      commandcenter agents status abc123
      commandcenter agents status abc123 --watch
    """
    config = ctx.obj["config"]

    try:
        with APIClient(config.api.url, config.auth.token, config.api.timeout) as api:
            if orchestration_id:
                if watch:
                    # Watch mode - live updates
                    with Live(console=console, refresh_per_second=2) as live:
                        while True:
                            orch = api.get_orchestration_status(orchestration_id)
                            display_orchestration_status(orch)
                            live.update(display_orchestration_status(orch))

                            status = orch.get("status")
                            if status in ["completed", "failed", "cancelled"]:
                                break

                            time.sleep(2)
                else:
                    # Single status check
                    orchestration = api.get_orchestration_status(orchestration_id)
                    display_orchestration_status(orchestration)
            else:
                # List all recent orchestrations
                orchestrations = api.list_orchestrations(limit=10)
                display_orchestrations_list(orchestrations)

    except APIError as e:
        display_error(f"Failed to fetch status: {e.message}")
        raise click.Abort()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        raise click.Abort()
    except Exception as e:
        display_error(f"Unexpected error: {e}")
        if config.output.verbose:
            raise
        raise click.Abort()


@agents.command("stop")
@click.argument("orchestration_id")
@click.pass_context
def stop(ctx, orchestration_id):
    """
    Stop a running orchestration.

    Example:
      commandcenter agents stop abc123
    """
    config = ctx.obj["config"]

    try:
        with APIClient(config.api.url, config.auth.token, config.api.timeout) as api:
            with create_progress_bar("Stopping orchestration...") as progress:
                task = progress.add_task("Stopping...", total=None)
                api.stop_orchestration(orchestration_id)
                progress.update(task, completed=True)

            display_success(f"Orchestration {orchestration_id} stopped")

    except APIError as e:
        display_error(f"Failed to stop orchestration: {e.message}")
        raise click.Abort()
    except Exception as e:
        display_error(f"Unexpected error: {e}")
        if config.output.verbose:
            raise
        raise click.Abort()


@agents.command("logs")
@click.argument("agent_id")
@click.option(
    "--follow",
    "-f",
    is_flag=True,
    help="Follow log output in real-time",
)
@click.pass_context
def logs(ctx, agent_id, follow):
    """
    View logs for a specific agent.

    Examples:
      commandcenter agents logs agent-123
      commandcenter agents logs agent-123 --follow
    """
    config = ctx.obj["config"]

    try:
        with APIClient(config.api.url, config.auth.token, config.api.timeout) as api:
            if follow:
                # Follow mode - poll for new logs
                console.print(f"[bold]Following logs for {agent_id}...[/bold]\n")
                last_log_count = 0

                try:
                    while True:
                        logs = api.get_agent_logs(agent_id)

                        # Display only new logs
                        new_logs = logs[last_log_count:]
                        if new_logs:
                            display_logs(new_logs)
                            last_log_count = len(logs)

                        time.sleep(2)
                except KeyboardInterrupt:
                    console.print("\n[yellow]Stopped following logs[/yellow]")
            else:
                # Get all logs once
                logs = api.get_agent_logs(agent_id)
                display_logs(logs)

    except APIError as e:
        display_error(f"Failed to fetch logs: {e.message}")
        raise click.Abort()
    except Exception as e:
        display_error(f"Unexpected error: {e}")
        if config.output.verbose:
            raise
        raise click.Abort()


@agents.command("retry")
@click.argument("agent_id")
@click.pass_context
def retry(ctx, agent_id):
    """
    Retry a failed agent.

    Example:
      commandcenter agents retry agent-123
    """
    config = ctx.obj["config"]

    try:
        with APIClient(config.api.url, config.auth.token, config.api.timeout) as api:
            with create_progress_bar("Retrying agent...") as progress:
                task = progress.add_task("Retrying...", total=None)
                api.retry_agent(agent_id)
                progress.update(task, completed=True)

            display_success(f"Agent {agent_id} retry initiated")

    except APIError as e:
        display_error(f"Failed to retry agent: {e.message}")
        raise click.Abort()
    except Exception as e:
        display_error(f"Unexpected error: {e}")
        if config.output.verbose:
            raise
        raise click.Abort()
