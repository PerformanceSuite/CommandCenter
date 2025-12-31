"""
Prompt analysis and improvement API endpoints.

Provides:
- POST /api/v1/prompts/quick-check - Fast local check (no API call)
- POST /api/v1/prompts/analyze - Full AI-powered analysis
- POST /api/v1/prompts/improve - Analyze and get improved version
"""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter(prefix="/api/v1/prompts", tags=["prompts"])


class PromptRequest(BaseModel):
    """Request body for prompt analysis."""

    prompt: str = Field(..., min_length=10, description="The prompt to analyze")


class QuickCheckResponse(BaseModel):
    """Response from quick check endpoint."""

    has_role: bool
    has_output_format: bool
    has_constraints: bool
    word_count: int
    suggestions: list[str]
    potential_conflicts: list[str]


class IssueResponse(BaseModel):
    """A single issue in the prompt."""

    type: str
    severity: str
    description: str
    suggestion: str


class AnalysisResponse(BaseModel):
    """Response from full analysis endpoint."""

    issues: list[IssueResponse]
    scores: dict[str, int]
    improved: str | None
    summary: str


@router.post("/quick-check", response_model=QuickCheckResponse)
async def quick_check(request: PromptRequest) -> QuickCheckResponse:
    """
    Fast local prompt check - no API call.

    Checks for:
    - Role definition
    - Output format specification
    - Constraints/guardrails
    - Potential conflicts

    Returns suggestions for improvement.
    """
    from libs.agent_framework.prompt_improver import PromptImprover

    improver = PromptImprover()
    result = improver.quick_check(request.prompt)

    return QuickCheckResponse(**result)


@router.post("/analyze", response_model=AnalysisResponse)
async def analyze(request: PromptRequest) -> AnalysisResponse:
    """
    Full AI-powered prompt analysis.

    Uses Claude to analyze the prompt for:
    - Conflicts and contradictions
    - Ambiguous instructions
    - Missing structure
    - Verbosity issues

    Returns scores (0-100) for clarity, structure, completeness.
    May include an improved version if score is below 80.
    """
    from libs.agent_framework.prompt_improver import PromptImprover

    improver = PromptImprover()
    analysis = await improver.analyze(request.prompt)

    return AnalysisResponse(
        issues=[IssueResponse(**i.to_dict()) for i in analysis.issues],
        scores=analysis.scores,
        improved=analysis.improved,
        summary=analysis.summary,
    )


@router.post("/improve", response_model=AnalysisResponse)
async def improve(request: PromptRequest) -> AnalysisResponse:
    """
    Analyze prompt and ensure improved version is generated.

    Like /analyze but guarantees an improved version will be returned
    if the prompt score is below 80.
    """
    from libs.agent_framework.prompt_improver import PromptImprover

    improver = PromptImprover()
    analysis = await improver.improve(request.prompt)

    return AnalysisResponse(
        issues=[IssueResponse(**i.to_dict()) for i in analysis.issues],
        scores=analysis.scores,
        improved=analysis.improved,
        summary=analysis.summary,
    )
