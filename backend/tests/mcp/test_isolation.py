"""
Tests for Per-Project Isolation

Integration tests to verify that per-project collection isolation works correctly.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

# Add paths
worktree_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(worktree_root))
sys.path.insert(0, str(worktree_root / "backend"))
sys.path.insert(0, str(worktree_root / ".commandcenter/mcp-servers"))

from knowledgebeast.config import get_collection_name


@pytest.mark.asyncio
class TestProjectIsolation:
    """Test per-project collection isolation"""

    def test_different_projects_get_different_collections(self):
        """Verify different projects get unique collection names"""
        project_a = "projectA"
        project_b = "projectB"

        collection_a = get_collection_name(project_a)
        collection_b = get_collection_name(project_b)

        assert collection_a != collection_b
        assert collection_a == "project_projectA"
        assert collection_b == "project_projectB"

    def test_same_project_gets_same_collection(self):
        """Verify same project always gets same collection name"""
        project_id = "myproject"

        collection_1 = get_collection_name(project_id)
        collection_2 = get_collection_name(project_id)

        assert collection_1 == collection_2
        assert collection_1 == "project_myproject"

    @pytest.mark.asyncio
    async def test_isolated_document_ingestion(self):
        """Test that documents from different projects are isolated"""
        with patch("knowledgebeast.server.RAGService") as MockRAGService:
            from knowledgebeast.server import KnowledgeBeastMCP

            # Create two servers for different projects
            mock_rag_a = AsyncMock()
            mock_rag_a.collection_name = "project_projectA"
            mock_rag_a.add_document.return_value = 3

            mock_rag_b = AsyncMock()
            mock_rag_b.collection_name = "project_projectB"
            mock_rag_b.add_document.return_value = 5

            MockRAGService.side_effect = [mock_rag_a, mock_rag_b]

            server_a = KnowledgeBeastMCP(project_id="projectA")
            server_b = KnowledgeBeastMCP(project_id="projectB")

            # Verify different collections
            assert server_a.collection_name != server_b.collection_name
            assert server_a.collection_name == "project_projectA"
            assert server_b.collection_name == "project_projectB"

    @pytest.mark.asyncio
    async def test_isolated_search(self):
        """Test that search only returns results from same project"""
        with patch("knowledgebeast.server.RAGService") as MockRAGService:
            from knowledgebeast.server import KnowledgeBeastMCP

            # Create mock services for two projects
            mock_rag_a = AsyncMock()
            mock_rag_a.collection_name = "project_projectA"
            mock_rag_a.query.return_value = [
                {
                    "content": "Project A content",
                    "source": "projectA/doc.md",
                    "category": "docs",
                    "score": 0.95
                }
            ]

            mock_rag_b = AsyncMock()
            mock_rag_b.collection_name = "project_projectB"
            mock_rag_b.query.return_value = [
                {
                    "content": "Project B content",
                    "source": "projectB/doc.md",
                    "category": "docs",
                    "score": 0.92
                }
            ]

            MockRAGService.side_effect = [mock_rag_a, mock_rag_b]

            server_a = KnowledgeBeastMCP(project_id="projectA")
            server_b = KnowledgeBeastMCP(project_id="projectB")

            # Search in project A
            result_a = await server_a._search_knowledge({"query": "test", "k": 5})
            assert "Project A content" in result_a[0].text

            # Search in project B
            result_b = await server_b._search_knowledge({"query": "test", "k": 5})
            assert "Project B content" in result_b[0].text

    @pytest.mark.asyncio
    async def test_collection_metadata_isolation(self):
        """Test that collection metadata is properly isolated"""
        with patch("knowledgebeast.server.RAGService") as MockRAGService:
            from knowledgebeast.server import KnowledgeBeastMCP

            # Mock RAG services
            mock_rag_a = AsyncMock()
            mock_rag_a.collection_name = "project_projectA"
            mock_rag_a.get_statistics.return_value = {
                "total_chunks": 100,
                "collection_name": "project_projectA"
            }

            mock_rag_b = AsyncMock()
            mock_rag_b.collection_name = "project_projectB"
            mock_rag_b.get_statistics.return_value = {
                "total_chunks": 50,
                "collection_name": "project_projectB"
            }

            MockRAGService.side_effect = [mock_rag_a, mock_rag_b]

            server_a = KnowledgeBeastMCP(project_id="projectA")
            server_b = KnowledgeBeastMCP(project_id="projectB")

            # Verify isolation
            isolation_a = await server_a.ensure_isolated()
            isolation_b = await server_b.ensure_isolated()

            assert isolation_a["project_id"] == "projectA"
            assert isolation_b["project_id"] == "projectB"
            assert isolation_a["collection_name"] != isolation_b["collection_name"]
            assert isolation_a["total_chunks"] == 100
            assert isolation_b["total_chunks"] == 50

    def test_collection_name_prefix(self):
        """Test that all collections have proper prefix"""
        project_ids = ["project1", "project2", "my-app", "TestApp"]

        for project_id in project_ids:
            collection_name = get_collection_name(project_id)
            assert collection_name.startswith("project_")

    @pytest.mark.asyncio
    async def test_no_cross_project_deletion(self):
        """Test that deletion only affects same project"""
        with patch("knowledgebeast.server.RAGService") as MockRAGService:
            from knowledgebeast.server import KnowledgeBeastMCP

            # Mock RAG services
            mock_rag_a = AsyncMock()
            mock_rag_a.collection_name = "project_projectA"
            mock_rag_a.delete_by_source.return_value = True

            mock_rag_b = AsyncMock()
            mock_rag_b.collection_name = "project_projectB"
            mock_rag_b.delete_by_source.return_value = False

            MockRAGService.side_effect = [mock_rag_a, mock_rag_b]

            server_a = KnowledgeBeastMCP(project_id="projectA")
            server_b = KnowledgeBeastMCP(project_id="projectB")

            # Delete from project A
            await server_a._delete_document({"source": "test.md"})

            # Verify only project A's delete was called
            mock_rag_a.delete_by_source.assert_called_once()
            mock_rag_b.delete_by_source.assert_not_called()


class TestCollectionNaming:
    """Test collection naming strategy"""

    def test_alphanumeric_preservation(self):
        """Test that alphanumeric characters are preserved"""
        assert get_collection_name("abc123") == "project_abc123"
        assert get_collection_name("MyApp2024") == "project_MyApp2024"

    def test_dash_underscore_preservation(self):
        """Test that dashes and underscores are preserved"""
        assert get_collection_name("my-app") == "project_my-app"
        assert get_collection_name("my_app") == "project_my_app"
        assert get_collection_name("my-app_v2") == "project_my-app_v2"

    def test_special_character_sanitization(self):
        """Test that special characters are sanitized"""
        assert get_collection_name("my app") == "project_my_app"
        assert get_collection_name("my@app") == "project_my_app"
        assert get_collection_name("my.app") == "project_my_app"
        assert get_collection_name("my!app?") == "project_my_app_"

    def test_unicode_sanitization(self):
        """Test that unicode characters are sanitized"""
        assert get_collection_name("app-émoji") == "project_app-_moji"
        assert get_collection_name("测试") == "project____"

    def test_empty_and_edge_cases(self):
        """Test edge cases for collection naming"""
        # Empty string
        assert get_collection_name("") == "project_"

        # Only special characters
        assert get_collection_name("!!!") == "project____"

        # Very long name (should not truncate)
        long_name = "a" * 100
        assert get_collection_name(long_name) == f"project_{long_name}"
