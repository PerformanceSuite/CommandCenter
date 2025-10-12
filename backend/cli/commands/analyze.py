"""
Analyze commands for CommandCenter CLI.

Commands for analyzing projects and GitHub repositories.
"""

import click
from pathlib import Path
import json
import yaml
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
def project(ctx, path, github, export, create_tasks, no_cache):
    """
    Analyze a project directory or GitHub repository.

    Examples:
      commandcenter analyze project .
      commandcenter analyze project --github facebook/react
      commandcenter analyze project . --create-tasks --export json
    """
    config = ctx.obj["config"]

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
                export_path = Path(f"analysis-{result.get('id')}.{export}")
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
