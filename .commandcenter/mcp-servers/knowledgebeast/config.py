"""
KnowledgeBeast MCP Server Configuration

This module provides configuration for the KnowledgeBeast MCP server,
including per-project isolation settings and RAG configuration.
"""

import os
from pathlib import Path
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class KnowledgeBeastConfig(BaseSettings):
    """Configuration for KnowledgeBeast MCP server"""

    # Project identification
    project_id: str = Field(
        default="default",
        description="Unique project identifier for collection isolation"
    )

    # ChromaDB configuration
    db_path: str = Field(
        default="./rag_storage",
        description="Path to ChromaDB storage directory"
    )

    # Embedding model configuration
    embedding_model: str = Field(
        default="sentence-transformers/all-MiniLM-L6-v2",
        description="HuggingFace embedding model name"
    )

    # Document processing configuration
    chunk_size: int = Field(
        default=1000,
        description="Default chunk size for document splitting"
    )
    chunk_overlap: int = Field(
        default=200,
        description="Overlap between chunks"
    )

    # Search configuration
    default_k: int = Field(
        default=5,
        description="Default number of search results"
    )

    # Supported file extensions
    supported_extensions: list[str] = Field(
        default=[".md", ".txt", ".pdf", ".docx", ".py", ".js", ".ts", ".json", ".yaml", ".yml"],
        description="Supported document file extensions"
    )

    # Documentation sources
    doc_sources_config: str = Field(
        default=".commandcenter/knowledge/sources.json",
        description="Path to documentation sources configuration"
    )

    class Config:
        env_prefix = "KNOWLEDGEBEAST_"
        case_sensitive = False


def get_collection_name(project_id: str) -> str:
    """
    Generate collection name with per-project isolation

    Args:
        project_id: Unique project identifier

    Returns:
        Collection name with project isolation (e.g., "project_myapp")
    """
    # Sanitize project_id to ensure it's a valid collection name
    sanitized_id = "".join(c if c.isalnum() or c in ("_", "-") else "_" for c in project_id)
    return f"project_{sanitized_id}"


def get_config(project_id: Optional[str] = None) -> KnowledgeBeastConfig:
    """
    Get KnowledgeBeast configuration with optional project override

    Args:
        project_id: Optional project ID override

    Returns:
        Configuration instance
    """
    config = KnowledgeBeastConfig()
    if project_id:
        config.project_id = project_id
    return config
