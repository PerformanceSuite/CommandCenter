"""
Search commands for CommandCenter CLI.

RAG-powered knowledge base search commands.
"""

import click
from cli.api_client import APIClient, APIError
from cli.output import create_progress_bar, display_error, display_search_results
from rich.console import Console
from rich.prompt import Prompt

console = Console()


@click.command()
@click.argument("query", required=False)
@click.option(
    "--filter",
    "filter_type",
    type=click.Choice(["technology", "research"]),
    help="Filter by type",
)
@click.option(
    "--limit",
    type=int,
    default=10,
    help="Maximum number of results",
)
@click.option(
    "--interactive",
    "-i",
    is_flag=True,
    help="Interactive search mode (prompt-based)",
)
@click.option(
    "--tui",
    is_flag=True,
    help="Launch full TUI (Text User Interface) mode",
)
@click.pass_context
def search(ctx, query, filter_type, limit, interactive, tui):
    """
    Search knowledge base using RAG.

    Examples:
      commandcenter search "FastAPI authentication"
      commandcenter search "RAG implementation" --filter technology
      commandcenter search --interactive  # Prompt-based interactive mode
      commandcenter search --tui          # Full TUI interface
    """
    config = ctx.obj["config"]

    # TUI mode takes precedence
    if tui:
        try:
            from cli.tui import SearchApp

            app = SearchApp(
                api_url=config.api.url,
                auth_token=config.auth.token,
                timeout=config.api.timeout,
            )
            app.run()
            return

        except ImportError:
            display_error("TUI mode requires 'textual' library. Install with: pip install textual")
            raise click.Abort()
        except Exception as e:
            display_error(f"TUI failed to start: {e}")
            if config.output.verbose:
                raise
            raise click.Abort()

    def perform_search(search_query: str):
        """Execute a search query."""
        try:
            with APIClient(config.api.url, config.auth.token, config.api.timeout) as api:
                with create_progress_bar("Searching...") as progress:
                    task = progress.add_task("Searching knowledge base...", total=None)
                    results = api.search_knowledge(
                        query=search_query,
                        filter_type=filter_type,
                        limit=limit,
                    )
                    progress.update(task, completed=True)

                display_search_results(results)

        except APIError as e:
            display_error(f"Search failed: {e.message}")
            return False
        except Exception as e:
            display_error(f"Unexpected error: {e}")
            if config.output.verbose:
                raise
            return False
        return True

    if interactive:
        # Interactive mode - keep prompting for queries
        console.print("[bold]Interactive Search Mode[/bold]")
        console.print("Enter 'exit' or press Ctrl+C to quit\n")

        try:
            while True:
                search_query = Prompt.ask("[bold cyan]Search[/bold cyan]")

                if search_query.lower() in ["exit", "quit", "q"]:
                    break

                if not search_query.strip():
                    continue

                perform_search(search_query)
                console.print()  # Blank line between searches

        except KeyboardInterrupt:
            console.print("\n[yellow]Exiting interactive mode[/yellow]")
    else:
        # Single query mode
        if not query:
            display_error("Query required. Use --interactive for interactive mode.")
            raise click.Abort()

        success = perform_search(query)
        if not success:
            raise click.Abort()
