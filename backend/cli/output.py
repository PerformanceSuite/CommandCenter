"""
Rich terminal output utilities for CommandCenter CLI.

Provides beautiful, colorful terminal output using the Rich library.
"""

from typing import Dict, Any, List
from rich.console import Console
from rich.table import Table
from rich.tree import Tree
from rich.syntax import Syntax
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
from datetime import datetime
import json

console = Console()


def display_success(message: str) -> None:
    """
    Display success message with checkmark.

    Args:
        message: Success message to display
    """
    console.print(f"[bold green]✓[/bold green] {message}")


def display_error(message: str) -> None:
    """
    Display error message with X mark.

    Args:
        message: Error message to display
    """
    console.print(f"[bold red]✗[/bold red] {message}", style="red")


def display_warning(message: str) -> None:
    """
    Display warning message with warning symbol.

    Args:
        message: Warning message to display
    """
    console.print(f"[bold yellow]⚠[/bold yellow] {message}", style="yellow")


def display_info(message: str) -> None:
    """
    Display info message.

    Args:
        message: Info message to display
    """
    console.print(f"[bold blue]ℹ[/bold blue] {message}")


def display_json(data: Any) -> None:
    """
    Display data as syntax-highlighted JSON.

    Args:
        data: Data to display as JSON
    """
    json_str = json.dumps(data, indent=2)
    syntax = Syntax(json_str, "json", theme="monokai")
    console.print(syntax)


def display_analysis_results(result: Dict[str, Any], format: str = "table") -> None:
    """
    Display project analysis results.

    Args:
        result: Analysis results dictionary
        format: Output format (table, json, yaml)
    """
    if format == "json":
        display_json(result)
        return

    # Summary panel
    summary = Panel(
        f"[bold]Project:[/bold] {result.get('project_path', 'N/A')}\n"
        f"[bold]Analyzed:[/bold] {result.get('analyzed_at', 'N/A')}\n"
        f"[bold]Duration:[/bold] {result.get('analysis_duration_ms', 0)}ms",
        title="Analysis Summary",
        border_style="green",
    )
    console.print(summary)

    # Technologies table
    technologies = result.get("technologies", [])
    if technologies:
        tech_table = Table(title="\nDetected Technologies")
        tech_table.add_column("Name", style="cyan")
        tech_table.add_column("Category", style="blue")
        tech_table.add_column("Version", style="green")
        tech_table.add_column("Confidence", style="yellow")

        for tech in technologies:
            tech_table.add_row(
                tech.get("name", "Unknown"),
                tech.get("category", "Unknown"),
                tech.get("version") or "-",
                f"{tech.get('confidence', 0):.0%}",
            )

        console.print(tech_table)

    # Dependencies tree
    dependencies = result.get("dependencies", [])
    if dependencies:
        console.print("\n[bold]Dependencies:[/bold]")

        deps_by_type = {}
        for dep in dependencies:
            dep_type = dep.get("type", "unknown")
            deps_by_type.setdefault(dep_type, []).append(dep)

        for dep_type, deps in deps_by_type.items():
            tree = Tree(f"[bold]{dep_type.upper()}[/bold]")
            for dep in deps[:10]:  # Limit to 10 per type
                is_outdated = dep.get("is_outdated", False)
                status = "🔴" if is_outdated else "🟢"
                tree.add(f"{status} {dep.get('name')}@{dep.get('version')}")
            console.print(tree)

    # Research gaps
    research_gaps = result.get("research_gaps", [])
    if research_gaps:
        console.print("\n[bold red]Research Gaps:[/bold red]")

        gaps_table = Table()
        gaps_table.add_column("Technology", style="cyan")
        gaps_table.add_column("Current", style="yellow")
        gaps_table.add_column("Latest", style="green")
        gaps_table.add_column("Severity", style="red")

        for gap in research_gaps:
            gaps_table.add_row(
                gap.get("technology", "Unknown"),
                gap.get("current_version", "N/A"),
                gap.get("latest_version", "N/A"),
                gap.get("severity", "unknown"),
            )

        console.print(gaps_table)


