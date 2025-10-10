"""
E2E Integration Tests for KnowledgeBeast

Tests the complete workflow with real KnowledgeBeast instance (not mocked).
Validates document upload, querying with different modes, and statistics.
"""

import pytest
from httpx import AsyncClient
import asyncio
import time

from app.main import app
from app.services.knowledgebeast_service import KNOWLEDGEBEAST_AVAILABLE
from app.config import settings


# Test documents for E2E validation
TEST_DOCUMENTS = [
    {
        "filename": "ml_basics.txt",
        "content": """Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence that enables systems to learn from data.
Key concepts include supervised learning, unsupervised learning, and reinforcement learning.

Supervised learning uses labeled data to train models for prediction tasks.
Common algorithms include linear regression, decision trees, and neural networks.

Deep learning is a specialized form of machine learning using neural networks with multiple layers.
It excels at tasks like image recognition, natural language processing, and speech recognition.
""",
        "category": "ai",
    },
    {
        "filename": "rag_systems.txt",
        "content": """Retrieval-Augmented Generation Systems

RAG combines vector search with language models for enhanced generation.
The process involves embedding documents, storing them in vector databases, and retrieving relevant context.

Vector databases like ChromaDB and Pinecone enable efficient similarity search.
Embeddings transform text into numerical representations that capture semantic meaning.

Hybrid search combines vector similarity with keyword matching (BM25) for better results.
The alpha parameter controls the balance between vector and keyword scores.
""",
        "category": "ai",
    },
    {
        "filename": "knowledgebeast.txt",
        "content": """KnowledgeBeast Overview

KnowledgeBeast is a production-ready RAG system with advanced search capabilities.
It supports vector search, keyword search, and hybrid search modes.

Key features include:
- Semantic caching for improved performance
- Per-project collection isolation
- Circuit breaker pattern for resilience
- Configurable embedding models (all-MiniLM-L6-v2, all-mpnet-base-v2)

Performance characteristics:
- Target latency: P99 < 200ms
- Cache hit rate: >90% after warmup
- Supports concurrent queries with thread safety
""",
        "category": "technical",
    },
]


# Mark as E2E test - requires KnowledgeBeast installed
pytestmark = pytest.mark.skipif(
    not KNOWLEDGEBEAST_AVAILABLE or not settings.use_knowledgebeast,
    reason="E2E tests require KnowledgeBeast enabled"
)


@pytest.fixture
async def kb_service():
    """Get KnowledgeBeast service instance"""
    from app.services.knowledgebeast_service import KnowledgeBeastService
    return KnowledgeBeastService(project_id=999)  # Use test project


@pytest.fixture
async def cleanup_test_data(kb_service):
    """Cleanup test data before and after tests"""
    # Cleanup before
    for doc in TEST_DOCUMENTS:
        try:
            await kb_service.delete_by_source(doc["filename"])
        except:
            pass

    yield

    # Cleanup after
    for doc in TEST_DOCUMENTS:
        try:
            await kb_service.delete_by_source(doc["filename"])
        except:
            pass


