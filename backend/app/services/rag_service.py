"""
RAG (Retrieval-Augmented Generation) service using KnowledgeBeast v3.0 PostgresBackend

This service provides knowledge base RAG operations backed by PostgreSQL with pgvector
for vector similarity search, replacing the legacy ChromaDB implementation.

Dependencies:
- knowledgebeast>=3.0.0 (PostgresBackend)
- sentence-transformers>=2.3.0 (embeddings)
- langchain>=0.1.0 (text splitting)
"""

from typing import List, Dict, Any, Optional
import logging

from app.config import settings

# Lazy imports - only import when RAGService is instantiated
try:
    from knowledgebeast.backends.postgres import PostgresBackend
    from sentence_transformers import SentenceTransformer
    RAG_AVAILABLE = True
except ImportError:
    RAG_AVAILABLE = False
    PostgresBackend = None
    SentenceTransformer = None

logger = logging.getLogger(__name__)


class RAGService:
    """Service for knowledge base RAG operations using KnowledgeBeast PostgresBackend"""

    def __init__(self, repository_id: int):
        """
        Initialize RAG service for a specific repository

        Args:
            repository_id: Repository ID for multi-tenant isolation
                          Each repository gets its own collection: commandcenter_{repo_id}

        Raises:
            ImportError: If RAG dependencies (KnowledgeBeast) are not installed
        """
        if not RAG_AVAILABLE:
            raise ImportError(
                "KnowledgeBeast dependencies not installed. "
                "Install with: pip install knowledgebeast>=3.0.0 sentence-transformers>=2.3.0"
            )

        self.repository_id = repository_id
        self.collection_name = f"{settings.KNOWLEDGE_COLLECTION_PREFIX}_{repository_id}"

        # Initialize embedding model (sentence-transformers)
        # This is used to generate embeddings for queries and documents
        self.embedding_model = SentenceTransformer(settings.EMBEDDING_MODEL)

        # Build connection string from settings
        connection_string = settings.get_postgres_url()

        # Initialize KnowledgeBeast PostgresBackend
        self.backend = PostgresBackend(
            connection_string=connection_string,
            collection_name=self.collection_name,
            embedding_dimension=settings.EMBEDDING_DIMENSION,
            pool_size=settings.KB_POOL_MAX_SIZE,
            pool_min_size=settings.KB_POOL_MIN_SIZE,
        )
        self._initialized = False

        logger.info(
            f"Initialized RAGService for repository {repository_id} "
            f"with collection '{self.collection_name}'"
        )

    async def initialize(self) -> None:
        """
        Initialize backend (creates schema if needed)

        This should be called before first use. It creates the necessary
        database tables and indexes if they don't exist.
        """
        if not self._initialized:
            await self.backend.initialize()
            self._initialized = True
            logger.info(f"Initialized backend for collection '{self.collection_name}'")

    async def query(
        self,
        question: str,
        category: Optional[str] = None,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query the knowledge base using hybrid search (vector + keyword)

        Args:
            question: Natural language question
            category: Filter by category (optional)
            k: Number of results to return

        Returns:
            List of relevant document chunks with metadata:
            [
                {
                    "content": "document text",
                    "metadata": {...},
                    "score": 0.95,
                    "category": "docs",
                    "source": "readme.md"
                },
                ...
            ]
        """
        if not self._initialized:
            await self.initialize()

        # Build metadata filter
        where = {"category": category} if category else None

        # Generate query embedding using sentence-transformers
        query_embedding = self.embedding_model.encode(question).tolist()

        # Use hybrid search (vector + keyword) for best results
        # alpha=0.7 means 70% vector, 30% keyword
        results = await self.backend.query_hybrid(
            query_embedding=query_embedding,
            query_text=question,
            top_k=k,
            alpha=0.7,
            where=where
        )

        # Format results to match expected API
        return [
            {
                "content": document,  # The actual document text
                "metadata": metadata,
                "score": float(score),
                "category": metadata.get("category", "unknown"),
                "source": metadata.get("source", "unknown"),
            }
            for doc_id, score, metadata, document in results
        ]

    async def add_document(
        self,
        content: str,
        metadata: Dict[str, Any],
        chunk_size: int = 1000
    ) -> int:
        """
        Add a document to the knowledge base

        The document is automatically chunked and embedded before storage.

        Args:
            content: Document content
            metadata: Document metadata (e.g., {"source": "readme.md", "category": "docs"})
            chunk_size: Size of text chunks (default: 1000 characters)

        Returns:
            Number of chunks added
        """
        if not self._initialized:
            await self.initialize()

        # Use LangChain for text chunking
        from langchain.text_splitter import RecursiveCharacterTextSplitter

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=200,
            length_function=len,
            separators=["\n\n", "\n", " ", ""],
        )
        chunks = text_splitter.split_text(content)

        # Generate embeddings for all chunks using sentence-transformers
        # encode returns numpy array, convert to list of lists
        embeddings_array = self.embedding_model.encode(chunks)
        embeddings = embeddings_array.tolist()

        # Prepare IDs and metadata for each chunk
        source = metadata.get('source', 'unknown')
        ids = [f"{source}_{i}" for i in range(len(chunks))]
        metadatas = [metadata.copy() for _ in chunks]

        # Add to backend
        await self.backend.add_documents(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas
        )

        logger.info(
            f"Added {len(chunks)} chunks from source '{source}' "
            f"to collection '{self.collection_name}'"
        )

        return len(chunks)

    async def delete_by_source(self, source: str) -> bool:
        """
        Delete all documents from a specific source file

        Args:
            source: Source file path (e.g., "docs/readme.md")

        Returns:
            True if any documents were deleted
        """
        if not self._initialized:
            await self.initialize()

        # Delete using metadata filter
        count = await self.backend.delete_documents(
            where={"source": source}
        )

        if count > 0:
            logger.info(
                f"Deleted {count} chunks from source '{source}' "
                f"in collection '{self.collection_name}'"
            )
            return True

        return False

    async def get_categories(self) -> List[str]:
        """
        Get list of all categories in the knowledge base

        Note: This is a simplified implementation that queries all documents.
        For large knowledge bases, consider maintaining a separate categories index.

        Returns:
            Sorted list of unique category names
        """
        if not self._initialized:
            await self.initialize()

        # Get all documents and extract unique categories
        # This could be optimized with a custom SQL query in production
        stats = await self.backend.get_statistics()

        # For now, return empty list - would need custom query to extract from metadata
        # This can be enhanced in PostgresBackend later
        logger.warning("get_categories() is not yet implemented for PostgresBackend")
        return []

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get knowledge base statistics

        Returns:
            Dictionary with statistics:
            {
                "total_chunks": 1234,
                "categories": {},  # Would need custom query
                "embedding_model": "all-MiniLM-L6-v2",
                "backend": "postgres",
                "collection_name": "commandcenter_1"
            }
        """
        if not self._initialized:
            await self.initialize()

        stats = await self.backend.get_statistics()

        return {
            "total_chunks": stats.get("document_count", 0),
            "categories": {},  # Would need custom query to group by category
            "embedding_model": settings.EMBEDDING_MODEL,
            "backend": "postgres",
            "collection_name": self.collection_name,
            "embedding_dimension": settings.EMBEDDING_DIMENSION,
        }

    async def close(self):
        """
        Close backend connection and cleanup resources

        Should be called when shutting down the service.
        """
        if self._initialized:
            await self.backend.close()
            self._initialized = False
            logger.info(f"Closed RAGService for collection '{self.collection_name}'")
