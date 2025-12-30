"""
Intelligence Integration API endpoints

Routes for Research Hub intelligence integration:
- Hypotheses under research tasks
- Quick hypothesis creation
- Evidence management
- Debate/validation management
- Intelligence dashboard
"""

from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import HypothesisStatus
from app.schemas.intelligence import (
    CreateTaskFromGapRequest,
    CreateTaskFromGapResponse,
    DebateCreate,
    DebateResponse,
    DebateStartResponse,
    EvidenceCreate,
    EvidenceFromSuggestion,
    EvidenceListResponse,
    EvidenceResponse,
    HypothesisCreate,
    HypothesisListResponse,
    HypothesisResponse,
    HypothesisUpdate,
    IndexFindingsResponse,
    IntelligenceSummary,
    NeedsAttentionItem,
    NeedsAttentionResponse,
    QuickHypothesisCreate,
    QuickHypothesisResponse,
    RecentValidation,
    RecentValidationsResponse,
    ResearchFindingListResponse,
    ResearchFindingResponse,
    SuggestedEvidenceResponse,
    SuggestedTasksResponse,
)
from app.services.hypothesis_crud_service import HypothesisCrudService
from app.services.intelligence_service import IntelligenceService

router = APIRouter(tags=["intelligence"])


# =============================================================================
# Dependencies
# =============================================================================


def get_hypothesis_crud_service(db: AsyncSession = Depends(get_db)) -> HypothesisCrudService:
    """Dependency to get hypothesis CRUD service"""
    return HypothesisCrudService(db)


def get_intelligence_service(db: AsyncSession = Depends(get_db)) -> IntelligenceService:
    """Dependency to get intelligence service"""
    return IntelligenceService(db)


# =============================================================================
# Hypothesis Endpoints (under Research Tasks)
# =============================================================================


@router.get(
    "/research-tasks/{task_id}/hypotheses",
    response_model=HypothesisListResponse,
    summary="List hypotheses for a research task",
)
async def list_task_hypotheses(
    task_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status_filter: Optional[HypothesisStatus] = Query(None, alias="status"),
    service: HypothesisCrudService = Depends(get_hypothesis_crud_service),
) -> HypothesisListResponse:
    """List all hypotheses for a specific research task."""
    hypotheses, total = await service.list_by_task(
        task_id=task_id, skip=skip, limit=limit, status=status_filter
    )
    return HypothesisListResponse(total=total, items=hypotheses)


@router.post(
    "/research-tasks/{task_id}/hypotheses",
    response_model=HypothesisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create hypothesis under a research task",
)
async def create_task_hypothesis(
    task_id: int,
    data: HypothesisCreate,
    service: HypothesisCrudService = Depends(get_hypothesis_crud_service),
) -> HypothesisResponse:
    """Create a new hypothesis under a research task."""
    return await service.create_hypothesis(task_id, data)


# =============================================================================
# Quick Hypothesis Endpoint (under Projects)
# =============================================================================


@router.post(
    "/projects/{project_id}/quick-hypothesis",
    response_model=QuickHypothesisResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create hypothesis with auto-generated parent task",
)
async def create_quick_hypothesis(
    project_id: int,
    data: QuickHypothesisCreate,
    service: HypothesisCrudService = Depends(get_hypothesis_crud_service),
) -> QuickHypothesisResponse:
    """
    Create a hypothesis with auto-generated parent research task.

    Useful for quick hypothesis entry when no existing task is appropriate.
    Creates a minimal "ad-hoc hypothesis" task as parent.
    """
    return await service.create_quick_hypothesis(project_id, data)


# =============================================================================
# Hypothesis Direct Access Endpoints
# =============================================================================


@router.get(
    "/hypotheses/{hypothesis_id}",
    response_model=HypothesisResponse,
    summary="Get hypothesis by ID",
)
async def get_hypothesis(
    hypothesis_id: int,
    service: HypothesisCrudService = Depends(get_hypothesis_crud_service),
) -> HypothesisResponse:
    """Get detailed information about a hypothesis."""
    return await service.get_hypothesis(hypothesis_id)


@router.patch(
    "/hypotheses/{hypothesis_id}",
    response_model=HypothesisResponse,
    summary="Update hypothesis",
)
async def update_hypothesis(
    hypothesis_id: int,
    data: HypothesisUpdate,
    service: HypothesisCrudService = Depends(get_hypothesis_crud_service),
) -> HypothesisResponse:
    """Update an existing hypothesis."""
    return await service.update_hypothesis(hypothesis_id, data)


