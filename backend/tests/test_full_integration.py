"""Full integration verification test."""
import pytest


def test_all_dependencies_available():
    """Verify all required dependencies are installed."""
    # KnowledgeBeast
    from knowledgebeast.backends.postgres import PostgresBackend

    # Dagger
    import dagger

    # LangChain (still used for chunking)
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    # Standard libraries
    import asyncpg

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

    assert hasattr(settings, 'EMBEDDING_MODEL')
    assert hasattr(settings, 'EMBEDDING_DIMENSION')
    assert hasattr(settings, 'KNOWLEDGE_COLLECTION_PREFIX')
    assert hasattr(settings, 'KB_POOL_MAX_SIZE')


def test_rag_service_imports():
    """Verify RAGService can be imported and instantiated."""
    from app.services.rag_service import RAGService

    service = RAGService(repository_id=1)
    assert service is not None
    assert service.collection_name == "commandcenter_1"


def test_dagger_module_imports():
    """Verify Dagger module can be imported."""
    import sys
    from pathlib import Path

    sys.path.insert(0, str(Path(__file__).parent.parent))

    from dagger_modules.postgres import PostgresStack, PostgresConfig

    config = PostgresConfig()
    stack = PostgresStack(config)

    assert config is not None
    assert stack is not None


@pytest.mark.asyncio
async def test_rag_service_lifecycle():
    """Test RAGService initialization and cleanup."""
    from app.services.rag_service import RAGService
    from unittest.mock import AsyncMock

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


def test_backward_compatibility():
    """Verify API surface matches old RAGService."""
    from app.services.rag_service import RAGService
    import inspect

    service = RAGService(repository_id=1)

    # Check required methods exist
    assert hasattr(service, 'query')
    assert hasattr(service, 'add_document')
    assert hasattr(service, 'delete_by_source')
    assert hasattr(service, 'get_statistics')
    assert hasattr(service, 'initialize')
    assert hasattr(service, 'close')

    # Check methods are async
    assert inspect.iscoroutinefunction(service.query)
    assert inspect.iscoroutinefunction(service.add_document)
    assert inspect.iscoroutinefunction(service.delete_by_source)
    assert inspect.iscoroutinefunction(service.get_statistics)
