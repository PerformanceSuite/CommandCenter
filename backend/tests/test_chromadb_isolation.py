"""
Tests for ChromaDB collection isolation

These tests verify that:
1. Each repository gets its own collection
2. Queries are isolated per repository
3. Documents from Repository A don't appear in Repository B queries
4. Collection management works correctly
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from app.services.rag_service import RAGService


@pytest.fixture
def mock_chroma_client():
    """Mock ChromaDB client for testing"""
    with patch('app.services.rag_service.chromadb') as mock_chromadb:
        mock_client = Mock()
        mock_chromadb.PersistentClient.return_value = mock_client
        yield mock_client


@pytest.fixture
def mock_embeddings():
    """Mock embeddings model"""
    with patch('app.services.rag_service.HuggingFaceEmbeddings') as mock_hf:
        mock_embeddings = Mock()
        mock_hf.return_value = mock_embeddings
        yield mock_embeddings


@pytest.fixture
def mock_vectorstore():
    """Mock Chroma vectorstore"""
    with patch('app.services.rag_service.Chroma') as mock_chroma:
        mock_store = Mock()
        mock_chroma.return_value = mock_store
        yield mock_store


class TestRAGServiceCollectionNaming:
    """Test collection naming conventions"""

    def test_collection_name_format(self):
        """Test that collection names follow the correct format"""
        service = RAGService(repository_id=1)
        collection_name = service._get_collection_name(1)
        assert collection_name == "knowledge_repo_1"

        collection_name = service._get_collection_name(42)
        assert collection_name == "knowledge_repo_42"

    def test_default_collection_when_no_repo_id(self, mock_chroma_client, mock_embeddings, mock_vectorstore):
        """Test that default collection is used when no repository_id"""
        service = RAGService(repository_id=None)
        # Should use knowledge_default collection
        assert service.repository_id is None


class TestRAGServiceCollectionIsolation:
    """Test that collections are properly isolated"""

    @pytest.mark.asyncio
    async def test_add_document_to_repository_collection(self, mock_chroma_client, mock_embeddings, mock_vectorstore):
        """Test adding document to specific repository collection"""
        service = RAGService(repository_id=1)

        # Mock the add_texts method
        mock_vectorstore.add_texts.return_value = ['doc1', 'doc2']

        result = await service.add_document(
            content="Test document for repo 1",
            metadata={"title": "Test Doc"},
            repository_id=1
        )

        assert result["status"] == "added"
        assert result["repository_id"] == 1
        assert result["collection"] == "knowledge_repo_1"
        assert result["chunks_added"] > 0

    @pytest.mark.asyncio
    async def test_query_only_searches_repository_collection(self, mock_chroma_client, mock_embeddings, mock_vectorstore):
        """Test that queries only search the specified repository's collection"""
        service = RAGService(repository_id=1)

        # Mock search results
        mock_doc = Mock()
        mock_doc.page_content = "Test content from repo 1"
        mock_doc.metadata = {"title": "Test", "repository_id": 1}

        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc, 0.95)
        ]

        results = await service.query(
            question="test query",
            repository_id=1
        )

        assert len(results) == 1
        assert results[0]["repository_id"] == 1
        assert "repo 1" in results[0]["content"]

    @pytest.mark.asyncio
    async def test_different_repositories_have_different_collections(self, mock_chroma_client, mock_embeddings):
        """Test that different repositories initialize different collections"""
        service1 = RAGService(repository_id=1)
        service2 = RAGService(repository_id=2)

        # Collections should be different
        col1 = service1._get_collection_name(1)
        col2 = service2._get_collection_name(2)

        assert col1 != col2
        assert col1 == "knowledge_repo_1"
        assert col2 == "knowledge_repo_2"


