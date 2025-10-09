"""
RAG (Retrieval-Augmented Generation) service for knowledge base
Wrapper around the existing process_docs.py knowledge base processor

Note: RAG dependencies are optional and imported lazily.
Install with: pip install langchain langchain-community langchain-chroma
chromadb sentence-transformers
"""

import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

from app.config import settings
from app.utils.path_security import PathValidator

# Lazy imports - only import when RAGService is instantiated
try:
    from langchain_community.embeddings import HuggingFaceEmbeddings
    from langchain_chroma import Chroma

    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    HuggingFaceEmbeddings = None
    Chroma = None

# Global cache for embeddings model (expensive to initialize - 8+ seconds)
_embeddings_cache: Dict[str, Any] = {}


class RAGService:
    """Service for knowledge base RAG operations"""

    def __init__(self, db_path: Optional[str] = None, collection_name: str = "default"):
        """
        Initialize RAG service

        Args:
            db_path: Path to ChromaDB database (uses config default if not provided)
            collection_name: Name of the collection for multi-collection support

        Raises:
            ImportError: If RAG dependencies are not installed
        """
        if not RAG_AVAILABLE:
            raise ImportError(
                "RAG dependencies not installed. "
                "Install with: pip install langchain langchain-community "
                "langchain-chroma chromadb sentence-transformers"
            )

        self.db_path = db_path or settings.knowledge_base_path
        self.embedding_model_name = settings.embedding_model
        self.collection_name = collection_name

        # Initialize embeddings (local model - no API costs)
        # Use cached embeddings model to avoid 8+ second reload on each instantiation
        if self.embedding_model_name not in _embeddings_cache:
            _embeddings_cache[self.embedding_model_name] = HuggingFaceEmbeddings(
                model_name=self.embedding_model_name
            )
        self.embeddings = _embeddings_cache[self.embedding_model_name]

        # Initialize vector store with specified collection
        self.vectorstore = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=self.db_path,
        )

    async def query(
        self, question: str, category: Optional[str] = None, k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query the knowledge base

        Args:
            question: Natural language question
            category: Filter by category (optional)
            k: Number of results to return

        Returns:
            List of relevant document chunks with metadata
        """
        # Build filter if category is provided
        filter_dict = {"category": category} if category else None

        # Search with similarity scores
        results = self.vectorstore.similarity_search_with_score(
            question, k=k, filter=filter_dict
        )

        return [
            {
                "content": doc.page_content,
                "metadata": doc.metadata,
                "score": float(score),
                "category": doc.metadata.get("category", "unknown"),
                "source": doc.metadata.get("source", "unknown"),
            }
            for doc, score in results
        ]

    async def add_document(
        self, content: str, metadata: Dict[str, Any], chunk_size: int = 1000
    ) -> int:
        """
        Add a document to the knowledge base

        Args:
            content: Document content
            metadata: Document metadata
            chunk_size: Size of text chunks

        Returns:
            Number of chunks added
        """
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        # Split into chunks
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )

        chunks = text_splitter.split_text(content)

        # Prepare metadata for each chunk
        metadatas = [metadata.copy() for _ in chunks]

        # Add to vector store
        self.vectorstore.add_texts(texts=chunks, metadatas=metadatas)

        return len(chunks)

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
            results = self.vectorstore.get(where={"source": source})

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

            return {
                "total_chunks": total_chunks,
                "categories": categories,
                "embedding_model": self.embedding_model_name,
                "db_path": self.db_path,
                "collection_name": self.collection_name,
            }

        except Exception as e:
            print(f"Error getting statistics: {e}")
            return {"total_chunks": 0, "categories": {}, "error": str(e)}

    def process_directory(
        self, directory: str, category: str, file_extensions: Optional[List[str]] = None
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

        Raises:
            ValueError: If directory path is invalid or traverses outside allowed boundaries
        """
        # Security: Validate directory path to prevent path traversal
        # Define allowed base directory for document processing
        allowed_base = Path(self.db_path).parent
        safe_directory = PathValidator.validate_path(
            directory, allowed_base, must_exist=True
        )

        # Import the existing processor
        sys.path.insert(
            0,
            str(
                Path(__file__).parent.parent.parent.parent.parent
                / "tools"
                / "knowledge-base"
            ),
        )

        try:
            from process_docs import PerformiaKnowledgeProcessor

            processor = PerformiaKnowledgeProcessor(db_path=self.db_path)
            # Use the validated safe directory path
            return processor.process_directory(str(safe_directory), category)

        except ImportError as e:
            print(f"Error importing process_docs: {e}")
            return 0