@router.delete(
    "/hypotheses/{hypothesis_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete hypothesis",
)
async def delete_hypothesis(
    hypothesis_id: int,
    service: HypothesisCrudService = Depends(get_hypothesis_crud_service),
) -> None:
    """Delete a hypothesis and all its evidence/debates."""
    await service.delete_hypothesis(hypothesis_id)


# =============================================================================
# Validation (Debate) Endpoints
# =============================================================================


@router.post(
    "/hypotheses/{hypothesis_id}/validate",
    response_model=DebateStartResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start hypothesis validation debate",
)
async def start_validation(
    hypothesis_id: int,
    data: DebateCreate = DebateCreate(),
    service: HypothesisCrudService = Depends(get_hypothesis_crud_service),
) -> DebateStartResponse:
    """
    Start a multi-agent validation debate for a hypothesis.

    The debate runs asynchronously. Use GET /debates/{id} to check status.
    """
    return await service.start_validation(hypothesis_id, data)


@router.get(
    "/debates/{debate_id}",
    response_model=DebateResponse,
    summary="Get debate status and results",
)
async def get_debate(
    debate_id: int,
    service: HypothesisCrudService = Depends(get_hypothesis_crud_service),
) -> DebateResponse:
    """Get debate status, results, and reasoning."""
    return await service.get_debate(debate_id)


@router.get(
    "/debates/{debate_id}/suggested-tasks",
    response_model=SuggestedTasksResponse,
    summary="Get suggested research tasks from gap analysis",
)
async def get_suggested_tasks(
    debate_id: int,
    service: IntelligenceService = Depends(get_intelligence_service),
) -> SuggestedTasksResponse:
    """Get research task suggestions from debate gap analysis."""
    suggestions = await service.get_suggested_tasks_from_gap(debate_id)
    return SuggestedTasksResponse(debate_id=debate_id, suggestions=suggestions)


@router.post(
    "/debates/{debate_id}/create-task-from-gap",
    response_model=CreateTaskFromGapResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create research task from gap suggestion",
)
async def create_task_from_gap(
    debate_id: int,
    data: CreateTaskFromGapRequest,
    service: IntelligenceService = Depends(get_intelligence_service),
) -> CreateTaskFromGapResponse:
    """Create a new research task from a gap analysis suggestion (one-click)."""
    task = await service.create_task_from_gap(debate_id, data.suggestion_index)
    if not task:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Suggestion {data.suggestion_index} not found for debate {debate_id}",
        )
    return CreateTaskFromGapResponse(research_task_id=task.id, title=task.title)


# =============================================================================
# Evidence Endpoints
# =============================================================================


@router.get(
    "/hypotheses/{hypothesis_id}/evidence",
    response_model=EvidenceListResponse,
    summary="List evidence for hypothesis",
)
async def list_evidence(
    hypothesis_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: HypothesisCrudService = Depends(get_hypothesis_crud_service),
) -> EvidenceListResponse:
    """List all evidence attached to a hypothesis."""
    evidence, total = await service.list_evidence(hypothesis_id, skip, limit)
    return EvidenceListResponse(total=total, items=evidence)


@router.post(
    "/hypotheses/{hypothesis_id}/evidence",
    response_model=EvidenceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add evidence manually",
)
async def add_evidence(
    hypothesis_id: int,
    data: EvidenceCreate,
    service: HypothesisCrudService = Depends(get_hypothesis_crud_service),
) -> EvidenceResponse:
    """Add evidence manually to a hypothesis."""
    return await service.add_evidence(hypothesis_id, data)


