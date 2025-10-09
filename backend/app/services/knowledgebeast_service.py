"""
KnowledgeBeast service wrapper for CommandCenter integration

This service provides a CommandCenter-compatible interface to KnowledgeBeast v2.3.2,
enabling production-ready vector RAG with multi-project isolation.

Features:
- True vector embeddings (sentence-transformers)
- Per-project ChromaDB collections (project_{id})
- Hybrid search (configurable vector + keyword)
- Production observability (metrics, health checks)
- Backward compatibility with existing RAG API
"""

from typing import List, Dict, Any, Optional, Union
from pathlib import Path
import time
import logging

# Lazy imports for KnowledgeBeast (optional dependency during migration)
try:
    from knowledgebeast.core.embeddings import EmbeddingEngine
    from knowledgebeast.core.vector_store import VectorStore
    from knowledgebeast.core.query_engine import HybridQueryEngine
    from knowledgebeast.core.repository import DocumentRepository

    KNOWLEDGEBEAST_AVAILABLE = True
except ImportError:
    KNOWLEDGEBEAST_AVAILABLE = False
    EmbeddingEngine = None
    VectorStore = None
    HybridQueryEngine = None
    DocumentRepository = None

from app.config import settings

logger = logging.getLogger(__name__)


class KnowledgeBeastService:
    """
    Service wrapper around KnowledgeBeast for CommandCenter

    Provides CommandCenter-compatible API while using KnowledgeBeast v2.3.2
    for vector search, embeddings, and knowledge management.

    Architecture:
    - project_id → collection_name mapping (project_{id})
    - Per-project ChromaDB collections (native isolation)
    - Hybrid search (vector + keyword)
    - Semantic caching (95%+ hit ratio)
    - Circuit breaker + retry logic
    """

    def __init__(
        self,
        project_id: int,
        db_path: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize KnowledgeBeast service for a specific project

        Args:
            project_id: CommandCenter project ID
            db_path: Path to ChromaDB storage (uses config default if not provided)
            embedding_model: Embedding model name (default: all-MiniLM-L6-v2)

        Raises:
            ImportError: If KnowledgeBeast is not installed
        """
        if not KNOWLEDGEBEAST_AVAILABLE:
            raise ImportError(
                "KnowledgeBeast not installed. "
                "Install with: pip install knowledgebeast>=2.3.2"
            )

        self.project_id = project_id
        self.collection_name = f"project_{project_id}"
        self.db_path = db_path or getattr(settings, "knowledgebeast_db_path", "./kb_chroma_db")
        self.embedding_model = embedding_model

        logger.info(
            f"Initializing KnowledgeBeast for project {project_id} "
            f"(collection: {self.collection_name}, model: {embedding_model})"
        )

        # Initialize KnowledgeBeast components
        self._init_components()

    def _init_components(self):
        """Initialize KnowledgeBeast core components"""
        try:
            # Embedding engine with LRU cache (1000 embeddings)
            self.embedding_engine = EmbeddingEngine(
                model_name=self.embedding_model, cache_size=1000
            )

            # Vector store with per-project collection
            self.vector_store = VectorStore(
                persist_directory=self.db_path,
                collection_name=self.collection_name,
                enable_circuit_breaker=True,
                circuit_breaker_threshold=5,
            )

            # Document repository for keyword search
            self.repository = DocumentRepository()

            # Hybrid query engine (vector + keyword)
            self.query_engine = HybridQueryEngine(
                repository=self.repository,
                vector_store=self.vector_store,
                embedding_engine=self.embedding_engine,
            )

            logger.info(f"KnowledgeBeast initialized successfully for project {self.project_id}")

        except Exception as e:
            logger.error(f"Failed to initialize KnowledgeBeast: {e}")
            raise

    async def query(
        self,
        question: str,
        category: Optional[str] = None,
        k: int = 5,
        mode: str = "hybrid",
        alpha: float = 0.7,
    ) -> List[Dict[str, Any]]:
        """
        Query the knowledge base

        Args:
            question: Natural language question
            category: Filter by category (optional)
            k: Number of results to return
            mode: Search mode ('vector', 'keyword', 'hybrid')
            alpha: Hybrid search blend (0=keyword only, 1=vector only, default: 0.7)

        Returns:
            List of relevant documents with scores

        Examples:
            >>> service = KnowledgeBeastService(project_id=1)
            >>> results = await service.query("What is machine learning?", mode="hybrid")
            >>> len(results) > 0
            True
        """
        logger.debug(
            f"Query: project={self.project_id}, question='{question[:50]}...', "
            f"mode={mode}, k={k}, alpha={alpha}"
        )

        try:
            # Generate query embedding for vector/hybrid modes
            if mode in ["vector", "hybrid"]:
                query_embedding = self.embedding_engine.embed(question)

            # Perform search based on mode
            if mode == "vector":
                results = self.vector_store.query(
                    query_embeddings=query_embedding,
                    n_results=k,
                    where={"category": category} if category else None,
                )
            elif mode == "keyword":
                results = self.query_engine.search_keyword(question, top_k=k)
            else:  # hybrid (default)
                results = self.query_engine.search_hybrid(question, top_k=k, alpha=alpha)

            # Format results to match CommandCenter schema
            formatted_results = self._format_results(results)

            logger.debug(f"Query returned {len(formatted_results)} results")
            return formatted_results

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    async def add_document(
        self, content: str, metadata: Dict[str, Any], chunk_size: int = 1000
    ) -> int:
        """
        Add a document to the knowledge base

        Args:
            content: Document content
            metadata: Document metadata (title, category, source, etc.)
            chunk_size: Size of text chunks (default: 1000)

        Returns:
            Number of chunks added

        Examples:
            >>> service = KnowledgeBeastService(project_id=1)
            >>> chunks = await service.add_document(
            ...     content="This is a test document.",
            ...     metadata={"category": "test", "source": "test.txt"}
            ... )
            >>> chunks > 0
            True
        """
        logger.info(
            f"Adding document: project={self.project_id}, "
            f"length={len(content)}, chunk_size={chunk_size}"
        )

        try:
            # Import chunker (only when needed)
            try:
                from knowledgebeast.chunking.recursive_chunker import RecursiveChunker
            except ImportError:
                # Fallback to simple chunking if advanced chunking not available
                logger.warning("RecursiveChunker not available, using simple chunking")
                chunks = self._simple_chunk(content, chunk_size)
            else:
                # Use advanced recursive chunking
                chunker = RecursiveChunker(chunk_size=chunk_size, chunk_overlap=200)
                chunks = chunker.chunk(content)

            if not chunks:
                logger.warning("No chunks generated from document")
                return 0

            # Generate embeddings for each chunk (batch processing)
            embeddings = self.embedding_engine.embed(chunks)

            # Generate unique IDs for chunks
            timestamp = int(time.time() * 1000)
            ids = [f"doc_{timestamp}_{i}" for i in range(len(chunks))]

            # Prepare metadata for each chunk
            metadatas = [metadata.copy() for _ in chunks]

            # Add to vector store
            self.vector_store.add(
                ids=ids, embeddings=embeddings, documents=chunks, metadatas=metadatas
            )

            # Also add to repository for keyword search
            for doc_id, chunk, meta in zip(ids, chunks, metadatas):
                self.repository.add_document(doc_id, {"content": chunk, **meta})

                # Index terms for keyword search
                terms = set(chunk.lower().split())
                for term in terms:
                    if len(term) > 2:  # Skip very short terms
                        self.repository.index_term(term, doc_id)

            logger.info(f"Successfully added {len(chunks)} chunks to project {self.project_id}")
            return len(chunks)

        except Exception as e:
            logger.error(f"Failed to add document: {e}")
            raise

    async def delete_by_source(self, source: str) -> bool:
        """
        Delete documents by source file

        Args:
            source: Source file path

        Returns:
            True if successful, False otherwise
        """
        logger.info(f"Deleting documents: project={self.project_id}, source={source}")

        try:
            # Query documents with this source
            results = self.vector_store.get(where={"source": source})

            if results and results.get("ids"):
                doc_ids = results["ids"]

                # Delete from vector store
                self.vector_store.delete(ids=doc_ids)

                # Delete from repository
                for doc_id in doc_ids:
                    if doc_id in self.repository.documents:
                        del self.repository.documents[doc_id]

                logger.info(f"Deleted {len(doc_ids)} documents with source={source}")
                return True

            logger.warning(f"No documents found with source={source}")
            return False

        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
            return False

    async def get_categories(self) -> List[str]:
        """
        Get list of all categories in the knowledge base

        Returns:
            List of unique category names
        """
        try:
            # Get all documents
            all_docs = self.vector_store.get()

            # Extract unique categories
            categories = set()
            if all_docs.get("metadatas"):
                for metadata in all_docs["metadatas"]:
                    if "category" in metadata:
                        categories.add(metadata["category"])

            return sorted(list(categories))

        except Exception as e:
            logger.error(f"Failed to get categories: {e}")
            return []

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get knowledge base statistics

        Returns:
            Statistics dictionary including:
            - total_chunks: Total number of document chunks
            - categories: Category breakdown
            - embedding_model: Model name
            - collection_name: ChromaDB collection name
            - cache_hit_rate: Embedding cache efficiency
            - circuit_breaker_state: Health status
        """
        try:
            # Get vector store statistics
            vector_stats = self.vector_store.get_stats()

            # Get embedding engine statistics
            embedding_stats = self.embedding_engine.get_stats()

            # Get category breakdown
            all_docs = self.vector_store.get()
            categories = {}
            if all_docs.get("metadatas"):
                for metadata in all_docs["metadatas"]:
                    category = metadata.get("category", "unknown")
                    categories[category] = categories.get(category, 0) + 1

            # Get circuit breaker status
            circuit_breaker_stats = (
                vector_stats.get("circuit_breaker", {})
                if "circuit_breaker" in vector_stats
                else {"state": "disabled"}
            )

            return {
                "total_chunks": vector_stats.get("total_documents", 0),
                "categories": categories,
                "embedding_model": self.embedding_engine.model_name,
                "embedding_dim": self.embedding_engine.embedding_dim,
                "collection_name": self.collection_name,
                "project_id": self.project_id,
                "db_path": self.db_path,
                "cache_hit_rate": embedding_stats.get("cache_hit_rate", 0.0),
                "cache_size": embedding_stats.get("cache_size", 0),
                "cache_capacity": embedding_stats.get("cache_capacity", 0),
                "circuit_breaker_state": circuit_breaker_stats.get("state", "unknown"),
                "total_queries": vector_stats.get("total_queries", 0),
            }

        except Exception as e:
            logger.error(f"Failed to get statistics: {e}")
            return {
                "total_chunks": 0,
                "categories": {},
                "error": str(e),
                "project_id": self.project_id,
            }

    async def get_health(self) -> Dict[str, str]:
        """
        Get health status of the knowledge base

        Returns:
            Health status dictionary with 'status' key
        """
        try:
            health = self.vector_store.get_health()
            return {
                "status": health.get("status", "unknown"),
                "chromadb_available": health.get("chromadb_available", False),
                "circuit_breaker_state": health.get("circuit_breaker_state", "unknown"),
                "document_count": health.get("document_count", 0),
                "collection": self.collection_name,
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {"status": "unhealthy", "error": str(e)}

    def _format_results(self, results: Any) -> List[Dict[str, Any]]:
        """
        Format KnowledgeBeast results to CommandCenter schema

        Args:
            results: Raw results from KnowledgeBeast (vector/keyword/hybrid)

        Returns:
            List of formatted results matching CommandCenter API schema
        """
        formatted = []

        # Handle different result formats
        if isinstance(results, dict):
            # Vector search results (from VectorStore.query)
            if "ids" in results and "documents" in results and results["ids"]:
                for i in range(len(results["ids"][0])):
                    formatted.append(
                        {
                            "content": results["documents"][0][i],
                            "metadata": (
                                results["metadatas"][0][i] if "metadatas" in results else {}
                            ),
                            "score": (
                                float(results["distances"][0][i])
                                if "distances" in results
                                else 0.0
                            ),
                            "category": (
                                results["metadatas"][0][i].get("category", "unknown")
                                if "metadatas" in results
                                else "unknown"
                            ),
                            "source": (
                                results["metadatas"][0][i].get("source", "unknown")
                                if "metadatas" in results
                                else "unknown"
                            ),
                            "title": (
                                results["metadatas"][0][i].get("title", "Untitled")
                                if "metadatas" in results
                                else "Untitled"
                            ),
                        }
                    )

        elif isinstance(results, list):
            # Hybrid/keyword search results (list of tuples: (doc_id, doc_data, score))
            for result in results:
                if len(result) == 3:
                    doc_id, doc_data, score = result
                    formatted.append(
                        {
                            "content": doc_data.get("content", ""),
                            "metadata": {
                                k: v for k, v in doc_data.items() if k != "content"
                            },
                            "score": float(score),
                            "category": doc_data.get("category", "unknown"),
                            "source": doc_data.get("source", "unknown"),
                            "title": doc_data.get("title", "Untitled"),
                        }
                    )

        return formatted

    def _simple_chunk(self, text: str, chunk_size: int = 1000) -> List[str]:
        """
        Simple text chunking fallback (if advanced chunking not available)

        Args:
            text: Text to chunk
            chunk_size: Maximum chunk size

        Returns:
            List of text chunks
        """
        chunks = []
        words = text.split()
        current_chunk = []
        current_size = 0

        for word in words:
            word_size = len(word) + 1  # +1 for space
            if current_size + word_size > chunk_size and current_chunk:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_size = word_size
            else:
                current_chunk.append(word)
                current_size += word_size

        if current_chunk:
            chunks.append(" ".join(current_chunk))

        return chunks


# Compatibility function for gradual migration
def get_knowledge_service(project_id: int, use_knowledgebeast: bool = False):
    """
    Factory function to get appropriate knowledge service

    Args:
        project_id: CommandCenter project ID
        use_knowledgebeast: If True, use KnowledgeBeast; else use legacy RAG

    Returns:
        KnowledgeBeastService or RAGService instance
    """
    if use_knowledgebeast and KNOWLEDGEBEAST_AVAILABLE:
        return KnowledgeBeastService(project_id=project_id)
    else:
        # Import legacy RAG service
        from app.services.rag_service import RAGService

        return RAGService(collection_name=f"project_{project_id}")