def display_orchestration_status(orchestration: Dict[str, Any]) -> None:
    """
    Display agent orchestration status.

    Args:
        orchestration: Orchestration status dictionary
    """
    table = Table(title=f"Orchestration {orchestration.get('id', 'Unknown')}")
    table.add_column("Agent", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Progress", style="yellow")
    table.add_column("Duration", style="blue")

    agents = orchestration.get("agents", [])
    for agent in agents:
        status_emoji = {
            "pending": "⏸️",
            "running": "▶️",
            "completed": "✅",
            "failed": "❌",
        }.get(agent.get("status", "unknown"), "❓")

        table.add_row(
            agent.get("name", "Unknown"),
            f"{status_emoji} {agent.get('status', 'unknown')}",
            f"{agent.get('progress', 0)}%",
            agent.get("duration") or "-",
        )

    console.print(table)


def display_orchestrations_list(orchestrations: List[Dict[str, Any]]) -> None:
    """
    Display list of orchestrations.

    Args:
        orchestrations: List of orchestration dictionaries
    """
    table = Table(title="Recent Orchestrations")
    table.add_column("ID", style="cyan")
    table.add_column("Status", style="green")
    table.add_column("Started", style="yellow")
    table.add_column("Agents", style="blue")

    for orch in orchestrations:
        started_at = orch.get("started_at")
        if started_at:
            try:
                dt = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
                started_str = dt.strftime("%Y-%m-%d %H:%M")
            except Exception:
                started_str = started_at
        else:
            started_str = "N/A"

        table.add_row(
            str(orch.get("id", "Unknown")),
            orch.get("status", "unknown"),
            started_str,
            f"{orch.get('completed_agents', 0)}/{orch.get('total_agents', 0)}",
        )

    console.print(table)


def display_search_results(results: Dict[str, Any]) -> None:
    """
    Display RAG search results.

    Args:
        results: Search results dictionary
    """
    query = results.get("query", "")
    matches = results.get("matches", [])

    console.print(f"\n[bold]Search Results for:[/bold] {query}\n")

    if not matches:
        console.print("[yellow]No results found.[/yellow]")
        return

    for i, match in enumerate(matches, 1):
        # Create panel for each result
        content = match.get("content", "")
        score = match.get("score", 0)
        source = match.get("source", "Unknown")
        category = match.get("category", "Unknown")

        panel = Panel(
            f"{content}\n\n"
            f"[dim]Source: {source} | Category: {category} | Score: {score:.2f}[/dim]",
            title=f"Result {i}",
            border_style="blue",
        )
        console.print(panel)


def display_statistics(stats: Dict[str, Any]) -> None:
    """
    Display statistics table.

    Args:
        stats: Statistics dictionary
    """
    table = Table(title="Analysis Statistics")
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    for key, value in stats.items():
        # Convert snake_case to Title Case
        metric_name = key.replace("_", " ").title()
        table.add_row(metric_name, str(value))

    console.print(table)


def create_progress_bar(description: str) -> Progress:
    """
    Create a progress bar with spinner.

    Args:
        description: Progress description

    Returns:
        Progress object
    """
    return Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console,
    )


def display_config(config_data: Dict[str, Any]) -> None:
    """
    Display configuration in a formatted table.

    Args:
        config_data: Configuration dictionary
    """
    table = Table(title="CommandCenter Configuration")
    table.add_column("Key", style="cyan")
    table.add_column("Value", style="green")

    def flatten_dict(d: Dict[str, Any], prefix: str = "") -> None:
        """Recursively flatten nested dictionary."""
        for key, value in d.items():
            full_key = f"{prefix}.{key}" if prefix else key
            if isinstance(value, dict):
                flatten_dict(value, full_key)
            else:
                table.add_row(full_key, str(value))

    flatten_dict(config_data)
    console.print(table)


def display_logs(logs: List[Dict[str, Any]]) -> None:
    """
    Display agent logs.

    Args:
        logs: List of log entries
    """
    for log in logs:
        timestamp = log.get("timestamp", "")
        level = log.get("level", "INFO")
        message = log.get("message", "")

        level_colors = {
            "DEBUG": "blue",
            "INFO": "green",
            "WARNING": "yellow",
            "ERROR": "red",
            "CRITICAL": "bold red",
        }
        color = level_colors.get(level.upper(), "white")

        console.print(f"[dim]{timestamp}[/dim] [{color}]{level}[/{color}] {message}")
