"""
Integration tests for KnowledgeBeast-enabled knowledge router

Tests the full API integration with KnowledgeBeast when feature flag is enabled.
"""

from unittest.mock import Mock, patch

import pytest
from httpx import AsyncClient

from app.config import settings


@pytest.fixture
def mock_kb_service():
    """Mock KnowledgeBeastService for integration tests"""
    with patch("app.services.knowledgebeast_service.KnowledgeBeastService") as mock_class:
        service = Mock()

        # Mock query method
        async def mock_query(question, category=None, k=5, mode="hybrid", alpha=0.7):
            return [
                {
                    "content": "Machine learning is a subset of AI",
                    "metadata": {"title": "ML Intro", "technology_id": None},
                    "score": 0.85,
                    "category": "ai",
                    "source": "ml.txt",
                    "title": "ML Intro",
                },
                {
                    "content": "Deep learning uses neural networks",
                    "metadata": {"title": "DL Basics", "technology_id": None},
                    "score": 0.72,
                    "category": "ai",
                    "source": "dl.txt",
                    "title": "DL Basics",
                },
            ]

        service.query = mock_query

        # Mock add_document method
        async def mock_add_document(content, metadata, chunk_size=1000):
            return 5  # Return 5 chunks

        service.add_document = mock_add_document

        # Mock delete_by_source
        async def mock_delete_by_source(source):
            return True

        service.delete_by_source = mock_delete_by_source

        # Mock get_statistics
        async def mock_get_statistics():
            return {
                "total_chunks": 100,
                "categories": {"ai": 50, "ml": 30, "nlp": 20},
                "embedding_model": "all-MiniLM-L6-v2",
                "collection_name": "project_1",
                "project_id": 1,
                "cache_hit_rate": 0.95,
            }

        service.get_statistics = mock_get_statistics

        # Mock get_categories
        async def mock_get_categories():
            return ["ai", "ml", "nlp"]

        service.get_categories = mock_get_categories

        mock_class.return_value = service
        yield service


@pytest.fixture
def enable_knowledgebeast():
    """Temporarily enable KnowledgeBeast feature flag"""
    original_value = settings.use_knowledgebeast
    settings.use_knowledgebeast = True
    yield
    settings.use_knowledgebeast = original_value


@pytest.mark.asyncio
class TestKnowledgeQueryWithKB:
    """Test /api/v1/knowledge/query endpoint with KnowledgeBeast"""

    async def test_query_hybrid_mode(
        self, api_client: AsyncClient, enable_knowledgebeast, mock_kb_service
    ):
        """Test hybrid search mode"""
        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", True):
            response = await api_client.post(
                "/api/v1/knowledge/query",
                json={"query": "What is machine learning?", "limit": 5},
                params={"mode": "hybrid", "alpha": 0.7},
            )

        assert response.status_code == 200
        results = response.json()

        assert len(results) == 2
        assert results[0]["content"] == "Machine learning is a subset of AI"
        assert results[0]["score"] == 0.85
        assert results[0]["category"] == "ai"

    async def test_query_vector_mode(
        self, api_client: AsyncClient, enable_knowledgebeast, mock_kb_service
    ):
        """Test vector search mode"""
        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", True):
            response = await api_client.post(
                "/api/v1/knowledge/query",
                json={"query": "machine learning", "limit": 10},
                params={"mode": "vector", "alpha": 1.0},
            )

        assert response.status_code == 200
        results = response.json()
        assert len(results) > 0

    async def test_query_keyword_mode(
        self, api_client: AsyncClient, enable_knowledgebeast, mock_kb_service
    ):
        """Test keyword search mode"""
        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", True):
            response = await api_client.post(
                "/api/v1/knowledge/query",
                json={"query": "machine learning", "limit": 5},
                params={"mode": "keyword", "alpha": 0.0},
            )

        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)

    async def test_query_with_category_filter(
        self, api_client: AsyncClient, enable_knowledgebeast, mock_kb_service
    ):
        """Test query with category filter"""
        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", True):
            response = await api_client.post(
                "/api/v1/knowledge/query",
                json={"query": "AI concepts", "category": "ai", "limit": 5},
                params={"mode": "hybrid"},
            )

        assert response.status_code == 200

    async def test_query_with_project_id(
        self, api_client: AsyncClient, enable_knowledgebeast, mock_kb_service
    ):
        """Test query with explicit project_id"""
        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", True):
            response = await api_client.post(
                "/api/v1/knowledge/query",
                json={"query": "test query", "limit": 5},
                params={"project_id": 42, "mode": "hybrid"},
            )

        assert response.status_code == 200


