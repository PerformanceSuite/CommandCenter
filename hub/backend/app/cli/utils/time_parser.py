"""Natural language time parsing for CLI.

Supports:
- Relative: 1h, 30m, 7d
- Natural: yesterday, last Monday, 2 hours ago
- ISO 8601: 2025-11-04T10:30:00Z
"""
import re
from datetime import datetime, timezone, timedelta
from typing import Optional
import dateparser


def parse_time(time_str: Optional[str]) -> Optional[datetime]:
    """Parse time string into datetime.

    Formats supported:
        - Relative: "1h", "30m", "7d" (hours, minutes, days ago)
        - Natural: "yesterday", "last Monday", "2 hours ago"
        - ISO 8601: "2025-11-04T10:30:00Z"

    Args:
        time_str: Time string to parse, or None

    Returns:
        Datetime in UTC timezone, or None if input is None/empty

    Raises:
        ValueError: If time_str cannot be parsed

    Examples:
        >>> parse_time("1h")
        datetime(2025, 11, 4, 9, 30, 0, tzinfo=timezone.utc)  # 1 hour ago

        >>> parse_time("yesterday")
        datetime(2025, 11, 3, 10, 30, 0, tzinfo=timezone.utc)
    """
    if not time_str:
        return None

    # Try relative format first (1h, 30m, 7d)
    relative_match = re.match(r'^(\d+)([hmd])$', time_str)
    if relative_match:
        value, unit = relative_match.groups()
        value = int(value)

        if unit == 'h':
            delta = timedelta(hours=value)
        elif unit == 'm':
            delta = timedelta(minutes=value)
        elif unit == 'd':
            delta = timedelta(days=value)

        return datetime.now(timezone.utc) - delta

    # Try ISO 8601 format
    try:
        dt = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
        # Ensure UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        else:
            dt = dt.astimezone(timezone.utc)
        return dt
    except (ValueError, AttributeError):
        pass

    # Try natural language parsing with dateparser
    parsed = dateparser.parse(
        time_str,
        settings={
            'TIMEZONE': 'UTC',
            'RETURN_AS_TIMEZONE_AWARE': True,
            'PREFER_DATES_FROM': 'past'  # Default to past dates
        }
    )

    if parsed:
        # Ensure UTC timezone
        return parsed.astimezone(timezone.utc)

    # Could not parse
    raise ValueError(f"Could not parse time string: {time_str}")
