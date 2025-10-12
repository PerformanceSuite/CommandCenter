"""
Interactive TUI application for knowledge base search.

Provides a rich terminal interface with live search, history, and results display.
"""

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal
from textual.widgets import Header, Footer, Input, Static, ListView, ListItem, Label, Button
from textual.binding import Binding
from rich.syntax import Syntax
from rich.table import Table
from typing import Optional, List, Dict, Any

from cli.api_client import APIClient, APIError


class SearchResultsView(Static):
    """Widget to display search results in a scrollable view."""

    def __init__(self):
        super().__init__()
        self.results = []

    def update_results(self, results: List[Dict[str, Any]]) -> None:
        """Update the displayed results."""
        self.results = results

        if not results:
            self.update("[yellow]No results found[/yellow]")
            return

        # Create results table
        table = Table(title="Search Results", show_header=True, header_style="bold magenta")
        table.add_column("Score", justify="right", style="cyan", width=8)
        table.add_column("Source", style="green", width=20)
        table.add_column("Category", style="blue", width=15)
        table.add_column("Content", style="white")

        for result in results[:10]:  # Show top 10
            score = f"{result.get('score', 0):.2f}"
            source = result.get("source", "Unknown")[:18]
            category = result.get("category", "N/A")[:13]
            content = result.get("content", "")[:60]

            table.add_row(score, source, category, content)

        self.update(table)


class SearchHistoryView(ListView):
    """Widget to display search history."""

    def __init__(self):
        super().__init__()
        self.history = []

    def add_query(self, query: str) -> None:
        """Add a query to history."""
        if query not in self.history:
            self.history.insert(0, query)  # Add to beginning
            if len(self.history) > 20:  # Keep last 20
                self.history = self.history[:20]

        # Refresh display
        self.clear()
        for q in self.history:
            self.append(ListItem(Label(q)))


class SearchApp(App):
    """
    Interactive search TUI application.

    Provides a rich terminal interface for searching the knowledge base
    with live results, history, and keyboard shortcuts.
    """

    CSS = """
    #search-container {
        height: 100%;
    }

    #search-input-container {
        height: 3;
        border: solid $primary;
        padding: 0 1;
    }

    #search-input {
        width: 100%;
    }

    #content-container {
        height: 1fr;
    }

    #history-panel {
        width: 25;
        border: solid $accent;
        padding: 1;
    }

    #results-panel {
        width: 1fr;
        border: solid $success;
        padding: 1;
    }

    #status-bar {
        height: 1;
        background: $surface;
        color: $text;
        padding: 0 1;
    }
    """

    BINDINGS = [
        Binding("ctrl+q", "quit", "Quit", show=True),
        Binding("ctrl+c", "quit", "Quit", show=False),
        Binding("escape", "clear_input", "Clear", show=True),
        Binding("ctrl+h", "toggle_history", "Toggle History", show=True),
    ]

    def __init__(self, api_url: str, auth_token: Optional[str] = None, timeout: int = 30):
        """
        Initialize search TUI app.

        Args:
            api_url: API base URL
            auth_token: Optional authentication token
            timeout: Request timeout in seconds
        """
        super().__init__()
        self.api_url = api_url
        self.auth_token = auth_token
        self.timeout = timeout
        self.show_history = True
        self.current_query = ""

    def compose(self) -> ComposeResult:
        """Compose the TUI layout."""
        yield Header(show_clock=True)

        with Container(id="search-container"):
            # Search input
            with Vertical(id="search-input-container"):
                yield Input(
                    placeholder="Enter search query...",
                    id="search-input",
                )

            # Content area (history + results)
            with Horizontal(id="content-container"):
                # Search history sidebar
                with Vertical(id="history-panel"):
                    yield Static("[bold]Search History[/bold]", id="history-title")
                    yield SearchHistoryView()

                # Search results
                with Vertical(id="results-panel"):
                    yield Static("[bold]Results[/bold]", id="results-title")
                    yield SearchResultsView()

            # Status bar
            yield Static(
                "Ready | Press Ctrl+Q to quit | Ctrl+H to toggle history",
                id="status-bar",
            )

        yield Footer()

    def on_mount(self) -> None:
        """Handle app mount event."""
        # Focus on search input
        self.query_one("#search-input", Input).focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle search input submission."""
        query = event.value.strip()

        if not query:
            return

        self.current_query = query

        # Update status
        self.query_one("#status-bar", Static).update(f"Searching: {query}...")

        # Add to history
        history_view = self.query_one(SearchHistoryView)
        history_view.add_query(query)

        # Perform search
        try:
            with APIClient(self.api_url, self.auth_token, self.timeout) as api:
                results = api.search_knowledge(query=query, limit=10)

                # Update results display
                results_view = self.query_one(SearchResultsView)
                results_view.update_results(results)

                # Update status
                result_count = len(results)
                self.query_one(
                    "#status-bar", Static
                ).update(
                    f"Found {result_count} results | Ctrl+Q to quit | Ctrl+H to toggle history"
                )

        except APIError as e:
            # Show error in results
            results_view = self.query_one(SearchResultsView)
            results_view.update(f"[red]Error:[/red] {e.message}")

            self.query_one("#status-bar", Static).update(
                f"Search failed: {e.message}"
            )
        except Exception as e:
            results_view = self.query_one(SearchResultsView)
            results_view.update(f"[red]Unexpected error:[/red] {str(e)}")

            self.query_one("#status-bar", Static).update(
                f"Error: {str(e)}"
            )

    def action_clear_input(self) -> None:
        """Clear the search input."""
        search_input = self.query_one("#search-input", Input)
        search_input.value = ""
        search_input.focus()

    def action_toggle_history(self) -> None:
        """Toggle history panel visibility."""
        self.show_history = not self.show_history
        history_panel = self.query_one("#history-panel")

        if self.show_history:
            history_panel.styles.display = "block"
        else:
            history_panel.styles.display = "none"

    def action_quit(self) -> None:
        """Quit the application."""
        self.exit()


def run_search_tui(api_url: str, auth_token: Optional[str] = None, timeout: int = 30) -> None:
    """
    Run the search TUI application.

    Args:
        api_url: API base URL
        auth_token: Optional authentication token
        timeout: Request timeout in seconds
    """
    app = SearchApp(api_url, auth_token, timeout)
    app.run()
