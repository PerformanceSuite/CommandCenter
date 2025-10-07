"""
Document Management Tools

Tools for managing documents in the KnowledgeBeast knowledge base.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.rag_service import RAGService


class DocumentManagement:
    """
    Document management tools for KnowledgeBeast

    Provides tools for:
    - Listing documents
    - Deleting documents
    - Updating documents
    - Document metadata management
    """

    def __init__(self, rag_service: RAGService):
        """
        Initialize document management tools

        Args:
            rag_service: RAG service instance
        """
        self.rag_service = rag_service

    async def list_documents(
        self,
        category: Optional[str] = None,
        include_chunks: bool = False
    ) -> Dict[str, Any]:
        """
        List all documents in the knowledge base

        Args:
            category: Filter by category (optional)
            include_chunks: Include chunk count per document

        Returns:
            List of documents with metadata
        """
        try:
            # Get all documents from vectorstore
            results = self.rag_service.vectorstore.get(
                where={"category": category} if category else None
            )

            if not results or not results.get("metadatas"):
                return {
                    "total_documents": 0,
                    "documents": [],
                    "collection": self.rag_service.collection_name
                }

            # Aggregate by source
            documents_map = {}

            for i, metadata in enumerate(results["metadatas"]):
                source = metadata.get("source", "unknown")

                if source not in documents_map:
                    documents_map[source] = {
                        "source": source,
                        "category": metadata.get("category", "unknown"),
                        "title": metadata.get("title"),
                        "metadata": metadata,
                        "chunks": 0
                    }

                if include_chunks:
                    documents_map[source]["chunks"] += 1

            documents_list = list(documents_map.values())

            return {
                "total_documents": len(documents_list),
                "documents": documents_list,
                "collection": self.rag_service.collection_name,
                "category_filter": category
            }

        except Exception as e:
            return {
                "error": f"Error listing documents: {str(e)}",
                "total_documents": 0,
                "documents": []
            }

    async def get_document(
        self,
        source: str,
        include_content: bool = True
    ) -> Dict[str, Any]:
        """
        Get a specific document by source

        Args:
            source: Source identifier
            include_content: Include full content chunks

        Returns:
            Document details
        """
        try:
            results = self.rag_service.vectorstore.get(
                where={"source": source}
            )

            if not results or not results.get("metadatas"):
                return {
                    "found": False,
                    "source": source,
                    "error": "Document not found"
                }

            document = {
                "found": True,
                "source": source,
                "total_chunks": len(results["ids"]),
                "metadata": results["metadatas"][0] if results["metadatas"] else {}
            }

            if include_content and results.get("documents"):
                document["chunks"] = [
                    {
                        "id": chunk_id,
                        "content": content,
                        "metadata": metadata
                    }
                    for chunk_id, content, metadata in zip(
                        results["ids"],
                        results["documents"],
                        results["metadatas"]
                    )
                ]

            return document

        except Exception as e:
            return {
                "found": False,
                "source": source,
                "error": str(e)
            }

    async def delete_document(
        self,
        source: str
    ) -> Dict[str, Any]:
        """
        Delete a document from the knowledge base

        Args:
            source: Source identifier

        Returns:
            Deletion result
        """
        try:
            success = await self.rag_service.delete_by_source(source)

            return {
                "success": success,
                "source": source,
                "message": "Document deleted" if success else "Document not found or error occurred",
                "collection": self.rag_service.collection_name
            }

        except Exception as e:
            return {
                "success": False,
                "source": source,
                "error": str(e)
            }

    async def update_document(
        self,
        source: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Update an existing document

        Args:
            source: Source identifier
            content: New content
            metadata: Updated metadata (optional)
            chunk_size: Chunk size for re-ingestion

        Returns:
            Update result
        """
        try:
            # Delete old version
            delete_result = await self.delete_document(source)

            if not delete_result["success"]:
                # Document might not exist, proceed anyway
                pass

            # Prepare metadata
            doc_metadata = metadata or {}
            doc_metadata["source"] = source

            # Add new version
            chunks_added = await self.rag_service.add_document(
                content=content,
                metadata=doc_metadata,
                chunk_size=chunk_size
            )

            return {
                "success": True,
                "source": source,
                "chunks_added": chunks_added,
                "message": "Document updated successfully",
                "collection": self.rag_service.collection_name
            }

        except Exception as e:
            return {
                "success": False,
                "source": source,
                "error": str(e)
            }

    async def delete_by_category(
        self,
        category: str
    ) -> Dict[str, Any]:
        """
        Delete all documents in a category

        Args:
            category: Category to delete

        Returns:
            Batch deletion result
        """
        try:
            # Get all documents in category
            results = self.rag_service.vectorstore.get(
                where={"category": category}
            )

            if not results or not results.get("ids"):
                return {
                    "success": True,
                    "category": category,
                    "documents_deleted": 0,
                    "message": "No documents found in category"
                }

            # Delete all chunks
            self.rag_service.vectorstore.delete(ids=results["ids"])

            # Count unique sources
            sources = set(m.get("source") for m in results["metadatas"] if m.get("source"))

            return {
                "success": True,
                "category": category,
                "documents_deleted": len(sources),
                "chunks_deleted": len(results["ids"]),
                "collection": self.rag_service.collection_name
            }

        except Exception as e:
            return {
                "success": False,
                "category": category,
                "error": str(e)
            }

    async def update_metadata(
        self,
        source: str,
        metadata_updates: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Update metadata for a document without re-ingesting content

        Note: ChromaDB doesn't support metadata-only updates,
        so this requires re-ingestion

        Args:
            source: Source identifier
            metadata_updates: Metadata fields to update

        Returns:
            Update result
        """
        try:
            # Get existing document
            doc = await self.get_document(source, include_content=True)

            if not doc["found"]:
                return {
                    "success": False,
                    "source": source,
                    "error": "Document not found"
                }

            # Reconstruct content from chunks
            content = "\n\n".join(
                chunk["content"] for chunk in doc.get("chunks", [])
            )

            # Merge metadata
            updated_metadata = doc["metadata"].copy()
            updated_metadata.update(metadata_updates)
            updated_metadata["source"] = source  # Ensure source is preserved

            # Re-ingest with updated metadata
            return await self.update_document(
                source=source,
                content=content,
                metadata=updated_metadata
            )

        except Exception as e:
            return {
                "success": False,
                "source": source,
                "error": str(e)
            }

    async def get_sources_by_category(
        self,
        category: str
    ) -> List[str]:
        """
        Get list of unique sources in a category

        Args:
            category: Category to query

        Returns:
            List of source identifiers
        """
        try:
            results = self.rag_service.vectorstore.get(
                where={"category": category}
            )

            if not results or not results.get("metadatas"):
                return []

            sources = set(
                m.get("source") for m in results["metadatas"]
                if m.get("source")
            )

            return sorted(list(sources))

        except Exception as e:
            print(f"Error getting sources: {e}")
            return []
