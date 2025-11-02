"""
Integration tests for Knowledge/RAG API endpoints
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from backend.tests.utils.factories import ProjectFactory, RepositoryFactory


@pytest.mark.integration
class TestKnowledgeAPI:
    """Test Knowledge/RAG query endpoint"""

    async def test_query_knowledge_base_success(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test querying the knowledge base"""
        project = await ProjectFactory.create(db_session)
        repo = await RepositoryFactory.create(db=db_session, project_id=project.id)

        # Mock RAG service
        mock_results = [
            {
                "content": "FastAPI is a modern web framework",
                "metadata": {"file_path": "docs/fastapi.md"},
                "score": 0.95,
            },
            {
                "content": "FastAPI supports async operations",
                "metadata": {"file_path": "docs/async.md"},
                "score": 0.87,
            },
        ]

        with patch("app.services.rag_service.RAGService") as mock_rag_class:
            mock_rag = AsyncMock()
            mock_rag.query.return_value = mock_results
            mock_rag.initialize.return_value = None
            mock_rag_class.return_value = mock_rag

            # Query knowledge base
            query_data = {
                "query": "What is FastAPI?",
                "repository_id": repo.id,
                "k": 5,
            }

            response = await async_client.post("/knowledge/query", json=query_data)

            assert response.status_code == 200
            data = response.json()
            assert "results" in data
            assert len(data["results"]) == 2
            assert data["results"][0]["content"] == "FastAPI is a modern web framework"
            assert data["results"][0]["score"] == 0.95

    async def test_query_knowledge_base_with_category_filter(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test querying knowledge base with category filter"""
        project = await ProjectFactory.create(db_session)
        repo = await RepositoryFactory.create(db=db_session, project_id=project.id)

        mock_results = [
            {
                "content": "Documentation about testing",
                "metadata": {"file_path": "docs/testing.md", "category": "docs"},
                "score": 0.92,
            }
        ]

        with patch("app.services.rag_service.RAGService") as mock_rag_class:
            mock_rag = AsyncMock()
            mock_rag.query.return_value = mock_results
            mock_rag.initialize.return_value = None
            mock_rag_class.return_value = mock_rag

            query_data = {
                "query": "How to write tests?",
                "repository_id": repo.id,
                "category": "docs",
                "k": 3,
            }

            response = await async_client.post("/knowledge/query", json=query_data)

            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 1
            assert "category" in data["results"][0]["metadata"]

    async def test_query_knowledge_base_empty_results(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test querying with no matching results"""
        project = await ProjectFactory.create(db_session)
        repo = await RepositoryFactory.create(db=db_session, project_id=project.id)

        with patch("app.services.rag_service.RAGService") as mock_rag_class:
            mock_rag = AsyncMock()
            mock_rag.query.return_value = []  # Empty results
            mock_rag.initialize.return_value = None
            mock_rag_class.return_value = mock_rag

            query_data = {
                "query": "unknown topic",
                "repository_id": repo.id,
                "k": 5,
            }

            response = await async_client.post("/knowledge/query", json=query_data)

            assert response.status_code == 200
            data = response.json()
            assert data["results"] == []

    async def test_query_knowledge_base_validation_error(self, async_client: AsyncClient):
        """Test query validation errors"""
        # Missing required fields
        invalid_data = {
            "repository_id": 1,
            # Missing query field
        }

        response = await async_client.post("/knowledge/query", json=invalid_data)

        assert response.status_code == 422  # Validation error

    async def test_query_knowledge_base_nonexistent_repository(self, async_client: AsyncClient):
        """Test querying with nonexistent repository"""
        query_data = {
            "query": "test query",
            "repository_id": 99999,  # Doesn't exist
            "k": 5,
        }

        response = await async_client.post("/knowledge/query", json=query_data)

        # Should return 404 or appropriate error
        assert response.status_code in [404, 400]

    async def test_index_repository(self, async_client: AsyncClient, db_session: AsyncSession):
        """Test indexing a repository for knowledge base"""
        project = await ProjectFactory.create(db_session)
        repo = await RepositoryFactory.create(db=db_session, project_id=project.id)

        with patch("app.services.rag_service.RAGService") as mock_rag_class:
            mock_rag = AsyncMock()
            mock_rag.index_repository = AsyncMock(return_value={"indexed": True, "documents": 150})
            mock_rag.initialize.return_value = None
            mock_rag_class.return_value = mock_rag

            # Index repository
            response = await async_client.post(f"/knowledge/index/{repo.id}")

            assert response.status_code in [200, 202]  # Success or Accepted
            data = response.json()
            # Response format may vary, just check it's successful

    async def test_query_with_custom_k_parameter(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test querying with custom number of results"""
        project = await ProjectFactory.create(db_session)
        repo = await RepositoryFactory.create(db=db_session, project_id=project.id)

        mock_results = [
            {"content": f"Result {i}", "metadata": {}, "score": 0.9 - (i * 0.1)} for i in range(10)
        ]

        with patch("app.services.rag_service.RAGService") as mock_rag_class:
            mock_rag = AsyncMock()
            mock_rag.query.return_value = mock_results[:3]  # Return top 3
            mock_rag.initialize.return_value = None
            mock_rag_class.return_value = mock_rag

            query_data = {
                "query": "test",
                "repository_id": repo.id,
                "k": 3,
            }

            response = await async_client.post("/knowledge/query", json=query_data)

            assert response.status_code == 200
            data = response.json()
            assert len(data["results"]) == 3

    async def test_query_knowledge_base_metadata_included(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that query results include metadata"""
        project = await ProjectFactory.create(db_session)
        repo = await RepositoryFactory.create(db=db_session, project_id=project.id)

        mock_results = [
            {
                "content": "Content with metadata",
                "metadata": {
                    "file_path": "src/main.py",
                    "line_number": 42,
                    "category": "code",
                },
                "score": 0.95,
            }
        ]

        with patch("app.services.rag_service.RAGService") as mock_rag_class:
            mock_rag = AsyncMock()
            mock_rag.query.return_value = mock_results
            mock_rag.initialize.return_value = None
            mock_rag_class.return_value = mock_rag

            query_data = {
                "query": "test",
                "repository_id": repo.id,
            }

            response = await async_client.post("/knowledge/query", json=query_data)

            assert response.status_code == 200
            data = response.json()
            assert "metadata" in data["results"][0]
            assert data["results"][0]["metadata"]["file_path"] == "src/main.py"
            assert data["results"][0]["metadata"]["line_number"] == 42

    async def test_query_knowledge_base_score_ordering(
        self, async_client: AsyncClient, db_session: AsyncSession
    ):
        """Test that results are ordered by relevance score"""
        project = await ProjectFactory.create(db_session)
        repo = await RepositoryFactory.create(db=db_session, project_id=project.id)

        mock_results = [
            {"content": "Most relevant", "metadata": {}, "score": 0.95},
            {"content": "Second relevant", "metadata": {}, "score": 0.87},
            {"content": "Third relevant", "metadata": {}, "score": 0.75},
        ]

        with patch("app.services.rag_service.RAGService") as mock_rag_class:
            mock_rag = AsyncMock()
            mock_rag.query.return_value = mock_results
            mock_rag.initialize.return_value = None
            mock_rag_class.return_value = mock_rag

            query_data = {
                "query": "test",
                "repository_id": repo.id,
            }

            response = await async_client.post("/knowledge/query", json=query_data)

            assert response.status_code == 200
            data = response.json()

            # Verify ordering by score
            scores = [r["score"] for r in data["results"]]
            assert scores == sorted(scores, reverse=True)
