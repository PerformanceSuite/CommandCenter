"""CLI entry point for hub events command.

Usage:
    hub events [COMMAND]
    hub events query --subject "hub.test.*"
    hub events follow --subject "hub.>"
"""
import click
from app.cli import __version__


@click.group()
@click.version_option(version=__version__)
@click.pass_context
def cli(ctx):
    """CommandCenter Hub Event CLI.

    Tools for querying, streaming, and monitoring Hub events.
    """
    ctx.ensure_object(dict)


# Subcommands will be added in subsequent tasks


if __name__ == '__main__':
    cli()
