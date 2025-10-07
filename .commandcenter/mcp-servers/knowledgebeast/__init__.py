"""
KnowledgeBeast MCP Server

Model Context Protocol server for RAG-powered knowledge base management
with per-project isolation.
"""

from .server import KnowledgeBeastMCP, main
from .config import KnowledgeBeastConfig, get_config, get_collection_name

__all__ = [
    "KnowledgeBeastMCP",
    "main",
    "KnowledgeBeastConfig",
    "get_config",
    "get_collection_name",
]
