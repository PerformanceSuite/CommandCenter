"""
Hypothesis Evidence Storage

Integrates hypothesis validation with KnowledgeBeast for persistent
evidence storage and retrieval.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import structlog

from .schema import Hypothesis, HypothesisCategory, HypothesisEvidence, HypothesisValidationResult

if TYPE_CHECKING:
    from app.services.knowledgebeast_service import KnowledgeBeastService

logger = structlog.get_logger(__name__)


# Evidence document category
EVIDENCE_CATEGORY = "hypothesis_evidence"


class HypothesisEvidenceStorage:
    """
    Stores hypothesis evidence in KnowledgeBeast for RAG retrieval.

    This enables:
    - Persistent evidence storage across sessions
    - Semantic search over collected evidence
    - Evidence reuse across related hypotheses
    - Historical tracking of validation findings

    Example:
        from app.services.knowledgebeast_service import KnowledgeBeastService

        kb_service = KnowledgeBeastService(project_id=1)
        storage = HypothesisEvidenceStorage(kb_service)

        # Store evidence from validation
        await storage.store_evidence(hypothesis, result)

        # Query related evidence
        evidence = await storage.query_related_evidence(
            "pricing for compliance products"
        )
    """

    def __init__(
        self,
        kb_service: KnowledgeBeastService,
        category: str = EVIDENCE_CATEGORY,
    ):
        """
        Initialize the evidence storage.

        Args:
            kb_service: KnowledgeBeast service instance
            category: Category for evidence documents (default: 'hypothesis_evidence')
        """
        self._kb = kb_service
        self._category = category

    async def store_evidence(
        self,
        hypothesis: Hypothesis,
        result: HypothesisValidationResult | None = None,
    ) -> int:
        """
        Store hypothesis evidence in KnowledgeBeast.

        Stores:
        - Individual evidence items
        - Debate summaries (if result provided)
        - Agent reasoning (if result provided)

        Args:
            hypothesis: Hypothesis with evidence
            result: Optional validation result with additional findings

        Returns:
            Number of evidence documents stored
        """
        stored_count = 0

        # Store individual evidence items
        for evidence in hypothesis.evidence:
            try:
                doc_count = await self._store_single_evidence(hypothesis, evidence)
                stored_count += doc_count
            except Exception as e:
                logger.warning(
                    "evidence_storage_failed",
                    hypothesis_id=hypothesis.id,
                    evidence_id=evidence.id,
                    error=str(e),
                )

        # Store validation result summary if provided
        if result:
            try:
                doc_count = await self._store_validation_summary(hypothesis, result)
                stored_count += doc_count
            except Exception as e:
                logger.warning(
                    "validation_summary_storage_failed",
                    hypothesis_id=hypothesis.id,
                    error=str(e),
                )

        logger.info(
            "hypothesis_evidence_stored",
            hypothesis_id=hypothesis.id,
            documents_stored=stored_count,
        )

        return stored_count

    async def _store_single_evidence(
        self,
        hypothesis: Hypothesis,
        evidence: HypothesisEvidence,
    ) -> int:
        """Store a single evidence item."""
        content = self._format_evidence_content(hypothesis, evidence)

        metadata = {
            "title": f"Evidence: {hypothesis.statement[:50]}...",
            "category": self._category,
            "source": f"hypothesis:{hypothesis.id}:evidence:{evidence.id}",
            "hypothesis_id": hypothesis.id,
            "hypothesis_category": hypothesis.category.value,
            "evidence_id": evidence.id,
            "supports_hypothesis": evidence.supports,
            "confidence": evidence.confidence,
            "collected_at": evidence.collected_at.isoformat(),
            "collected_by": evidence.collected_by,
            "document_type": "evidence",
        }

        return await self._kb.add_document(content, metadata)

    async def _store_validation_summary(
        self,
        hypothesis: Hypothesis,
        result: HypothesisValidationResult,
    ) -> int:
        """Store validation result summary."""
        content = self._format_validation_summary(hypothesis, result)

        metadata = {
            "title": f"Validation: {hypothesis.statement[:50]}...",
            "category": self._category,
            "source": f"hypothesis:{hypothesis.id}:validation:{result.debate_id}",
            "hypothesis_id": hypothesis.id,
            "hypothesis_category": hypothesis.category.value,
            "validation_status": result.status.value,
            "validation_score": result.validation_score,
            "consensus_reached": result.consensus_reached,
            "validated_at": result.validated_at.isoformat(),
            "document_type": "validation_summary",
        }

        return await self._kb.add_document(content, metadata)

    def _format_evidence_content(
        self,
        hypothesis: Hypothesis,
        evidence: HypothesisEvidence,
    ) -> str:
        """Format evidence for storage."""
        support_str = "SUPPORTS" if evidence.supports else "CONTRADICTS"

        return f"""# Hypothesis Evidence

## Hypothesis
{hypothesis.statement}

## Category
{hypothesis.category.value}

## Evidence ({support_str})

**Source:** {evidence.source}
**Confidence:** {evidence.confidence}%
**Collected by:** {evidence.collected_by}

### Content
{evidence.content}

### Success Criteria
{hypothesis.success_criteria}