@pytest.mark.asyncio
@pytest.mark.e2e
class TestKnowledgeBeastE2E:
    """Complete E2E workflow tests"""

    async def test_complete_workflow(self, kb_service, cleanup_test_data):
        """Test: Upload → Query → Verify → Delete cycle"""

        # Step 1: Upload test documents
        print("\n📤 Step 1: Uploading test documents...")
        uploaded_docs = []

        for doc_data in TEST_DOCUMENTS:
            chunks_added = await kb_service.add_document(
                content=doc_data["content"],
                metadata={
                    "source": doc_data["filename"],
                    "category": doc_data["category"],
                    "title": doc_data["filename"],
                }
            )
            uploaded_docs.append({
                "filename": doc_data["filename"],
                "chunks": chunks_added,
            })
            print(f"  ✅ {doc_data['filename']}: {chunks_added} chunks")

        assert all(doc["chunks"] > 0 for doc in uploaded_docs), "All documents should create chunks"

        # Step 2: Vector search
        print("\n🔍 Step 2: Testing vector search...")
        vector_results = await kb_service.query(
            question="What is machine learning?",
            mode="vector",
            k=5
        )

        assert len(vector_results) > 0, "Vector search should return results"
        assert vector_results[0]["score"] > 0.3, "Top result should have decent score"
        assert "machine learning" in vector_results[0]["content"].lower() or "ml" in vector_results[0]["content"].lower()
        print(f"  ✅ Found {len(vector_results)} results, top score: {vector_results[0]['score']:.3f}")

        # Step 3: Keyword search
        print("\n🔍 Step 3: Testing keyword search...")
        keyword_results = await kb_service.query(
            question="RAG retrieval augmented generation",
            mode="keyword",
            k=5
        )

        assert len(keyword_results) > 0, "Keyword search should return results"
        print(f"  ✅ Found {len(keyword_results)} results, top score: {keyword_results[0]['score']:.3f}")

        # Step 4: Hybrid search
        print("\n🔍 Step 4: Testing hybrid search...")
        hybrid_results = await kb_service.query(
            question="KnowledgeBeast performance caching",
            mode="hybrid",
            alpha=0.7,
            k=5
        )

        assert len(hybrid_results) > 0, "Hybrid search should return results"
        print(f"  ✅ Found {len(hybrid_results)} results, top score: {hybrid_results[0]['score']:.3f}")

        # Step 5: Category filtering
        print("\n🔍 Step 5: Testing category filter...")
        ai_results = await kb_service.query(
            question="artificial intelligence concepts",
            category="ai",
            mode="vector",
            k=5
        )

        assert all(r["category"] == "ai" for r in ai_results), "All results should be from 'ai' category"
        print(f"  ✅ Category filter working: {len(ai_results)} AI results")

        # Step 6: Statistics
        print("\n📊 Step 6: Checking statistics...")
        stats = await kb_service.get_statistics()

        assert stats["total_chunks"] >= sum(doc["chunks"] for doc in uploaded_docs)
        assert stats["collection_name"] == "project_999"
        assert stats["project_id"] == 999
        assert "cache_hit_rate" in stats
        print(f"  ✅ Total chunks: {stats['total_chunks']}")
        print(f"  ✅ Collection: {stats['collection_name']}")
        print(f"  ✅ Cache hit rate: {stats.get('cache_hit_rate', 0):.2%}")

        # Step 7: Delete documents
        print("\n🗑️  Step 7: Cleaning up documents...")
        for doc_data in TEST_DOCUMENTS:
            success = await kb_service.delete_by_source(doc_data["filename"])
            assert success, f"Should delete {doc_data['filename']}"
            print(f"  ✅ Deleted {doc_data['filename']}")

        # Step 8: Verify deletion
        print("\n✅ Step 8: Verifying deletion...")
        post_delete_results = await kb_service.query(
            question="machine learning",
            mode="vector",
            k=5
        )

        # Should have no or very few results now
        assert len(post_delete_results) == 0 or all(
            r["source"] not in [d["filename"] for d in TEST_DOCUMENTS]
            for r in post_delete_results
        ), "Deleted documents should not appear in results"
        print("  ✅ Deletion verified")

        print("\n🎉 E2E Test PASSED!")

    async def test_performance_baseline(self, kb_service, cleanup_test_data):
        """Test: Query performance and caching"""

        # Upload one document for testing
        await kb_service.add_document(
            content=TEST_DOCUMENTS[0]["content"],
            metadata={
                "source": "perf_test.txt",
                "category": "test",
                "title": "Performance Test"
            }
        )

        # First query (cache miss)
        start = time.time()
        results1 = await kb_service.query(
            question="machine learning algorithms",
            mode="hybrid",
            k=3
        )
        first_query_time = (time.time() - start) * 1000  # ms

        # Second identical query (should be cached)
        start = time.time()
        results2 = await kb_service.query(
            question="machine learning algorithms",
            mode="hybrid",
            k=3
        )
        cached_query_time = (time.time() - start) * 1000  # ms

        print(f"\n⏱️  Performance Results:")
        print(f"  First query (cache miss): {first_query_time:.2f}ms")
        print(f"  Cached query: {cached_query_time:.2f}ms")
        print(f"  Speedup: {first_query_time/cached_query_time:.1f}x")

        # Performance assertions
        assert first_query_time < 2000, f"First query should be < 2s, got {first_query_time:.0f}ms"
        assert cached_query_time < first_query_time, "Cached query should be faster"

        # Results should be identical
        assert len(results1) == len(results2)
        assert results1[0]["content"] == results2[0]["content"]

        # Cleanup
        await kb_service.delete_by_source("perf_test.txt")

    async def test_concurrent_queries(self, kb_service, cleanup_test_data):
        """Test: Concurrent query handling"""

        # Upload test document
        await kb_service.add_document(
            content=TEST_DOCUMENTS[2]["content"],
            metadata={
                "source": "concurrent_test.txt",
                "category": "test",
                "title": "Concurrent Test"
            }
        )

        # Run 10 concurrent queries
        queries = [
            "KnowledgeBeast features",
            "vector search performance",
            "caching mechanism",
            "circuit breaker pattern",
            "embedding models",
        ] * 2  # 10 queries total

        start = time.time()
        results = await asyncio.gather(*[
            kb_service.query(q, mode="vector", k=3)
            for q in queries
        ])
        total_time = (time.time() - start) * 1000

        print(f"\n🚀 Concurrent Query Results:")
        print(f"  Total queries: {len(queries)}")
        print(f"  Total time: {total_time:.2f}ms")
        print(f"  Avg per query: {total_time/len(queries):.2f}ms")

        # All queries should succeed
        assert all(len(r) > 0 for r in results), "All queries should return results"
        assert total_time < 5000, f"10 concurrent queries should complete < 5s, got {total_time:.0f}ms"

        # Cleanup
        await kb_service.delete_by_source("concurrent_test.txt")

    async def test_search_mode_comparison(self, kb_service, cleanup_test_data):
        """Test: Compare all search modes"""

        # Upload document
        await kb_service.add_document(
            content="Vector embeddings enable semantic similarity search in AI systems.",
            metadata={
                "source": "mode_test.txt",
                "category": "test",
                "title": "Mode Comparison"
            }
        )

        query = "semantic search AI"

        # Test all modes
        vector_results = await kb_service.query(query, mode="vector", k=3)
        keyword_results = await kb_service.query(query, mode="keyword", k=3)
        hybrid_results = await kb_service.query(query, mode="hybrid", alpha=0.7, k=3)

        print(f"\n🔬 Search Mode Comparison for: '{query}'")
        print(f"  Vector results: {len(vector_results)}, top score: {vector_results[0]['score']:.3f if vector_results else 0}")
        print(f"  Keyword results: {len(keyword_results)}, top score: {keyword_results[0]['score']:.3f if keyword_results else 0}")
        print(f"  Hybrid results: {len(hybrid_results)}, top score: {hybrid_results[0]['score']:.3f if hybrid_results else 0}")

        # All modes should work
        assert len(vector_results) > 0, "Vector mode should return results"
        assert len(keyword_results) > 0, "Keyword mode should return results"
        assert len(hybrid_results) > 0, "Hybrid mode should return results"

        # Cleanup
        await kb_service.delete_by_source("mode_test.txt")


