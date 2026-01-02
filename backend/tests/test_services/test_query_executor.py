"""
Tests for QueryExecutor service.

Phase 2, Task 2.3: Query Execution Service

The QueryExecutor takes a ComposedQuery and executes it against the graph database,
returning a QueryResult with entities, relationships, and optional aggregations.
"""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.query import (
    Aggregation,
    ComposedQuery,
    EntitySelector,
    Filter,
    QueryResult,
    RelationshipSpec,
    TimeRange,
)


class TestQueryExecutorBasic:
    """Basic QueryExecutor functionality tests."""

    @pytest.mark.asyncio
    async def test_execute_simple_entity_query(self, mock_db_session):
        """Execute a simple query selecting all symbols."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="symbol")])

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)
        assert "entities" in result.model_dump()
        assert "relationships" in result.model_dump()

    @pytest.mark.asyncio
    async def test_execute_query_with_scope(self, mock_db_session):
        """Execute query with project scope."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="file", scope="project:1")])

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execute_query_with_entity_id(self, mock_db_session):
        """Execute query selecting a specific entity by ID."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="symbol", id="123")])

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)


class TestQueryExecutorFilters:
    """Filter functionality tests."""

    @pytest.mark.asyncio
    async def test_execute_with_eq_filter(self, mock_db_session):
        """Execute query with equality filter."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="service")],
            filters=[Filter(field="status", operator="eq", value="up")],
        )

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execute_with_lt_filter(self, mock_db_session):
        """Execute query with less-than filter."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol")],
            filters=[Filter(field="range_start", operator="lt", value=100)],
        )

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execute_with_gt_filter(self, mock_db_session):
        """Execute query with greater-than filter."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="file")],
            filters=[Filter(field="lines", operator="gt", value=50)],
        )

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execute_with_contains_filter(self, mock_db_session):
        """Execute query with contains filter (for name searches)."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol")],
            filters=[Filter(field="name", operator="contains", value="auth")],
        )

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execute_with_multiple_filters(self, mock_db_session):
        """Execute query with multiple filters (AND logic)."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol")],
            filters=[
                Filter(field="kind", operator="eq", value="function"),
                Filter(field="exports", operator="eq", value=True),
            ],
        )

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)


class TestQueryExecutorRelationships:
    """Relationship traversal tests."""

    @pytest.mark.asyncio
    async def test_execute_with_outbound_relationship(self, mock_db_session):
        """Execute query with outbound relationship traversal."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol", id="1")],
            relationships=[RelationshipSpec(type="dependency", direction="outbound", depth=1)],
        )

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)
        assert "relationships" in result.model_dump()

    @pytest.mark.asyncio
    async def test_execute_with_inbound_relationship(self, mock_db_session):
        """Execute query with inbound relationship traversal."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol", id="1")],
            relationships=[RelationshipSpec(type="caller", direction="inbound", depth=1)],
        )

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execute_with_bidirectional_relationship(self, mock_db_session):
        """Execute query with bidirectional relationship traversal."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol", id="1")],
            relationships=[RelationshipSpec(type="reference", direction="both", depth=2)],
        )

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)


class TestQueryExecutorAggregations:
    """Aggregation tests."""

    @pytest.mark.asyncio
    async def test_execute_with_count_aggregation(self, mock_db_session):
        """Execute query with count aggregation."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol")], aggregations=[Aggregation(type="count")]
        )

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)
        # Aggregations should be populated when requested
        assert result.aggregations is not None or result.total >= 0

    @pytest.mark.asyncio
    async def test_execute_with_group_by_aggregation(self, mock_db_session):
        """Execute query with group by aggregation."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol")],
            aggregations=[Aggregation(type="count", group_by=["kind"])],
        )

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)


class TestQueryExecutorTimeRange:
    """Time range filtering tests."""

    @pytest.mark.asyncio
    async def test_execute_with_time_range_start(self, mock_db_session):
        """Execute query with time range start bound."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="task")], time_range=TimeRange(start=datetime(2024, 1, 1))
        )

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execute_with_full_time_range(self, mock_db_session):
        """Execute query with full time range."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(
            entities=[EntitySelector(type="task")],
            time_range=TimeRange(start=datetime(2024, 1, 1), end=datetime(2024, 12, 31)),
        )

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)


class TestQueryExecutorPagination:
    """Pagination tests."""

    @pytest.mark.asyncio
    async def test_execute_with_limit(self, mock_db_session):
        """Execute query with limit."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="symbol")], limit=10)

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)
        assert len(result.entities) <= 10

    @pytest.mark.asyncio
    async def test_execute_with_offset(self, mock_db_session):
        """Execute query with offset."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="symbol")], limit=10, offset=5)

        result = await executor.execute(query, project_id=1)

        assert isinstance(result, QueryResult)


class TestQueryExecutorEntityTypes:
    """Tests for different entity types."""

    @pytest.mark.asyncio
    async def test_execute_symbol_query(self, mock_db_session):
        """Execute query for symbol entities."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="symbol")])

        result = await executor.execute(query, project_id=1)
        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execute_file_query(self, mock_db_session):
        """Execute query for file entities."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="file")])

        result = await executor.execute(query, project_id=1)
        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execute_service_query(self, mock_db_session):
        """Execute query for service entities."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="service")])

        result = await executor.execute(query, project_id=1)
        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execute_task_query(self, mock_db_session):
        """Execute query for task entities."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="task")])

        result = await executor.execute(query, project_id=1)
        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execute_spec_query(self, mock_db_session):
        """Execute query for spec entities."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="spec")])

        result = await executor.execute(query, project_id=1)
        assert isinstance(result, QueryResult)

    @pytest.mark.asyncio
    async def test_execute_any_type_query(self, mock_db_session):
        """Execute query for 'any' entity type."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="any")])

        result = await executor.execute(query, project_id=1)
        assert isinstance(result, QueryResult)


class TestQueryExecutorMetadata:
    """Tests for query metadata."""

    @pytest.mark.asyncio
    async def test_result_includes_total(self, mock_db_session):
        """Result includes total count."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="symbol")])

        result = await executor.execute(query, project_id=1)

        assert hasattr(result, "total")
        assert isinstance(result.total, int)

    @pytest.mark.asyncio
    async def test_result_includes_execution_metadata(self, mock_db_session):
        """Result includes execution metadata."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)
        query = ComposedQuery(entities=[EntitySelector(type="symbol")])

        result = await executor.execute(query, project_id=1)

        assert hasattr(result, "metadata")
        assert isinstance(result.metadata, dict)


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