### Tags
{', '.join(hypothesis.tags) if hypothesis.tags else 'None'}
"""

    def _format_validation_summary(
        self,
        hypothesis: Hypothesis,
        result: HypothesisValidationResult,
    ) -> str:
        """Format validation summary for storage."""
        return f"""# Hypothesis Validation Summary

## Hypothesis
{hypothesis.statement}

## Category
{hypothesis.category.value}

## Validation Result
**Status:** {result.status.value}
**Confidence:** {result.validation_score:.1f}%
**Consensus Reached:** {'Yes' if result.consensus_reached else 'No'}
**Debate Rounds:** {result.rounds_taken}

## Final Answer
{result.final_answer}

## Reasoning Summary
{result.reasoning_summary}

## Recommendation
{result.recommendation}

## Follow-up Questions
{chr(10).join(f'- {q}' for q in result.follow_up_questions) if result.follow_up_questions else 'None identified'}

## Success Criteria
{hypothesis.success_criteria}

## Metadata
- Debate ID: {result.debate_id}
- Duration: {result.duration_seconds:.1f} seconds
- Cost: ${result.total_cost:.4f}
- Validated: {result.validated_at.isoformat()}
"""

    async def query_related_evidence(
        self,
        query: str,
        hypothesis_category: HypothesisCategory | None = None,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Query for evidence related to a topic.

        Args:
            query: Search query
            hypothesis_category: Optional category filter
            limit: Maximum results

        Returns:
            List of relevant evidence documents
        """
        try:
            results = await self._kb.query(
                question=query,
                category=self._category,
                k=limit * 2,  # Fetch more for filtering
                mode="hybrid",
            )

            # Filter by category if specified
            if hypothesis_category:
                results = [
                    r
                    for r in results
                    if r.get("metadata", {}).get("hypothesis_category") == hypothesis_category.value
                ]

            return results[:limit]

        except Exception as e:
            logger.error(
                "evidence_query_failed",
                query=query[:100],
                error=str(e),
            )
            return []

    async def get_hypothesis_evidence(
        self,
        hypothesis_id: str,
        document_type: str | None = None,
    ) -> list[dict[str, Any]]:
        """
        Get all stored evidence for a specific hypothesis.

        Args:
            hypothesis_id: The hypothesis ID
            document_type: Optional filter ('evidence' or 'validation_summary')

        Returns:
            List of evidence documents
        """
        try:
            # Query by hypothesis ID
            results = await self._kb.query(
                question=f"hypothesis {hypothesis_id}",
                category=self._category,
                k=50,  # Get all evidence
                mode="keyword",  # Use keyword for ID matching
            )

            # Filter to matching hypothesis
            results = [
                r for r in results if r.get("metadata", {}).get("hypothesis_id") == hypothesis_id
            ]

            # Filter by document type if specified
            if document_type:
                results = [
                    r
                    for r in results
                    if r.get("metadata", {}).get("document_type") == document_type
                ]

            return results

        except Exception as e:
            logger.error(
                "hypothesis_evidence_fetch_failed",
                hypothesis_id=hypothesis_id,
                error=str(e),
            )
            return []

    async def find_similar_hypotheses(
        self,
        hypothesis: Hypothesis,
        limit: int = 5,
    ) -> list[dict[str, Any]]:
        """
        Find evidence from similar hypotheses.

        Useful for:
        - Pre-populating evidence for new hypotheses
        - Finding related research
        - Identifying patterns across hypotheses

        Args:
            hypothesis: Current hypothesis
            limit: Maximum results

        Returns:
            Evidence from similar hypotheses
        """
        # Build query from hypothesis details
        query = f"{hypothesis.statement} {hypothesis.category.value} {hypothesis.success_criteria}"

        return await self.query_related_evidence(
            query=query,
            hypothesis_category=hypothesis.category,
            limit=limit,
        )

    async def get_category_summary(
        self,
        category: HypothesisCategory,
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """
        Get recent evidence for a hypothesis category.

        Args:
            category: Hypothesis category
            limit: Maximum results

        Returns:
            Recent evidence in the category
        """
        return await self.query_related_evidence(
            query=f"{category.value} hypothesis validation evidence",
            hypothesis_category=category,
            limit=limit,
        )

    async def delete_hypothesis_evidence(self, hypothesis_id: str) -> bool:
        """
        Delete all stored evidence for a hypothesis.

        Args:
            hypothesis_id: Hypothesis ID

        Returns:
            True if deletion succeeded
        """
        try:
            source_pattern = f"hypothesis:{hypothesis_id}"
            return await self._kb.delete_by_source(source_pattern)
        except Exception as e:
            logger.error(
                "hypothesis_evidence_deletion_failed",
                hypothesis_id=hypothesis_id,
                error=str(e),
            )
            return False


async def create_evidence_storage(project_id: int = 1) -> HypothesisEvidenceStorage:
    """
    Create an evidence storage instance.

    Args:
        project_id: CommandCenter project ID for KnowledgeBeast

    Returns:
        Configured HypothesisEvidenceStorage
    """
    try:
        from app.services.knowledgebeast_service import KnowledgeBeastService

        kb_service = KnowledgeBeastService(project_id=project_id)
        return HypothesisEvidenceStorage(kb_service)
    except ImportError as e:
        logger.warning(
            "knowledgebeast_not_available",
            error=str(e),
        )
        raise