@pytest.mark.asyncio
@pytest.mark.e2e
class TestKnowledgeAPIE2E:
    """E2E tests via HTTP API"""

    async def test_api_query_with_modes(self, async_client: AsyncClient):
        """Test: Query API with different search modes"""

        # Test vector mode
        response = await async_client.post(
            "/api/v1/knowledge/query",
            json={"query": "test query", "limit": 3},
            params={"mode": "vector", "alpha": 1.0}
        )
        assert response.status_code == 200

        # Test keyword mode
        response = await async_client.post(
            "/api/v1/knowledge/query",
            json={"query": "test query", "limit": 3},
            params={"mode": "keyword", "alpha": 0.0}
        )
        assert response.status_code == 200

        # Test hybrid mode (default)
        response = await async_client.post(
            "/api/v1/knowledge/query",
            json={"query": "test query", "limit": 3},
            params={"mode": "hybrid", "alpha": 0.7}
        )
        assert response.status_code == 200

        print("  ✅ All API modes functional")

    async def test_api_backward_compatibility(self, async_client: AsyncClient):
        """Test: API works without mode/alpha parameters"""

        # Query without new parameters (backward compatible)
        response = await async_client.post(
            "/api/v1/knowledge/query",
            json={"query": "test", "limit": 5}
        )

        assert response.status_code == 200
        results = response.json()
        assert isinstance(results, list)

        print("  ✅ Backward compatibility confirmed")
