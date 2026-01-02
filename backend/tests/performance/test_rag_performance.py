"""RAG search performance tests."""
import asyncio
import time
from unittest.mock import AsyncMock

import pytest


@pytest.mark.asyncio
@pytest.mark.xfail(reason="RAG service requires KnowledgeBeast dependencies", strict=False)
async def test_rag_query_response_time(performance_threshold, client, auth_headers_factory, user_a):
    """RAG query completes within threshold (1500ms)."""
    from app.main import app
    from app.routers.knowledge import get_rag_service

    # Mock RAG service to avoid dependency on KnowledgeBeast
    async def mock_get_rag_service(repository_id: int = 1):
        mock_rag = AsyncMock()
        mock_rag.initialize.return_value = None
        mock_rag.query.return_value = [{"content": "Test result", "metadata": {}, "score": 0.9}]
        return mock_rag

    app.dependency_overrides[get_rag_service] = mock_get_rag_service

    try:
        headers = auth_headers_factory(user_a)

        query = "What technologies are we evaluating for backend development?"

        start = time.time()
        response = await client.post(
            "/api/v1/knowledge/query",
            json={"query": query, "repository_id": 1},
            headers=headers,
        )
        elapsed = (time.time() - start) * 1000

        assert response.status_code == 200
        assert elapsed < performance_threshold["rag_search"], (
            f"RAG query took {elapsed:.0f}ms, "
            f"exceeds {performance_threshold['rag_search']}ms threshold"
        )
    finally:
        app.dependency_overrides.pop(get_rag_service, None)


@pytest.mark.asyncio
@pytest.mark.xfail(reason="RAG service requires KnowledgeBeast dependencies", strict=False)
async def test_rag_concurrent_queries(performance_threshold, client, auth_headers_factory, user_a):
    """5 concurrent RAG queries complete within threshold (3000ms)."""
    from app.main import app
    from app.routers.knowledge import get_rag_service

    # Mock RAG service to avoid dependency on KnowledgeBeast
    async def mock_get_rag_service(repository_id: int = 1):
        mock_rag = AsyncMock()
        mock_rag.initialize.return_value = None
        mock_rag.query.return_value = [{"content": "Test result", "metadata": {}, "score": 0.9}]
        return mock_rag

    app.dependency_overrides[get_rag_service] = mock_get_rag_service

    try:
        headers = auth_headers_factory(user_a)

        queries = [
            "What is our technology strategy?",
            "Which databases are we considering?",
            "What frameworks are in evaluation?",
            "Tell me about our research priorities",
            "What are the key technologies?",
        ]

        start = time.time()

        tasks = [
            client.post(
                "/api/v1/knowledge/query",
                json={"query": q, "repository_id": 1},
                headers=headers,
            )
            for q in queries
        ]

        responses = await asyncio.gather(*tasks)

        elapsed = (time.time() - start) * 1000

        # All should succeed
        assert all(r.status_code == 200 for r in responses)

        # Should complete within threshold
        assert (
            elapsed < 3000
        ), f"5 concurrent RAG queries took {elapsed:.0f}ms, exceeds 3000ms threshold"
    finally:
        app.dependency_overrides.pop(get_rag_service, None)
