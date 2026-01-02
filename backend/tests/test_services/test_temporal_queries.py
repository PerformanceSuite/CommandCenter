"""
Tests for Temporal Query Support.

Phase 4, Task 4.1: Enhanced time-based query filtering.

Tests cover:
- Relative time expressions (last 7 days, yesterday, this week)
- Named time periods (Q1 2025, last month)
- Time field selection (created_at, updated_at, last_indexed_at)
- Time-based aggregations (count per day/week/month)
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock
from zoneinfo import ZoneInfo

import pytest

from app.schemas.query import (
    ComposedQuery,
    EntitySelector,
    RelativeTimeRange,
    TemporalAggregation,
    TimeRange,
)


class TestRelativeTimeRange:
    """Tests for RelativeTimeRange schema."""

    def test_relative_time_range_last_n_days(self):
        """Parse 'last 7 days' expression."""
        tr = RelativeTimeRange(expression="last 7 days")
        assert tr.expression == "last 7 days"

    def test_relative_time_range_yesterday(self):
        """Parse 'yesterday' expression."""
        tr = RelativeTimeRange(expression="yesterday")
        assert tr.expression == "yesterday"

    def test_relative_time_range_this_week(self):
        """Parse 'this week' expression."""
        tr = RelativeTimeRange(expression="this week")
        assert tr.expression == "this week"

    def test_relative_time_range_last_month(self):
        """Parse 'last month' expression."""
        tr = RelativeTimeRange(expression="last month")
        assert tr.expression == "last month"

    def test_relative_time_range_this_quarter(self):
        """Parse 'this quarter' expression."""
        tr = RelativeTimeRange(expression="this quarter")
        assert tr.expression == "this quarter"


class TestTemporalResolver:
    """Tests for TemporalResolver service."""

    def test_resolve_last_n_days(self):
        """Resolve 'last 7 days' to absolute datetime range."""
        from app.services.temporal_resolver import TemporalResolver

        resolver = TemporalResolver()
        now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

        start, end = resolver.resolve("last 7 days", reference_time=now)

        assert start == datetime(2025, 12, 25, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert end == now

    def test_resolve_yesterday(self):
        """Resolve 'yesterday' to absolute datetime range."""
        from app.services.temporal_resolver import TemporalResolver

        resolver = TemporalResolver()
        now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

        start, end = resolver.resolve("yesterday", reference_time=now)

        assert start == datetime(2025, 12, 31, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert end == datetime(2025, 12, 31, 23, 59, 59, tzinfo=ZoneInfo("UTC"))

    def test_resolve_today(self):
        """Resolve 'today' to absolute datetime range."""
        from app.services.temporal_resolver import TemporalResolver

        resolver = TemporalResolver()
        now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

        start, end = resolver.resolve("today", reference_time=now)

        assert start == datetime(2026, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert end == now

    def test_resolve_this_week(self):
        """Resolve 'this week' to Monday-Sunday range."""
        from app.services.temporal_resolver import TemporalResolver

        resolver = TemporalResolver()
        # Jan 1, 2026 is a Thursday
        now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

        start, end = resolver.resolve("this week", reference_time=now)

        # Monday of that week is Dec 29, 2025
        assert start == datetime(2025, 12, 29, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert end == now

    def test_resolve_last_week(self):
        """Resolve 'last week' to previous Monday-Sunday range."""
        from app.services.temporal_resolver import TemporalResolver

        resolver = TemporalResolver()
        # Jan 1, 2026 is a Thursday
        now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

        start, end = resolver.resolve("last week", reference_time=now)

        # Previous week is Dec 22-28, 2025
        assert start == datetime(2025, 12, 22, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert end == datetime(2025, 12, 28, 23, 59, 59, tzinfo=ZoneInfo("UTC"))

    def test_resolve_this_month(self):
        """Resolve 'this month' to start of month to now."""
        from app.services.temporal_resolver import TemporalResolver

        resolver = TemporalResolver()
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

        start, end = resolver.resolve("this month", reference_time=now)

        assert start == datetime(2026, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert end == now

    def test_resolve_last_month(self):
        """Resolve 'last month' to previous month range."""
        from app.services.temporal_resolver import TemporalResolver

        resolver = TemporalResolver()
        now = datetime(2026, 1, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

        start, end = resolver.resolve("last month", reference_time=now)

        assert start == datetime(2025, 12, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert end == datetime(2025, 12, 31, 23, 59, 59, tzinfo=ZoneInfo("UTC"))

    def test_resolve_this_quarter(self):
        """Resolve 'this quarter' to Q1 2026."""
        from app.services.temporal_resolver import TemporalResolver

        resolver = TemporalResolver()
        now = datetime(2026, 2, 15, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

        start, end = resolver.resolve("this quarter", reference_time=now)

        # Q1 2026 is Jan-Mar
        assert start == datetime(2026, 1, 1, 0, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert end == now

    def test_resolve_last_n_hours(self):
        """Resolve 'last 24 hours' to datetime range."""
        from app.services.temporal_resolver import TemporalResolver

        resolver = TemporalResolver()
        now = datetime(2026, 1, 1, 12, 0, 0, tzinfo=ZoneInfo("UTC"))

        start, end = resolver.resolve("last 24 hours", reference_time=now)

        assert start == datetime(2025, 12, 31, 12, 0, 0, tzinfo=ZoneInfo("UTC"))
        assert end == now

    def test_resolve_invalid_expression(self):
        """Invalid expression raises ValueError."""
        from app.services.temporal_resolver import TemporalResolver

        resolver = TemporalResolver()

        with pytest.raises(ValueError, match="Unknown temporal expression"):
            resolver.resolve("invalid expression")


class TestTimeRangeWithField:
    """Tests for enhanced TimeRange with field selection."""

    def test_time_range_with_field_created_at(self):
        """TimeRange can specify created_at field."""
        tr = TimeRange(
            start=datetime(2025, 1, 1),
            end=datetime(2025, 12, 31),
            field="created_at",
        )
        assert tr.field == "created_at"

    def test_time_range_with_field_updated_at(self):
        """TimeRange can specify updated_at field."""
        tr = TimeRange(
            start=datetime(2025, 1, 1),
            field="updated_at",
        )
        assert tr.field == "updated_at"

    def test_time_range_with_relative_expression(self):
        """TimeRange can use relative expression."""
        tr = TimeRange(relative="last 7 days")
        assert tr.relative == "last 7 days"

    def test_time_range_default_field(self):
        """TimeRange defaults to None (auto-detect)."""
        tr = TimeRange(start=datetime(2025, 1, 1))
        assert tr.field is None


class TestTemporalAggregation:
    """Tests for temporal aggregation schema."""

    def test_temporal_aggregation_per_day(self):
        """Create per-day aggregation."""
        agg = TemporalAggregation(bucket="day", metric="count")
        assert agg.bucket == "day"
        assert agg.metric == "count"

    def test_temporal_aggregation_per_week(self):
        """Create per-week aggregation."""
        agg = TemporalAggregation(bucket="week", metric="count")
        assert agg.bucket == "week"

    def test_temporal_aggregation_per_month(self):
        """Create per-month aggregation."""
        agg = TemporalAggregation(bucket="month", metric="count")
        assert agg.bucket == "month"


class TestQueryExecutorTemporalFiltering:
    """Tests for QueryExecutor with temporal filtering."""

    @pytest.mark.asyncio
    async def test_execute_with_relative_time_range(self, mock_db_session):
        """Execute query with relative time range."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="task")],
            time_range=TimeRange(relative="last 7 days"),
        )

        result = await executor.execute(query, project_id=1)

        assert result.metadata.get("time_range_resolved") is not None

    @pytest.mark.asyncio
    async def test_execute_with_specific_time_field(self, mock_db_session):
        """Execute query filtering on specific time field."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="file")],
            time_range=TimeRange(
                relative="last 7 days",
                field="updated_at",
            ),
        )

        result = await executor.execute(query, project_id=1)

        assert result.metadata.get("time_field_used") == "updated_at"

    @pytest.mark.asyncio
    async def test_execute_with_temporal_aggregation(self, mock_db_session):
        """Execute query with temporal aggregation."""
        from app.schemas.query import Aggregation
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="task")],
            time_range=TimeRange(relative="last 30 days"),
            aggregations=[
                Aggregation(
                    type="count",
                    temporal=TemporalAggregation(bucket="day", metric="count"),
                )
            ],
        )

        result = await executor.execute(query, project_id=1)

        # Should have temporal buckets in aggregations
        assert "temporal" in (result.aggregations or {})


# Fixtures


@pytest.fixture
def mock_db_session():
    """Create a mock async database session."""
    session = AsyncMock()

    # Mock execute to return empty results by default
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar.return_value = 0

    session.execute = AsyncMock(return_value=mock_result)

    return session
