"""
Analyze commands for CommandCenter CLI.

Commands for analyzing projects and GitHub repositories.
"""

import click
from pathlib import Path
import json
import yaml
import time
from cli.api_client import APIClient, APIError
from cli.output import (
    display_analysis_results,
    display_error,
    display_success,
    display_statistics,
    create_progress_bar,
)


@click.group()
def analyze():
    """Analyze projects to detect technologies and research gaps"""
    pass


@analyze.command("project")
@click.argument("path", type=click.Path(exists=True), default=".")
@click.option(
    "--github",
    help="Analyze GitHub repository (format: owner/repo)",
)
@click.option(
    "--export",
    type=click.Choice(["json", "yaml"]),
    help="Export results to file",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    help="Output path for export (default: analysis-{id}.{format})",
)
@click.option(
    "--watch",
    "-w",
    is_flag=True,
    help="Watch mode: re-analyze on file changes",
)
@click.option(
    "--create-tasks",
    is_flag=True,
    help="Auto-generate research tasks from gaps",
)
@click.option(
    "--no-cache",
    is_flag=True,
    help="Disable cache, force fresh analysis",
)
@click.pass_context
def project(ctx, path, github, export, output, watch, create_tasks, no_cache):
    """
    Analyze a project directory or GitHub repository.

    Examples:
      commandcenter analyze project .
      commandcenter analyze project --github facebook/react
      commandcenter analyze project . --create-tasks --export json
      commandcenter analyze project . --watch  # Re-analyze on file changes
    """
    config = ctx.obj["config"]

    # Watch mode
    if watch:
        if github:
            display_error("Watch mode not supported for GitHub repositories")
            raise click.Abort()

        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler

            project_path = Path(path).resolve()
            last_analysis_time = 0
            debounce_seconds = 1.0

            class AnalysisHandler(FileSystemEventHandler):
                def on_any_event(self, event):
                    nonlocal last_analysis_time
                    # Ignore changes in common ignored directories
                    if any(ignored in event.src_path for ignored in
                           ['.git', '__pycache__', 'node_modules', '.venv', 'venv']):
                        return

                    # Debounce: only analyze if 1 second has passed
                    current_time = time.time()
                    if current_time - last_analysis_time < debounce_seconds:
                        return

                    last_analysis_time = current_time
                    click.echo(f"\n[{time.strftime('%H:%M:%S')}] File changed, re-analyzing...")
                    perform_analysis()

            def perform_analysis():
                try:
                    with APIClient(config.api.url, config.auth.token, config.api.timeout) as api:
                        with create_progress_bar("Analyzing...") as progress:
                            task = progress.add_task(f"Analyzing {project_path.name}...", total=None)
                            result = api.analyze_project(str(project_path), use_cache=not no_cache)
                            progress.update(task, completed=True)

                        display_analysis_results(result, format=config.output.format)

                        if export:
                            export_path = Path(output) if output else Path(f"analysis-{result.get('id')}.{export}")
                            export_path.parent.mkdir(parents=True, exist_ok=True)
                            with open(export_path, "w") as f:
                                if export == "json":
                                    json.dump(result, f, indent=2)
                                else:
                                    yaml.dump(result, f)
                            display_success(f"Exported to {export_path}")

                except Exception as e:
                    display_error(f"Analysis failed: {e}")

            # Initial analysis
            click.echo(f"[Watch Mode] Watching {project_path}")
            click.echo("Press Ctrl+C to exit or Enter to manually trigger analysis\n")
            perform_analysis()

            # Setup file watcher
            observer = Observer()
            observer.schedule(AnalysisHandler(), str(project_path), recursive=True)
            observer.start()

            try:
                while True:
                    user_input = click.getchar(echo=False)
                    if user_input in ['\r', '\n']:  # Enter key
                        click.echo("\nManual analysis triggered...")
                        perform_analysis()
            except KeyboardInterrupt:
                observer.stop()
                click.echo("\n[Watch Mode] Stopped")
            observer.join()
            return

        except ImportError:
            display_error("Watch mode requires 'watchdog' library. Install with: pip install watchdog")
            raise click.Abort()

    # Normal (non-watch) mode
    try:
        with APIClient(config.api.url, config.auth.token, config.api.timeout) as api:
            with create_progress_bar("Analyzing...") as progress:
                if github:
                    task = progress.add_task(f"Analyzing {github}...", total=None)
                    result = api.analyze_github_repo(github, use_cache=not no_cache)
                else:
                    path = Path(path).resolve()
                    task = progress.add_task(f"Analyzing {path.name}...", total=None)
                    result = api.analyze_project(str(path), use_cache=not no_cache)
                progress.update(task, completed=True)

            # Display results
            display_analysis_results(result, format=config.output.format)

            # Create research tasks if requested
            if create_tasks:
                click.echo("\n")
                with create_progress_bar("Creating research tasks...") as progress:
                    task = progress.add_task("Creating tasks...", total=None)
                    tasks = api.create_research_tasks_from_analysis(result.get("id"))
                    progress.update(task, completed=True)
                display_success(f"Created {len(tasks)} research tasks")

            # Export if requested
            if export:
                export_path = Path(output) if output else Path(f"analysis-{result.get('id')}.{export}")
                export_path.parent.mkdir(parents=True, exist_ok=True)
                with open(export_path, "w") as f:
                    if export == "json":
                        json.dump(result, f, indent=2)
                    else:
                        yaml.dump(result, f)
                display_success(f"Exported to {export_path}")

    except APIError as e:
        display_error(f"Analysis failed: {e.message}")
        raise click.Abort()
    except Exception as e:
        display_error(f"Unexpected error: {e}")
        if config.output.verbose:
            raise
        raise click.Abort()


@analyze.command("stats")
@click.pass_context
def stats(ctx):
    """
    Show analysis statistics.

    Example:
      commandcenter analyze stats
    """
    config = ctx.obj["config"]

    try:
        with APIClient(config.api.url, config.auth.token, config.api.timeout) as api:
            with create_progress_bar("Fetching statistics...") as progress:
                task = progress.add_task("Loading...", total=None)
                stats = api.get_analysis_statistics()
                progress.update(task, completed=True)

            display_statistics(stats)

    except APIError as e:
        display_error(f"Failed to fetch statistics: {e.message}")
        raise click.Abort()
    except Exception as e:
        display_error(f"Unexpected error: {e}")
        if config.output.verbose:
            raise
        raise click.Abort()
