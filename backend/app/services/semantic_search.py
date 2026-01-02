"""
Semantic Search Service (Phase 4, Task 4.2)

Integrates KnowledgeBeast/RAG semantic search with the ComposedQuery layer.
Provides vector similarity and hybrid (vector + keyword) search across
the knowledge base.

This service wraps RAGService and provides:
- Semantic search with configurable thresholds
- Category filtering
- Conversion to entity format for QueryExecutor integration
"""

import logging
from typing import Any, Optional

from app.schemas.query import SemanticSearchSpec

# Lazy import to handle optional RAG dependencies
try:
    from app.services.rag_service import RAG_AVAILABLE, RAGService
except ImportError:
    RAG_AVAILABLE = False
    RAGService = None

logger = logging.getLogger(__name__)


class SemanticSearchService:
    """Service for semantic search over knowledge base.

    Wraps RAGService to provide semantic search integration with
    the ComposedQuery layer. Handles initialization, threshold
    filtering, and conversion to entity format.

    Examples:
        >>> service = SemanticSearchService(repository_id=1)
        >>> spec = SemanticSearchSpec(query="authentication", limit=5)
        >>> results = await service.search(spec)
        >>> entities = await service.search_as_entities(spec)
    """

    def __init__(self, repository_id: int):
        """Initialize SemanticSearchService for a repository.

        Args:
            repository_id: Repository ID for multi-tenant isolation.
                          Maps to RAGService collection.

        Raises:
            ImportError: If RAG dependencies are not available.
        """
        if not RAG_AVAILABLE:
            raise ImportError(
                "RAG dependencies not available. Install with: "
                "pip install knowledgebeast>=3.0.0 sentence-transformers>=2.3.0"
            )

        self.repository_id = repository_id
        self._rag_service: Optional[RAGService] = None
        self._initialized = False

        logger.info(f"SemanticSearchService created for repository {repository_id}")

    async def _ensure_initialized(self) -> RAGService:
        """Ensure RAG service is initialized.

        Returns:
            Initialized RAGService instance.
        """
        if self._rag_service is None:
            self._rag_service = RAGService(self.repository_id)

        if not self._initialized:
            await self._rag_service.initialize()
            self._initialized = True

        return self._rag_service

    async def search(
        self,
        spec: SemanticSearchSpec,
    ) -> list[dict[str, Any]]:
        """Perform semantic search on knowledge base.

        Uses hybrid search (vector + keyword) for best results.
        Applies threshold filtering if specified.

        Args:
            spec: Semantic search specification.

        Returns:
            List of search results with content, metadata, and scores.
        """
        rag = await self._ensure_initialized()

        # Get first category if specified (RAG service takes single category)
        category = spec.categories[0] if spec.categories else None

        # Perform search
        results = await rag.query(
            question=spec.query,
            category=category,
            k=spec.limit,
        )

        # Apply threshold filter if specified
        if spec.threshold is not None:
            results = [r for r in results if r.get("score", 0) >= spec.threshold]

        # Optionally strip content
        if not spec.include_content:
            for r in results:
                r.pop("content", None)

        return results

    async def search_as_entities(
        self,
        spec: SemanticSearchSpec,
    ) -> list[dict[str, Any]]:
        """Perform semantic search and convert results to entity format.

        Converts RAG results to the entity format used by QueryExecutor,
        making semantic results compatible with graph query results.

        Args:
            spec: Semantic search specification.

        Returns:
            List of entities in QueryExecutor format.
        """
        results = await self.search(spec)

        entities = []
        for i, result in enumerate(results):
            entity = {
                "id": f"kb_{self.repository_id}_{i}",
                "type": "knowledge",
                "label": result.get("source", "unknown"),
                "semantic_score": result.get("score", 0.0),
                "source": result.get("source", "unknown"),
                "category": result.get("category", "unknown"),
            }

            # Include content if available
            if spec.include_content and "content" in result:
                entity["content"] = result["content"]

            # Include any additional metadata
            if "metadata" in result:
                entity["metadata"] = result["metadata"]

            entities.append(entity)

        return entities

    async def close(self):
        """Close underlying RAG service and cleanup resources."""
        if self._rag_service is not None:
            await self._rag_service.close()
            self._rag_service = None
            self._initialized = False
            logger.info(f"SemanticSearchService closed for repository {self.repository_id}")


# =============================================================================
# Factory for creating services per repository
# =============================================================================

_service_cache: dict[int, SemanticSearchService] = {}


def get_semantic_search_service(repository_id: int) -> SemanticSearchService:
    """Get or create SemanticSearchService for a repository.

    Caches services per repository ID to reuse connections.

    Args:
        repository_id: Repository ID for multi-tenant isolation.

    Returns:
        SemanticSearchService instance.
    """
    if repository_id not in _service_cache:
        _service_cache[repository_id] = SemanticSearchService(repository_id)
    return _service_cache[repository_id]


async def clear_service_cache():
    """Clear and close all cached semantic search services.

    Should be called during application shutdown.
    """
    for service in _service_cache.values():
        await service.close()
    _service_cache.clear()
