"""
TemporalResolver - Resolve relative time expressions to absolute datetime ranges.

Phase 4, Task 4.1: Temporal Query Support

This service parses natural language time expressions and converts them
to absolute datetime ranges for database queries.

Supported expressions:
- "last N days/hours/weeks/months"
- "yesterday", "today", "tomorrow"
- "this week", "last week"
- "this month", "last month"
- "this quarter", "last quarter"
- "this year", "last year"
"""

import calendar
import re
from datetime import datetime, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

# Regex patterns for parsing relative expressions
LAST_N_PATTERN = re.compile(
    r"last\s+(\d+)\s+(hour|hours|day|days|week|weeks|month|months|year|years)",
    re.IGNORECASE,
)

NAMED_PERIOD_PATTERN = re.compile(
    r"(this|last)\s+(hour|day|week|month|quarter|year)",
    re.IGNORECASE,
)


class TemporalResolver:
    """Resolve relative time expressions to absolute datetime ranges.

    Examples:
        >>> resolver = TemporalResolver()
        >>> now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        >>> start, end = resolver.resolve("last 7 days", reference_time=now)
        >>> print(start)  # 2025-12-25 00:00:00+00:00
    """

    def __init__(self, default_timezone: str = "UTC"):
        """Initialize resolver with default timezone.

        Args:
            default_timezone: IANA timezone name for reference time
        """
        self.default_timezone = ZoneInfo(default_timezone)

    def resolve(
        self,
        expression: str,
        reference_time: Optional[datetime] = None,
    ) -> tuple[datetime, datetime]:
        """Resolve a relative time expression to absolute datetime range.

        Args:
            expression: Relative time expression (e.g., "last 7 days")
            reference_time: Reference point for relative calculations (default: now)

        Returns:
            Tuple of (start, end) datetimes

        Raises:
            ValueError: If expression cannot be parsed
        """
        if reference_time is None:
            reference_time = datetime.now(self.default_timezone)
        elif reference_time.tzinfo is None:
            reference_time = reference_time.replace(tzinfo=self.default_timezone)

        # Normalize expression
        expr = expression.lower().strip()

        # Try named expressions first
        if expr == "yesterday":
            return self._resolve_yesterday(reference_time)
        elif expr == "today":
            return self._resolve_today(reference_time)
        elif expr == "tomorrow":
            return self._resolve_tomorrow(reference_time)

        # Try "last N units" pattern
        match = LAST_N_PATTERN.match(expr)
        if match:
            count = int(match.group(1))
            unit = match.group(2).lower().rstrip("s")  # Normalize to singular
            return self._resolve_last_n(count, unit, reference_time)

        # Try "this/last period" pattern
        match = NAMED_PERIOD_PATTERN.match(expr)
        if match:
            modifier = match.group(1).lower()  # "this" or "last"
            period = match.group(2).lower()
            return self._resolve_named_period(modifier, period, reference_time)

        raise ValueError(f"Unknown temporal expression: {expression}")

    def _resolve_yesterday(self, ref: datetime) -> tuple[datetime, datetime]:
        """Resolve 'yesterday' to previous day 00:00:00 to 23:59:59."""
        yesterday = ref - timedelta(days=1)
        start = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
        end = yesterday.replace(hour=23, minute=59, second=59, microsecond=0)
        return start, end

    def _resolve_today(self, ref: datetime) -> tuple[datetime, datetime]:
        """Resolve 'today' to current day 00:00:00 to reference time."""
        start = ref.replace(hour=0, minute=0, second=0, microsecond=0)
        return start, ref

    def _resolve_tomorrow(self, ref: datetime) -> tuple[datetime, datetime]:
        """Resolve 'tomorrow' to next day 00:00:00 to 23:59:59."""
        tomorrow = ref + timedelta(days=1)
        start = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
        end = tomorrow.replace(hour=23, minute=59, second=59, microsecond=0)
        return start, end

    def _resolve_last_n(
        self,
        count: int,
        unit: str,
        ref: datetime,
    ) -> tuple[datetime, datetime]:
        """Resolve 'last N units' expressions."""
        if unit == "hour":
            start = ref - timedelta(hours=count)
        elif unit == "day":
            # Start at 00:00:00 of the day N days ago
            start = (ref - timedelta(days=count)).replace(hour=0, minute=0, second=0, microsecond=0)
        elif unit == "week":
            start = ref - timedelta(weeks=count)
            start = start.replace(hour=0, minute=0, second=0, microsecond=0)
        elif unit == "month":
            # Go back N months from start of current month
            year = ref.year
            month = ref.month - count
            while month <= 0:
                month += 12
                year -= 1
            start = ref.replace(
                year=year, month=month, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        elif unit == "year":
            start = ref.replace(
                year=ref.year - count, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
        else:
            raise ValueError(f"Unknown time unit: {unit}")

        return start, ref

    def _resolve_named_period(
        self,
        modifier: str,
        period: str,
        ref: datetime,
    ) -> tuple[datetime, datetime]:
        """Resolve 'this/last week/month/quarter/year' expressions."""
        if period == "hour":
            return self._resolve_hour(modifier, ref)
        elif period == "day":
            return self._resolve_day(modifier, ref)
        elif period == "week":
            return self._resolve_week(modifier, ref)
        elif period == "month":
            return self._resolve_month(modifier, ref)
        elif period == "quarter":
            return self._resolve_quarter(modifier, ref)
        elif period == "year":
            return self._resolve_year(modifier, ref)
        else:
            raise ValueError(f"Unknown period: {period}")

    def _resolve_hour(self, modifier: str, ref: datetime) -> tuple[datetime, datetime]:
        """Resolve hour period."""
        if modifier == "this":
            start = ref.replace(minute=0, second=0, microsecond=0)
            return start, ref
        else:  # last
            hour_ago = ref - timedelta(hours=1)
            start = hour_ago.replace(minute=0, second=0, microsecond=0)
            end = hour_ago.replace(minute=59, second=59, microsecond=0)
            return start, end

    def _resolve_day(self, modifier: str, ref: datetime) -> tuple[datetime, datetime]:
        """Resolve day period."""
        if modifier == "this":
            return self._resolve_today(ref)
        else:  # last
            return self._resolve_yesterday(ref)

    def _resolve_week(self, modifier: str, ref: datetime) -> tuple[datetime, datetime]:
        """Resolve week period (Monday = start of week)."""
        # Find Monday of current week
        days_since_monday = ref.weekday()
        monday = ref - timedelta(days=days_since_monday)
        monday = monday.replace(hour=0, minute=0, second=0, microsecond=0)

        if modifier == "this":
            return monday, ref
        else:  # last
            last_monday = monday - timedelta(weeks=1)
            last_sunday = monday - timedelta(seconds=1)
            last_sunday = last_sunday.replace(hour=23, minute=59, second=59, microsecond=0)
            return last_monday, last_sunday

    def _resolve_month(self, modifier: str, ref: datetime) -> tuple[datetime, datetime]:
        """Resolve month period."""
        if modifier == "this":
            start = ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return start, ref
        else:  # last
            # First day of current month
            first_of_month = ref.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            # Last day of previous month
            last_of_prev = first_of_month - timedelta(days=1)
            last_of_prev = last_of_prev.replace(hour=23, minute=59, second=59, microsecond=0)
            # First day of previous month
            first_of_prev = last_of_prev.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            return first_of_prev, last_of_prev

    def _resolve_quarter(self, modifier: str, ref: datetime) -> tuple[datetime, datetime]:
        """Resolve quarter period (Q1=Jan-Mar, Q2=Apr-Jun, Q3=Jul-Sep, Q4=Oct-Dec)."""
        # Determine current quarter
        current_quarter = (ref.month - 1) // 3 + 1
        quarter_start_month = (current_quarter - 1) * 3 + 1

        if modifier == "this":
            start = ref.replace(
                month=quarter_start_month, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            return start, ref
        else:  # last
            # Previous quarter
            if current_quarter == 1:
                # Q4 of previous year
                prev_quarter_start = ref.replace(
                    year=ref.year - 1, month=10, day=1, hour=0, minute=0, second=0, microsecond=0
                )
                prev_quarter_end = ref.replace(
                    year=ref.year - 1,
                    month=12,
                    day=31,
                    hour=23,
                    minute=59,
                    second=59,
                    microsecond=0,
                )
            else:
                prev_quarter = current_quarter - 1
                prev_start_month = (prev_quarter - 1) * 3 + 1
                prev_end_month = prev_start_month + 2
                last_day = calendar.monthrange(ref.year, prev_end_month)[1]

                prev_quarter_start = ref.replace(
                    month=prev_start_month, day=1, hour=0, minute=0, second=0, microsecond=0
                )
                prev_quarter_end = ref.replace(
                    month=prev_end_month, day=last_day, hour=23, minute=59, second=59, microsecond=0
                )

            return prev_quarter_start, prev_quarter_end

    def _resolve_year(self, modifier: str, ref: datetime) -> tuple[datetime, datetime]:
        """Resolve year period."""
        if modifier == "this":
            start = ref.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            return start, ref
        else:  # last
            start = ref.replace(
                year=ref.year - 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
            )
            end = ref.replace(
                year=ref.year - 1, month=12, day=31, hour=23, minute=59, second=59, microsecond=0
            )
            return start, end
