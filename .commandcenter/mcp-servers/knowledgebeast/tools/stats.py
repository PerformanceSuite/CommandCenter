"""
Knowledge Statistics Tools

Tools for getting statistics and insights about the knowledge base.
"""

import sys
from pathlib import Path
from typing import Any, Dict, List

# Add backend to path
backend_path = Path(__file__).parent.parent.parent.parent.parent / "backend"
sys.path.insert(0, str(backend_path))

from app.services.rag_service import RAGService


class KnowledgeStatistics:
    """
    Knowledge statistics tools for KnowledgeBeast

    Provides analytics and statistics about the knowledge base:
    - Overall statistics
    - Category breakdown
    - Source statistics
    - Collection information
    """

    def __init__(self, rag_service: RAGService):
        """
        Initialize knowledge statistics tools

        Args:
            rag_service: RAG service instance
        """
        self.rag_service = rag_service

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get comprehensive knowledge base statistics

        Returns:
            Statistics dictionary
        """
        stats = await self.rag_service.get_statistics()

        # Enhance with additional information
        try:
            # Get total unique sources
            results = self.rag_service.vectorstore.get()
            if results and results.get("metadatas"):
                sources = set(
                    m.get("source") for m in results["metadatas"]
                    if m.get("source")
                )
                stats["total_documents"] = len(sources)
            else:
                stats["total_documents"] = 0

        except Exception:
            stats["total_documents"] = 0

        return stats

    async def get_category_stats(self) -> Dict[str, Any]:
        """
        Get detailed statistics per category

        Returns:
            Category statistics
        """
        try:
            results = self.rag_service.vectorstore.get()

            if not results or not results.get("metadatas"):
                return {
                    "total_categories": 0,
                    "categories": {}
                }

            # Aggregate by category
            category_stats = {}

            for metadata in results["metadatas"]:
                category = metadata.get("category", "uncategorized")

                if category not in category_stats:
                    category_stats[category] = {
                        "chunks": 0,
                        "sources": set()
                    }

                category_stats[category]["chunks"] += 1
                if metadata.get("source"):
                    category_stats[category]["sources"].add(metadata["source"])

            # Convert sets to counts
            for category in category_stats:
                category_stats[category]["documents"] = len(category_stats[category]["sources"])
                category_stats[category]["sources"] = len(category_stats[category]["sources"])

            return {
                "total_categories": len(category_stats),
                "categories": category_stats,
                "collection": self.rag_service.collection_name
            }

        except Exception as e:
            return {
                "error": f"Error getting category statistics: {str(e)}",
                "total_categories": 0,
                "categories": {}
            }

    async def get_source_stats(self, source: str) -> Dict[str, Any]:
        """
        Get statistics for a specific source

        Args:
            source: Source identifier

        Returns:
            Source statistics
        """
        try:
            results = self.rag_service.vectorstore.get(
                where={"source": source}
            )

            if not results or not results.get("ids"):
                return {
                    "source": source,
                    "found": False,
                    "error": "Source not found"
                }

            # Calculate statistics
            total_chunks = len(results["ids"])
            total_chars = sum(len(doc) for doc in results.get("documents", []))

            return {
                "source": source,
                "found": True,
                "total_chunks": total_chunks,
                "total_characters": total_chars,
                "avg_chunk_size": total_chars // total_chunks if total_chunks > 0 else 0,
                "metadata": results["metadatas"][0] if results["metadatas"] else {},
                "collection": self.rag_service.collection_name
            }

        except Exception as e:
            return {
                "source": source,
                "found": False,
                "error": str(e)
            }

    async def get_collection_info(self) -> Dict[str, Any]:
        """
        Get information about the current collection

        Returns:
            Collection information
        """
        stats = await self.get_statistics()

        return {
            "collection_name": self.rag_service.collection_name,
            "db_path": self.rag_service.db_path,
            "embedding_model": self.rag_service.embedding_model_name,
            "total_chunks": stats.get("total_chunks", 0),
            "total_documents": stats.get("total_documents", 0),
            "categories": list(stats.get("categories", {}).keys())
        }

    async def get_top_sources(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get top sources by chunk count

        Args:
            limit: Number of top sources to return

        Returns:
            List of top sources with statistics
        """
        try:
            results = self.rag_service.vectorstore.get()

            if not results or not results.get("metadatas"):
                return []

            # Count chunks per source
            source_counts = {}

            for metadata in results["metadatas"]:
                source = metadata.get("source", "unknown")
                if source not in source_counts:
                    source_counts[source] = {
                        "source": source,
                        "chunks": 0,
                        "category": metadata.get("category", "unknown")
                    }
                source_counts[source]["chunks"] += 1

            # Sort and limit
            top_sources = sorted(
                source_counts.values(),
                key=lambda x: x["chunks"],
                reverse=True
            )[:limit]

            return top_sources

        except Exception as e:
            print(f"Error getting top sources: {e}")
            return []

    async def get_embedding_stats(self) -> Dict[str, Any]:
        """
        Get embedding model statistics

        Returns:
            Embedding model information
        """
        return {
            "model_name": self.rag_service.embedding_model_name,
            "model_type": "HuggingFace Sentence Transformers",
            "local_processing": True,
            "api_costs": "None (local model)",
            "collection": self.rag_service.collection_name
        }

    async def get_health_check(self) -> Dict[str, Any]:
        """
        Perform health check on the knowledge base

        Returns:
            Health status
        """
        try:
            # Try to get basic stats
            stats = await self.rag_service.get_statistics()

            # Check if vectorstore is accessible
            _ = self.rag_service.vectorstore.get()

            return {
                "healthy": True,
                "collection": self.rag_service.collection_name,
                "total_chunks": stats.get("total_chunks", 0),
                "embedding_model": self.rag_service.embedding_model_name,
                "db_path": self.rag_service.db_path,
                "message": "Knowledge base is healthy and accessible"
            }

        except Exception as e:
            return {
                "healthy": False,
                "error": str(e),
                "collection": self.rag_service.collection_name,
                "message": "Knowledge base health check failed"
            }
