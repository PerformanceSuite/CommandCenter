"""
Hypothesis Validation Events

NATS event schemas and publisher for hypothesis validation progress.
Enables real-time tracking of validation workflows.

Subject Namespace:
    hypothesis.validation.started     # Validation started
    hypothesis.validation.round       # Debate round completed
    hypothesis.validation.completed   # Validation completed
    hypothesis.validation.failed      # Validation failed
    hypothesis.evidence.added         # New evidence added
    hypothesis.status.changed         # Hypothesis status changed
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import UUID

import structlog
from pydantic import BaseModel, Field

from .schema import (
    HypothesisCategory,
    HypothesisEvidence,
    HypothesisStatus,
    HypothesisValidationResult,
)

if TYPE_CHECKING:
    from app.nats_client import NATSClient

logger = structlog.get_logger(__name__)


# Event Schemas


class HypothesisValidationStartedEvent(BaseModel):
    """Event published when hypothesis validation starts.

    Subject: hypothesis.validation.started
    Published by: HypothesisValidator.validate()
    Consumed by: UI dashboards, progress trackers
    """

    validation_id: str = Field(..., description="Unique validation ID")
    hypothesis_id: str = Field(..., description="Hypothesis being validated")
    hypothesis_statement: str = Field(..., description="Hypothesis statement")
    category: HypothesisCategory = Field(..., description="Hypothesis category")
    agent_count: int = Field(..., description="Number of agents in debate")
    max_rounds: int = Field(..., description="Maximum debate rounds")
    correlation_id: UUID | None = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HypothesisDebateRoundEvent(BaseModel):
    """Event published after each debate round.

    Subject: hypothesis.validation.round
    Published by: HypothesisValidator during debate
    Consumed by: UI for real-time progress updates
    """

    validation_id: str = Field(..., description="Validation ID")
    hypothesis_id: str = Field(..., description="Hypothesis being validated")
    round_number: int = Field(..., description="Current round (0-indexed)")
    total_rounds: int = Field(..., description="Maximum rounds")
    responses_count: int = Field(..., description="Number of agent responses")
    consensus_level: str | None = Field(None, description="Current consensus level")
    average_confidence: float = Field(..., description="Average agent confidence")
    correlation_id: UUID | None = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HypothesisValidationCompletedEvent(BaseModel):
    """Event published when hypothesis validation completes.

    Subject: hypothesis.validation.completed
    Published by: HypothesisValidator.validate()
    Consumed by: UI dashboards, notification systems
    """

    validation_id: str = Field(..., description="Validation ID")
    hypothesis_id: str = Field(..., description="Hypothesis validated")
    status: HypothesisStatus = Field(..., description="Final validation status")
    validation_score: float = Field(..., description="Validation confidence score")
    consensus_reached: bool = Field(..., description="Whether consensus was reached")
    rounds_taken: int = Field(..., description="Number of rounds completed")
    final_answer: str = Field(..., description="Summarized answer")
    recommendation: str = Field(..., description="Action recommendation")
    total_cost: float = Field(..., description="Total API cost")
    duration_seconds: float = Field(..., description="Validation duration")
    correlation_id: UUID | None = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HypothesisValidationFailedEvent(BaseModel):
    """Event published when hypothesis validation fails.

    Subject: hypothesis.validation.failed
    Published by: HypothesisValidator on error
    Consumed by: Error tracking, retry systems
    """

    validation_id: str = Field(..., description="Validation ID")
    hypothesis_id: str = Field(..., description="Hypothesis that failed validation")
    error_type: str = Field(..., description="Error type/class name")
    error_message: str = Field(..., description="Error description")
    rounds_completed: int = Field(default=0, description="Rounds completed before failure")
    correlation_id: UUID | None = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HypothesisEvidenceAddedEvent(BaseModel):
    """Event published when evidence is added to a hypothesis.

    Subject: hypothesis.evidence.added
    Published by: HypothesisRegistry.add_evidence() or HypothesisValidator
    Consumed by: Evidence tracking, knowledge base updates
    """

    hypothesis_id: str = Field(..., description="Hypothesis ID")
    evidence_id: str = Field(..., description="New evidence ID")
    source: str = Field(..., description="Evidence source")
    supports: bool = Field(..., description="Whether evidence supports hypothesis")
    confidence: int = Field(..., description="Evidence confidence (0-100)")
    correlation_id: UUID | None = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class HypothesisStatusChangedEvent(BaseModel):
    """Event published when hypothesis status changes.

    Subject: hypothesis.status.changed
    Published by: HypothesisRegistry, HypothesisValidator
    Consumed by: UI dashboards, workflow triggers
    """

    hypothesis_id: str = Field(..., description="Hypothesis ID")
    old_status: HypothesisStatus = Field(..., description="Previous status")
    new_status: HypothesisStatus = Field(..., description="New status")
    validation_score: float | None = Field(None, description="Validation score if validated")
    reason: str | None = Field(None, description="Reason for status change")
    correlation_id: UUID | None = Field(None, description="Request correlation ID")
    timestamp: datetime = Field(default_factory=datetime.utcnow)


# Event Publisher


class HypothesisEventPublisher:
    """
    Publishes hypothesis validation events to NATS.

    Example:
        from app.nats_client import get_nats_client

        nats = await get_nats_client()
        publisher = HypothesisEventPublisher(nats)

        # Publish validation started
        await publisher.publish_validation_started(
            validation_id="val_abc123",
            hypothesis_id="hyp_xyz789",
            hypothesis_statement="Enterprise customers will pay $2K/month",
            category=HypothesisCategory.PRICING,
            agent_count=3,
            max_rounds=3,
        )
    """

    # Subject prefixes
    SUBJECT_PREFIX = "hypothesis"
    VALIDATION_STARTED = f"{SUBJECT_PREFIX}.validation.started"
    VALIDATION_ROUND = f"{SUBJECT_PREFIX}.validation.round"
    VALIDATION_COMPLETED = f"{SUBJECT_PREFIX}.validation.completed"
    VALIDATION_FAILED = f"{SUBJECT_PREFIX}.validation.failed"
    EVIDENCE_ADDED = f"{SUBJECT_PREFIX}.evidence.added"
    STATUS_CHANGED = f"{SUBJECT_PREFIX}.status.changed"

    def __init__(self, nats_client: NATSClient | None = None):
        """
        Initialize the event publisher.

        Args:
            nats_client: Optional NATSClient instance. If None, events
                        will be logged but not published.
        """
        self._nats = nats_client
        self._enabled = nats_client is not None

    async def publish_validation_started(
        self,
        validation_id: str,
        hypothesis_id: str,
        hypothesis_statement: str,
        category: HypothesisCategory,
        agent_count: int,
        max_rounds: int,
        correlation_id: UUID | None = None,
    ) -> None:
        """Publish validation started event."""
        event = HypothesisValidationStartedEvent(
            validation_id=validation_id,
            hypothesis_id=hypothesis_id,
            hypothesis_statement=hypothesis_statement,
            category=category,
            agent_count=agent_count,
            max_rounds=max_rounds,
            correlation_id=correlation_id,
        )
        await self._publish(self.VALIDATION_STARTED, event, correlation_id)

    async def publish_debate_round(
        self,
        validation_id: str,
        hypothesis_id: str,
        round_number: int,
        total_rounds: int,
        responses_count: int,
        consensus_level: str | None,
        average_confidence: float,
        correlation_id: UUID | None = None,
    ) -> None:
        """Publish debate round completed event."""
        event = HypothesisDebateRoundEvent(
            validation_id=validation_id,
            hypothesis_id=hypothesis_id,
            round_number=round_number,
            total_rounds=total_rounds,
            responses_count=responses_count,
            consensus_level=consensus_level,
            average_confidence=average_confidence,
            correlation_id=correlation_id,
        )
        await self._publish(self.VALIDATION_ROUND, event, correlation_id)

    async def publish_validation_completed(
        self,
        result: HypothesisValidationResult,
        hypothesis_id: str,
        correlation_id: UUID | None = None,
    ) -> None:
        """Publish validation completed event."""
        event = HypothesisValidationCompletedEvent(
            validation_id=result.metadata.get("validation_id", "unknown"),
            hypothesis_id=hypothesis_id,
            status=result.status,
            validation_score=result.validation_score,
            consensus_reached=result.consensus_reached,
            rounds_taken=result.rounds_taken,
            final_answer=result.final_answer[:500],  # Truncate for event size
            recommendation=result.recommendation[:300],
            total_cost=result.total_cost,
            duration_seconds=result.duration_seconds,
            correlation_id=correlation_id,
        )
        await self._publish(self.VALIDATION_COMPLETED, event, correlation_id)

    async def publish_validation_failed(
        self,
        validation_id: str,
        hypothesis_id: str,
        error: Exception,
        rounds_completed: int = 0,
        correlation_id: UUID | None = None,
    ) -> None:
        """Publish validation failed event."""
        event = HypothesisValidationFailedEvent(
            validation_id=validation_id,
            hypothesis_id=hypothesis_id,
            error_type=type(error).__name__,
            error_message=str(error),
            rounds_completed=rounds_completed,
            correlation_id=correlation_id,
        )
        await self._publish(self.VALIDATION_FAILED, event, correlation_id)

    async def publish_evidence_added(
        self,
        hypothesis_id: str,
        evidence: HypothesisEvidence,
        correlation_id: UUID | None = None,
    ) -> None:
        """Publish evidence added event."""
        event = HypothesisEvidenceAddedEvent(
            hypothesis_id=hypothesis_id,
            evidence_id=evidence.id,
            source=evidence.source,
            supports=evidence.supports,
            confidence=evidence.confidence,
            correlation_id=correlation_id,
        )
        await self._publish(self.EVIDENCE_ADDED, event, correlation_id)

    async def publish_status_changed(
        self,
        hypothesis_id: str,
        old_status: HypothesisStatus,
        new_status: HypothesisStatus,
        validation_score: float | None = None,
        reason: str | None = None,
        correlation_id: UUID | None = None,
    ) -> None:
        """Publish hypothesis status changed event."""
        event = HypothesisStatusChangedEvent(
            hypothesis_id=hypothesis_id,
            old_status=old_status,
            new_status=new_status,
            validation_score=validation_score,
            reason=reason,
            correlation_id=correlation_id,
        )
        await self._publish(self.STATUS_CHANGED, event, correlation_id)

    async def _publish(
        self,
        subject: str,
        event: BaseModel,
        correlation_id: UUID | None = None,
    ) -> None:
        """Internal method to publish event to NATS."""
        payload = event.model_dump(mode="json")

        if self._enabled and self._nats:
            try:
                await self._nats.publish(subject, payload, correlation_id)
                logger.debug(
                    "hypothesis_event_published",
                    subject=subject,
                    event_type=type(event).__name__,
                )
            except Exception as e:
                logger.warning(
                    "hypothesis_event_publish_failed",
                    subject=subject,
                    error=str(e),
                )
        else:
            # Log event when NATS is not available
            logger.info(
                "hypothesis_event_logged",
                subject=subject,
                event_type=type(event).__name__,
                payload_preview=str(payload)[:200],
            )


# Convenience function for getting publisher instance
async def get_hypothesis_event_publisher() -> HypothesisEventPublisher:
    """
    Get a HypothesisEventPublisher instance.

    Attempts to use the global NATS client if available.

    Returns:
        HypothesisEventPublisher (may be in logging-only mode if NATS unavailable)
    """
    try:
        from app.nats_client import get_nats_client

        nats = await get_nats_client()
        return HypothesisEventPublisher(nats)
    except ImportError:
        logger.warning("NATS client not available, events will be logged only")
        return HypothesisEventPublisher(None)
