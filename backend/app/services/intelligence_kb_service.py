"""
Intelligence KnowledgeBeast Service

Extends KnowledgeBeast integration for Research Hub intelligence features.
Provides specialized collections and methods for:
- Research findings indexing
- Validated hypotheses with debate context
- Evidence corpus management

Collection naming:
- project_{id}_findings - Research findings from agent runs
- project_{id}_hypotheses - Validated hypotheses with debate context
- project_{id}_evidence - Evidence corpus
"""

import logging
from typing import Any, Dict, List, Optional

from app.services.knowledgebeast_service import KNOWLEDGEBEAST_AVAILABLE

if KNOWLEDGEBEAST_AVAILABLE:
    from knowledgebeast.core.query_engine import HybridQueryEngine
    from knowledgebeast.core.repository import DocumentRepository

logger = logging.getLogger(__name__)


class IntelligenceKBService:
    """
    KnowledgeBeast service extension for Research Hub intelligence integration.

    Manages three specialized collections per project:
    - findings: Individual insights from research agent runs
    - hypotheses: Validated hypotheses with debate context and reasoning
    - evidence: Evidence corpus supporting/contradicting hypotheses

    The intelligence loop:
    Research → Findings → Hypotheses → Validation → Evidence → KnowledgeBase
    """

    # Collection suffixes for intelligence features
    COLLECTION_FINDINGS = "findings"
    COLLECTION_HYPOTHESES = "hypotheses"
    COLLECTION_EVIDENCE = "evidence"

    def __init__(
        self,
        project_id: int,
        db_path: Optional[str] = None,
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize Intelligence KB service for a project.

        Creates or connects to the three intelligence collections.

        Args:
            project_id: CommandCenter project ID
            db_path: Path to ChromaDB storage
            embedding_model: Embedding model name
        """
        if not KNOWLEDGEBEAST_AVAILABLE:
            raise ImportError(
                "KnowledgeBeast not installed. " "Install with: pip install knowledgebeast>=2.3.2"
            )

        self.project_id = project_id
        self.db_path = db_path
        self.embedding_model = embedding_model

        # Collection names
        self.findings_collection = f"project_{project_id}_{self.COLLECTION_FINDINGS}"
        self.hypotheses_collection = f"project_{project_id}_{self.COLLECTION_HYPOTHESES}"
        self.evidence_collection = f"project_{project_id}_{self.COLLECTION_EVIDENCE}"

        # Initialize repositories for each collection
        self._repositories: Dict[str, DocumentRepository] = {}
        self._query_engines: Dict[str, HybridQueryEngine] = {}

        logger.info(
            f"Initializing IntelligenceKBService for project {project_id} "
            f"(collections: findings, hypotheses, evidence)"
        )

    def _get_repository(self, collection_type: str) -> DocumentRepository:
        """Get or create repository for a collection type."""
        if collection_type not in self._repositories:
            self._repositories[collection_type] = DocumentRepository()
        return self._repositories[collection_type]

    def _get_query_engine(self, collection_type: str) -> HybridQueryEngine:
        """Get or create query engine for a collection type."""
        if collection_type not in self._query_engines:
            repo = self._get_repository(collection_type)
            self._query_engines[collection_type] = HybridQueryEngine(
                repo,
                model_name=self.embedding_model,
                alpha=0.7,
                cache_size=500,
            )
        return self._query_engines[collection_type]

    async def initialize_collections(self) -> Dict[str, bool]:
        """
        Initialize all intelligence collections for a project.

        Called when a project is created or when intelligence features
        are first enabled.

        Returns:
            Dict mapping collection name to initialization success
        """
        results = {}

        for collection_type in [
            self.COLLECTION_FINDINGS,
            self.COLLECTION_HYPOTHESES,
            self.COLLECTION_EVIDENCE,
        ]:
            try:
                # Initialize repository and query engine
                self._get_repository(collection_type)
                self._get_query_engine(collection_type)
                results[collection_type] = True
                logger.info(f"Initialized collection project_{self.project_id}_{collection_type}")
            except Exception as e:
                logger.error(f"Failed to initialize {collection_type}: {e}")
                results[collection_type] = False

        return results

    async def index_finding(
        self,
        finding_id: int,
        task_id: int,
        content: str,
        finding_type: str,
        agent_role: str,
        confidence: float,
        sources: Optional[List[str]] = None,
    ) -> str:
        """
        Index a research finding to the findings collection.

        Args:
            finding_id: Database finding ID
            task_id: Parent research task ID
            content: Finding content
            finding_type: Type (fact, claim, insight, question, recommendation)
            agent_role: Which agent produced this
            confidence: Confidence score (0-1)
            sources: Optional list of source URLs

        Returns:
            Document ID in the collection
        """
        doc_id = f"finding_{finding_id}"
        repo = self._get_repository(self.COLLECTION_FINDINGS)
        query_engine = self._get_query_engine(self.COLLECTION_FINDINGS)

        doc_data = {
            "name": f"Finding {finding_id}",
            "content": content,
            "path": f"task/{task_id}/finding/{finding_id}",
            "category": finding_type,
            "metadata": {
                "finding_id": finding_id,
                "task_id": task_id,
                "type": finding_type,
                "agent": agent_role,
                "confidence": confidence,
                "sources": sources or [],
            },
        }

        repo.add_document(doc_id, doc_data)

        # Index terms for keyword search
        terms = set(content.lower().split())
        for term in terms:
            if len(term) > 2:
                repo.index_term(term, doc_id)

        query_engine.refresh_embeddings()

        logger.debug(f"Indexed finding {finding_id} to project {self.project_id}")
        return doc_id

    async def index_validated_hypothesis(
        self,
        hypothesis_id: int,
        statement: str,
        category: str,
        status: str,
        validation_score: Optional[float],
        verdict: Optional[str],
        verdict_reasoning: Optional[str],
    ) -> str:
        """
        Index a validated hypothesis to the hypotheses collection.

        Called after a debate completes with a verdict.

        Args:
            hypothesis_id: Database hypothesis ID
            statement: Hypothesis statement
            category: Hypothesis category
            status: Current status (validated, invalidated, needs_more_data)
            validation_score: Final validation score
            verdict: Debate verdict
            verdict_reasoning: Reasoning behind the verdict

        Returns:
            Document ID in the collection
        """
        doc_id = f"hypothesis_{hypothesis_id}"
        repo = self._get_repository(self.COLLECTION_HYPOTHESES)
        query_engine = self._get_query_engine(self.COLLECTION_HYPOTHESES)

        # Build rich content for semantic search
        content = f"""
Hypothesis: {statement}
Verdict: {verdict or 'pending'}
Confidence: {validation_score or 'N/A'}
Reasoning: {verdict_reasoning or 'No reasoning available'}
        """.strip()

        doc_data = {
            "name": f"Hypothesis {hypothesis_id}",
            "content": content,
            "path": f"hypothesis/{hypothesis_id}",
            "category": category,
            "metadata": {
                "hypothesis_id": hypothesis_id,
                "category": category,
                "status": status,
                "validation_score": validation_score,
                "verdict": verdict,
            },
        }

        repo.add_document(doc_id, doc_data)

        # Index terms for keyword search
        terms = set(content.lower().split())
        for term in terms:
            if len(term) > 2:
                repo.index_term(term, doc_id)

        query_engine.refresh_embeddings()

        logger.debug(f"Indexed hypothesis {hypothesis_id} to project {self.project_id}")
        return doc_id

    async def index_evidence(
        self,
        evidence_id: int,
        hypothesis_id: int,
        content: str,
        source_type: str,
        stance: str,
        confidence: float,
        source_id: Optional[str] = None,
    ) -> str:
        """
        Index evidence to the evidence collection.

        Args:
            evidence_id: Database evidence ID
            hypothesis_id: Parent hypothesis ID
            content: Evidence content
            source_type: Source type (research_finding, knowledge_base, manual, external)
            stance: Stance (supporting, contradicting, neutral)
            confidence: Confidence score
            source_id: Optional source reference

        Returns:
            Document ID in the collection
        """
        doc_id = f"evidence_{evidence_id}"
        repo = self._get_repository(self.COLLECTION_EVIDENCE)
        query_engine = self._get_query_engine(self.COLLECTION_EVIDENCE)

        doc_data = {
            "name": f"Evidence {evidence_id}",
            "content": content,
            "path": f"hypothesis/{hypothesis_id}/evidence/{evidence_id}",
            "category": stance,
            "metadata": {
                "evidence_id": evidence_id,
                "hypothesis_id": hypothesis_id,
                "source_type": source_type,
                "stance": stance,
                "confidence": confidence,
                "source_id": source_id,
            },
        }

        repo.add_document(doc_id, doc_data)

        # Index terms
        terms = set(content.lower().split())
        for term in terms:
            if len(term) > 2:
                repo.index_term(term, doc_id)

        query_engine.refresh_embeddings()

        logger.debug(f"Indexed evidence {evidence_id} to project {self.project_id}")
        return doc_id

    async def query_for_evidence(
        self,
        hypothesis_statement: str,
        limit: int = 10,
    ) -> List[Dict[str, Any]]:
        """
        Search all collections for evidence relevant to a hypothesis.

        Used to suggest evidence when creating or validating a hypothesis.

        Args:
            hypothesis_statement: The hypothesis statement to find evidence for
            limit: Maximum results per collection

        Returns:
            Combined and ranked results from all collections
        """
        all_results = []
        per_collection_limit = max(1, limit // 3)

        for collection_type in [
            self.COLLECTION_FINDINGS,
            self.COLLECTION_HYPOTHESES,
            self.COLLECTION_EVIDENCE,
        ]:
            try:
                query_engine = self._get_query_engine(collection_type)
                raw_results, _ = query_engine.search_hybrid(
                    hypothesis_statement,
                    alpha=0.7,
                    top_k=per_collection_limit,
                )

                for doc_id, doc_data, score in raw_results:
                    all_results.append(
                        {
                            "content": doc_data.get("content", ""),
                            "metadata": doc_data.get("metadata", {}),
                            "score": float(score),
                            "category": doc_data.get("category"),
                            "source": doc_data.get("path"),
                            "collection": collection_type,
                        }
                    )
            except Exception as e:
                logger.warning(f"Failed to query {collection_type} for evidence: {e}")

        # Sort by score and limit
        all_results.sort(key=lambda x: x["score"], reverse=True)
        return all_results[:limit]

    async def get_collection_stats(self) -> Dict[str, Dict[str, Any]]:
        """
        Get statistics for all intelligence collections.

        Returns:
            Dict with stats for each collection
        """
        stats = {}

        for collection_type in [
            self.COLLECTION_FINDINGS,
            self.COLLECTION_HYPOTHESES,
            self.COLLECTION_EVIDENCE,
        ]:
            try:
                repo = self._get_repository(collection_type)
                query_engine = self._get_query_engine(collection_type)

                repo_stats = repo.get_stats()
                embedding_stats = query_engine.get_embedding_stats()

                stats[collection_type] = {
                    "document_count": repo_stats.get("documents", 0),
                    "term_count": repo_stats.get("terms", 0),
                    "cache_hit_rate": embedding_stats.get("hit_rate", 0.0),
                }
            except Exception as e:
                logger.warning(f"Failed to get stats for {collection_type}: {e}")
                stats[collection_type] = {"error": str(e)}

        return stats


async def initialize_project_intelligence_collections(project_id: int) -> bool:
    """
    Convenience function to initialize intelligence collections for a project.

    Call this when:
    - A new project is created
    - Intelligence features are enabled for an existing project

    Args:
        project_id: Project ID to initialize

    Returns:
        True if all collections initialized successfully
    """
    try:
        service = IntelligenceKBService(project_id)
        results = await service.initialize_collections()
        return all(results.values())
    except ImportError:
        logger.warning(
            f"KnowledgeBeast not available, skipping collection init for project {project_id}"
        )
        return False
    except Exception as e:
        logger.error(f"Failed to initialize intelligence collections: {e}")
        return False
