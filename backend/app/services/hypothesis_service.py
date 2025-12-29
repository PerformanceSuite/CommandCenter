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
from libs.ai_arena.hypothesis.schema import Hypothesis, HypothesisCategory, HypothesisStatus

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
        offset: int = 0,
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
        return hypotheses[offset : offset + limit], total

    async def get_hypothesis(self, hypothesis_id: str) -> Hypothesis | None:
        """Get a single hypothesis by ID."""
        return self.registry.get(hypothesis_id)

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

            # Update final state
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


# Singleton instance
hypothesis_service = HypothesisService()