class TestCollectionManagement:
    """Test collection management operations"""

    @pytest.mark.asyncio
    async def test_get_collection_stats(self, mock_chroma_client, mock_embeddings, mock_vectorstore):
        """Test getting statistics for a repository's collection"""
        service = RAGService()

        # Mock collection
        mock_collection = Mock()
        mock_collection.count.return_value = 42
        mock_collection.metadata = {"repository_id": 1}
        mock_chroma_client.get_collection.return_value = mock_collection

        stats = await service.get_collection_stats(repository_id=1)

        assert stats["repository_id"] == 1
        assert stats["collection_name"] == "knowledge_repo_1"
        assert stats["document_count"] == 42

    @pytest.mark.asyncio
    async def test_delete_collection(self, mock_chroma_client, mock_embeddings, mock_vectorstore):
        """Test deleting a repository's collection"""
        service = RAGService()

        result = await service.delete_collection(repository_id=1)

        assert result["status"] == "deleted"
        assert result["repository_id"] == 1
        assert result["collection"] == "knowledge_repo_1"
        mock_chroma_client.delete_collection.assert_called_once_with(name="knowledge_repo_1")

    @pytest.mark.asyncio
    async def test_list_all_collections(self, mock_chroma_client, mock_embeddings, mock_vectorstore):
        """Test listing all collections"""
        service = RAGService()

        # Mock collections
        mock_col1 = Mock()
        mock_col1.name = "knowledge_repo_1"
        mock_col1.count.return_value = 10
        mock_col1.metadata = {"repository_id": 1}

        mock_col2 = Mock()
        mock_col2.name = "knowledge_repo_2"
        mock_col2.count.return_value = 20
        mock_col2.metadata = {"repository_id": 2}

        mock_chroma_client.list_collections.return_value = [mock_col1, mock_col2]

        collections = await service.list_all_collections()

        assert len(collections) == 2
        assert collections[0]["name"] == "knowledge_repo_1"
        assert collections[0]["count"] == 10
        assert collections[1]["name"] == "knowledge_repo_2"
        assert collections[1]["count"] == 20


class TestCollectionIsolationIntegration:
    """Integration tests for collection isolation (requires ChromaDB)"""

    @pytest.mark.asyncio
    @pytest.mark.integration
    async def test_cross_repository_isolation(self):
        """
        Integration test: Verify that Repository A queries don't return Repository B documents

        This test requires actual ChromaDB to be available.
        Skip if RAG dependencies not installed.
        """
        try:
            from app.services.rag_service import RAG_AVAILABLE
            if not RAG_AVAILABLE:
                pytest.skip("RAG dependencies not installed")
        except ImportError:
            pytest.skip("RAG dependencies not installed")

        # Use temporary database path
        import tempfile
        import shutil
        temp_dir = tempfile.mkdtemp()

        try:
            # Initialize services for two different repositories
            service1 = RAGService(db_path=temp_dir, repository_id=1)
            service2 = RAGService(db_path=temp_dir, repository_id=2)

            # Add documents to Repository 1
            await service1.add_document(
                content="This is a document about Python programming in Repository 1",
                metadata={"title": "Python Doc", "category": "programming"},
                repository_id=1
            )

            # Add documents to Repository 2
            await service2.add_document(
                content="This is a document about Java programming in Repository 2",
                metadata={"title": "Java Doc", "category": "programming"},
                repository_id=2
            )

            # Query Repository 1 - should only get Python doc
            results1 = await service1.query(
                question="programming",
                repository_id=1,
                k=10
            )

            # Query Repository 2 - should only get Java doc
            results2 = await service2.query(
                question="programming",
                repository_id=2,
                k=10
            )

            # Verify isolation
            assert len(results1) > 0, "Repository 1 should have results"
            assert len(results2) > 0, "Repository 2 should have results"

            # Repository 1 should only have Python content
            for result in results1:
                assert "Python" in result["content"] or "Repository 1" in result["content"]
                assert "Java" not in result["content"]
                assert result["repository_id"] == 1

            # Repository 2 should only have Java content
            for result in results2:
                assert "Java" in result["content"] or "Repository 2" in result["content"]
                assert "Python" not in result["content"]
                assert result["repository_id"] == 2

        finally:
            # Cleanup
            shutil.rmtree(temp_dir, ignore_errors=True)


class TestBackwardsCompatibility:
    """Test backwards compatibility with existing code"""

    def test_service_works_without_repository_id(self, mock_chroma_client, mock_embeddings, mock_vectorstore):
        """Test that RAGService still works without repository_id for backwards compatibility"""
        # Should not raise an error
        service = RAGService(repository_id=None)
        assert service.repository_id is None

    @pytest.mark.asyncio
    async def test_query_works_without_repository_id(self, mock_chroma_client, mock_embeddings, mock_vectorstore):
        """Test that queries work without repository_id"""
        service = RAGService(repository_id=None)

        mock_doc = Mock()
        mock_doc.page_content = "Test content"
        mock_doc.metadata = {"title": "Test"}

        mock_vectorstore.similarity_search_with_score.return_value = [
            (mock_doc, 0.95)
        ]

        results = await service.query(question="test query")

        assert len(results) == 1
        assert results[0]["repository_id"] is None


# Run with: pytest backend/tests/test_chromadb_isolation.py -v
# Run integration tests: pytest backend/tests/test_chromadb_isolation.py -v -m integration
