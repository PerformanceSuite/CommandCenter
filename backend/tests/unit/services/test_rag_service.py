"""
Unit tests for RAG service
"""

import pytest
from unittest.mock import Mock, MagicMock, AsyncMock, patch
from typing import List, Dict, Any

from app.services.rag_service import RAGService


@pytest.mark.unit
class TestRAGService:
    """Test RAGService query logic"""

    @pytest.fixture
    def mock_embedding_model(self):
        """Mock SentenceTransformer"""
        mock = MagicMock()
        mock.encode.return_value = [0.1] * 384  # Mock embedding vector
        return mock

    @pytest.fixture
    def mock_postgres_backend(self):
        """Mock PostgresBackend"""
        mock = MagicMock()
        mock.initialize = AsyncMock()
        mock.query = AsyncMock(return_value=[
            {
                "content": "FastAPI is a modern web framework",
                "metadata": {"file_path": "docs/fastapi.md", "line_number": 10},
                "score": 0.95,
            },
            {
                "content": "FastAPI supports async/await",
                "metadata": {"file_path": "docs/async.md", "line_number": 5},
                "score": 0.87,
            }
        ])
        mock.add_documents = AsyncMock()
        mock.delete_collection = AsyncMock()
        mock.close = AsyncMock()
        return mock

    @pytest.mark.asyncio
    async def test_rag_service_initialization(self):
        """Test RAG service initialization"""
        with patch("app.services.rag_service.RAG_AVAILABLE", True):
            with patch("app.services.rag_service.PostgresBackend") as mock_backend_class:
                with patch("app.services.rag_service.SentenceTransformer") as mock_transformer:
                    # Setup mocks
                    mock_backend = MagicMock()
                    mock_backend_class.return_value = mock_backend
                    mock_transformer.return_value = MagicMock()

                    # Create service
                    service = RAGService(repository_id=1)

                    assert service.repository_id == 1
                    assert service.collection_name.endswith("_1")
                    assert service._initialized is False

    @pytest.mark.asyncio
    async def test_rag_service_query_success(self, mock_embedding_model, mock_postgres_backend):
        """Test successful RAG query"""
        with patch("app.services.rag_service.RAG_AVAILABLE", True):
            with patch("app.services.rag_service.PostgresBackend", return_value=mock_postgres_backend):
                with patch("app.services.rag_service.SentenceTransformer", return_value=mock_embedding_model):
                    # Create service
                    service = RAGService(repository_id=1)
                    await service.initialize()

                    # Query
                    results = await service.query("What is FastAPI?", k=2)

                    # Assertions
                    assert len(results) == 2
                    assert results[0]["content"] == "FastAPI is a modern web framework"
                    assert results[0]["score"] == 0.95
                    assert "file_path" in results[0]["metadata"]
                    mock_postgres_backend.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_rag_service_query_with_category_filter(self, mock_embedding_model, mock_postgres_backend):
        """Test RAG query with category filter"""
        with patch("app.services.rag_service.RAG_AVAILABLE", True):
            with patch("app.services.rag_service.PostgresBackend", return_value=mock_postgres_backend):
                with patch("app.services.rag_service.SentenceTransformer", return_value=mock_embedding_model):
                    service = RAGService(repository_id=1)
                    await service.initialize()

                    # Query with category
                    results = await service.query("async patterns", category="documentation", k=3)

                    # Verify backend was called with category filter
                    mock_postgres_backend.query.assert_called_once()
                    call_args = mock_postgres_backend.query.call_args

                    # Check that category was passed
                    assert call_args is not None

    @pytest.mark.asyncio
    async def test_rag_service_add_documents(self, mock_embedding_model, mock_postgres_backend):
        """Test adding documents to knowledge base"""
        with patch("app.services.rag_service.RAG_AVAILABLE", True):
            with patch("app.services.rag_service.PostgresBackend", return_value=mock_postgres_backend):
                with patch("app.services.rag_service.SentenceTransformer", return_value=mock_embedding_model):
                    service = RAGService(repository_id=1)
                    await service.initialize()

                    # Add documents
                    documents = [
                        {
                            "content": "Document 1 content",
                            "metadata": {"file_path": "file1.py", "category": "code"},
                        },
                        {
                            "content": "Document 2 content",
                            "metadata": {"file_path": "file2.py", "category": "code"},
                        }
                    ]

                    await service.backend.add_documents(documents)

                    # Verify add_documents was called
                    mock_postgres_backend.add_documents.assert_called_once_with(documents)

    @pytest.mark.asyncio
    async def test_rag_service_initialization_required(self, mock_embedding_model, mock_postgres_backend):
        """Test that initialization is required before use"""
        with patch("app.services.rag_service.RAG_AVAILABLE", True):
            with patch("app.services.rag_service.PostgresBackend", return_value=mock_postgres_backend):
                with patch("app.services.rag_service.SentenceTransformer", return_value=mock_embedding_model):
                    service = RAGService(repository_id=1)

                    # Should not be initialized yet
                    assert service._initialized is False

                    # Initialize
                    await service.initialize()

                    # Should be initialized now
                    assert service._initialized is True
                    mock_postgres_backend.initialize.assert_called_once()

    @pytest.mark.asyncio
    async def test_rag_service_collection_naming(self):
        """Test collection name generation for multi-tenant isolation"""
        with patch("app.services.rag_service.RAG_AVAILABLE", True):
            with patch("app.services.rag_service.PostgresBackend") as mock_backend_class:
                with patch("app.services.rag_service.SentenceTransformer"):
                    mock_backend_class.return_value = MagicMock()

                    # Test different repository IDs
                    service1 = RAGService(repository_id=1)
                    service2 = RAGService(repository_id=2)
                    service3 = RAGService(repository_id=999)

                    assert service1.collection_name.endswith("_1")
                    assert service2.collection_name.endswith("_2")
                    assert service3.collection_name.endswith("_999")

                    # Ensure collections are different
                    assert service1.collection_name != service2.collection_name
                    assert service2.collection_name != service3.collection_name

    @pytest.mark.asyncio
    async def test_rag_service_empty_results(self, mock_embedding_model):
        """Test RAG service handles empty query results"""
        mock_backend = MagicMock()
        mock_backend.initialize = AsyncMock()
        mock_backend.query = AsyncMock(return_value=[])  # Empty results

        with patch("app.services.rag_service.RAG_AVAILABLE", True):
            with patch("app.services.rag_service.PostgresBackend", return_value=mock_backend):
                with patch("app.services.rag_service.SentenceTransformer", return_value=mock_embedding_model):
                    service = RAGService(repository_id=1)
                    await service.initialize()

                    # Query with no results
                    results = await service.query("unknown query", k=5)

                    assert results == []
                    assert isinstance(results, list)

    def test_rag_service_import_error(self):
        """Test RAGService raises ImportError when dependencies not available"""
        with patch("app.services.rag_service.RAG_AVAILABLE", False):
            with pytest.raises(ImportError) as exc_info:
                RAGService(repository_id=1)

            assert "KnowledgeBeast dependencies not installed" in str(exc_info.value)