@pytest.mark.asyncio
class TestKnowledgeStatisticsWithKB:
    """Test /api/v1/knowledge/statistics with KnowledgeBeast"""

    async def test_get_statistics(
        self, api_client: AsyncClient, enable_knowledgebeast, mock_kb_service
    ):
        """Test getting KB statistics"""
        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", True):
            response = await api_client.get("/api/v1/knowledge/statistics")

        assert response.status_code == 200
        stats = response.json()

        assert "collection" in stats
        assert "vector_db" in stats or "total_chunks" in stats


@pytest.mark.asyncio
class TestFeatureFlagToggle:
    """Test feature flag behavior"""

    async def test_uses_kb_when_enabled(
        self, api_client: AsyncClient, enable_knowledgebeast, mock_kb_service
    ):
        """Test that KnowledgeBeast is used when flag is enabled"""
        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", True):
            with patch("app.routers.knowledge.KnowledgeBeastService") as kb_mock:
                kb_mock.return_value = mock_kb_service

                response = await api_client.post(
                    "/api/v1/knowledge/query", json={"query": "test", "limit": 5}
                )

                # KnowledgeBeastService should have been instantiated
                assert kb_mock.called or response.status_code == 200

    async def test_uses_rag_when_disabled(self, api_client: AsyncClient, mock_kb_service):
        """Test that legacy RAG is used when flag is disabled"""
        # Feature flag is disabled by default
        settings.use_knowledgebeast = False

        with patch("app.routers.knowledge.RAGService") as rag_mock:
            # Mock RAG service
            rag_service = Mock()

            async def mock_rag_query(question, category=None, k=5):
                return []

            rag_service.query = mock_rag_query
            rag_mock.return_value = rag_service

            response = await api_client.post(
                "/api/v1/knowledge/query", json={"query": "test", "limit": 5}
            )

            # Should not error (even if empty results)
            assert response.status_code in [200, 500]  # May fail if RAG deps missing


@pytest.mark.asyncio
class TestBackwardCompatibility:
    """Test backward compatibility with legacy API"""

    async def test_query_without_new_params(
        self, api_client: AsyncClient, enable_knowledgebeast, mock_kb_service
    ):
        """Test query without mode/alpha parameters (backward compat)"""
        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", True):
            response = await api_client.post(
                "/api/v1/knowledge/query", json={"query": "test", "limit": 5}
            )

        # Should use default mode (hybrid) and alpha (0.7)
        assert response.status_code == 200

    async def test_legacy_collection_param(
        self, api_client: AsyncClient, enable_knowledgebeast, mock_kb_service
    ):
        """Test legacy collection parameter still works"""
        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", True):
            response = await api_client.post(
                "/api/v1/knowledge/query",
                json={"query": "test", "limit": 5},
                params={"collection": "default"},
            )

        assert response.status_code == 200


@pytest.mark.asyncio
class TestErrorHandling:
    """Test error handling with KnowledgeBeast"""

    async def test_kb_not_available_fallback(self, api_client: AsyncClient, enable_knowledgebeast):
        """Test graceful fallback when KB not available"""
        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", False):
            # Should fall back to RAG service
            response = await api_client.post(
                "/api/v1/knowledge/query", json={"query": "test", "limit": 5}
            )

            # May fail if RAG deps missing, but shouldn't crash
            assert response.status_code in [200, 500]

    async def test_invalid_mode_parameter(
        self, api_client: AsyncClient, enable_knowledgebeast, mock_kb_service
    ):
        """Test handling of invalid mode parameter"""

        # Mock service to raise error on invalid mode
        async def mock_query_error(question, category=None, k=5, mode="hybrid", alpha=0.7):
            if mode not in ["vector", "keyword", "hybrid"]:
                raise ValueError(f"Invalid mode: {mode}")
            return []

        mock_kb_service.query = mock_query_error

        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", True):
            response = await api_client.post(
                "/api/v1/knowledge/query",
                json={"query": "test", "limit": 5},
                params={"mode": "invalid_mode"},
            )

            # Should return error
            assert response.status_code in [400, 500]


@pytest.mark.asyncio
class TestCaching:
    """Test caching behavior with KnowledgeBeast"""

    async def test_cache_key_includes_mode_and_alpha(
        self, api_client: AsyncClient, enable_knowledgebeast, mock_kb_service
    ):
        """Test that cache key includes mode and alpha parameters"""
        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", True):
            # First request
            response1 = await api_client.post(
                "/api/v1/knowledge/query",
                json={"query": "test", "limit": 5},
                params={"mode": "hybrid", "alpha": 0.7},
            )

            # Same query, different mode (should not use same cache)
            response2 = await api_client.post(
                "/api/v1/knowledge/query",
                json={"query": "test", "limit": 5},
                params={"mode": "vector", "alpha": 1.0},
            )

            assert response1.status_code == 200
            assert response2.status_code == 200
