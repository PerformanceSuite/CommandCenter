"""
Tests for KnowledgeBeast MCP Server

Unit tests for the KnowledgeBeast MCP server core functionality.
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

from knowledgebeast.config import get_collection_name, get_config, KnowledgeBeastConfig


class TestKnowledgeBeastConfig:
    """Test KnowledgeBeast configuration"""

    def test_get_collection_name(self):
        """Test collection name generation"""
        # Test normal project ID
        assert get_collection_name("myproject") == "project_myproject"

        # Test sanitization
        assert get_collection_name("my-project") == "project_my-project"
        assert get_collection_name("my_project") == "project_my_project"

        # Test special characters (should be sanitized)
        assert get_collection_name("my project!") == "project_my_project_"

    def test_get_config(self):
        """Test config retrieval"""
        config = get_config()
        assert isinstance(config, KnowledgeBeastConfig)
        assert config.project_id == "default"

        # Test with custom project ID
        config = get_config("testproject")
        assert config.project_id == "testproject"

    def test_config_defaults(self):
        """Test default configuration values"""
        config = KnowledgeBeastConfig()

        assert config.project_id == "default"
        assert config.chunk_size == 1000
        assert config.chunk_overlap == 200
        assert config.default_k == 5
        assert "sentence-transformers" in config.embedding_model


@pytest.mark.asyncio
class TestKnowledgeBeastMCP:
    """Test KnowledgeBeast MCP server"""

    @pytest.fixture
    def mock_rag_service(self):
        """Mock RAG service"""
        mock = AsyncMock()
        mock.collection_name = "project_test"
        mock.db_path = "./test_rag_storage"
        mock.embedding_model_name = "sentence-transformers/all-MiniLM-L6-v2"
        mock.vectorstore = Mock()
        return mock

    @pytest.fixture
    def mcp_server(self, mock_rag_service):
        """Create test MCP server"""
        with patch("knowledgebeast.server.RAGService", return_value=mock_rag_service):
            from knowledgebeast.server import KnowledgeBeastMCP
            server = KnowledgeBeastMCP(project_id="test")
            return server

    async def test_server_initialization(self, mcp_server):
        """Test server initializes correctly"""
        assert mcp_server.project_id == "test"
        assert mcp_server.collection_name == "project_test"
        assert mcp_server.server is not None

    async def test_ingest_document(self, mcp_server, mock_rag_service):
        """Test document ingestion"""
        mock_rag_service.add_document.return_value = 5

        arguments = {
            "content": "Test document content",
            "metadata": {
                "source": "test.md",
                "category": "test"
            },
            "chunk_size": 1000
        }

        result = await mcp_server._ingest_document(arguments)

        assert len(result) == 1
        assert "Successfully ingested" in result[0].text
        assert "5 chunks" in result[0].text
        mock_rag_service.add_document.assert_called_once()

    async def test_search_knowledge(self, mcp_server, mock_rag_service):
        """Test semantic search"""
        mock_rag_service.query.return_value = [
            {
                "content": "Test result",
                "metadata": {},
                "score": 0.95,
                "category": "test",
                "source": "test.md"
            }
        ]

        arguments = {
            "query": "test query",
            "k": 5
        }

        result = await mcp_server._search_knowledge(arguments)

        assert len(result) == 1
        assert "Found 1 results" in result[0].text
        assert "test query" in result[0].text
        mock_rag_service.query.assert_called_once()

    async def test_search_no_results(self, mcp_server, mock_rag_service):
        """Test search with no results"""
        mock_rag_service.query.return_value = []

        arguments = {
            "query": "nonexistent query",
            "k": 5
        }

        result = await mcp_server._search_knowledge(arguments)

        assert len(result) == 1
        assert "No results found" in result[0].text

    async def test_get_statistics(self, mcp_server, mock_rag_service):
        """Test statistics retrieval"""
        mock_rag_service.get_statistics.return_value = {
            "total_chunks": 100,
            "categories": {"test": 50, "docs": 50},
            "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
            "db_path": "./test_rag_storage",
            "collection_name": "project_test"
        }

        result = await mcp_server._get_statistics({})

        assert len(result) == 1
        text = result[0].text
        assert "Total Chunks: 100" in text
        assert "project_test" in text
        assert "test: 50" in text

    async def test_delete_document(self, mcp_server, mock_rag_service):
        """Test document deletion"""
        mock_rag_service.delete_by_source.return_value = True

        arguments = {"source": "test.md"}
        result = await mcp_server._delete_document(arguments)

        assert len(result) == 1
        assert "Successfully deleted" in result[0].text
        mock_rag_service.delete_by_source.assert_called_once_with("test.md")

    async def test_update_document(self, mcp_server, mock_rag_service):
        """Test document update"""
        mock_rag_service.delete_by_source.return_value = True
        mock_rag_service.add_document.return_value = 3

        arguments = {
            "source": "test.md",
            "content": "Updated content",
            "metadata": {"category": "updated"}
        }

        result = await mcp_server._update_document(arguments)

        assert len(result) == 1
        assert "Successfully updated" in result[0].text
        assert "3 chunks" in result[0].text

    async def test_list_documents(self, mcp_server, mock_rag_service):
        """Test listing documents"""
        mock_rag_service.vectorstore.get.return_value = {
            "ids": ["1", "2", "3"],
            "metadatas": [
                {"source": "test1.md", "category": "test"},
                {"source": "test1.md", "category": "test"},
                {"source": "test2.md", "category": "docs"}
            ]
        }

        result = await mcp_server._list_documents({})

        assert len(result) == 1
        text = result[0].text
        assert "test1.md" in text
        assert "test2.md" in text

    async def test_ensure_isolated(self, mcp_server, mock_rag_service):
        """Test isolation verification"""
        mock_rag_service.get_statistics.return_value = {
            "total_chunks": 50
        }

        result = await mcp_server.ensure_isolated()

        assert result["project_id"] == "test"
        assert result["collection_name"] == "project_test"
        assert result["isolated"] is True
        assert result["total_chunks"] == 50


def test_collection_name_sanitization():
    """Test collection name sanitization"""
    # Test various special characters
    test_cases = [
        ("simple", "project_simple"),
        ("with-dash", "project_with-dash"),
        ("with_underscore", "project_with_underscore"),
        ("with spaces", "project_with_spaces"),
        ("with@special!", "project_with_special_"),
        ("CamelCase", "project_CamelCase"),
        ("123numeric", "project_123numeric")
    ]

    for input_name, expected_output in test_cases:
        assert get_collection_name(input_name) == expected_output
