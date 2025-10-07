"""
Semantic Search Tools

Tools for searching the KnowledgeBeast knowledge base using semantic similarity.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.rag_service import RAGService


class SemanticSearch:
    """
    Semantic search tools for KnowledgeBeast

    Provides advanced search capabilities including:
    - Semantic similarity search
    - Category filtering
    - Score-based ranking
    - Multi-query search
    """

    def __init__(self, rag_service: RAGService):
        """
        Initialize semantic search tools

        Args:
            rag_service: RAG service instance
        """
        self.rag_service = rag_service

    async def search(
        self,
        query: str,
        category: Optional[str] = None,
        k: int = 5,
        min_score: Optional[float] = None
    ) -> Dict[str, Any]:
        """
        Perform semantic search on the knowledge base

        Args:
            query: Natural language search query
            category: Filter by category (optional)
            k: Number of results to return
            min_score: Minimum similarity score threshold (0-1)

        Returns:
            Search results with metadata and scores
        """
        results = await self.rag_service.query(
            question=query,
            category=category,
            k=k
        )

        # Filter by minimum score if specified
        if min_score is not None:
            results = [r for r in results if r["score"] >= min_score]

        return {
            "query": query,
            "category": category,
            "total_results": len(results),
            "results": results,
            "collection": self.rag_service.collection_name
        }

    async def multi_query_search(
        self,
        queries: List[str],
        category: Optional[str] = None,
        k: int = 5,
        aggregate: bool = True
    ) -> Dict[str, Any]:
        """
        Search with multiple queries and aggregate results

        Args:
            queries: List of search queries
            category: Filter by category
            k: Results per query
            aggregate: Combine and deduplicate results

        Returns:
            Aggregated search results
        """
        all_results = []

        for query in queries:
            results = await self.search(query, category, k)
            all_results.append({
                "query": query,
                "results": results["results"]
            })

        if not aggregate:
            return {
                "queries": queries,
                "results_by_query": all_results,
                "collection": self.rag_service.collection_name
            }

        # Aggregate and deduplicate by source+content
        seen = set()
        aggregated = []

        for query_result in all_results:
            for result in query_result["results"]:
                key = (result["source"], result["content"][:100])
                if key not in seen:
                    seen.add(key)
                    aggregated.append(result)

        # Sort by score
        aggregated.sort(key=lambda x: x["score"], reverse=True)

        return {
            "queries": queries,
            "total_unique_results": len(aggregated),
            "results": aggregated[:k * 2],  # Return up to 2x k results
            "collection": self.rag_service.collection_name
        }

    async def search_by_category(
        self,
        query: str,
        k_per_category: int = 3
    ) -> Dict[str, Any]:
        """
        Search across all categories separately

        Args:
            query: Search query
            k_per_category: Results per category

        Returns:
            Results grouped by category
        """
        # Get all categories
        categories = await self.rag_service.get_categories()

        results_by_category = {}

        for category in categories:
            results = await self.search(query, category, k_per_category)
            if results["results"]:
                results_by_category[category] = results["results"]

        return {
            "query": query,
            "categories_searched": len(categories),
            "categories_with_results": len(results_by_category),
            "results_by_category": results_by_category,
            "collection": self.rag_service.collection_name
        }

    async def find_similar_documents(
        self,
        source: str,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Find documents similar to a given source document

        Args:
            source: Source identifier of reference document
            k: Number of similar documents to return

        Returns:
            Similar documents
        """
        # Get the reference document
        try:
            ref_docs = self.rag_service.vectorstore.get(
                where={"source": source}
            )

            if not ref_docs or not ref_docs.get("documents"):
                return {
                    "error": f"Source document not found: {source}",
                    "results": []
                }

            # Use first chunk as query
            query_text = ref_docs["documents"][0]

            # Search for similar documents
            results = await self.search(query_text, k=k + 1)

            # Filter out the source document itself
            filtered_results = [
                r for r in results["results"]
                if r["source"] != source
            ][:k]

            return {
                "reference_source": source,
                "total_results": len(filtered_results),
                "results": filtered_results,
                "collection": self.rag_service.collection_name
            }

        except Exception as e:
            return {
                "error": f"Error finding similar documents: {str(e)}",
                "results": []
            }

    async def context_search(
        self,
        query: str,
        context_window: int = 3,
        k: int = 5
    ) -> Dict[str, Any]:
        """
        Search with expanded context from surrounding chunks

        Args:
            query: Search query
            context_window: Number of chunks before/after to include
            k: Number of primary results

        Returns:
            Results with expanded context
        """
        # Perform initial search
        initial_results = await self.search(query, k=k)

        # For each result, try to get surrounding chunks
        enhanced_results = []

        for result in initial_results["results"]:
            enhanced_result = result.copy()
            # Note: This is a simplified implementation
            # A production version would need chunk IDs and ordering
            enhanced_result["context_note"] = (
                f"Context window: {context_window} chunks "
                "(full implementation requires chunk ordering)"
            )
            enhanced_results.append(enhanced_result)

        return {
            "query": query,
            "context_window": context_window,
            "total_results": len(enhanced_results),
            "results": enhanced_results,
            "collection": self.rag_service.collection_name
        }
