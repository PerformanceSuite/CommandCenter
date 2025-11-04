"""Follow command for live event streaming.

Usage:
    hub follow --subject "hub.test.*"
"""
import asyncio
import click
from datetime import datetime, timezone
from typing import Optional

from rich.console import Console
from rich.live import Live
from rich.table import Table

from app.cli.utils.nats_client import subscribe_stream
from app.config import get_nats_url


@click.command()
@click.option(
    '--subject',
    '-s',
    default='hub.>',
    help='Filter by subject pattern (default: hub.>)'
)
@click.option(
    '--format',
    '-f',
    type=click.Choice(['table', 'json', 'compact']),
    default='compact',
    help='Output format (default: compact)'
)
def follow(subject: str, format: str):
    """Follow live events in real-time.

    Streams events from NATS as they occur. Press Ctrl+C to stop.

    Examples:
        hub follow --subject "hub.test.*"
        hub follow --format json
        hub follow  # All hub events
    """
    console = Console()

    # Track events for table display
    recent_events = []
    max_display = 20

    async def event_handler(subj: str, data: dict):
        """Handle incoming events."""
        nonlocal recent_events

        timestamp = data.get('timestamp', datetime.now(timezone.utc).isoformat())
        correlation_id = data.get('correlation_id', 'unknown')[:8]
        payload = data.get('payload', {})

        if format == 'json':
            # JSON output
            import json
            console.print(json.dumps(data, indent=2))
        elif format == 'compact':
            # One-line compact format
            console.print(
                f"[cyan]{timestamp}[/cyan] "
                f"[green]{subj}[/green] "
                f"[yellow]{correlation_id}[/yellow] "
                f"{payload}"
            )
        else:
            # Table format (update live)
            recent_events.append({
                'timestamp': timestamp,
                'subject': subj,
                'correlation_id': correlation_id,
                'payload': str(payload)[:50]
            })

            # Keep only recent events
            recent_events = recent_events[-max_display:]

    async def stream_events():
        """Start event stream."""
        try:
            console.print(f"[bold]Following events: {subject}[/bold]")
            console.print("[dim]Press Ctrl+C to stop[/dim]\n")

            await subscribe_stream(
                get_nats_url(),
                subject,
                event_handler
            )
        except asyncio.CancelledError:
            console.print("\n[yellow]Stopped[/yellow]")
        except KeyboardInterrupt:
            console.print("\n[yellow]Stopped[/yellow]")
        except Exception as e:
            # Handle connection errors gracefully
            error_msg = str(e)
            if "connection" in error_msg.lower() or "refused" in error_msg.lower():
                console.print("[red]Error: Cannot connect to NATS server. Is it running?[/red]", err=True)
            else:
                console.print(f"[red]Error: {e}[/red]", err=True)

    # Run stream
    try:
        asyncio.run(stream_events())
    except KeyboardInterrupt:
        pass  # Clean exit
