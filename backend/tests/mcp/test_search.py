"""
Tests for Semantic Search

Tests for KnowledgeBeast semantic search functionality.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import AsyncMock

# Add paths
worktree_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(worktree_root))
sys.path.insert(0, str(worktree_root / "backend"))
sys.path.insert(0, str(worktree_root / ".commandcenter/mcp-servers"))

from knowledgebeast.tools.search import SemanticSearch


@pytest.mark.asyncio
class TestSemanticSearch:
    """Test semantic search tools"""

    @pytest.fixture
    def mock_rag_service(self):
        """Mock RAG service"""
        mock = AsyncMock()
        mock.collection_name = "project_test"
        mock.query = AsyncMock()
        mock.get_categories = AsyncMock()
        mock.vectorstore = AsyncMock()
        return mock

    @pytest.fixture
    def search_tool(self, mock_rag_service):
        """Create SemanticSearch instance"""
        return SemanticSearch(mock_rag_service)

    async def test_basic_search(self, search_tool, mock_rag_service):
        """Test basic semantic search"""
        mock_rag_service.query.return_value = [
            {
                "content": "Test result",
                "metadata": {"title": "Test"},
                "score": 0.95,
                "category": "test",
                "source": "test.md"
            }
        ]

        result = await search_tool.search("test query", k=5)

        assert result["query"] == "test query"
        assert result["total_results"] == 1
        assert len(result["results"]) == 1
        assert result["results"][0]["score"] == 0.95

    async def test_search_with_category_filter(self, search_tool, mock_rag_service):
        """Test search with category filtering"""
        mock_rag_service.query.return_value = [
            {
                "content": "Documentation result",
                "metadata": {},
                "score": 0.92,
                "category": "docs",
                "source": "docs.md"
            }
        ]

        result = await search_tool.search("query", category="docs", k=5)

        assert result["category"] == "docs"
        assert result["total_results"] == 1
        mock_rag_service.query.assert_called_once_with(
            question="query",
            category="docs",
            k=5
        )

    async def test_search_with_min_score(self, search_tool, mock_rag_service):
        """Test search with minimum score threshold"""
        mock_rag_service.query.return_value = [
            {"content": "High score", "score": 0.95, "category": "test", "source": "a.md", "metadata": {}},
            {"content": "Medium score", "score": 0.75, "category": "test", "source": "b.md", "metadata": {}},
            {"content": "Low score", "score": 0.45, "category": "test", "source": "c.md", "metadata": {}},
        ]

        result = await search_tool.search("query", k=10, min_score=0.70)

        assert result["total_results"] == 2
        assert all(r["score"] >= 0.70 for r in result["results"])

    async def test_multi_query_search(self, search_tool, mock_rag_service):
        """Test multi-query search"""
        mock_rag_service.query.return_value = [
            {"content": "Result", "score": 0.9, "category": "test", "source": "test.md", "metadata": {}}
        ]

        queries = ["query 1", "query 2", "query 3"]
        result = await search_tool.multi_query_search(queries, k=5, aggregate=False)

        assert len(result["results_by_query"]) == 3
        assert result["queries"] == queries

    async def test_multi_query_search_aggregated(self, search_tool, mock_rag_service):
        """Test multi-query search with aggregation"""
        # Different results for different queries
        results_map = {
            "query 1": [
                {"content": "Result A", "score": 0.95, "category": "test", "source": "a.md", "metadata": {}}
            ],
            "query 2": [
                {"content": "Result B", "score": 0.92, "category": "test", "source": "b.md", "metadata": {}},
                {"content": "Result A", "score": 0.90, "category": "test", "source": "a.md", "metadata": {}}  # Duplicate
            ],
            "query 3": [
                {"content": "Result C", "score": 0.88, "category": "test", "source": "c.md", "metadata": {}}
            ]
        }

        async def mock_query(question, category, k):
            return results_map.get(question, [])

        mock_rag_service.query.side_effect = mock_query

        queries = ["query 1", "query 2", "query 3"]
        result = await search_tool.multi_query_search(queries, k=5, aggregate=True)

        # Should deduplicate Result A
        assert result["total_unique_results"] <= 3

    async def test_search_by_category(self, search_tool, mock_rag_service):
        """Test searching across categories"""
        mock_rag_service.get_categories.return_value = ["docs", "code", "test"]

        # Different results for different categories
        async def mock_query(question, category, k):
            if category == "docs":
                return [{"content": "Doc result", "score": 0.95, "category": "docs", "source": "d.md", "metadata": {}}]
            elif category == "code":
                return [{"content": "Code result", "score": 0.88, "category": "code", "source": "c.py", "metadata": {}}]
            else:
                return []

        mock_rag_service.query.side_effect = mock_query

        result = await search_tool.search_by_category("test query", k_per_category=3)

        assert result["categories_searched"] == 3
        assert result["categories_with_results"] == 2
        assert "docs" in result["results_by_category"]
        assert "code" in result["results_by_category"]

    async def test_find_similar_documents(self, search_tool, mock_rag_service):
        """Test finding similar documents"""
        # Mock getting reference document
        mock_rag_service.vectorstore.get.return_value = {
            "documents": ["Reference document content"],
            "ids": ["ref_1"],
            "metadatas": [{"source": "ref.md"}]
        }

        # Mock search results
        mock_rag_service.query.return_value = [
            {"content": "Ref doc", "score": 1.0, "category": "test", "source": "ref.md", "metadata": {}},  # Should be filtered
            {"content": "Similar doc 1", "score": 0.92, "category": "test", "source": "sim1.md", "metadata": {}},
            {"content": "Similar doc 2", "score": 0.88, "category": "test", "source": "sim2.md", "metadata": {}},
        ]

        result = await search_tool.find_similar_documents("ref.md", k=5)

        assert result["reference_source"] == "ref.md"
        # Should not include the reference document itself
        assert all(r["source"] != "ref.md" for r in result["results"])

    async def test_find_similar_documents_not_found(self, search_tool, mock_rag_service):
        """Test finding similar documents when source doesn't exist"""
        mock_rag_service.vectorstore.get.return_value = {
            "documents": [],
            "ids": []
        }

        result = await search_tool.find_similar_documents("nonexistent.md", k=5)

        assert "error" in result
        assert result["results"] == []

    async def test_context_search(self, search_tool, mock_rag_service):
        """Test context-aware search"""
        mock_rag_service.query.return_value = [
            {"content": "Result", "score": 0.95, "category": "test", "source": "test.md", "metadata": {}}
        ]

        result = await search_tool.context_search("query", context_window=3, k=5)

        assert result["context_window"] == 3
        assert result["total_results"] == 1
        # Verify context note is added
        assert "context_note" in result["results"][0]

    async def test_empty_search_results(self, search_tool, mock_rag_service):
        """Test handling empty search results"""
        mock_rag_service.query.return_value = []

        result = await search_tool.search("nonexistent query", k=5)

        assert result["total_results"] == 0
        assert result["results"] == []

    async def test_search_score_ordering(self, search_tool, mock_rag_service):
        """Test that results are ordered by score"""
        mock_rag_service.query.return_value = [
            {"content": "Low", "score": 0.65, "category": "test", "source": "a.md", "metadata": {}},
            {"content": "High", "score": 0.95, "category": "test", "source": "b.md", "metadata": {}},
            {"content": "Med", "score": 0.80, "category": "test", "source": "c.md", "metadata": {}},
        ]

        result = await search_tool.search("query", k=10)

        # Results should maintain order from RAG service
        scores = [r["score"] for r in result["results"]]
        assert scores == [0.65, 0.95, 0.80]

    async def test_large_k_value(self, search_tool, mock_rag_service):
        """Test search with large k value"""
        # Generate many results
        many_results = [
            {
                "content": f"Result {i}",
                "score": 0.9 - (i * 0.01),
                "category": "test",
                "source": f"doc{i}.md",
                "metadata": {}
            }
            for i in range(50)
        ]

        mock_rag_service.query.return_value = many_results

        result = await search_tool.search("query", k=50)

        assert result["total_results"] == 50
        assert len(result["results"]) == 50


