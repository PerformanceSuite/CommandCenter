"""
Project CRUD endpoints for multi-project isolation
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models.project import Project
from app.models.repository import Repository
from app.models.technology import Technology
from app.models.research_task import ResearchTask
from app.models.knowledge_entry import KnowledgeEntry
from app.schemas.project import (
    ProjectCreate,
    ProjectUpdate,
    ProjectResponse,
    ProjectWithCounts,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post(
    "/",
    response_model=ProjectResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new project",
    description="Create a new isolated project workspace",
)
async def create_project(project: ProjectCreate, db: AsyncSession = Depends(get_db)) -> Project:
    """Create a new project"""

    # Check if project with same owner and name already exists
    result = await db.execute(
        select(Project).filter(Project.owner == project.owner, Project.name == project.name)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project '{project.name}' already exists for owner '{project.owner}'",
        )

    db_project = Project(**project.model_dump())
    db.add(db_project)
    await db.commit()
    await db.refresh(db_project)
    return db_project


@router.get(
    "/",
    response_model=List[ProjectResponse],
    summary="List all projects",
    description="Retrieve all projects in the system",
)
async def list_projects(
    skip: int = 0, limit: int = 100, db: AsyncSession = Depends(get_db)
) -> List[Project]:
    """List all projects"""
    result = await db.execute(select(Project).offset(skip).limit(limit))
    return result.scalars().all()


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Retrieve a specific project by its ID",
)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)) -> Project:
    """Get project by ID"""
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )
    return project


@router.get(
    "/{project_id}/stats",
    response_model=ProjectWithCounts,
    summary="Get project with statistics",
    description="Retrieve project with entity counts",
)
async def get_project_stats(project_id: int, db: AsyncSession = Depends(get_db)) -> dict:
    """Get project with entity counts"""
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )

    # Get counts for all related entities
    repo_result = await db.execute(
        select(func.count(Repository.id)).filter(Repository.project_id == project_id)
    )
    repo_count = repo_result.scalar()

    tech_result = await db.execute(
        select(func.count(Technology.id)).filter(Technology.project_id == project_id)
    )
    tech_count = tech_result.scalar()

    task_result = await db.execute(
        select(func.count(ResearchTask.id)).filter(ResearchTask.project_id == project_id)
    )
    task_count = task_result.scalar()

    knowledge_result = await db.execute(
        select(func.count(KnowledgeEntry.id)).filter(KnowledgeEntry.project_id == project_id)
    )
    knowledge_count = knowledge_result.scalar()

    return {
        **project.__dict__,
        "repository_count": repo_count,
        "technology_count": tech_count,
        "research_task_count": task_count,
        "knowledge_entry_count": knowledge_count,
    }


@router.patch(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Update project",
    description="Update project details",
)
async def update_project(
    project_id: int, project_update: ProjectUpdate, db: AsyncSession = Depends(get_db)
) -> Project:
    """Update project"""
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )

    # Update only provided fields
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    await db.commit()
    await db.refresh(project)
    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Delete a project and ALL associated data (CASCADE DELETE)",
)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db)) -> None:
    """Delete project and all associated data

    WARNING: This will CASCADE DELETE all:
    - Repositories
    - Technologies
    - Research tasks
    - Knowledge entries
    - Webhooks
    - Rate limits
    """
    result = await db.execute(select(Project).filter(Project.id == project_id))
    project = result.scalar_one_or_none()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found",
        )

    await db.delete(project)
    await db.commit()
