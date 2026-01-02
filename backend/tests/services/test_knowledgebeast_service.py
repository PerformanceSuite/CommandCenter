"""
Unit tests for KnowledgeBeastService

Tests the KnowledgeBeast service wrapper for CommandCenter integration.
Mocks KnowledgeBeast components to test service logic in isolation.
"""

from unittest.mock import Mock, patch

import pytest

from app.services.knowledgebeast_service import KNOWLEDGEBEAST_AVAILABLE, KnowledgeBeastService

# Skip all tests if KnowledgeBeast not installed
pytestmark = pytest.mark.skipif(not KNOWLEDGEBEAST_AVAILABLE, reason="KnowledgeBeast not installed")


@pytest.fixture
def mock_embedding_engine():
    """Mock EmbeddingEngine - not directly used by service anymore but still patched"""
    with patch("app.services.knowledgebeast_service.EmbeddingEngine") as mock:
        engine = Mock()
        engine.embed = Mock(return_value=[0.1] * 384)  # Mock 384-dim embedding
        engine.model_name = "all-MiniLM-L6-v2"
        engine.embedding_dim = 384
        engine.get_stats = Mock(
            return_value={
                "cache_hits": 10,
                "cache_misses": 5,
                "cache_hit_rate": 0.67,
                "cache_size": 10,
                "cache_capacity": 1000,
            }
        )
        mock.return_value = engine
        yield engine


@pytest.fixture
def mock_vector_store():
    """Mock VectorStore - not directly used by service anymore but still patched"""
    with patch("app.services.knowledgebeast_service.VectorStore") as mock:
        store = Mock()
        store.collection_name = "project_1"
        mock.return_value = store
        yield store


@pytest.fixture
def mock_repository():
    """Mock DocumentRepository"""
    with patch("app.services.knowledgebeast_service.DocumentRepository") as mock:
        repo = Mock()
        repo.documents = {}
        repo.inverted_index = {}
        repo.add_document = Mock()
        repo.index_term = Mock()
        repo.get_stats = Mock(return_value={"documents": 100, "terms": 500})
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_query_engine():
    """Mock HybridQueryEngine"""
    with patch("app.services.knowledgebeast_service.HybridQueryEngine") as mock:
        engine = Mock()
        # search_keyword returns just a list (no degraded flag)
        engine.search_keyword = Mock(
            return_value=[
                (
                    "doc1",
                    {
                        "content": "Machine learning",
                        "category": "ai",
                        "path": "ml.txt",
                        "name": "ML",
                    },
                    0.8,
                ),
                (
                    "doc2",
                    {
                        "content": "Deep learning",
                        "category": "ai",
                        "path": "dl.txt",
                        "name": "DL",
                    },
                    0.6,
                ),
            ]
        )
        # search_vector returns tuple (results, degraded_flag)
        engine.search_vector = Mock(
            return_value=(
                [
                    (
                        "doc1",
                        {
                            "content": "Machine learning is AI",
                            "category": "ai",
                            "path": "ml.txt",
                            "name": "ML Intro",
                        },
                        0.2,
                    ),
                    (
                        "doc2",
                        {
                            "content": "Deep learning is ML",
                            "category": "ai",
                            "path": "dl.txt",
                            "name": "DL Basics",
                        },
                        0.3,
                    ),
                ],
                False,  # degraded flag
            )
        )
        # search_hybrid returns tuple (results, degraded_flag)
        engine.search_hybrid = Mock(
            return_value=(
                [
                    (
                        "doc1",
                        {
                            "content": "Machine learning",
                            "category": "ai",
                            "path": "ml.txt",
                            "name": "ML",
                        },
                        0.9,
                    ),
                    (
                        "doc2",
                        {
                            "content": "Deep learning",
                            "category": "ai",
                            "path": "dl.txt",
                            "name": "DL",
                        },
                        0.7,
                    ),
                ],
                False,  # degraded flag
            )
        )
        # refresh_embeddings - called after adding documents
        engine.refresh_embeddings = Mock()
        # get_embedding_stats - for statistics
        engine.get_embedding_stats = Mock(
            return_value={"hit_rate": 0.95, "size": 100, "capacity": 1000}
        )
        mock.return_value = engine
        yield engine


@pytest.fixture
def kb_service(mock_embedding_engine, mock_vector_store, mock_repository, mock_query_engine):
    """Create KnowledgeBeastService with mocked components"""
    service = KnowledgeBeastService(
        project_id=1, db_path="./test_kb_chroma", embedding_model="all-MiniLM-L6-v2"
    )
    return service


