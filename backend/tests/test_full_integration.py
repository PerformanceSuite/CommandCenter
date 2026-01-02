"""Full integration verification test.

These tests verify that all dependencies are properly configured.
Tests are skipped when optional dependencies are not available.
"""
import pytest


def _knowledgebeast_available():
    """Check if KnowledgeBeast is available."""
    try:
        from knowledgebeast.backends.postgres import PostgresBackend  # noqa: F401

        return True
    except ImportError:
        return False


def _dagger_available():
    """Check if Dagger is available."""
    try:
        import dagger  # noqa: F401

        return True
    except ImportError:
        return False


def _sentence_transformers_available():
    """Check if sentence-transformers is available."""
    try:
        from sentence_transformers import SentenceTransformer  # noqa: F401

        return True
    except ImportError:
        return False


def _rag_service_available():
    """Check if RAGService can be imported."""
    try:
        from app.services.rag_service import RAGService  # noqa: F401

        return True
    except ImportError:
        return False


@pytest.mark.skipif(
    not (
        _knowledgebeast_available() and _dagger_available() and _sentence_transformers_available()
    ),
    reason="Optional dependencies (KnowledgeBeast, Dagger, sentence-transformers) not available",
)
def test_all_dependencies_available():
    """Verify all optional dependencies are installed when test runs."""
    # Standard libraries
    import asyncpg

    # Dagger
    import dagger
    from knowledgebeast.backends.postgres import PostgresBackend

    # LangChain (still used for chunking)
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    # Sentence transformers
    from sentence_transformers import SentenceTransformer

    assert PostgresBackend is not None
    assert dagger is not None
    assert RecursiveCharacterTextSplitter is not None
    assert asyncpg is not None
    assert SentenceTransformer is not None


def test_config_has_kb_settings():
    """Verify configuration has KnowledgeBeast settings."""
    from app.config import settings

    assert hasattr(settings, "EMBEDDING_MODEL")
    assert hasattr(settings, "EMBEDDING_DIMENSION")
    assert hasattr(settings, "KNOWLEDGE_COLLECTION_PREFIX")
    assert hasattr(settings, "KB_POOL_MAX_SIZE")


@pytest.mark.skipif(
    not _rag_service_available(),
    reason="RAGService not available (missing dependencies)",
)
def test_rag_service_imports():
    """Verify RAGService can be imported and instantiated."""
    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)
    assert service is not None
    assert service.collection_name == "commandcenter_1"


@pytest.mark.skipif(not _dagger_available(), reason="Dagger not installed")
def test_dagger_module_imports():
    """Verify Dagger module can be imported."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))

    from dagger_modules.postgres import PostgresConfig, PostgresStack

    config = PostgresConfig()
    stack = PostgresStack(config)

    assert config is not None
    assert stack is not None


@pytest.mark.asyncio
@pytest.mark.skipif(
    not _rag_service_available(),
    reason="RAGService not available (missing dependencies)",
)
async def test_rag_service_lifecycle():
    """Test RAGService initialization and cleanup."""
    from unittest.mock import AsyncMock

    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)

    # Mock backend
    service.backend.initialize = AsyncMock()
    service.backend.close = AsyncMock()

    # Initialize
    await service.initialize()
    assert service._initialized
    service.backend.initialize.assert_called_once()

    # Close
    await service.close()
    assert not service._initialized
    service.backend.close.assert_called_once()


@pytest.mark.skipif(
    not _rag_service_available(),
    reason="RAGService not available (missing dependencies)",
)
def test_backward_compatibility():
    """Verify API surface matches old RAGService."""
    import inspect

    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)

    # Check required methods exist
    assert hasattr(service, "query")
    assert hasattr(service, "add_document")
    assert hasattr(service, "delete_by_source")
    assert hasattr(service, "get_statistics")
    assert hasattr(service, "initialize")
    assert hasattr(service, "close")

    # Check methods are async
    assert inspect.iscoroutinefunction(service.query)
    assert inspect.iscoroutinefunction(service.add_document)
    assert inspect.iscoroutinefunction(service.delete_by_source)
    assert inspect.iscoroutinefunction(service.get_statistics)
