"""
Document Ingestion Tools

Tools for ingesting documents into the KnowledgeBeast knowledge base.
Supports multiple formats and automatic chunking.
"""

import sys
from pathlib import Path
from typing import Any, Dict, Optional

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.rag_service import RAGService


class DocumentIngestion:
    """
    Document ingestion tools for KnowledgeBeast

    Handles adding documents to the knowledge base with automatic
    chunking, metadata extraction, and embedding generation.
    """

    def __init__(self, rag_service: RAGService):
        """
        Initialize document ingestion tools

        Args:
            rag_service: RAG service instance
        """
        self.rag_service = rag_service

    async def ingest_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 1000
    ) -> Dict[str, Any]:
        """
        Ingest a single document into the knowledge base

        Args:
            content: Document content
            metadata: Document metadata (must include 'source')
            chunk_size: Size of text chunks

        Returns:
            Ingestion result with chunk count
        """
        if not metadata.get("source"):
            raise ValueError("Document metadata must include 'source' field")

        chunks_added = await self.rag_service.add_document(
            content=content,
            metadata=metadata,
            chunk_size=chunk_size
        )

        return {
            "success": True,
            "source": metadata["source"],
            "chunks_added": chunks_added,
            "collection": self.rag_service.collection_name
        }

    async def ingest_file(
        self,
        file_path: str,
        category: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Ingest a file from the filesystem

        Args:
            file_path: Path to file
            category: Optional category for the document
            metadata: Additional metadata

        Returns:
            Ingestion result
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Read file content
        try:
            content = file_path_obj.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            # Try alternative encodings
            content = file_path_obj.read_text(encoding="latin-1")

        # Prepare metadata
        doc_metadata = metadata or {}
        doc_metadata["source"] = str(file_path_obj)
        doc_metadata["filename"] = file_path_obj.name
        doc_metadata["extension"] = file_path_obj.suffix

        if category:
            doc_metadata["category"] = category

        # Ingest document
        return await self.ingest_document(content, doc_metadata)

    async def ingest_directory(
        self,
        directory_path: str,
        category: str,
        file_extensions: Optional[list[str]] = None,
        recursive: bool = True
    ) -> Dict[str, Any]:
        """
        Ingest all documents in a directory

        Args:
            directory_path: Path to directory
            category: Category for all documents
            file_extensions: List of extensions to include (default: all supported)
            recursive: Process subdirectories recursively

        Returns:
            Batch ingestion results
        """
        dir_path = Path(directory_path)

        if not dir_path.exists() or not dir_path.is_dir():
            raise ValueError(f"Invalid directory: {directory_path}")

        # Default supported extensions
        if not file_extensions:
            file_extensions = [".md", ".txt", ".pdf", ".docx", ".py", ".js", ".ts"]

        # Find files
        files = []
        if recursive:
            for ext in file_extensions:
                files.extend(dir_path.rglob(f"*{ext}"))
        else:
            for ext in file_extensions:
                files.extend(dir_path.glob(f"*{ext}"))

        # Ingest each file
        results = {
            "total_files": len(files),
            "successful": 0,
            "failed": 0,
            "total_chunks": 0,
            "errors": []
        }

        for file_path in files:
            try:
                result = await self.ingest_file(
                    str(file_path),
                    category=category
                )
                results["successful"] += 1
                results["total_chunks"] += result["chunks_added"]
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "file": str(file_path),
                    "error": str(e)
                })

        return results

    async def batch_ingest(
        self,
        documents: list[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Ingest multiple documents in batch

        Args:
            documents: List of documents with 'content' and 'metadata' fields

        Returns:
            Batch ingestion results
        """
        results = {
            "total_documents": len(documents),
            "successful": 0,
            "failed": 0,
            "total_chunks": 0,
            "errors": []
        }

        for doc in documents:
            try:
                result = await self.ingest_document(
                    content=doc["content"],
                    metadata=doc["metadata"],
                    chunk_size=doc.get("chunk_size", 1000)
                )
                results["successful"] += 1
                results["total_chunks"] += result["chunks_added"]
            except Exception as e:
                results["failed"] += 1
                results["errors"].append({
                    "source": doc.get("metadata", {}).get("source", "unknown"),
                    "error": str(e)
                })

        return results