class TestKnowledgeBeastServiceInit:
    """Test service initialization"""

    def test_init_with_defaults(self, kb_service):
        """Test initialization with default parameters"""
        assert kb_service.project_id == 1
        assert kb_service.collection_name == "project_1"
        assert kb_service.embedding_model == "all-MiniLM-L6-v2"

    def test_init_with_custom_project(
        self, mock_embedding_engine, mock_vector_store, mock_repository, mock_query_engine
    ):
        """Test initialization with different project ID"""
        service = KnowledgeBeastService(project_id=42)
        assert service.project_id == 42
        assert service.collection_name == "project_42"

    def test_init_without_kb_raises_error(self):
        """Test that ImportError is raised when KB not available"""
        with patch("app.services.knowledgebeast_service.KNOWLEDGEBEAST_AVAILABLE", False):
            with pytest.raises(ImportError, match="KnowledgeBeast not installed"):
                KnowledgeBeastService(project_id=1)


class TestQuery:
    """Test query methods"""

    @pytest.mark.asyncio
    async def test_query_vector_mode(self, kb_service, mock_query_engine):
        """Test vector search mode"""
        results = await kb_service.query(question="What is machine learning?", mode="vector", k=5)

        assert len(results) == 2
        assert results[0]["content"] == "Machine learning is AI"
        assert results[0]["category"] == "ai"
        assert results[0]["score"] == 0.2
        assert results[0]["title"] == "ML Intro"

        # Verify query_engine.search_vector was called
        mock_query_engine.search_vector.assert_called_once_with(
            "What is machine learning?", top_k=5
        )

    @pytest.mark.asyncio
    async def test_query_keyword_mode(self, kb_service, mock_query_engine):
        """Test keyword search mode"""
        results = await kb_service.query(question="machine learning", mode="keyword", k=5)

        assert len(results) == 2
        assert results[0]["content"] == "Machine learning"
        assert results[0]["score"] == 0.8

        # Verify keyword search was called (no top_k argument in service)
        mock_query_engine.search_keyword.assert_called_once_with("machine learning")

    @pytest.mark.asyncio
    async def test_query_hybrid_mode(self, kb_service, mock_query_engine):
        """Test hybrid search mode"""
        results = await kb_service.query(question="machine learning", mode="hybrid", k=5, alpha=0.7)

        assert len(results) == 2
        assert results[0]["score"] == 0.9

        # Verify hybrid search was called
        mock_query_engine.search_hybrid.assert_called_once_with(
            "machine learning", alpha=0.7, top_k=5
        )

    @pytest.mark.asyncio
    async def test_query_with_category_filter(self, kb_service, mock_query_engine):
        """Test query with category filter"""
        results = await kb_service.query(question="What is AI?", category="ai", mode="vector", k=5)

        # Results should be filtered by category (done in service after query)
        assert results is not None
        # Verify search was called
        mock_query_engine.search_vector.assert_called_once()


class TestAddDocument:
    """Test document addition"""

    @pytest.mark.asyncio
    async def test_add_document_simple(self, kb_service, mock_repository, mock_query_engine):
        """Test adding a simple document"""
        content = "This is a test document about machine learning."
        metadata = {"category": "test", "source": "test.txt", "title": "Test Doc"}

        chunks_added = await kb_service.add_document(
            content=content, metadata=metadata, chunk_size=1000
        )

        assert chunks_added > 0

        # Verify repository add was called
        assert mock_repository.add_document.called

        # Verify query engine refresh_embeddings was called
        assert mock_query_engine.refresh_embeddings.called

    @pytest.mark.asyncio
    async def test_add_document_with_chunking(self, kb_service, mock_repository, mock_query_engine):
        """Test document chunking"""
        # Long content that will be chunked
        content = " ".join(["word"] * 1500)  # ~7500 chars
        metadata = {"category": "test", "source": "long.txt"}

        chunks_added = await kb_service.add_document(
            content=content, metadata=metadata, chunk_size=1000
        )

        # Should create multiple chunks
        assert chunks_added > 1

    @pytest.mark.asyncio
    async def test_add_document_empty_content(self, kb_service):
        """Test adding empty document returns 0"""
        chunks_added = await kb_service.add_document(
            content="", metadata={"category": "test", "source": "empty.txt"}
        )

        assert chunks_added == 0


class TestDeleteBySource:
    """Test document deletion"""

    @pytest.mark.asyncio
    async def test_delete_by_source_success(self, kb_service, mock_repository):
        """Test successful deletion"""
        # Set up documents in repository with matching source
        mock_repository.documents = {
            "doc1": {"path": "test.txt", "content": "test1"},
            "doc2": {"path": "test.txt", "content": "test2"},
        }
        mock_repository.inverted_index = {"test": {"doc1", "doc2"}}

        success = await kb_service.delete_by_source("test.txt")

        assert success is True
        # Documents should be removed (we can check the mock was modified)

    @pytest.mark.asyncio
    async def test_delete_by_source_not_found(self, kb_service, mock_repository):
        """Test deletion when source not found"""
        mock_repository.documents = {}

        success = await kb_service.delete_by_source("nonexistent.txt")

        assert success is False

    @pytest.mark.asyncio
    async def test_delete_by_source_error_handling(self, kb_service, mock_repository):
        """Test error handling during deletion"""
        # Make documents.items() raise an exception
        mock_repository.documents = Mock()
        mock_repository.documents.items.side_effect = Exception("Database error")

        success = await kb_service.delete_by_source("test.txt")

        assert success is False


