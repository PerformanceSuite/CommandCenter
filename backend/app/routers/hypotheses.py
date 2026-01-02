"""
Hypothesis management and validation API endpoints.

Provides REST API for the AI Arena hypothesis validation system.
"""

from datetime import datetime

from fastapi import APIRouter, HTTPException, Query, status
from libs.ai_arena.hypothesis.schema import (
    Hypothesis,
    HypothesisCategory,
    HypothesisCreate,
    HypothesisEvidence,
    HypothesisStatus,
    HypothesisUpdate,
    ImpactLevel,
    RiskLevel,
    TestabilityLevel,
)
from libs.llm_gateway.metrics import get_cost_statistics

from app.schemas.hypothesis import (
    AgentResponseSchema,
    CostStatsResponse,
    CreateHypothesisRequest,
    DebateResultResponse,
    DebateRoundSchema,
    EvidenceCreateRequest,
    EvidenceItemResponse,
    EvidenceListResponse,
    EvidenceStatsResponse,
    HypothesisCreateRequest,
    HypothesisDetailResponse,
    HypothesisEvidenceResponse,
    HypothesisListResponse,
    HypothesisStatsResponse,
    HypothesisSummaryResponse,
    HypothesisUpdateRequest,
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


# ============================================================================
# Static path routes (must come before dynamic /{hypothesis_id} routes)
# ============================================================================


@router.get("/", response_model=HypothesisListResponse)
async def list_hypotheses(
    status_filter: HypothesisStatus | None = Query(None, alias="status"),
    category: HypothesisCategory | None = None,
    limit: int = Query(default=20, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
) -> HypothesisListResponse:
    """
    List hypotheses with optional filtering.

    Results are sorted by priority score (highest first).
    """
    hypotheses, total = await hypothesis_service.list_hypotheses(
        status=status_filter,
        category=category,
        limit=limit,
        skip=skip,
    )

    return HypothesisListResponse(
        items=[_to_summary_response(h) for h in hypotheses],
        total=total,
        limit=limit,
        skip=skip,
    )


@router.post("/", response_model=HypothesisDetailResponse, status_code=status.HTTP_201_CREATED)
async def create_hypothesis(
    request: HypothesisCreateRequest | CreateHypothesisRequest,
) -> HypothesisDetailResponse:
    """Create a new hypothesis with either full or quick input."""
    # Check if it's a simple CreateHypothesisRequest (quick input)
    if isinstance(request, CreateHypothesisRequest):
        # Map string category to enum
        try:
            category_enum = HypothesisCategory(request.category)
        except ValueError:
            category_enum = HypothesisCategory.CUSTOMER  # Default fallback

        # Use sensible defaults for quick input
        create_data = HypothesisCreate(
            statement=request.statement,
            category=category_enum,
            impact=ImpactLevel.MEDIUM,
            risk=RiskLevel.MEDIUM,
            testability=TestabilityLevel.MEDIUM,
            success_criteria="To be defined through validation",
            context=request.context,
            tags=[],
            metadata={},
        )
    else:
        # Full HypothesisCreateRequest with all fields
        create_data = HypothesisCreate(
            statement=request.statement,
            category=request.category,
            impact=request.impact,
            risk=request.risk,
            testability=request.testability,
            success_criteria=request.success_criteria,
            context=request.context,
            tags=request.tags,
            metadata=request.metadata,
        )

    hypothesis = await hypothesis_service.create_hypothesis(create_data)
    return _to_detail_response(hypothesis)


@router.get("/stats", response_model=HypothesisStatsResponse)
async def get_statistics() -> HypothesisStatsResponse:
    """Get dashboard statistics for hypotheses."""
    stats = await hypothesis_service.get_statistics()
    return HypothesisStatsResponse(**stats)


@router.get("/costs", response_model=CostStatsResponse)
async def get_cost_stats() -> CostStatsResponse:
    """
    Get LLM cost and usage statistics.

    Returns aggregate costs, tokens, and request counts by provider.
    Data is derived from Prometheus metrics collected during API usage.
    """
    stats = get_cost_statistics()
    return CostStatsResponse(**stats)


# Evidence Explorer Endpoints


@router.get("/evidence/list", response_model=EvidenceListResponse)
async def list_evidence(
    supports: bool | None = Query(None, description="Filter by supports (true/false)"),
    source: str | None = Query(None, description="Filter by source text"),
    min_confidence: int | None = Query(None, ge=0, le=100, description="Minimum confidence"),
    limit: int = Query(default=50, ge=1, le=100),
    skip: int = Query(default=0, ge=0),
) -> EvidenceListResponse:
    """
    List all evidence across all hypotheses with optional filtering.

    Useful for exploring evidence patterns and finding insights.
    """
    items, total = await hypothesis_service.list_all_evidence(
        supports=supports,
        source_filter=source,
        min_confidence=min_confidence,
        limit=limit,
        skip=skip,
    )

    return EvidenceListResponse(
        items=[
            EvidenceItemResponse(
                id=e["id"],
                hypothesis_id=e["hypothesis_id"],
                hypothesis_statement=e["hypothesis_statement"],
                source=e["source"],
                content=e["content"],
                supports=e["supports"],
                confidence=e["confidence"],
                collected_at=datetime.fromisoformat(e["collected_at"]),
                collected_by=e["collected_by"],
                metadata=e.get("metadata", {}),
            )
            for e in items
        ],
        total=total,
        limit=limit,
        skip=skip,
    )


@router.get("/evidence/stats", response_model=EvidenceStatsResponse)
async def get_evidence_stats() -> EvidenceStatsResponse:
    """Get statistics about all evidence across hypotheses."""
    stats = await hypothesis_service.get_evidence_stats()
    return EvidenceStatsResponse(**stats)


# Validation task routes (static prefix before dynamic hypothesis_id)


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


@router.get("/validation/{task_id}/debate", response_model=DebateResultResponse)
async def get_debate_result(task_id: str) -> DebateResultResponse:
    """
    Get the full debate result for a completed validation task.

    Returns all rounds, agent responses, and consensus information.
    """
    debate_result = await hypothesis_service.get_debate_result(task_id)

    if not debate_result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Debate result not found for task: {task_id}",
        )

    # Convert nested structures to schema objects
    rounds = [
        DebateRoundSchema(
            round_number=r["round_number"],
            responses=[
                AgentResponseSchema(
                    answer=resp["answer"],
                    reasoning=resp["reasoning"],
                    confidence=resp["confidence"],
                    evidence=resp.get("evidence", []),
                    agent_name=resp["agent_name"],
                    model=resp["model"],
                )
                for resp in r["responses"]
            ],
            consensus_level=r.get("consensus_level"),
            started_at=datetime.fromisoformat(r["started_at"]),
            completed_at=(
                datetime.fromisoformat(r["completed_at"]) if r.get("completed_at") else None
            ),
            metadata=r.get("metadata", {}),
        )
        for r in debate_result.get("rounds", [])
    ]

    dissenting = [
        AgentResponseSchema(
            answer=resp["answer"],
            reasoning=resp["reasoning"],
            confidence=resp["confidence"],
            evidence=resp.get("evidence", []),
            agent_name=resp["agent_name"],
            model=resp["model"],
        )
        for resp in debate_result.get("dissenting_views", [])
    ]

    return DebateResultResponse(
        debate_id=debate_result["debate_id"],
        question=debate_result["question"],
        rounds=rounds,
        final_answer=debate_result["final_answer"],
        final_confidence=debate_result["final_confidence"],
        consensus_level=debate_result["consensus_level"],
        dissenting_views=dissenting,
        status=debate_result["status"],
        started_at=datetime.fromisoformat(debate_result["started_at"]),
        completed_at=(
            datetime.fromisoformat(debate_result["completed_at"])
            if debate_result.get("completed_at")
            else None
        ),
        total_cost=debate_result.get("total_cost", 0.0),
        error_message=debate_result.get("error_message"),
    )


# ============================================================================
# Dynamic /{hypothesis_id} routes (must come after static paths)
# ============================================================================


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


@router.patch("/{hypothesis_id}", response_model=HypothesisDetailResponse)
async def update_hypothesis(
    hypothesis_id: str, request: HypothesisUpdateRequest
) -> HypothesisDetailResponse:
    """Update an existing hypothesis."""
    update_data = HypothesisUpdate(**request.model_dump(exclude_unset=True))
    hypothesis = await hypothesis_service.update_hypothesis(hypothesis_id, update_data)
    if not hypothesis:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hypothesis not found: {hypothesis_id}",
        )
    return _to_detail_response(hypothesis)


@router.delete("/{hypothesis_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_hypothesis(hypothesis_id: str) -> None:
    """Delete a hypothesis."""
    deleted = await hypothesis_service.delete_hypothesis(hypothesis_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Hypothesis not found: {hypothesis_id}",
        )


@router.post(
    "/{hypothesis_id}/evidence",
    response_model=HypothesisDetailResponse,
    status_code=status.HTTP_201_CREATED,
)
async def add_evidence(
    hypothesis_id: str, request: EvidenceCreateRequest
) -> HypothesisDetailResponse:
    """Add evidence to a hypothesis."""
    evidence = HypothesisEvidence(
        source=request.source,
        content=request.content,
        supports=request.supports,
        confidence=request.confidence,
        collected_by=request.collected_by,
        metadata=request.metadata,
    )
    hypothesis = await hypothesis_service.add_evidence(hypothesis_id, evidence)
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
