"""Test configuration settings."""
from app.config import settings


def test_embedding_model_config():
    """Test embedding model configuration."""
    assert hasattr(settings, "EMBEDDING_MODEL")
    assert settings.EMBEDDING_MODEL == "all-MiniLM-L6-v2"


def test_embedding_dimension_config():
    """Test embedding dimension configuration."""
    assert hasattr(settings, "EMBEDDING_DIMENSION")
    assert settings.EMBEDDING_DIMENSION == 384


def test_knowledge_collection_prefix():
    """Test knowledge collection prefix."""
    assert hasattr(settings, "KNOWLEDGE_COLLECTION_PREFIX")
    assert settings.KNOWLEDGE_COLLECTION_PREFIX == "commandcenter"


def test_kb_pool_config():
    """Test KnowledgeBeast connection pool configuration."""
    assert hasattr(settings, "KB_POOL_MIN_SIZE")
    assert hasattr(settings, "KB_POOL_MAX_SIZE")
    assert settings.KB_POOL_MIN_SIZE == 2
    assert settings.KB_POOL_MAX_SIZE == 10
