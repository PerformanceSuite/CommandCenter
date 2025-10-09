"""
RAG (Retrieval-Augmented Generation) service for knowledge base
Wrapper around the existing process_docs.py knowledge base processor

Note: RAG dependencies are optional and imported lazily.
Install with: pip install langchain langchain-community langchain-chroma chromadb sentence-transformers
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from app.config import settings

# Lazy imports - only import when RAGService is instantiated
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_chroma import Chroma
    import chromadb
    from chromadb.config import Settings as ChromaSettings
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    HuggingFaceEmbeddings = None
    Chroma = None
    chromadb = None
    ChromaSettings = None

# Global cache for embeddings model (expensive to initialize - 8+ seconds)
_embeddings_cache: Dict[str, Any] = {}


class RAGService:
    """
    Service for knowledge base RAG operations with per-repository collection isolation

    Each repository gets its own ChromaDB collection to prevent knowledge base data leaks.
    This ensures that queries for Repository A only search Repository A's documents.
    """

    def __init__(self, db_path: Optional[str] = None, repository_id: Optional[int] = None):
        """
        Initialize RAG service with repository-based collection isolation

        Args:
            db_path: Path to ChromaDB database (uses config default if not provided)
            repository_id: Repository ID for collection isolation (optional for backwards compatibility)

        Raises:
            ImportError: If RAG dependencies are not installed
        """
        if not RAG_AVAILABLE:
            raise ImportError(
                "RAG dependencies not installed. "
                "Install with: pip install langchain langchain-community langchain-chroma chromadb sentence-transformers"
            )

        self.db_path = db_path or settings.knowledge_base_path
        self.embedding_model_name = settings.embedding_model
        self.repository_id = repository_id

        # Initialize embeddings (local model - no API costs)
        # Use cached embeddings model to avoid 8+ second reload on each instantiation
        if self.embedding_model_name not in _embeddings_cache:
            _embeddings_cache[self.embedding_model_name] = HuggingFaceEmbeddings(
                model_name=self.embedding_model_name
            )
        self.embeddings = _embeddings_cache[self.embedding_model_name]

        # Initialize ChromaDB client for collection management
        self.chroma_client = chromadb.PersistentClient(path=self.db_path)

        # Determine collection name based on repository_id
        if repository_id is not None:
            collection_name = self._get_collection_name(repository_id)
        else:
            # Backwards compatibility - use default collection if no repository_id
            collection_name = "knowledge_default"

        # Initialize vector store with specified collection
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.db_path
        )

    def _get_collection_name(self, repository_id: int) -> str:
        """
        Get collection name for repository

        Args:
            repository_id: Repository ID

        Returns:
            Collection name string
        """
        return f"knowledge_repo_{repository_id}"

    def get_or_create_collection(self, repository_id: int):
        """
        Get existing collection or create new one for repository.

        Each repository gets its own collection for complete isolation.
        This prevents Repository A's queries from returning Repository B's documents.

        Args:
            repository_id: Repository ID

        Returns:
            ChromaDB collection object
        """
        collection_name = self._get_collection_name(repository_id)

        try:
            collection = self.chroma_client.get_collection(name=collection_name)
            print(f"Using existing collection: {collection_name}")
        except:
            collection = self.chroma_client.create_collection(
                name=collection_name,
                metadata={
                    "repository_id": repository_id,
                    "created_at": str(datetime.utcnow())
                }
            )
            print(f"Created new collection: {collection_name}")

        return collection

    async def query(
        self,
        question: str,
        category: Optional[str] = None,
        k: int = 5,
        repository_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Query the knowledge base

        IMPORTANT: Only searches the repository's own documents when repository_id is provided.
        This prevents cross-repository knowledge leaks.

        Args:
            question: Natural language question
            category: Filter by category (optional)
            k: Number of results to return
            repository_id: Repository ID for isolated search (uses instance repository_id if not provided)

        Returns:
            List of relevant document chunks with metadata
        """
        # Use provided repository_id or fall back to instance repository_id
        target_repo_id = repository_id if repository_id is not None else self.repository_id

        # If repository_id is specified, reinitialize with that repository's collection
        if target_repo_id is not None and target_repo_id != self.repository_id:
            temp_service = RAGService(db_path=self.db_path, repository_id=target_repo_id)
            vectorstore = temp_service.vectorstore
        else:
            vectorstore = self.vectorstore

        # Build filter if category is provided
        filter_dict = {"category": category} if category else None

        # Search with similarity scores
        results = vectorstore.similarity_search_with_score(
            question,
            k=k,
            filter=filter_dict
        )

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
                "category": doc.metadata.get("category", "unknown"),
                "source": doc.metadata.get("source", "unknown"),
                "repository_id": target_repo_id,
            }
            for doc, score in results
        ]

    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 1000,
        repository_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        Add a document to the repository's knowledge base collection

        Args:
            content: Document content
            metadata: Document metadata
            chunk_size: Size of text chunks
            repository_id: Repository ID for collection isolation (uses instance repository_id if not provided)

        Returns:
            Dictionary with status and number of chunks added
        """
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        # Use provided repository_id or fall back to instance repository_id
        target_repo_id = repository_id if repository_id is not None else self.repository_id

        # If repository_id is specified, reinitialize with that repository's collection
        if target_repo_id is not None and target_repo_id != self.repository_id:
            temp_service = RAGService(db_path=self.db_path, repository_id=target_repo_id)
            vectorstore = temp_service.vectorstore
        else:
            vectorstore = self.vectorstore

        # Add repository_id to metadata
        metadata_with_repo = metadata.copy()
        if target_repo_id is not None:
            metadata_with_repo["repository_id"] = target_repo_id

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""]
        )

        chunks = text_splitter.split_text(content)

        # Prepare metadata for each chunk
        metadatas = [metadata_with_repo.copy() for _ in chunks]

        # Add to vector store
        ids = vectorstore.add_texts(texts=chunks, metadatas=metadatas)

        return {
            "status": "added",
            "chunks_added": len(chunks),
            "repository_id": target_repo_id,
            "collection": self._get_collection_name(target_repo_id) if target_repo_id else "knowledge_default",
            "document_ids": ids
        }

    async def delete_by_source(self, source: str) -> bool:
        """
        Delete documents by source file

        Args:
            source: Source file path

        Returns:
            True if successful
        """
        # Note: ChromaDB delete by metadata filter
        # This requires the collection to support metadata filtering
        try:
            # Get all documents with this source
            results = self.vectorstore.get(
                where={"source": source}
            )

            if results and results.get("ids"):
                self.vectorstore.delete(ids=results["ids"])
                return True

            return False

        except Exception as e:
            print(f"Error deleting documents: {e}")
            return False

    async def get_categories(self) -> List[str]:
        """
        Get list of all categories in the knowledge base

        Returns:
            List of category names
        """
        # This is a simplified implementation
        # In production, you might want to maintain a separate categories table
        try:
            # Get all documents and extract unique categories
            # Note: This might be expensive for large databases
            results = self.vectorstore.get()

            categories = set()
            if results and results.get("metadatas"):
                for metadata in results["metadatas"]:
                    if "category" in metadata:
                        categories.add(metadata["category"])

            return sorted(list(categories))

        except Exception as e:
            print(f"Error getting categories: {e}")
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get knowledge base statistics

        Returns:
            Statistics dictionary
        """
        try:
            results = self.vectorstore.get()

            total_chunks = len(results.get("ids", []))

            # Count by category
            categories = {}
            if results.get("metadatas"):
                for metadata in results["metadatas"]:
                    category = metadata.get("category", "unknown")
                    categories[category] = categories.get(category, 0) + 1

            # Determine collection name
            if self.repository_id is not None:
                collection_name = self._get_collection_name(self.repository_id)
            else:
                collection_name = "knowledge_default"

            return {
                "total_chunks": total_chunks,
                "categories": categories,
                "embedding_model": self.embedding_model_name,
                "db_path": self.db_path,
                "collection_name": collection_name,
                "repository_id": self.repository_id,
            }

        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {
                "total_chunks": 0,
                "categories": {},
                "error": str(e)
            }

    async def get_collection_stats(self, repository_id: int) -> Dict[str, Any]:
        """
        Get statistics for repository's collection

        Args:
            repository_id: Repository ID

        Returns:
            Collection statistics
        """
        collection_name = self._get_collection_name(repository_id)

        try:
            collection = self.chroma_client.get_collection(name=collection_name)

            return {
                "repository_id": repository_id,
                "collection_name": collection_name,
                "document_count": collection.count(),
                "metadata": collection.metadata
            }
        except Exception as e:
            return {
                "repository_id": repository_id,
                "collection_name": collection_name,
                "document_count": 0,
                "error": str(e),
                "exists": False
            }

    async def delete_document(self, repository_id: int, document_id: str) -> Dict[str, Any]:
        """
        Delete document from repository's collection

        Args:
            repository_id: Repository ID
            document_id: Document ID to delete

        Returns:
            Deletion status
        """
        collection = self.get_or_create_collection(repository_id)

        try:
            collection.delete(ids=[document_id])
            return {
                "status": "deleted",
                "document_id": document_id,
                "repository_id": repository_id
            }
        except Exception as e:
            return {
                "status": "error",
                "document_id": document_id,
                "repository_id": repository_id,
                "error": str(e)
            }

    async def delete_collection(self, repository_id: int) -> Dict[str, Any]:
        """
        Delete entire collection for repository (use when repository deleted)

        Args:
            repository_id: Repository ID

        Returns:
            Deletion status
        """
        collection_name = self._get_collection_name(repository_id)

        try:
            self.chroma_client.delete_collection(name=collection_name)
            return {
                "status": "deleted",
                "collection": collection_name,
                "repository_id": repository_id
            }
        except Exception as e:
            return {
                "status": "not_found",
                "collection": collection_name,
                "repository_id": repository_id,
                "error": str(e)
            }

    async def list_all_collections(self) -> List[Dict[str, Any]]:
        """
        List all collections in the ChromaDB instance

        Returns:
            List of collection information
        """
        try:
            collections = self.chroma_client.list_collections()

            return [
                {
                    "name": col.name,
                    "count": col.count(),
                    "metadata": col.metadata
                }
                for col in collections
            ]
        except Exception as e:
            print(f"Error listing collections: {e}")
            return []

    def process_directory(
        self,
        directory: str,
        category: str,
        file_extensions: Optional[List[str]] = None
    ) -> int:
        """
        Process all documents in a directory
        This wraps the existing process_docs.py functionality

        Args:
            directory: Directory path
            category: Document category
            file_extensions: List of file extensions to process

        Returns:
            Total number of chunks added
        """
        # Import the existing processor
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent / "tools" / "knowledge-base"))

        try:
            from process_docs import PerformiaKnowledgeProcessor

            processor = PerformiaKnowledgeProcessor(db_path=self.db_path)
            return processor.process_directory(directory, category)

        except ImportError as e:
            print(f"Error importing process_docs: {e}")
            return 0
