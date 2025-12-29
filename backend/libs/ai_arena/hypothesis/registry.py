"""
Hypothesis Registry

Manages a collection of hypotheses, providing CRUD operations,
filtering, and prioritization capabilities.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any

import structlog

from .schema import (
    Hypothesis,
    HypothesisCategory,
    HypothesisCreate,
    HypothesisEvidence,
    HypothesisPriority,
    HypothesisStatus,
    HypothesisUpdate,
)

logger = structlog.get_logger(__name__)


class HypothesisRegistry:
    """
    Registry for managing hypothesis lifecycle.

    Provides:
    - CRUD operations for hypotheses
    - Filtering and search
    - Priority-based ordering
    - Status tracking

    Example:
        registry = HypothesisRegistry()

        # Create hypothesis
        hypothesis = registry.create(HypothesisCreate(
            statement="Enterprise customers will pay $2K/month",
            category=HypothesisCategory.PRICING,
            impact=ImpactLevel.HIGH,
            risk=RiskLevel.HIGH,
            testability=TestabilityLevel.MEDIUM,
            success_criteria="5 of 10 prospects confirm"
        ))

        # Get prioritized list
        prioritized = registry.get_prioritized()
        for h in prioritized:
            print(f"{h.priority.score}: {h.statement}")
    """

    def __init__(self, storage_backend: Any | None = None):
        """
        Initialize the registry.

        Args:
            storage_backend: Optional persistent storage backend.
                            If None, uses in-memory storage.
        """
        self._hypotheses: dict[str, Hypothesis] = {}
        self._storage = storage_backend

    def create(self, data: HypothesisCreate) -> Hypothesis:
        """
        Create a new hypothesis.

        Args:
            data: Hypothesis creation data

        Returns:
            Created Hypothesis instance
        """
        hypothesis_id = f"hyp_{uuid.uuid4().hex[:12]}"

        hypothesis = Hypothesis(
            id=hypothesis_id,
            statement=data.statement,
            category=data.category,
            impact=data.impact,
            risk=data.risk,
            testability=data.testability,
            success_criteria=data.success_criteria,
            context=data.context,
            tags=data.tags,
            metadata=data.metadata,
        )

        self._hypotheses[hypothesis_id] = hypothesis

        logger.info(
            "hypothesis_created",
            hypothesis_id=hypothesis_id,
            category=data.category.value,
            priority_score=hypothesis.priority.score if hypothesis.priority else 0,
        )

        return hypothesis

    def get(self, hypothesis_id: str) -> Hypothesis | None:
        """
        Get a hypothesis by ID.

        Args:
            hypothesis_id: The hypothesis ID

        Returns:
            Hypothesis if found, None otherwise
        """
        return self._hypotheses.get(hypothesis_id)

    def update(self, hypothesis_id: str, data: HypothesisUpdate) -> Hypothesis | None:
        """
        Update an existing hypothesis.

        Args:
            hypothesis_id: The hypothesis ID
            data: Fields to update

        Returns:
            Updated Hypothesis if found, None otherwise
        """
        hypothesis = self._hypotheses.get(hypothesis_id)
        if not hypothesis:
            return None

        # Update only provided fields
        update_data = data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if value is not None:
                setattr(hypothesis, field, value)

        # Recalculate priority if relevant fields changed
        if any(f in update_data for f in ["impact", "risk", "testability"]):
            hypothesis.priority = HypothesisPriority.calculate(
                hypothesis.impact, hypothesis.risk, hypothesis.testability
            )

        hypothesis.updated_at = datetime.utcnow()

        logger.info(
            "hypothesis_updated",
            hypothesis_id=hypothesis_id,
            updated_fields=list(update_data.keys()),
        )

        return hypothesis

    def delete(self, hypothesis_id: str) -> bool:
        """
        Delete a hypothesis.

        Args:
            hypothesis_id: The hypothesis ID

        Returns:
            True if deleted, False if not found
        """
        if hypothesis_id in self._hypotheses:
            del self._hypotheses[hypothesis_id]
            logger.info("hypothesis_deleted", hypothesis_id=hypothesis_id)
            return True
        return False

    def list(
        self,
        status: HypothesisStatus | None = None,
        category: HypothesisCategory | None = None,
        tags: list[str] | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> list[Hypothesis]:
        """
        List hypotheses with optional filtering.

        Args:
            status: Filter by status
            category: Filter by category
            tags: Filter by tags (any match)
            limit: Maximum results
            offset: Pagination offset

        Returns:
            List of matching hypotheses
        """
        results = list(self._hypotheses.values())

        # Apply filters
        if status:
            results = [h for h in results if h.status == status]
        if category:
            results = [h for h in results if h.category == category]
        if tags:
            results = [h for h in results if any(t in h.tags for t in tags)]

        # Apply pagination
        results = results[offset:]
        if limit:
            results = results[:limit]

        return results

    def get_prioritized(
        self,
        status: HypothesisStatus | None = None,
        category: HypothesisCategory | None = None,
        limit: int | None = None,
    ) -> list[Hypothesis]:
        """
        Get hypotheses sorted by priority score (highest first).

        Args:
            status: Filter by status
            category: Filter by category
            limit: Maximum results

        Returns:
            Priority-sorted list of hypotheses
        """
        results = self.list(status=status, category=category)

        # Sort by priority score (descending)
        results.sort(
            key=lambda h: h.priority.score if h.priority else 0,
            reverse=True,
        )

        if limit:
            results = results[:limit]

        return results

    def get_untested(self, limit: int | None = None) -> list[Hypothesis]:
        """Get untested hypotheses, prioritized."""
        return self.get_prioritized(status=HypothesisStatus.UNTESTED, limit=limit)

    def get_needs_data(self, limit: int | None = None) -> list[Hypothesis]:
        """Get hypotheses that need more data, prioritized."""
        return self.get_prioritized(status=HypothesisStatus.NEEDS_MORE_DATA, limit=limit)

    def get_validated(self, limit: int | None = None) -> list[Hypothesis]:
        """Get validated hypotheses."""
        return self.list(status=HypothesisStatus.VALIDATED, limit=limit)

    def get_invalidated(self, limit: int | None = None) -> list[Hypothesis]:
        """Get invalidated hypotheses."""
        return self.list(status=HypothesisStatus.INVALIDATED, limit=limit)

    def get_by_category(
        self, category: HypothesisCategory, limit: int | None = None
    ) -> list[Hypothesis]:
        """Get hypotheses by category, prioritized."""
        return self.get_prioritized(category=category, limit=limit)

    def add_evidence(self, hypothesis_id: str, evidence: HypothesisEvidence) -> Hypothesis | None:
        """
        Add evidence to a hypothesis.

        Args:
            hypothesis_id: The hypothesis ID
            evidence: Evidence to add

        Returns:
            Updated Hypothesis if found, None otherwise
        """
        hypothesis = self._hypotheses.get(hypothesis_id)
        if not hypothesis:
            return None

        hypothesis.add_evidence(evidence)

        logger.info(
            "hypothesis_evidence_added",
            hypothesis_id=hypothesis_id,
            evidence_id=evidence.id,
            supports=evidence.supports,
        )

        return hypothesis

    def update_status(self, hypothesis_id: str, status: HypothesisStatus) -> Hypothesis | None:
        """
        Update hypothesis status.

        Args:
            hypothesis_id: The hypothesis ID
            status: New status

        Returns:
            Updated Hypothesis if found, None otherwise
        """
        hypothesis = self._hypotheses.get(hypothesis_id)
        if not hypothesis:
            return None

        old_status = hypothesis.status
        hypothesis.status = status
        hypothesis.updated_at = datetime.utcnow()

        if status in (HypothesisStatus.VALIDATED, HypothesisStatus.INVALIDATED):
            hypothesis.validated_at = datetime.utcnow()

        logger.info(
            "hypothesis_status_updated",
            hypothesis_id=hypothesis_id,
            old_status=old_status.value,
            new_status=status.value,
        )

        return hypothesis

    def search(self, query: str, limit: int = 10) -> list[Hypothesis]:
        """
        Search hypotheses by statement text.

        Args:
            query: Search query
            limit: Maximum results

        Returns:
            Matching hypotheses
        """
        query_lower = query.lower()
        results = [
            h
            for h in self._hypotheses.values()
            if query_lower in h.statement.lower()
            or query_lower in h.success_criteria.lower()
            or (h.context and query_lower in h.context.lower())
        ]
        return results[:limit]

    def get_statistics(self) -> dict[str, Any]:
        """
        Get registry statistics.

        Returns:
            Dictionary with counts and metrics
        """
        total = len(self._hypotheses)
        by_status = {}
        by_category = {}

        for h in self._hypotheses.values():
            # Count by status
            status_key = h.status.value
            by_status[status_key] = by_status.get(status_key, 0) + 1

            # Count by category
            category_key = h.category.value
            by_category[category_key] = by_category.get(category_key, 0) + 1

        # Calculate average validation score
        scored = [h.validation_score for h in self._hypotheses.values() if h.validation_score]
        avg_score = sum(scored) / len(scored) if scored else 0.0

        return {
            "total": total,
            "by_status": by_status,
            "by_category": by_category,
            "average_validation_score": round(avg_score, 1),
            "validated_count": by_status.get("validated", 0),
            "invalidated_count": by_status.get("invalidated", 0),
            "needs_data_count": by_status.get("needs_more_data", 0),
            "untested_count": by_status.get("untested", 0),
        }

    def export(self) -> list[dict[str, Any]]:
        """
        Export all hypotheses as dictionaries.

        Returns:
            List of hypothesis dictionaries
        """
        return [h.to_dict() for h in self._hypotheses.values()]

    def import_hypotheses(self, data: list[dict[str, Any]]) -> int:
        """
        Import hypotheses from dictionaries.

        Args:
            data: List of hypothesis dictionaries

        Returns:
            Number of hypotheses imported
        """
        count = 0
        for item in data:
            try:
                hypothesis = Hypothesis.from_dict(item)
                self._hypotheses[hypothesis.id] = hypothesis
                count += 1
            except Exception as e:
                logger.warning("hypothesis_import_failed", error=str(e), data=item)

        logger.info("hypotheses_imported", count=count)
        return count

    def clear(self) -> None:
        """Clear all hypotheses from registry."""
        self._hypotheses.clear()
        logger.info("hypothesis_registry_cleared")

    def __len__(self) -> int:
        """Get total number of hypotheses."""
        return len(self._hypotheses)

    def __contains__(self, hypothesis_id: str) -> bool:
        """Check if hypothesis exists."""
        return hypothesis_id in self._hypotheses
