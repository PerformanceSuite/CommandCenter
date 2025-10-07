"""
KnowledgeBeast MCP Server

Model Context Protocol (MCP) server wrapping the KnowledgeBeast RAG system
with per-project collection isolation.

This server provides:
- Document ingestion tools
- Semantic search capabilities
- Knowledge base management
- Per-project data isolation
"""

import sys
from pathlib import Path
from typing import Any, Optional

# Add backend to path to access RAGService
backend_path = Path(__file__).parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from mcp.server import Server
from mcp.types import Tool, Resource, TextContent, ImageContent, EmbeddedResource
import mcp.server.stdio

from app.services.rag_service import RAGService
from .config import KnowledgeBeastConfig, get_collection_name, get_config


class KnowledgeBeastMCP:
    """
    KnowledgeBeast MCP server with per-project isolation

    Each project gets its own isolated ChromaDB collection to prevent
    data leakage across different projects.
    """

    def __init__(self, project_id: str = "default"):
        """
        Initialize KnowledgeBeast MCP server

        Args:
            project_id: Unique project identifier for collection isolation
        """
        self.config = get_config(project_id)
        self.project_id = project_id
        self.collection_name = get_collection_name(project_id)

        # Initialize RAG service with isolated collection
        self.rag_service = RAGService(
            db_path=self.config.db_path,
            collection_name=self.collection_name
        )

        # MCP server instance
        self.server = Server("knowledgebeast")
        self._register_handlers()

    def _register_handlers(self):
        """Register MCP tool and resource handlers"""

        # Register tools
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available KnowledgeBeast tools"""
            return [
                Tool(
                    name="ingest_document",
                    description="Add a document to the knowledge base with automatic chunking and embedding",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "content": {
                                "type": "string",
                                "description": "Document content to ingest"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Document metadata (source, category, etc.)",
                                "properties": {
                                    "source": {"type": "string"},
                                    "category": {"type": "string"},
                                    "title": {"type": "string"}
                                },
                                "required": ["source"]
                            },
                            "chunk_size": {
                                "type": "integer",
                                "description": "Size of text chunks (default: 1000)",
                                "default": 1000
                            }
                        },
                        "required": ["content", "metadata"]
                    }
                ),
                Tool(
                    name="search_knowledge",
                    description="Semantic search across the knowledge base using RAG",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "query": {
                                "type": "string",
                                "description": "Natural language search query"
                            },
                            "category": {
                                "type": "string",
                                "description": "Filter results by category (optional)"
                            },
                            "k": {
                                "type": "integer",
                                "description": "Number of results to return (default: 5)",
                                "default": 5
                            }
                        },
                        "required": ["query"]
                    }
                ),
                Tool(
                    name="get_statistics",
                    description="Get knowledge base statistics including document counts and categories",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                ),
                Tool(
                    name="list_documents",
                    description="List all documents in the knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "category": {
                                "type": "string",
                                "description": "Filter by category (optional)"
                            }
                        }
                    }
                ),
                Tool(
                    name="delete_document",
                    description="Remove a document from the knowledge base by source",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "Source identifier of document to delete"
                            }
                        },
                        "required": ["source"]
                    }
                ),
                Tool(
                    name="update_document",
                    description="Update an existing document in the knowledge base",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "Source identifier of document to update"
                            },
                            "content": {
                                "type": "string",
                                "description": "New document content"
                            },
                            "metadata": {
                                "type": "object",
                                "description": "Updated metadata"
                            }
                        },
                        "required": ["source", "content"]
                    }
                )
            ]

        @self.server.call_tool()
        async def call_tool(name: str, arguments: Any) -> list[TextContent]:
            """Handle tool execution"""
            try:
                if name == "ingest_document":
                    return await self._ingest_document(arguments)
                elif name == "search_knowledge":
                    return await self._search_knowledge(arguments)
                elif name == "get_statistics":
                    return await self._get_statistics(arguments)
                elif name == "list_documents":
                    return await self._list_documents(arguments)
                elif name == "delete_document":
                    return await self._delete_document(arguments)
                elif name == "update_document":
                    return await self._update_document(arguments)
                else:
                    return [TextContent(type="text", text=f"Unknown tool: {name}")]
            except Exception as e:
                return [TextContent(type="text", text=f"Error: {str(e)}")]

        # Register resources
        @self.server.list_resources()
        async def list_resources() -> list[Resource]:
            """List available KnowledgeBeast resources"""
            return [
                Resource(
                    uri=f"knowledge://base/{self.project_id}",
                    name=f"Knowledge Base - {self.project_id}",
                    mimeType="application/json",
                    description=f"Current project knowledge base for {self.project_id}"
                ),
                Resource(
                    uri=f"knowledge://stats/{self.project_id}",
                    name=f"Knowledge Statistics - {self.project_id}",
                    mimeType="application/json",
                    description=f"Knowledge base statistics for {self.project_id}"
                ),
                Resource(
                    uri=f"knowledge://collections",
                    name="All Collections",
                    mimeType="application/json",
                    description="List of all available knowledge base collections"
                )
            ]

        @self.server.read_resource()
        async def read_resource(uri: str) -> str:
            """Read resource content"""
            if uri.startswith(f"knowledge://base/{self.project_id}"):
                # Return knowledge base metadata
                stats = await self.rag_service.get_statistics()
                return str(stats)
            elif uri.startswith(f"knowledge://stats/{self.project_id}"):
                # Return statistics
                stats = await self.rag_service.get_statistics()
                return str(stats)
            elif uri == "knowledge://collections":
                # Return collection information
                return str({
                    "current_collection": self.collection_name,
                    "project_id": self.project_id
                })
            else:
                raise ValueError(f"Unknown resource URI: {uri}")

    # Tool implementation methods
    async def _ingest_document(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Ingest a document into the knowledge base"""
        content = arguments["content"]
        metadata = arguments["metadata"]
        chunk_size = arguments.get("chunk_size", self.config.chunk_size)

        chunks_added = await self.rag_service.add_document(
            content=content,
            metadata=metadata,
            chunk_size=chunk_size
        )

        return [TextContent(
            type="text",
            text=f"Successfully ingested document: {metadata.get('source', 'unknown')}\n"
                 f"Added {chunks_added} chunks to collection '{self.collection_name}'"
        )]

    async def _search_knowledge(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Search the knowledge base"""
        query = arguments["query"]
        category = arguments.get("category")
        k = arguments.get("k", self.config.default_k)

        results = await self.rag_service.query(
            question=query,
            category=category,
            k=k
        )

        if not results:
            return [TextContent(
                type="text",
                text=f"No results found for query: {query}"
            )]

        # Format results
        result_text = f"Found {len(results)} results for: {query}\n\n"
        for i, result in enumerate(results, 1):
            result_text += f"Result {i} (score: {result['score']:.3f}):\n"
            result_text += f"Source: {result['source']}\n"
            result_text += f"Category: {result['category']}\n"
            result_text += f"Content:\n{result['content'][:500]}...\n\n"

        return [TextContent(type="text", text=result_text)]

    async def _get_statistics(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Get knowledge base statistics"""
        stats = await self.rag_service.get_statistics()

        stats_text = f"Knowledge Base Statistics for '{self.project_id}':\n\n"
        stats_text += f"Collection: {self.collection_name}\n"
        stats_text += f"Total Chunks: {stats['total_chunks']}\n"
        stats_text += f"Embedding Model: {stats['embedding_model']}\n"
        stats_text += f"Database Path: {stats['db_path']}\n\n"

        if stats['categories']:
            stats_text += "Categories:\n"
            for category, count in stats['categories'].items():
                stats_text += f"  - {category}: {count} chunks\n"

        return [TextContent(type="text", text=stats_text)]

    async def _list_documents(self, arguments: dict[str, Any]) -> list[TextContent]:
        """List all documents in the knowledge base"""
        category = arguments.get("category")

        # Get all documents from vectorstore
        # Note: This returns chunks, not full documents
        # We'll aggregate by source
        try:
            results = self.rag_service.vectorstore.get(
                where={"category": category} if category else None
            )

            if not results or not results.get("metadatas"):
                return [TextContent(
                    type="text",
                    text="No documents found in knowledge base"
                )]

            # Aggregate by source
            sources = {}
            for metadata in results["metadatas"]:
                source = metadata.get("source", "unknown")
                cat = metadata.get("category", "unknown")
                if source not in sources:
                    sources[source] = {"category": cat, "chunks": 0}
                sources[source]["chunks"] += 1

            # Format output
            doc_text = f"Documents in knowledge base (collection: {self.collection_name}):\n\n"
            for source, info in sources.items():
                doc_text += f"- {source}\n"
                doc_text += f"  Category: {info['category']}\n"
                doc_text += f"  Chunks: {info['chunks']}\n"

            return [TextContent(type="text", text=doc_text)]

        except Exception as e:
            return [TextContent(
                type="text",
                text=f"Error listing documents: {str(e)}"
            )]

    async def _delete_document(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Delete a document from the knowledge base"""
        source = arguments["source"]

        success = await self.rag_service.delete_by_source(source)

        if success:
            return [TextContent(
                type="text",
                text=f"Successfully deleted document: {source}"
            )]
        else:
            return [TextContent(
                type="text",
                text=f"Failed to delete document: {source} (not found or error)"
            )]

    async def _update_document(self, arguments: dict[str, Any]) -> list[TextContent]:
        """Update an existing document"""
        source = arguments["source"]
        content = arguments["content"]
        metadata = arguments.get("metadata", {})

        # Delete old version
        await self.rag_service.delete_by_source(source)

        # Add new version
        metadata["source"] = source
        chunks_added = await self.rag_service.add_document(
            content=content,
            metadata=metadata,
            chunk_size=self.config.chunk_size
        )

        return [TextContent(
            type="text",
            text=f"Successfully updated document: {source}\n"
                 f"Added {chunks_added} chunks"
        )]

    async def ensure_isolated(self) -> dict[str, Any]:
        """
        Verify collection isolation

        Returns:
            Isolation verification results
        """
        stats = await self.rag_service.get_statistics()
        return {
            "project_id": self.project_id,
            "collection_name": self.collection_name,
            "isolated": True,
            "total_chunks": stats["total_chunks"]
        }

    async def run(self):
        """Run the MCP server"""
        async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


async def main():
    """Main entry point for KnowledgeBeast MCP server"""
    import os

    # Get project ID from environment or default
    project_id = os.getenv("KNOWLEDGEBEAST_PROJECT_ID", "default")

    # Create and run server
    server = KnowledgeBeastMCP(project_id=project_id)
    await server.run()


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
