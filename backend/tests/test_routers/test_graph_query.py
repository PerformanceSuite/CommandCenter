"""
Tests for the /query endpoint on the graph router.

Phase 2, Task 2.4: Query API Endpoint

The /query endpoint accepts ComposedQuery objects and returns QueryResult,
enabling the frontend to execute composed queries against the graph database.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi import status


class TestQueryEndpointBasic:
    """Basic /query endpoint tests."""

    @pytest.mark.asyncio
    async def test_query_endpoint_exists(self, test_client_with_mocks):
        """Verify the /query endpoint exists."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query", json={"entities": [{"type": "symbol"}]}
        )
        # Should not be 404 (method not allowed or other errors are acceptable for setup tests)
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_query_returns_expected_structure(self, test_client_with_mocks):
        """Query returns entities and relationships."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query", json={"entities": [{"type": "symbol"}]}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "entities" in data
        assert "relationships" in data
        assert "total" in data
        assert "metadata" in data

    @pytest.mark.asyncio
    async def test_query_with_filters(self, test_client_with_mocks):
        """Query with filter conditions."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query",
            json={
                "entities": [{"type": "symbol"}],
                "filters": [{"field": "name", "operator": "contains", "value": "auth"}],
            },
        )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_query_with_relationships(self, test_client_with_mocks):
        """Query with relationship traversal."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query",
            json={
                "entities": [{"type": "symbol", "id": "1"}],
                "relationships": [{"type": "dependency", "direction": "outbound", "depth": 2}],
            },
        )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_query_with_aggregations(self, test_client_with_mocks):
        """Query with aggregation request."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query",
            json={"entities": [{"type": "symbol"}], "aggregations": [{"type": "count"}]},
        )

        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_query_with_pagination(self, test_client_with_mocks):
        """Query with limit and offset."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query", json={"entities": [{"type": "symbol"}], "limit": 10, "offset": 5}
        )

        assert response.status_code == status.HTTP_200_OK


class TestQueryEndpointValidation:
    """Request validation tests."""

    @pytest.mark.asyncio
    async def test_query_requires_entities(self, test_client_with_mocks):
        """Query must have at least one entity selector."""
        response = await test_client_with_mocks.post("/api/v1/graph/query", json={})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_query_entities_cannot_be_empty(self, test_client_with_mocks):
        """Entities list cannot be empty."""
        response = await test_client_with_mocks.post("/api/v1/graph/query", json={"entities": []})

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_query_filter_requires_field(self, test_client_with_mocks):
        """Filter must have field, operator, and value."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query",
            json={
                "entities": [{"type": "symbol"}],
                "filters": [{"operator": "eq", "value": "test"}],
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    @pytest.mark.asyncio
    async def test_query_filter_validates_operator(self, test_client_with_mocks):
        """Filter operator must be valid."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query",
            json={
                "entities": [{"type": "symbol"}],
                "filters": [{"field": "name", "operator": "invalid_op", "value": "test"}],
            },
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


class TestQueryEndpointEntityTypes:
    """Entity type support tests."""

    @pytest.mark.asyncio
    async def test_query_symbol_entities(self, test_client_with_mocks):
        """Query symbol entities."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query", json={"entities": [{"type": "symbol"}]}
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_query_file_entities(self, test_client_with_mocks):
        """Query file entities."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query", json={"entities": [{"type": "file"}]}
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_query_service_entities(self, test_client_with_mocks):
        """Query service entities."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query", json={"entities": [{"type": "service"}]}
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_query_task_entities(self, test_client_with_mocks):
        """Query task entities."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query", json={"entities": [{"type": "task"}]}
        )
        assert response.status_code == status.HTTP_200_OK

    @pytest.mark.asyncio
    async def test_query_any_entities(self, test_client_with_mocks):
        """Query all entity types."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query", json={"entities": [{"type": "any"}]}
        )
        assert response.status_code == status.HTTP_200_OK


class TestQueryEndpointIntentParsing:
    """Tests for intent parsing via query string."""

    @pytest.mark.asyncio
    async def test_query_parse_endpoint_exists(self, test_client_with_mocks):
        """Verify the /query/parse endpoint exists."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query/parse", json={"query": "show me all services"}
        )
        # Should not be 404
        assert response.status_code != status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_query_parse_natural_language(self, test_client_with_mocks):
        """Parse natural language query."""
        response = await test_client_with_mocks.post(
            "/api/v1/graph/query/parse",
            json={"query": "show me all services with health below 100"},
        )

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            assert "entities" in data
            assert "relationships" in data


# Fixtures


@pytest.fixture
async def test_client_with_mocks():
    """Create an async test client with database mocks."""
    from httpx import ASGITransport, AsyncClient

    from app.auth.project_context import get_current_project_id
    from app.database import get_db
    from app.main import app

    # Create mock database session
    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.all.return_value = []
    mock_result.scalar.return_value = 0
    mock_session.execute = AsyncMock(return_value=mock_result)

    async def override_get_db():
        yield mock_session

    async def override_get_project_id():
        return 1

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_project_id] = override_get_project_id

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client

    # Clean up overrides
    app.dependency_overrides.clear()