@router.get(
    "/hypotheses/{hypothesis_id}/suggested-evidence",
    response_model=SuggestedEvidenceResponse,
    summary="Get AI-suggested evidence",
)
async def get_suggested_evidence(
    hypothesis_id: int,
    limit: int = Query(10, ge=1, le=50),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> SuggestedEvidenceResponse:
    """Get AI-suggested evidence from KB and task findings."""
    result = await service.suggest_evidence(hypothesis_id, limit)
    return SuggestedEvidenceResponse(suggestions=result.suggestions, query_used=result.query_used)


@router.post(
    "/hypotheses/{hypothesis_id}/evidence/accept",
    response_model=list[EvidenceResponse],
    status_code=status.HTTP_201_CREATED,
    summary="Accept suggested evidence",
)
async def accept_suggested_evidence(
    hypothesis_id: int,
    data: EvidenceFromSuggestion,
    service: HypothesisCrudService = Depends(get_hypothesis_crud_service),
) -> list[EvidenceResponse]:
    """Accept one or more suggested evidence items."""
    return await service.accept_suggested_evidence(hypothesis_id, data.suggestion_indices)


# =============================================================================
# Research Findings Endpoints
# =============================================================================


@router.get(
    "/research-tasks/{task_id}/findings",
    response_model=ResearchFindingListResponse,
    summary="List findings for a research task",
)
async def list_findings(
    task_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> ResearchFindingListResponse:
    """List research findings from agent runs."""
    # Access through repository
    findings = await service.finding_repo.get_by_task(task_id, skip, limit)
    total = len(findings)  # TODO: Add count method

    items = [
        ResearchFindingResponse(
            id=f.id,
            research_task_id=f.research_task_id,
            content=f.content,
            finding_type=f.finding_type,
            agent_role=f.agent_role,
            confidence=f.confidence,
            sources=f.sources,
            knowledge_entry_id=f.knowledge_entry_id,
            created_at=f.created_at,
        )
        for f in findings
    ]

    return ResearchFindingListResponse(total=total, items=items)


@router.post(
    "/research-tasks/{task_id}/index-findings",
    response_model=IndexFindingsResponse,
    summary="Index all task findings to KB",
)
async def index_findings(
    task_id: int,
    service: IntelligenceService = Depends(get_intelligence_service),
) -> IndexFindingsResponse:
    """Bulk index all unindexed findings from a task to KnowledgeBeast."""
    count = await service.index_research_findings(task_id)
    return IndexFindingsResponse(indexed_count=count, task_id=task_id)


# =============================================================================
# Intelligence Dashboard Endpoints
# =============================================================================


@router.get(
    "/projects/{project_id}/intelligence/summary",
    response_model=IntelligenceSummary,
    summary="Get combined intelligence stats",
)
async def get_intelligence_summary(
    project_id: int,
    service: IntelligenceService = Depends(get_intelligence_service),
) -> IntelligenceSummary:
    """
    Get combined intelligence statistics for a project.

    Includes research tasks, hypotheses, KB stats, and gaps.
    """
    summary = await service.get_intelligence_summary(project_id)
    return IntelligenceSummary(**summary)


@router.get(
    "/projects/{project_id}/intelligence/needs-attention",
    response_model=NeedsAttentionResponse,
    summary="Get items needing attention",
)
async def get_needs_attention(
    project_id: int,
    limit: int = Query(20, ge=1, le=100),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> NeedsAttentionResponse:
    """Get hypotheses and tasks that need attention."""
    hypotheses = await service.hypothesis_repo.get_needing_attention(project_id, limit)

    items = [
        NeedsAttentionItem(
            id=h.id,
            type="hypothesis",
            title=h.statement[:100],
            reason=_get_attention_reason(h),
            priority="high" if h.priority_score > 50 else "medium",
            created_at=h.created_at,
        )
        for h in hypotheses
    ]

    return NeedsAttentionResponse(items=items, total=len(items))


@router.get(
    "/projects/{project_id}/intelligence/recent-validations",
    response_model=RecentValidationsResponse,
    summary="Get recent validation activity",
)
async def get_recent_validations(
    project_id: int,
    limit: int = Query(10, ge=1, le=50),
    service: IntelligenceService = Depends(get_intelligence_service),
) -> RecentValidationsResponse:
    """Get recent validation completions."""
    # Get recently validated hypotheses
    validated = await service.hypothesis_repo.get_recently_validated(project_id, limit)

    validations = [
        RecentValidation(
            hypothesis_id=h.id,
            statement=h.statement,
            verdict=_status_to_verdict(h.status),
            validation_score=h.validation_score,
            completed_at=h.updated_at,
        )
        for h in validated
    ]

    return RecentValidationsResponse(validations=validations)


# =============================================================================
# Helper Functions
# =============================================================================


def _get_attention_reason(h) -> str:
    """Get human-readable reason why hypothesis needs attention."""
    from app.models import HypothesisStatus

    if h.status == HypothesisStatus.NEEDS_MORE_DATA:
        return "Validation incomplete - more research needed"
    elif h.status == HypothesisStatus.UNTESTED:
        if h.priority_score > 50:
            return "High priority hypothesis not yet validated"
        return "Hypothesis awaiting validation"
    return "Review recommended"


def _status_to_verdict(status):
    """Convert hypothesis status to debate verdict."""
    from app.models import DebateVerdict, HypothesisStatus

    status_map = {
        HypothesisStatus.VALIDATED: DebateVerdict.VALIDATED,
        HypothesisStatus.INVALIDATED: DebateVerdict.INVALIDATED,
        HypothesisStatus.NEEDS_MORE_DATA: DebateVerdict.NEEDS_MORE_DATA,
    }
    return status_map.get(status)