class TestSearchEdgeCases:
    """Test edge cases for search functionality"""

    @pytest.mark.asyncio
    async def test_search_with_special_characters(self):
        """Test search with special characters in query"""
        mock_rag = AsyncMock()
        mock_rag.collection_name = "project_test"
        mock_rag.query.return_value = []

        search = SemanticSearch(mock_rag)

        # Should not crash with special characters
        result = await search.search("query with @#$% special chars!")

        assert result["query"] == "query with @#$% special chars!"
        mock_rag.query.assert_called_once()

    @pytest.mark.asyncio
    async def test_search_with_unicode(self):
        """Test search with unicode characters"""
        mock_rag = AsyncMock()
        mock_rag.collection_name = "project_test"
        mock_rag.query.return_value = []

        search = SemanticSearch(mock_rag)

        # Should handle unicode
        result = await search.search("测试 unicode 🚀")

        assert result["query"] == "测试 unicode 🚀"

    @pytest.mark.asyncio
    async def test_search_with_empty_query(self):
        """Test search with empty query"""
        mock_rag = AsyncMock()
        mock_rag.collection_name = "project_test"
        mock_rag.query.return_value = []

        search = SemanticSearch(mock_rag)

        # Should handle empty query
        result = await search.search("", k=5)

        assert result["query"] == ""
        assert result["total_results"] == 0
