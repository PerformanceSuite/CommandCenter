"""
Tests for Computed Properties Service (Phase 4, Task 4.3)

Tests the computation of derived properties on entities:
- symbolCount: Count of symbols in a file
- allDependencies: Transitive closure of symbol dependencies
- projectHealth: Aggregate health score for a project
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.schemas.query import ComputedPropertySpec
from app.services.computed_properties import ComputedPropertiesService

# =============================================================================
# Schema Tests
# =============================================================================


class TestComputedPropertySpec:
    """Tests for ComputedPropertySpec schema."""

    def test_basic_computed_property(self):
        """Test basic computed property specification."""
        spec = ComputedPropertySpec(
            property="symbolCount",
            entity_type="file",
        )
        assert spec.property == "symbolCount"
        assert spec.entity_type == "file"

    def test_computed_property_with_options(self):
        """Test computed property with options."""
        spec = ComputedPropertySpec(
            property="allDependencies",
            entity_type="symbol",
            options={"depth": 3, "include_indirect": True},
        )
        assert spec.options["depth"] == 3
        assert spec.options["include_indirect"] is True

    def test_project_health_spec(self):
        """Test project health computed property."""
        spec = ComputedPropertySpec(
            property="projectHealth",
            entity_type="project",
        )
        assert spec.property == "projectHealth"


# =============================================================================
# Service Tests
# =============================================================================


class TestComputedPropertiesService:
    """Tests for ComputedPropertiesService."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = MagicMock()
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_compute_symbol_count(self, mock_db_session):
        """Test symbol count computation for files."""
        # Mock query result - 5 symbols in the file
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db_session.execute.return_value = mock_result

        service = ComputedPropertiesService(mock_db_session)

        result = await service.compute_symbol_count(file_id=123)

        assert result == 5
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_compute_all_dependencies(self, mock_db_session):
        """Test transitive dependency computation for symbols."""
        # Mock query results for dependency traversal
        # First call: direct deps, Second call: indirect deps, Third: no more
        mock_result1 = MagicMock()
        mock_result1.scalars.return_value.all.return_value = [
            MagicMock(to_symbol_id=2),
            MagicMock(to_symbol_id=3),
        ]
        mock_result2 = MagicMock()
        mock_result2.scalars.return_value.all.return_value = [
            MagicMock(to_symbol_id=4),
        ]
        mock_result3 = MagicMock()
        mock_result3.scalars.return_value.all.return_value = []

        mock_db_session.execute.side_effect = [mock_result1, mock_result2, mock_result3]

        service = ComputedPropertiesService(mock_db_session)

        result = await service.compute_all_dependencies(symbol_id=1, max_depth=3)

        assert "direct" in result
        assert "indirect" in result
        assert "total_count" in result
        assert result["total_count"] == 3  # 2 direct + 1 indirect

    @pytest.mark.asyncio
    async def test_compute_project_health(self, mock_db_session):
        """Test project health score computation."""
        # Return different values for different queries
        mock_db_session.execute.side_effect = [
            MagicMock(scalar=lambda: 100),  # total_symbols
            MagicMock(scalar=lambda: 10),  # symbols_with_issues
            MagicMock(scalar=lambda: 50),  # total_files
            MagicMock(scalar=lambda: 5),  # files_with_issues
            MagicMock(scalar=lambda: 20),  # total_tasks
            MagicMock(scalar=lambda: 3),  # open_tasks
        ]

        service = ComputedPropertiesService(mock_db_session)

        result = await service.compute_project_health(project_id=1)

        assert "score" in result
        assert "components" in result
        assert 0 <= result["score"] <= 100

    @pytest.mark.asyncio
    async def test_compute_for_entity(self, mock_db_session):
        """Test generic compute_for_entity method."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 10
        mock_db_session.execute.return_value = mock_result

        service = ComputedPropertiesService(mock_db_session)

        spec = ComputedPropertySpec(
            property="symbolCount",
            entity_type="file",
        )

        result = await service.compute_for_entity(
            entity={"id": 123, "type": "file"},
            spec=spec,
        )

        assert result == 10

    @pytest.mark.asyncio
    async def test_unknown_property(self, mock_db_session):
        """Test handling of unknown computed property."""
        service = ComputedPropertiesService(mock_db_session)

        spec = ComputedPropertySpec(
            property="unknownProperty",
            entity_type="file",
        )

        result = await service.compute_for_entity(
            entity={"id": 123, "type": "file"},
            spec=spec,
        )

        assert result is None

    @pytest.mark.asyncio
    async def test_batch_compute(self, mock_db_session):
        """Test batch computation for multiple entities."""
        mock_result = MagicMock()
        mock_result.scalar.return_value = 5
        mock_db_session.execute.return_value = mock_result

        service = ComputedPropertiesService(mock_db_session)

        entities = [
            {"id": 1, "type": "file"},
            {"id": 2, "type": "file"},
            {"id": 3, "type": "file"},
        ]

        results = await service.batch_compute(
            entities=entities,
            property="symbolCount",
        )

        assert len(results) == 3
        assert all(r == 5 for r in results.values())


# =============================================================================
# Integration Tests with ComposedQuery
# =============================================================================


class TestComposedQueryComputedProperties:
    """Tests for computed properties integration with ComposedQuery."""

    def test_composed_query_with_computed(self):
        """Test ComposedQuery with computed property request."""
        from app.schemas.query import ComposedQuery, EntitySelector

        query = ComposedQuery(
            entities=[EntitySelector(type="file")],
            computed=[
                ComputedPropertySpec(
                    property="symbolCount",
                    entity_type="file",
                )
            ],
        )

        assert query.computed is not None
        assert len(query.computed) == 1
        assert query.computed[0].property == "symbolCount"

    def test_composed_query_multiple_computed(self):
        """Test ComposedQuery with multiple computed properties."""
        from app.schemas.query import ComposedQuery, EntitySelector

        query = ComposedQuery(
            entities=[EntitySelector(type="symbol")],
            computed=[
                ComputedPropertySpec(property="allDependencies", entity_type="symbol"),
            ],
        )

        assert len(query.computed) == 1


class TestQueryExecutorComputedProperties:
    """Tests for computed properties in QueryExecutor."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = MagicMock()
        session.execute = AsyncMock()
        return session

    @pytest.mark.asyncio
    async def test_execute_with_computed_properties(self, mock_db_session):
        """Test query execution with computed properties."""
        from app.schemas.query import ComposedQuery, EntitySelector, QueryResult
        from app.services.query_executor import QueryExecutor

        # Mock database to return empty results for entity query
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_result.scalar.return_value = 0
        mock_db_session.execute.return_value = mock_result

        executor = QueryExecutor(mock_db_session)

        query = ComposedQuery(
            entities=[EntitySelector(type="file")],
            computed=[
                ComputedPropertySpec(
                    property="symbolCount",
                    entity_type="file",
                )
            ],
        )

        result = await executor.execute(query=query, project_id=1)

        assert isinstance(result, QueryResult)
        # Computed property metadata should be in results
        assert "computed_properties" in result.metadata
