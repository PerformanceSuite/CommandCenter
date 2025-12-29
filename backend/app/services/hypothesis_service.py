"""
Hypothesis Service

Business logic for hypothesis management and validation.
Bridges the REST API to the ai_arena hypothesis module.
"""

import asyncio
import uuid
from datetime import datetime
from typing import Any

import structlog
from libs.ai_arena.hypothesis.registry import HypothesisRegistry
from libs.ai_arena.hypothesis.schema import (
    Hypothesis,
    HypothesisCategory,
    HypothesisCreate,
    HypothesisEvidence,
    HypothesisStatus,
    HypothesisUpdate,
)

from app.services.redis_service import redis_service

logger = structlog.get_logger(__name__)


class ValidationTaskStorage:
    """
    Redis-backed storage for validation tasks.
    Falls back to in-memory storage if Redis is unavailable.
    """

    PREFIX = "validation_task:"
    TTL = 86400  # 24 hours

    _memory_fallback: dict[str, Any] = {}

    @classmethod
    async def save(cls, task_id: str, data: dict[str, Any]) -> None:
        """Save validation task state."""
        try:
            if redis_service.is_available():
                await redis_service.set_json(
                    f"{cls.PREFIX}{task_id}",
                    data,
                    expire=cls.TTL,
                )
            else:
                cls._memory_fallback[task_id] = data
        except Exception as e:
            logger.warning("validation_task_save_failed", task_id=task_id, error=str(e))
            cls._memory_fallback[task_id] = data

    @classmethod
    async def get(cls, task_id: str) -> dict[str, Any] | None:
        """Get validation task state."""
        try:
            if redis_service.is_available():
                data = await redis_service.get_json(f"{cls.PREFIX}{task_id}")
                if data:
                    return data
        except Exception as e:
            logger.warning("validation_task_get_failed", task_id=task_id, error=str(e))

        return cls._memory_fallback.get(task_id)

    @classmethod
    async def update(cls, task_id: str, updates: dict[str, Any]) -> None:
        """Update validation task state."""
        data = await cls.get(task_id) or {}
        data.update(updates)
        await cls.save(task_id, data)


