from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional, List
from app.database import get_db
from app.services.catalog_service import CatalogService
from app.schemas.project import ProjectCreate, ProjectResponse
from app.models.project import ProjectStatus
from app.auth import verify_api_key
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/fed",
    tags=["federation"],
    dependencies=[Depends(verify_api_key)]  # Apply auth to all endpoints
)


@router.get("/projects", response_model=List[ProjectResponse])
async def list_projects(
    status: Optional[str] = Query(None, regex="^(online|offline|degraded)$"),
    db: AsyncSession = Depends(get_db)
):
    """List all registered projects, optionally filtered by status."""
    service = CatalogService(db)

    status_filter = None
    if status:
        status_filter = ProjectStatus(status)

    projects = await service.get_projects(status_filter=status_filter)
    return projects


@router.post("/projects", response_model=ProjectResponse, status_code=201)
async def register_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db)
):
    """Manually register a new project."""
    service = CatalogService(db)

    try:
        project = await service.register_project(
            slug=data.slug,
            name=data.name,
            hub_url=data.hub_url,
            mesh_namespace=data.mesh_namespace,
            tags=data.tags
        )
        return project
    except Exception as e:
        logger.error(f"Failed to register project: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/projects/{slug}", response_model=ProjectResponse)
async def get_project(
    slug: str,
    db: AsyncSession = Depends(get_db)
):
    """Get single project by slug."""
    service = CatalogService(db)
    project = await service.get_project(slug)

    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{slug}' not found")

    return project
