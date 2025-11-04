"""Output formatters for CLI.

Uses rich library for beautiful terminal output.
"""
import json
from typing import List, Optional
from datetime import datetime

from rich.console import Console
from rich.table import Table
from rich.json import JSON

from app.models.event import Event


def format_events_table(
    events: List[Event],
    limit: Optional[int] = None,
    show_payload: bool = False
) -> str:
    """Format events as a table.

    Args:
        events: List of Event objects
        limit: Maximum events to display
        show_payload: Include payload column

    Returns:
        Formatted table string
    """
    if not events:
        return "No events found."

    # Create table
    table = Table(title="Events")

    table.add_column("Timestamp", style="cyan")
    table.add_column("Subject", style="green")
    table.add_column("Correlation ID", style="yellow")

    if show_payload:
        table.add_column("Payload", style="magenta")

    # Add rows
    for event in events[:limit] if limit else events:
        # Format timestamp
        ts = event.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Truncate long subjects
        subject = event.subject
        if len(subject) > 50:
            subject = subject[:47] + "..."

        # Short correlation ID (first 8 chars)
        corr_id = str(event.correlation_id)[:8]

        row = [ts, subject, corr_id]

        if show_payload:
            payload_str = json.dumps(event.payload)
            if len(payload_str) > 50:
                payload_str = payload_str[:47] + "..."
            row.append(payload_str)

        table.add_row(*row)

    # Render to string
    console = Console()
    with console.capture() as capture:
        console.print(table)

    return capture.get()


def format_event_json(event: Event, pretty: bool = True) -> str:
    """Format single event as JSON.

    Args:
        event: Event object
        pretty: Pretty-print JSON

    Returns:
        JSON string
    """
    event_dict = {
        "id": str(event.id),
        "subject": event.subject,
        "origin": event.origin,
        "correlation_id": str(event.correlation_id),
        "payload": event.payload,
        "timestamp": event.timestamp.isoformat()
    }

    if pretty:
        return json.dumps(event_dict, indent=2)
    else:
        return json.dumps(event_dict)


def format_events_json(events: List[Event], pretty: bool = True) -> str:
    """Format multiple events as JSON array.

    Args:
        events: List of Event objects
        pretty: Pretty-print JSON

    Returns:
        JSON array string
    """
    events_list = []

    for event in events:
        events_list.append({
            "id": str(event.id),
            "subject": event.subject,
            "origin": event.origin,
            "correlation_id": str(event.correlation_id),
            "payload": event.payload,
            "timestamp": event.timestamp.isoformat()
        })

    if pretty:
        return json.dumps(events_list, indent=2)
    else:
        return json.dumps(events_list)
