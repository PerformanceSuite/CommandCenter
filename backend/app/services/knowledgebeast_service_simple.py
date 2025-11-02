"""
Simplified KnowledgeBeast service wrapper using actual KB API

This uses the actual KnowledgeBeast.KnowledgeBase class
with its native query() and index() methods.
"""

import logging
from typing import Any, Dict, List, Optional

# Lazy import for KnowledgeBeast
try:
    from knowledgebeast import KnowledgeBase, KnowledgeBeastConfig

    KNOWLEDGEBEAST_AVAILABLE = True
except ImportError:
    KNOWLEDGEBEAST_AVAILABLE = False
    KnowledgeBase = None
    KnowledgeBeastConfig = None

from app.config import settings

logger = logging.getLogger(__name__)


class KnowledgeBeastService:
    """
    Simplified wrapper around KnowledgeBeast v0.1.0

    Uses the actual KB API:
    - KnowledgeBase.query() for search
    - KnowledgeBase.index() for adding documents
    - Per-project persist directories
    """

    def __init__(
        self,
        project_id: int,
        db_path: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """Initialize KnowledgeBeast for a project"""
        if not KNOWLEDGEBEAST_AVAILABLE:
            raise ImportError("KnowledgeBeast not installed")

        self.project_id = project_id
        self.collection_name = f"project_{project_id}"
        self.db_path = db_path or getattr(settings, "knowledgebeast_db_path", "./kb_chroma_db")
        self.embedding_model = embedding_model

        # Create per-project persist directory
        import os

        self.persist_dir = os.path.join(self.db_path, self.collection_name)
        os.makedirs(self.persist_dir, exist_ok=True)

        # Initialize KnowledgeBase
        self.kb = KnowledgeBase(
            embedding_model=embedding_model,
            persist_directory=self.persist_dir,
            vector_cache_size=1000,
        )

        logger.info(f"KB initialized: project={project_id}, dir={self.persist_dir}")

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

        Note: KB v0.1.0 doesn't support mode/alpha natively,
        so we use the default query() method
        """
        try:
            # Use KB's native query method
            # It returns: {"results": [{"content": ..., "metadata": ..., "score": ...}]}
            response = self.kb.query(question, k=k)

            # Format to CommandCenter schema
            results = []
            for item in response.get("results", []):
                metadata = item.get("metadata", {})
                results.append(
                    {
                        "content": item.get("content", ""),
                        "metadata": metadata,
                        "score": item.get("score", 0.0),
                        "category": metadata.get("category", "unknown"),
                        "source": metadata.get("source", "unknown"),
                        "title": metadata.get("title", "Untitled"),
                    }
                )

            # Filter by category if requested
            if category:
                results = [r for r in results if r["category"] == category]

            return results[:k]

        except Exception as e:
            logger.error(f"Query failed: {e}")
            raise

    async def add_document(
        self, content: str, metadata: Dict[str, Any], chunk_size: int = 1000
    ) -> int:
        """Add document to KB"""
        try:
            # Save content to temp file (KB expects file path)
            import os
            import tempfile

            with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".txt") as f:
                f.write(content)
                temp_path = f.name

            try:
                # Index the document
                self.kb.index(
                    temp_path,
                    metadata=metadata,
                )

                # Estimate chunks (rough)
                chunks = len(content) // chunk_size + 1
                return chunks

            finally:
                # Cleanup temp file
                if os.path.exists(temp_path):
                    os.unlink(temp_path)

        except Exception as e:
            logger.error(f"Add document failed: {e}")
            raise

    async def delete_by_source(self, source: str) -> bool:
        """Delete by source - KB may not support this natively"""
        logger.warning(f"delete_by_source not fully supported in KB v0.1.0")
        # Would need to rebuild index without the document
        return False

    async def get_statistics(self) -> Dict[str, Any]:
        """Get statistics"""
        try:
            stats = self.kb.get_stats()
            return {
                "total_chunks": stats.get("total_documents", 0),
                "categories": {},  # Would need to scan all docs
                "embedding_model": self.embedding_model,
                "collection_name": self.collection_name,
                "project_id": self.project_id,
                "cache_hit_rate": 0.0,  # Not exposed by KB v0.1.0
            }
        except Exception as e:
            logger.error(f"Get stats failed: {e}")
            return {
                "total_chunks": 0,
                "categories": {},
                "project_id": self.project_id,
                "error": str(e),
            }

    async def get_categories(self) -> List[str]:
        """Get categories - would need to scan all documents"""
        return []

    async def get_health(self) -> Dict[str, str]:
        """Health check"""
        return {
            "status": "healthy" if self.kb else "unhealthy",
            "collection": self.collection_name,
        }
