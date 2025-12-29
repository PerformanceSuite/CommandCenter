"""
Hypothesis management and validation API endpoints.

Provides REST API for the AI Arena hypothesis validation system.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from libs.ai_arena.hypothesis.schema import Hypothesis, HypothesisCategory, HypothesisStatus

from app.schemas.hypothesis import (
    HypothesisDetailResponse,
    HypothesisEvidenceResponse,
    HypothesisListResponse,
    HypothesisStatsResponse,
    HypothesisSummaryResponse,
    HypothesisValidateRequest,
    ValidationStatusResponse,
    ValidationTaskResponse,
)
from app.services.hypothesis_service import hypothesis_service

router = APIRouter(prefix="/hypotheses", tags=["hypotheses"])


def _to_summary_response(h: Hypothesis) -> HypothesisSummaryResponse:
    """Convert Hypothesis to summary response."""
    return HypothesisSummaryResponse(
        id=h.id,
        statement=h.statement,
        category=h.category,
        status=h.status,
        priority_score=h.priority.score if h.priority else 0.0,
        evidence_count=len(h.evidence),
        validation_score=h.validation_score,
        created_at=h.created_at,
        updated_at=h.updated_at,
    )


def _to_detail_response(h: Hypothesis) -> HypothesisDetailResponse:
    """Convert Hypothesis to detail response."""
    return HypothesisDetailResponse(
        id=h.id,
        statement=h.statement,
        category=h.category,
        status=h.status,
        priority_score=h.priority.score if h.priority else 0.0,
        evidence_count=len(h.evidence),
        validation_score=h.validation_score,
        created_at=h.created_at,
        updated_at=h.updated_at,
        impact=h.impact,
        risk=h.risk,
        testability=h.testability,
        success_criteria=h.success_criteria,
        context=h.context,
        tags=h.tags,
        evidence=[
            HypothesisEvidenceResponse(
                id=e.id,
                source=e.source,
                content=e.content,
                supports=e.supports,
                confidence=e.confidence,
                collected_at=e.collected_at,
                collected_by=e.collected_by,
            )
            for e in h.evidence
        ],
        validated_at=h.validated_at,
        metadata=h.metadata,
    )


@router.get("/", response_model=HypothesisListResponse)
async def list_hypotheses(
    status_filter: HypothesisStatus | None = Query(None, alias="status"),
    category: HypothesisCategory | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> HypothesisListResponse:
    """
    List hypotheses with optional filtering.

    Results are sorted by priority score (highest first).
    """
    hypotheses, total = await hypothesis_service.list_hypotheses(
        status=status_filter,
        category=category,
        limit=limit,
        offset=offset,
    )

    return HypothesisListResponse(
        items=[_to_summary_response(h) for h in hypotheses],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/stats", response_model=HypothesisStatsResponse)
async def get_statistics() -> HypothesisStatsResponse:
    """Get dashboard statistics for hypotheses."""
    stats = await hypothesis_service.get_statistics()
    return HypothesisStatsResponse(**stats)


@router.get("/{hypothesis_id}", response_model=HypothesisDetailResponse)
async def get_hypothesis(hypothesis_id: str) -> HypothesisDetailResponse:
    """Get detailed hypothesis information including evidence."""
    hypothesis = await hypothesis_service.get_hypothesis(hypothesis_id)
    if not hypothesis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hypothesis not found: {hypothesis_id}",
        )
    return _to_detail_response(hypothesis)


@router.post(
    "/{hypothesis_id}/validate",
    response_model=ValidationTaskResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def start_validation(
    hypothesis_id: str,
    request: HypothesisValidateRequest | None = None,
) -> ValidationTaskResponse:
    """
    Start async validation of a hypothesis.

    Returns a task_id that can be used to poll for progress.
    """
    req = request or HypothesisValidateRequest()

    try:
        task_id = await hypothesis_service.start_validation(
            hypothesis_id=hypothesis_id,
            max_rounds=req.max_rounds,
            agents=req.agents,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )

    return ValidationTaskResponse(
        task_id=task_id,
        hypothesis_id=hypothesis_id,
        status="started",
        message="Validation started successfully",
    )


@router.get(
    "/{hypothesis_id}/validation-status",
    response_model=ValidationStatusResponse,
)
async def get_validation_status(hypothesis_id: str) -> ValidationStatusResponse:
    """
    Get current validation status for a hypothesis.

    Returns the status of the most recent validation task.
    """
    task_state = await hypothesis_service.get_validation_status_by_hypothesis(hypothesis_id)

    if not task_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No active validation for hypothesis: {hypothesis_id}",
        )

    return ValidationStatusResponse(
        task_id=task_state["task_id"],
        hypothesis_id=task_state["hypothesis_id"],
        status=task_state["status"],
        current_round=task_state.get("current_round", 0),
        max_rounds=task_state.get("max_rounds", 3),
        responses_count=task_state.get("responses_count", 0),
        consensus_level=task_state.get("consensus_level"),
        started_at=datetime.fromisoformat(task_state["started_at"]),
        completed_at=(
            datetime.fromisoformat(task_state["completed_at"])
            if task_state.get("completed_at")
            else None
        ),
        error=task_state.get("error"),
    )


@router.get("/validation/{task_id}", response_model=ValidationStatusResponse)
async def get_validation_task(task_id: str) -> ValidationStatusResponse:
    """Get validation task status by task ID."""
    task_state = await hypothesis_service.get_validation_status(task_id)

    if not task_state:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Validation task not found: {task_id}",
        )

    return ValidationStatusResponse(
        task_id=task_state["task_id"],
        hypothesis_id=task_state["hypothesis_id"],
        status=task_state["status"],
        current_round=task_state.get("current_round", 0),
        max_rounds=task_state.get("max_rounds", 3),
        responses_count=task_state.get("responses_count", 0),
        consensus_level=task_state.get("consensus_level"),
        started_at=datetime.fromisoformat(task_state["started_at"]),
        completed_at=(
            datetime.fromisoformat(task_state["completed_at"])
            if task_state.get("completed_at")
            else None
        ),
        error=task_state.get("error"),
    )
