"""
Tests for Semantic Search Service (Phase 4, Task 4.2)

Tests the integration of RAG/KnowledgeBeast semantic search
with the ComposedQuery layer.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.schemas.query import ComposedQuery, EntitySelector, QueryResult, SemanticSearchSpec
from app.services.semantic_search import SemanticSearchService

# =============================================================================
# Schema Tests
# =============================================================================


class TestSemanticSearchSpec:
    """Tests for SemanticSearchSpec schema."""

    def test_basic_semantic_spec(self):
        """Test basic semantic search specification."""
        spec = SemanticSearchSpec(
            query="authentication flow",
            limit=5,
        )
        assert spec.query == "authentication flow"
        assert spec.limit == 5
        assert spec.threshold is None
        assert spec.categories is None

    def test_semantic_spec_with_threshold(self):
        """Test semantic search with similarity threshold."""
        spec = SemanticSearchSpec(
            query="security vulnerabilities",
            limit=10,
            threshold=0.7,
        )
        assert spec.threshold == 0.7

    def test_semantic_spec_with_categories(self):
        """Test semantic search with category filter."""
        spec = SemanticSearchSpec(
            query="database migrations",
            categories=["docs", "code"],
        )
        assert spec.categories == ["docs", "code"]

    def test_semantic_spec_defaults(self):
        """Test default values for semantic search."""
        spec = SemanticSearchSpec(query="test query")
        assert spec.limit == 5
        assert spec.include_content is True


# =============================================================================
# Service Tests
# =============================================================================


class TestSemanticSearchService:
    """Tests for SemanticSearchService."""

    @pytest.fixture
    def mock_rag_service(self):
        """Create a mock RAG service."""
        mock = MagicMock()
        mock.query = AsyncMock(
            return_value=[
                {
                    "content": "Authentication uses JWT tokens for session management.",
                    "metadata": {"source": "docs/auth.md", "category": "docs"},
                    "score": 0.92,
                    "category": "docs",
                    "source": "docs/auth.md",
                },
                {
                    "content": "The login function validates credentials against the database.",
                    "metadata": {"source": "backend/auth.py", "category": "code"},
                    "score": 0.85,
                    "category": "code",
                    "source": "backend/auth.py",
                },
            ]
        )
        mock.initialize = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_search_returns_results(self, mock_rag_service):
        """Test that search returns formatted results."""
        with patch("app.services.semantic_search.RAG_AVAILABLE", True), patch(
            "app.services.semantic_search.RAGService",
            return_value=mock_rag_service,
        ):
            service = SemanticSearchService(repository_id=1)
            service._rag_service = mock_rag_service

            spec = SemanticSearchSpec(query="authentication", limit=5)
            results = await service.search(spec)

            assert len(results) == 2
            assert results[0]["score"] == 0.92
            assert "content" in results[0]
            assert "source" in results[0]

    @pytest.mark.asyncio
    async def test_search_applies_threshold(self, mock_rag_service):
        """Test that threshold filters low-score results."""
        with patch("app.services.semantic_search.RAG_AVAILABLE", True), patch(
            "app.services.semantic_search.RAGService",
            return_value=mock_rag_service,
        ):
            service = SemanticSearchService(repository_id=1)
            service._rag_service = mock_rag_service

            spec = SemanticSearchSpec(query="authentication", threshold=0.9)
            results = await service.search(spec)

            # Only first result (0.92) should pass 0.9 threshold
            assert len(results) == 1
            assert results[0]["score"] >= 0.9

    @pytest.mark.asyncio
    async def test_search_applies_category_filter(self, mock_rag_service):
        """Test that category filter is passed to RAG service."""
        mock_rag_service.query = AsyncMock(
            return_value=[
                {
                    "content": "Code content",
                    "score": 0.85,
                    "category": "code",
                    "source": "auth.py",
                    "metadata": {},
                },
            ]
        )

        with patch("app.services.semantic_search.RAG_AVAILABLE", True), patch(
            "app.services.semantic_search.RAGService",
            return_value=mock_rag_service,
        ):
            service = SemanticSearchService(repository_id=1)
            service._rag_service = mock_rag_service

            spec = SemanticSearchSpec(
                query="authentication",
                categories=["code"],
            )
            await service.search(spec)

            # Verify category was passed to RAG
            mock_rag_service.query.assert_called_once()
            call_kwargs = mock_rag_service.query.call_args
            assert call_kwargs.kwargs.get("category") == "code"

    @pytest.mark.asyncio
    async def test_convert_to_entities(self, mock_rag_service):
        """Test conversion of semantic results to entity format."""
        with patch("app.services.semantic_search.RAG_AVAILABLE", True), patch(
            "app.services.semantic_search.RAGService",
            return_value=mock_rag_service,
        ):
            service = SemanticSearchService(repository_id=1)
            service._rag_service = mock_rag_service

            spec = SemanticSearchSpec(query="authentication", limit=5)
            entities = await service.search_as_entities(spec)

            assert len(entities) == 2
            assert entities[0]["type"] == "knowledge"
            assert entities[0]["label"] == "docs/auth.md"
            assert "semantic_score" in entities[0]

    @pytest.mark.asyncio
    async def test_search_handles_empty_results(self, mock_rag_service):
        """Test handling of empty search results."""
        mock_rag_service.query = AsyncMock(return_value=[])

        with patch("app.services.semantic_search.RAG_AVAILABLE", True), patch(
            "app.services.semantic_search.RAGService",
            return_value=mock_rag_service,
        ):
            service = SemanticSearchService(repository_id=1)
            service._rag_service = mock_rag_service

            spec = SemanticSearchSpec(query="nonexistent topic")
            results = await service.search(spec)

            assert results == []


# =============================================================================
# ComposedQuery Integration Tests
# =============================================================================


class TestComposedQuerySemanticIntegration:
    """Tests for semantic search integration with ComposedQuery."""

    def test_composed_query_accepts_semantic_spec(self):
        """Test that ComposedQuery accepts semantic search specification."""
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol")],
            semantic=SemanticSearchSpec(
                query="authentication flow",
                limit=10,
            ),
        )
        assert query.semantic is not None
        assert query.semantic.query == "authentication flow"

    def test_composed_query_without_semantic(self):
        """Test ComposedQuery works without semantic search."""
        query = ComposedQuery(
            entities=[EntitySelector(type="symbol")],
        )
        assert query.semantic is None


# =============================================================================
# QueryExecutor Integration Tests
# =============================================================================


class TestQueryExecutorSemanticSearch:
    """Tests for semantic search integration in QueryExecutor."""

    @pytest.fixture
    def mock_db_session(self):
        """Create a mock async database session."""
        session = MagicMock()
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def mock_semantic_service(self):
        """Create a mock semantic search service."""
        service = MagicMock()
        service.search_as_entities = AsyncMock(
            return_value=[
                {
                    "id": "kb_1",
                    "type": "knowledge",
                    "label": "docs/auth.md",
                    "content": "JWT authentication...",
                    "semantic_score": 0.92,
                    "source": "docs/auth.md",
                    "category": "docs",
                },
            ]
        )
        return service

    @pytest.mark.asyncio
    async def test_execute_with_semantic_search(self, mock_db_session, mock_semantic_service):
        """Test query execution with semantic search."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)

        # Patch the semantic service
        with patch.object(
            executor,
            "_get_semantic_service",
            return_value=mock_semantic_service,
        ):
            query = ComposedQuery(
                entities=[EntitySelector(type="knowledge")],
                semantic=SemanticSearchSpec(query="authentication"),
            )

            result = await executor.execute(
                query=query,
                project_id=1,
            )

            assert isinstance(result, QueryResult)
            # Semantic results should be included
            assert len(result.entities) > 0
            assert any(e.get("type") == "knowledge" for e in result.entities)

    @pytest.mark.asyncio
    async def test_semantic_metadata_in_result(self, mock_db_session, mock_semantic_service):
        """Test that semantic search metadata is included in results."""
        from app.services.query_executor import QueryExecutor

        executor = QueryExecutor(mock_db_session)

        with patch.object(
            executor,
            "_get_semantic_service",
            return_value=mock_semantic_service,
        ):
            query = ComposedQuery(
                entities=[EntitySelector(type="knowledge")],
                semantic=SemanticSearchSpec(query="database queries"),
            )

            result = await executor.execute(query=query, project_id=1)

            assert "semantic_query" in result.metadata
            assert result.metadata["semantic_query"] == "database queries"
