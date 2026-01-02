"""API router for skills."""
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.auth.project_context import get_current_project_id
from app.auth.dependencies import get_current_user
from app.models.user import User
from app.services.skill_service import SkillService
from app.schemas.skill import (
    SkillCreate, SkillUpdate, SkillResponse,
    SkillUsageCreate, SkillUsageResponse,
    SkillImportRequest, SkillSearchRequest
)

router = APIRouter(prefix="/skills", tags=["skills"])


def get_skill_service(db: AsyncSession = Depends(get_db)) -> SkillService:
    return SkillService(db)


@router.get("", response_model=List[SkillResponse])
async def list_skills(
    include_global: bool = True,
    limit: int = 100,
    offset: int = 0,
    project_id: Optional[int] = Depends(get_current_project_id),
    service: SkillService = Depends(get_skill_service)
):
    """List all available skills."""
    return await service.list_all(
        project_id=project_id,
        include_global=include_global,
        limit=limit,
        offset=offset
    )


@router.get("/{skill_id}", response_model=SkillResponse)
async def get_skill(
    skill_id: int,
    service: SkillService = Depends(get_skill_service)
):
    """Get a skill by ID."""
    skill = await service.get_by_id(skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.get("/by-slug/{slug}", response_model=SkillResponse)
async def get_skill_by_slug(
    slug: str,
    service: SkillService = Depends(get_skill_service)
):
    """Get a skill by slug."""
    skill = await service.get_by_slug(slug)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.post("", response_model=SkillResponse, status_code=status.HTTP_201_CREATED)
async def create_skill(
    skill_data: SkillCreate,
    project_id: Optional[int] = Depends(get_current_project_id),
    service: SkillService = Depends(get_skill_service)
):
    """Create a new skill."""
    # Check for duplicate slug
    existing = await service.get_by_slug(skill_data.slug)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Skill with slug '{skill_data.slug}' already exists"
        )

    if skill_data.project_id is None:
        skill_data.project_id = project_id

    return await service.create(skill_data)


@router.patch("/{skill_id}", response_model=SkillResponse)
async def update_skill(
    skill_id: int,
    skill_data: SkillUpdate,
    service: SkillService = Depends(get_skill_service)
):
    """Update a skill."""
    skill = await service.update(skill_id, skill_data)
    if not skill:
        raise HTTPException(status_code=404, detail="Skill not found")
    return skill


@router.delete("/{skill_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_skill(
    skill_id: int,
    service: SkillService = Depends(get_skill_service)
):
    """Delete a skill."""
    deleted = await service.delete(skill_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Skill not found")


@router.post("/search", response_model=List[SkillResponse])
async def search_skills(
    search: SkillSearchRequest,
    project_id: Optional[int] = Depends(get_current_project_id),
    service: SkillService = Depends(get_skill_service)
):
    """Search skills."""
    return await service.search(search, project_id=project_id)


@router.post("/import", response_model=List[SkillResponse])
async def import_skills(
    import_request: SkillImportRequest,
    project_id: Optional[int] = Depends(get_current_project_id),
    service: SkillService = Depends(get_skill_service)
):
    """Import skills from filesystem."""
    try:
        return await service.import_from_filesystem(import_request, project_id=project_id)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/usage", response_model=SkillUsageResponse, status_code=status.HTTP_201_CREATED)
async def record_skill_usage(
    usage_data: SkillUsageCreate,
    project_id: Optional[int] = Depends(get_current_project_id),
    user: User = Depends(get_current_user),
    service: SkillService = Depends(get_skill_service)
):
    """Record a skill usage for effectiveness tracking."""
    try:
        return await service.record_usage(
            usage_data,
            project_id=project_id,
            user_id=user.id
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
