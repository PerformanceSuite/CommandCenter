"""Query command for historical events.

Usage:
    hub query --subject "hub.test.*" --since "1h"
"""
import asyncio
import click
from uuid import UUID
from typing import Optional

from app.cli.utils.time_parser import parse_time
from app.cli.utils.formatters import format_events_table, format_events_json
from app.events.service import EventService
from app.database import get_db
from app.config import get_nats_url


@click.command()
@click.option(
    '--subject',
    '-s',
    default=None,
    help='Filter by subject pattern (NATS wildcards: *, >)'
)
@click.option(
    '--since',
    default=None,
    help='Show events since time (e.g., 1h, yesterday, 2025-11-04)'
)
@click.option(
    '--until',
    default=None,
    help='Show events until time'
)
@click.option(
    '--correlation-id',
    default=None,
    help='Filter by correlation ID'
)
@click.option(
    '--limit',
    '-n',
    default=100,
    type=int,
    help='Maximum events to return (default: 100)'
)
@click.option(
    '--format',
    '-f',
    type=click.Choice(['table', 'json']),
    default='table',
    help='Output format (default: table)'
)
def query(
    subject: Optional[str],
    since: Optional[str],
    until: Optional[str],
    correlation_id: Optional[str],
    limit: int,
    format: str
):
    """Query historical events from database.

    Examples:
        hub query --subject "hub.test.*" --since "1h"
        hub query --correlation-id "abc123" --format json
        hub query --since "yesterday" --limit 50
    """
    # Parse time filters
    since_dt = parse_time(since) if since else None
    until_dt = parse_time(until) if until else None

    # Parse correlation ID
    correlation_uuid = None
    if correlation_id:
        try:
            correlation_uuid = UUID(correlation_id)
        except ValueError:
            click.echo(f"Error: Invalid correlation ID format: {correlation_id}")
            return

    # Query events
    async def query_events():
        async for session in get_db():
            event_service = EventService(get_nats_url(), session)
            await event_service.connect()

            try:
                events = await event_service.query_events(
                    subject=subject,
                    since=since_dt,
                    until=until_dt,
                    correlation_id=correlation_uuid,
                    limit=limit
                )
                return events
            finally:
                await event_service.disconnect()

    # Run query
    try:
        events = asyncio.run(query_events())

        # Format output
        if format == 'json':
            output = format_events_json(events)
        else:
            output = format_events_table(events)

        click.echo(output)

    except KeyboardInterrupt:
        click.echo("\nAborted!", err=True)
    except Exception as e:
        # For database connection errors, show friendly message
        error_msg = str(e)
        if "unable to open database file" in error_msg or "connection" in error_msg.lower():
            click.echo("Error: Cannot connect to database. Is the Hub backend running?", err=True)
        else:
            click.echo(f"Error: {e}", err=True)
