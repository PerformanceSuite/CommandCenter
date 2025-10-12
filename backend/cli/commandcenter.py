"""
CommandCenter CLI - Main entry point.

Professional command-line interface for CommandCenter R&D management system.
"""

import click
from pathlib import Path
from cli.config import Config
from cli.commands.analyze import analyze
from cli.commands.agents import agents
from cli.commands.search import search
from cli.commands.config_cmd import config as config_cmd
from cli.commands.completion import completion


@click.group()
@click.version_option(version="0.1.0", prog_name="commandcenter")
@click.option(
    "--config",
    type=click.Path(exists=True),
    default=None,
    help="Path to config file (default: ~/.commandcenter/config.yaml)",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
@click.option(
    "--format",
    type=click.Choice(["table", "json", "yaml"]),
    default=None,
    help="Output format",
)
@click.pass_context
def cli(ctx, config, verbose, format):
    """
    CommandCenter CLI - R&D Management & Knowledge Base

    Analyze projects, orchestrate agents, and search knowledge.

    Examples:
      commandcenter analyze project .
      commandcenter agents launch
      commandcenter search "FastAPI authentication"
    """
    # Initialize context
    ctx.ensure_object(dict)

    # Load config
    config_path = Path(config) if config else Config.get_default_config_path()
    ctx.obj["config"] = Config.load(config_path)
    ctx.obj["config_path"] = config_path

    # Override with CLI options
    if verbose:
        ctx.obj["config"].output.verbose = True
    if format:
        ctx.obj["config"].output.format = format


# Register command groups
cli.add_command(analyze)
cli.add_command(agents)
cli.add_command(search)
cli.add_command(config_cmd)
cli.add_command(completion)


if __name__ == "__main__":
    cli()