class TestGetStatistics:
    """Test statistics retrieval"""

    @pytest.mark.asyncio
    async def test_get_statistics(self, kb_service, mock_repository, mock_query_engine):
        """Test getting knowledge base statistics"""
        # Mock repository.documents for category breakdown
        mock_repository.documents = {
            "doc1": {"category": "ai"},
            "doc2": {"category": "ai"},
            "doc3": {"category": "ml"},
        }

        stats = await kb_service.get_statistics()

        assert stats["total_chunks"] == 100  # From mock_repository.get_stats
        assert stats["categories"]["ai"] == 2
        assert stats["categories"]["ml"] == 1
        assert stats["embedding_model"] == "all-MiniLM-L6-v2"
        assert stats["collection_name"] == "project_1"
        assert stats["project_id"] == 1
        assert "cache_hit_rate" in stats

    @pytest.mark.asyncio
    async def test_get_statistics_error_handling(self, kb_service, mock_repository):
        """Test statistics error handling"""
        mock_repository.get_stats.side_effect = Exception("Stats error")

        stats = await kb_service.get_statistics()

        assert stats["total_chunks"] == 0
        assert "error" in stats


class TestGetHealth:
    """Test health check"""

    @pytest.mark.asyncio
    async def test_get_health_healthy(self, kb_service, mock_repository):
        """Test health check when healthy"""
        # Set up documents for health check
        mock_repository.documents = {"doc1": {}, "doc2": {}}

        health = await kb_service.get_health()

        assert health["status"] == "healthy"
        assert health["document_count"] == 2
        assert health["collection"] == "project_1"

    @pytest.mark.asyncio
    async def test_get_health_unhealthy(self, kb_service, mock_repository):
        """Test health check when unhealthy"""
        # Make documents access raise an exception
        mock_repository.documents = Mock()
        mock_repository.documents.__len__ = Mock(side_effect=Exception("Health check failed"))

        health = await kb_service.get_health()

        assert health["status"] == "unhealthy"
        assert "error" in health


class TestGetCategories:
    """Test category listing"""

    @pytest.mark.asyncio
    async def test_get_categories(self, kb_service, mock_repository):
        """Test getting unique categories"""
        mock_repository.documents = {
            "doc1": {"category": "ai"},
            "doc2": {"category": "ml"},
            "doc3": {"category": "ai"},
            "doc4": {"category": "nlp"},
        }

        categories = await kb_service.get_categories()

        assert sorted(categories) == ["ai", "ml", "nlp"]

    @pytest.mark.asyncio
    async def test_get_categories_empty(self, kb_service, mock_repository):
        """Test getting categories when empty"""
        mock_repository.documents = {}

        categories = await kb_service.get_categories()

        assert categories == []


class TestResultFormatting:
    """Test result formatting for CommandCenter compatibility"""

    def test_format_vector_results(self, kb_service):
        """Test formatting vector search results (tuple format from HybridQueryEngine)"""
        # HybridQueryEngine returns list of tuples: (doc_id, doc_data, score)
        raw_results = [
            (
                "doc1",
                {"content": "Content 1", "category": "ai", "path": "1.txt", "name": "Doc 1"},
                0.1,
            ),
            (
                "doc2",
                {"content": "Content 2", "category": "ml", "path": "2.txt", "name": "Doc 2"},
                0.2,
            ),
        ]

        formatted = kb_service._format_results(raw_results)

        assert len(formatted) == 2
        assert formatted[0]["content"] == "Content 1"
        assert formatted[0]["category"] == "ai"
        assert formatted[0]["source"] == "1.txt"
        assert formatted[0]["title"] == "Doc 1"
        assert formatted[0]["score"] == 0.1

    def test_format_hybrid_results(self, kb_service):
        """Test formatting hybrid/keyword search results"""
        raw_results = [
            (
                "doc1",
                {"content": "Content 1", "category": "ai", "path": "1.txt", "name": "Doc 1"},
                0.9,
            ),
            (
                "doc2",
                {"content": "Content 2", "category": "ml", "path": "2.txt", "name": "Doc 2"},
                0.8,
            ),
        ]

        formatted = kb_service._format_results(raw_results)

        assert len(formatted) == 2
        assert formatted[0]["content"] == "Content 1"
        assert formatted[0]["score"] == 0.9


class TestSimpleChunking:
    """Test fallback chunking"""

    def test_simple_chunk(self, kb_service):
        """Test simple text chunking"""
        text = " ".join(["word"] * 200)  # 1000+ chars
        chunks = kb_service._simple_chunk(text, chunk_size=500)

        assert len(chunks) > 1
        assert all(len(chunk) <= 600 for chunk in chunks)  # Allow some overhead

    def test_simple_chunk_short_text(self, kb_service):
        """Test chunking short text"""
        text = "Short text"
        chunks = kb_service._simple_chunk(text, chunk_size=1000)

        assert len(chunks) == 1
        assert chunks[0] == text
