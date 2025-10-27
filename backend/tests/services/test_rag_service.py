"""
Unit tests for RAGService with KnowledgeBeast PostgresBackend

Tests the RAG service using mocked PostgresBackend to avoid requiring
a real database connection during unit tests.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import List, Dict, Any

from app.services.rag_service import RAGService, RAG_AVAILABLE


# Skip all tests if RAG dependencies not installed
pytestmark = pytest.mark.skipif(
    not RAG_AVAILABLE,
    reason="KnowledgeBeast dependencies not installed"
)


@pytest.fixture
def mock_postgres_backend():
    """Mock PostgresBackend for testing"""
    with patch('app.services.rag_service.PostgresBackend') as mock_class:
        # Create mock instance
        backend = AsyncMock()
        backend.initialize = AsyncMock()
        backend.query_hybrid = AsyncMock(return_value=[
            ("doc1", 0.95, {"category": "docs", "source": "readme.md"}, "Test document content"),
            ("doc2", 0.85, {"category": "docs", "source": "guide.md"}, "Guide content"),
        ])
        backend.add_documents = AsyncMock()
        backend.delete_documents = AsyncMock(return_value=2)
        backend.get_statistics = AsyncMock(return_value={
            "document_count": 100,
            "collection": "commandcenter_1"
        })
        backend.close = AsyncMock()

        # Mock class returns our mock instance
        mock_class.return_value = backend

        yield backend


@pytest.fixture
def mock_embed_text():
    """Mock embed_text function"""
    with patch('app.services.rag_service.embed_text') as mock:
        mock.return_value = [0.1] * 384  # Mock 384-dim embedding
        yield mock


@pytest.fixture
def mock_embed_texts():
    """Mock embed_texts function"""
    with patch('app.services.rag_service.embed_texts') as mock:
        # Return list of embeddings (one per text)
        mock.return_value = [[0.1] * 384, [0.2] * 384]
        yield mock


@pytest.fixture
def mock_settings():
    """Mock settings"""
    with patch('app.services.rag_service.settings') as mock:
        mock.KNOWLEDGE_COLLECTION_PREFIX = "commandcenter"
        mock.EMBEDDING_MODEL = "all-MiniLM-L6-v2"
        mock.EMBEDDING_DIMENSION = 384
        mock.KB_POOL_MAX_SIZE = 10
        mock.KB_POOL_MIN_SIZE = 2
        mock.get_postgres_url = Mock(return_value="postgresql://user:pass@localhost/db")
        yield mock


@pytest.fixture
def rag_service(mock_postgres_backend, mock_settings):
    """Create RAGService with mocked dependencies"""
    service = RAGService(repository_id=1)
    return service


class TestRAGServiceInit:
    """Test RAGService initialization"""

    def test_init_with_repository_id(self, mock_postgres_backend, mock_settings):
        """Test initialization with repository ID"""
        service = RAGService(repository_id=1)

        assert service.repository_id == 1
        assert service.collection_name == "commandcenter_1"
        assert service._initialized is False
        assert service.backend is not None

    def test_init_different_repository(self, mock_postgres_backend, mock_settings):
        """Test initialization with different repository ID"""
        service = RAGService(repository_id=42)

        assert service.repository_id == 42
        assert service.collection_name == "commandcenter_42"

    def test_init_without_dependencies_raises_error(self):
        """Test that ImportError is raised when dependencies not available"""
        with patch('app.services.rag_service.RAG_AVAILABLE', False):
            with pytest.raises(ImportError, match="KnowledgeBeast dependencies not installed"):
                RAGService(repository_id=1)


class TestInitialize:
    """Test backend initialization"""

    @pytest.mark.asyncio
    async def test_initialize_backend(self, rag_service, mock_postgres_backend):
        """Test backend initialization"""
        await rag_service.initialize()

        assert rag_service._initialized is True
        mock_postgres_backend.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_initialize_only_once(self, rag_service, mock_postgres_backend):
        """Test that initialization only happens once"""
        await rag_service.initialize()
        await rag_service.initialize()

        # Should only be called once
        assert mock_postgres_backend.initialize.call_count == 1


class TestQuery:
    """Test query method"""

    @pytest.mark.asyncio
    async def test_query_basic(self, rag_service, mock_postgres_backend, mock_embed_text):
        """Test basic query"""
        results = await rag_service.query(question="What is machine learning?", k=5)

        assert len(results) == 2
        assert results[0]["content"] == "Test document content"
        assert results[0]["category"] == "docs"
        assert results[0]["source"] == "readme.md"
        assert results[0]["score"] == 0.95

        # Verify embed_text was called
        mock_embed_text.assert_called_once_with(
            "What is machine learning?",
            model_name="all-MiniLM-L6-v2"
        )

        # Verify hybrid search was called
        mock_postgres_backend.query_hybrid.assert_called_once()

    @pytest.mark.asyncio
    async def test_query_with_category_filter(self, rag_service, mock_postgres_backend, mock_embed_text):
        """Test query with category filter"""
        results = await rag_service.query(
            question="Python tutorials",
            category="tutorials",
            k=10
        )

        # Verify filter was passed to backend
        call_args = mock_postgres_backend.query_hybrid.call_args
        assert call_args[1]["where"] == {"category": "tutorials"}
        assert call_args[1]["top_k"] == 10

    @pytest.mark.asyncio
    async def test_query_initializes_if_needed(self, rag_service, mock_postgres_backend):
        """Test that query initializes backend if not already initialized"""
        assert rag_service._initialized is False

        await rag_service.query(question="test")

        assert rag_service._initialized is True
        mock_postgres_backend.initialize.assert_called_once()


class TestAddDocument:
    """Test add_document method"""

    @pytest.mark.asyncio
    async def test_add_document_basic(self, rag_service, mock_postgres_backend, mock_embed_texts):
        """Test adding a document"""
        content = "This is a test document about machine learning."
        metadata = {"category": "docs", "source": "test.md"}

        chunks_added = await rag_service.add_document(
            content=content,
            metadata=metadata,
            chunk_size=1000
        )

        assert chunks_added > 0

        # Verify embeddings were generated
        mock_embed_texts.assert_called_once()

        # Verify backend add_documents was called
        mock_postgres_backend.add_documents.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_document_chunking(self, rag_service, mock_postgres_backend, mock_embed_texts):
        """Test document chunking"""
        # Create long content that will be chunked
        content = " ".join(["word"] * 500)  # ~2500 chars
        metadata = {"category": "docs", "source": "long.md"}

        # Mock embed_texts to return embeddings for each chunk
        mock_embed_texts.return_value = [[0.1] * 384, [0.2] * 384, [0.3] * 384]

        chunks_added = await rag_service.add_document(
            content=content,
            metadata=metadata,
            chunk_size=1000
        )

        # Should create multiple chunks
        assert chunks_added >= 2

    @pytest.mark.asyncio
    async def test_add_document_metadata_preservation(self, rag_service, mock_postgres_backend, mock_embed_texts):
        """Test that metadata is preserved for each chunk"""
        content = "Test content"
        metadata = {"category": "test", "source": "test.md", "author": "Test Author"}

        await rag_service.add_document(content=content, metadata=metadata)

        # Get the call arguments
        call_args = mock_postgres_backend.add_documents.call_args
        metadatas = call_args[1]["metadatas"]

        # Each chunk should have the same metadata
        for meta in metadatas:
            assert meta["category"] == "test"
            assert meta["source"] == "test.md"
            assert meta["author"] == "Test Author"


class TestDeleteBySource:
    """Test delete_by_source method"""

    @pytest.mark.asyncio
    async def test_delete_by_source_success(self, rag_service, mock_postgres_backend):
        """Test successful deletion"""
        # Mock backend to return count of 5
        mock_postgres_backend.delete_documents.return_value = 5

        success = await rag_service.delete_by_source("test.md")

        assert success is True

        # Verify delete was called with correct filter
        mock_postgres_backend.delete_documents.assert_called_once_with(
            where={"source": "test.md"}
        )

    @pytest.mark.asyncio
    async def test_delete_by_source_not_found(self, rag_service, mock_postgres_backend):
        """Test deletion when source not found"""
        # Mock backend to return count of 0
        mock_postgres_backend.delete_documents.return_value = 0

        success = await rag_service.delete_by_source("nonexistent.md")

        assert success is False


class TestGetCategories:
    """Test get_categories method"""

    @pytest.mark.asyncio
    async def test_get_categories_not_implemented(self, rag_service):
        """Test that get_categories returns empty list (not yet implemented)"""
        categories = await rag_service.get_categories()

        # Current implementation returns empty list
        # This can be enhanced later with custom SQL queries
        assert categories == []


class TestGetStatistics:
    """Test get_statistics method"""

    @pytest.mark.asyncio
    async def test_get_statistics(self, rag_service, mock_postgres_backend):
        """Test getting statistics"""
        stats = await rag_service.get_statistics()

        assert stats["total_chunks"] == 100
        assert stats["backend"] == "postgres"
        assert stats["collection_name"] == "commandcenter_1"
        assert stats["embedding_model"] == "all-MiniLM-L6-v2"
        assert stats["embedding_dimension"] == 384

        # Verify backend get_statistics was called
        mock_postgres_backend.get_statistics.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_statistics_initializes_if_needed(self, rag_service, mock_postgres_backend):
        """Test that get_statistics initializes backend if needed"""
        assert rag_service._initialized is False

        await rag_service.get_statistics()

        assert rag_service._initialized is True


class TestClose:
    """Test close method"""

    @pytest.mark.asyncio
    async def test_close(self, rag_service, mock_postgres_backend):
        """Test closing the service"""
        # Initialize first
        await rag_service.initialize()
        assert rag_service._initialized is True

        # Close
        await rag_service.close()

        assert rag_service._initialized is False
        mock_postgres_backend.close.assert_called_once()

    @pytest.mark.asyncio
    async def test_close_when_not_initialized(self, rag_service, mock_postgres_backend):
        """Test closing when not initialized"""
        assert rag_service._initialized is False

        await rag_service.close()

        # Should not call backend.close() if not initialized
        mock_postgres_backend.close.assert_not_called()
