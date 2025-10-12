"""
Configuration commands for CommandCenter CLI.

Commands for managing CLI configuration.
"""

import click
from cli.config import Config
from cli.output import (
    display_success,
    display_error,
    display_config,
)
from rich.console import Console

console = Console()


@click.group("config")
def config():
    """Manage CLI configuration"""
    pass


@config.command("init")
@click.option(
    "--force",
    is_flag=True,
    help="Overwrite existing configuration",
)
@click.pass_context
def init(ctx, force):
    """
    Initialize configuration file.

    Example:
      commandcenter config init
      commandcenter config init --force
    """
    config_path = Config.get_default_config_path()

    if config_path.exists() and not force:
        display_error(
            f"Configuration already exists at {config_path}. Use --force to overwrite."
        )
        raise click.Abort()

    # Create default config
    new_config = Config()
    new_config.save(config_path)

    display_success(f"Configuration initialized at {config_path}")


@config.command("get")
@click.argument("key")
@click.pass_context
def get(ctx, key):
    """
    Get configuration value.

    Examples:
      commandcenter config get api.url
      commandcenter config get auth.token
    """
    config_obj = ctx.obj["config"]

    try:
        value = config_obj.get(key)
        console.print(f"[bold]{key}[/bold]: [green]{value}[/green]")
    except AttributeError:
        display_error(f"Configuration key '{key}' not found")
        raise click.Abort()


@config.command("set")
@click.argument("key")
@click.argument("value")
@click.pass_context
def set_config(ctx, key, value):
    """
    Set configuration value.

    Examples:
      commandcenter config set api.url http://localhost:8000
      commandcenter config set auth.token my-token
      commandcenter config set output.format json
    """
    config_obj = ctx.obj["config"]
    config_path = ctx.obj["config_path"]

    try:
        # Type conversion for known boolean/int fields
        if key in ["api.timeout", "agents.max_concurrent"]:
            value = int(value)
        elif key in [
            "api.verify_ssl",
            "output.verbose",
            "analysis.cache",
            "analysis.create_tasks",
            "agents.retry_failed",
        ]:
            value = value.lower() in ["true", "1", "yes", "y"]

        config_obj.set(key, value)
        config_obj.save(config_path)

        display_success(f"Set {key} = {value}")
    except AttributeError:
        display_error(f"Configuration key '{key}' not found")
        raise click.Abort()
    except Exception as e:
        display_error(f"Failed to set configuration: {e}")
        raise click.Abort()


@config.command("list")
@click.pass_context
def list_config(ctx):
    """
    List all configuration values.

    Example:
      commandcenter config list
    """
    config_obj = ctx.obj["config"]
    config_data = config_obj.model_dump()

    display_config(config_data)


@config.command("path")
@click.pass_context
def path(ctx):
    """
    Show configuration file path.

    Example:
      commandcenter config path
    """
    config_path = ctx.obj["config_path"]
    console.print(f"[bold]Configuration file:[/bold] {config_path}")