class HypothesisService:
    """
    Service layer for hypothesis operations.

    Uses an in-memory HypothesisRegistry for hypothesis storage.
    In production, this could be backed by a database.
    """

    # Shared registry instance (in-memory for now)
    _registry: HypothesisRegistry | None = None
    _active_validations: dict[str, asyncio.Task] = {}

    @classmethod
    def get_registry(cls) -> HypothesisRegistry:
        """Get or create the shared registry instance."""
        if cls._registry is None:
            cls._registry = HypothesisRegistry()
        return cls._registry

    def __init__(self):
        """Initialize the service."""
        self.registry = self.get_registry()

    async def list_hypotheses(
        self,
        status: HypothesisStatus | None = None,
        category: HypothesisCategory | None = None,
        limit: int = 20,
        skip: int = 0,
    ) -> tuple[list[Hypothesis], int]:
        """
        List hypotheses with filtering.

        Returns:
            Tuple of (hypotheses, total_count)
        """
        hypotheses = self.registry.get_prioritized(
            status=status,
            category=category,
        )
        total = len(hypotheses)
        return hypotheses[skip : skip + limit], total

    async def get_hypothesis(self, hypothesis_id: str) -> Hypothesis | None:
        """Get a single hypothesis by ID."""
        return self.registry.get(hypothesis_id)

    async def create_hypothesis(self, data: HypothesisCreate) -> Hypothesis:
        """Create a new hypothesis."""
        return self.registry.create(data)

    async def update_hypothesis(
        self, hypothesis_id: str, data: HypothesisUpdate
    ) -> Hypothesis | None:
        """Update an existing hypothesis."""
        return self.registry.update(hypothesis_id, data)

    async def delete_hypothesis(self, hypothesis_id: str) -> bool:
        """Delete a hypothesis."""
        return self.registry.delete(hypothesis_id)

    async def add_evidence(
        self, hypothesis_id: str, evidence: HypothesisEvidence
    ) -> Hypothesis | None:
        """Add evidence to a hypothesis."""
        return self.registry.add_evidence(hypothesis_id, evidence)

    async def get_statistics(self) -> dict[str, Any]:
        """Get dashboard statistics."""
        return self.registry.get_statistics()

    async def start_validation(
        self,
        hypothesis_id: str,
        max_rounds: int = 3,
        agents: list[str] | None = None,
    ) -> str:
        """
        Start async validation of a hypothesis.

        Returns:
            task_id for tracking progress
        """
        hypothesis = self.registry.get(hypothesis_id)
        if not hypothesis:
            raise ValueError(f"Hypothesis not found: {hypothesis_id}")

        task_id = f"val_{uuid.uuid4().hex[:12]}"

        # Initialize task state
        await ValidationTaskStorage.save(
            task_id,
            {
                "task_id": task_id,
                "hypothesis_id": hypothesis_id,
                "status": "running",
                "current_round": 0,
                "max_rounds": max_rounds,
                "responses_count": 0,
                "consensus_level": None,
                "started_at": datetime.utcnow().isoformat(),
                "completed_at": None,
                "error": None,
                "agents": agents or ["analyst", "researcher", "critic"],
            },
        )

        # Update hypothesis status
        self.registry.update_status(hypothesis_id, HypothesisStatus.VALIDATING)

        # Start background validation
        task = asyncio.create_task(self._run_validation(task_id, hypothesis, max_rounds, agents))
        self._active_validations[task_id] = task

        logger.info(
            "validation_started",
            task_id=task_id,
            hypothesis_id=hypothesis_id,
            max_rounds=max_rounds,
        )

        return task_id

    async def _run_validation(
        self,
        task_id: str,
        hypothesis: Hypothesis,
        max_rounds: int,
        agents: list[str] | None,
    ) -> None:
        """Run the actual validation (background task)."""
        try:
            # Import here to avoid circular imports
            from libs.ai_arena.hypothesis.validator import HypothesisValidator

            validator = HypothesisValidator()

            # Run validation with progress updates
            result = await validator.validate(
                hypothesis=hypothesis,
                max_rounds=max_rounds,
                progress_callback=lambda progress: asyncio.create_task(
                    self._update_progress(task_id, progress)
                ),
            )

            # Update final state with full debate result
            debate_result_dict = None
            if result.debate_result:
                debate_result_dict = result.debate_result.to_dict()

            await ValidationTaskStorage.update(
                task_id,
                {
                    "status": "completed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "result": {
                        "status": result.status.value,
                        "validation_score": result.validation_score,
                        "consensus_reached": result.consensus_reached,
                        "rounds_taken": result.rounds_taken,
                        "final_answer": result.final_answer,
                        "reasoning_summary": result.reasoning_summary,
                        "recommendation": result.recommendation,
                        "follow_up_questions": result.follow_up_questions,
                        "duration_seconds": result.duration_seconds,
                        "total_cost": result.total_cost,
                    },
                    "debate_result": debate_result_dict,
                },
            )

            # Update hypothesis with result
            hypothesis.status = result.status
            hypothesis.validation_score = result.validation_score
            hypothesis.validated_at = result.validated_at

            logger.info(
                "validation_completed",
                task_id=task_id,
                hypothesis_id=hypothesis.id,
                status=result.status.value,
            )

        except Exception as e:
            logger.error(
                "validation_failed",
                task_id=task_id,
                hypothesis_id=hypothesis.id,
                error=str(e),
            )

            await ValidationTaskStorage.update(
                task_id,
                {
                    "status": "failed",
                    "completed_at": datetime.utcnow().isoformat(),
                    "error": str(e),
                },
            )

            # Revert hypothesis status
            self.registry.update_status(hypothesis.id, HypothesisStatus.UNTESTED)

        finally:
            # Clean up active task reference
            self._active_validations.pop(task_id, None)

    async def _update_progress(self, task_id: str, progress: dict[str, Any]) -> None:
        """Update validation progress."""
        await ValidationTaskStorage.update(
            task_id,
            {
                "current_round": progress.get("current_round", 0),
                "responses_count": progress.get("responses_count", 0),
                "consensus_level": progress.get("consensus_level"),
            },
        )

    async def get_validation_status(self, task_id: str) -> dict[str, Any] | None:
        """Get current validation task status."""
        return await ValidationTaskStorage.get(task_id)

    async def get_validation_status_by_hypothesis(
        self, hypothesis_id: str
    ) -> dict[str, Any] | None:
        """Get validation status for a hypothesis (finds most recent task)."""
        # Check active validations first
        for tid, task in self._active_validations.items():
            state = await ValidationTaskStorage.get(tid)
            if state and state.get("hypothesis_id") == hypothesis_id:
                return state

        return None

    async def get_debate_result(self, task_id: str) -> dict[str, Any] | None:
        """Get the full debate result for a completed validation task."""
        state = await ValidationTaskStorage.get(task_id)
        if not state:
            return None

        # Return debate result if available
        return state.get("debate_result")

    async def list_all_evidence(
        self,
        supports: bool | None = None,
        source_filter: str | None = None,
        min_confidence: int | None = None,
        limit: int = 50,
        skip: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """
        List all evidence across all hypotheses.

        Returns:
            Tuple of (evidence_items, total_count)
        """
        all_evidence: list[dict[str, Any]] = []

        # Collect evidence from all hypotheses
        for hypothesis in self.registry._hypotheses.values():
            for evidence in hypothesis.evidence:
                evidence_dict = {
                    "id": evidence.id,
                    "hypothesis_id": hypothesis.id,
                    "hypothesis_statement": hypothesis.statement[:100],
                    "source": evidence.source,
                    "content": evidence.content,
                    "supports": evidence.supports,
                    "confidence": evidence.confidence,
                    "collected_at": evidence.collected_at.isoformat(),
                    "collected_by": evidence.collected_by,
                    "metadata": evidence.metadata,
                }
                all_evidence.append(evidence_dict)

        # Apply filters
        if supports is not None:
            all_evidence = [e for e in all_evidence if e["supports"] == supports]
        if source_filter:
            source_lower = source_filter.lower()
            all_evidence = [e for e in all_evidence if source_lower in e["source"].lower()]
        if min_confidence is not None:
            all_evidence = [e for e in all_evidence if e["confidence"] >= min_confidence]

        # Sort by collected_at descending (most recent first)
        all_evidence.sort(key=lambda e: e["collected_at"], reverse=True)

        total = len(all_evidence)
        return all_evidence[skip : skip + limit], total

    async def get_evidence_stats(self) -> dict[str, Any]:
        """Get statistics about all evidence."""
        supporting = 0
        contradicting = 0
        total_confidence = 0
        count = 0
        by_source: dict[str, int] = {}
        by_collector: dict[str, int] = {}

        for hypothesis in self.registry._hypotheses.values():
            for evidence in hypothesis.evidence:
                count += 1
                total_confidence += evidence.confidence
                if evidence.supports:
                    supporting += 1
                else:
                    contradicting += 1

                # Count by source domain/type
                source_key = self._extract_source_type(evidence.source)
                by_source[source_key] = by_source.get(source_key, 0) + 1

                # Count by collector
                by_collector[evidence.collected_by] = by_collector.get(evidence.collected_by, 0) + 1

        return {
            "total": count,
            "supporting": supporting,
            "contradicting": contradicting,
            "average_confidence": round(total_confidence / count, 1) if count > 0 else 0,
            "by_source_type": by_source,
            "by_collector": by_collector,
        }

    def _extract_source_type(self, source: str) -> str:
        """Extract source type from source string."""
        source_lower = source.lower()
        if "interview" in source_lower:
            return "interview"
        if "survey" in source_lower:
            return "survey"
        if any(domain in source_lower for domain in ["http://", "https://", ".com", ".org"]):
            return "web"
        if "report" in source_lower or "study" in source_lower:
            return "research"
        if "ai_arena" in source_lower or "debate" in source_lower:
            return "ai_debate"
        return "other"


# Singleton instance
hypothesis_service = HypothesisService()
