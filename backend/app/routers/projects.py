"""
Project CRUD endpoints for multi-project isolation
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

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
    description="Create a new isolated project workspace"
)
def create_project(
    project: ProjectCreate,
    db: Session = Depends(get_db)
) -> Project:
    """Create a new project"""

    # Check if project with same owner and name already exists
    existing = db.query(Project).filter(
        Project.owner == project.owner,
        Project.name == project.name
    ).first()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Project '{project.name}' already exists for owner '{project.owner}'"
        )

    db_project = Project(**project.model_dump())
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return db_project


@router.get(
    "/",
    response_model=List[ProjectResponse],
    summary="List all projects",
    description="Retrieve all projects in the system"
)
def list_projects(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
) -> List[Project]:
    """List all projects"""
    return db.query(Project).offset(skip).limit(limit).all()


@router.get(
    "/{project_id}",
    response_model=ProjectResponse,
    summary="Get project by ID",
    description="Retrieve a specific project by its ID"
)
def get_project(
    project_id: int,
    db: Session = Depends(get_db)
) -> Project:
    """Get project by ID"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )
    return project


@router.get(
    "/{project_id}/stats",
    response_model=ProjectWithCounts,
    summary="Get project with statistics",
    description="Retrieve project with entity counts"
)
def get_project_stats(
    project_id: int,
    db: Session = Depends(get_db)
) -> dict:
    """Get project with entity counts"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )

    # Get counts for all related entities
    repo_count = db.query(func.count(Repository.id)).filter(
        Repository.project_id == project_id
    ).scalar()

    tech_count = db.query(func.count(Technology.id)).filter(
        Technology.project_id == project_id
    ).scalar()

    task_count = db.query(func.count(ResearchTask.id)).filter(
        ResearchTask.project_id == project_id
    ).scalar()

    knowledge_count = db.query(func.count(KnowledgeEntry.id)).filter(
        KnowledgeEntry.project_id == project_id
    ).scalar()

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
    description="Update project details"
)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db)
) -> Project:
    """Update project"""
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )

    # Update only provided fields
    update_data = project_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(project, field, value)

    db.commit()
    db.refresh(project)
    return project


@router.delete(
    "/{project_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete project",
    description="Delete a project and ALL associated data (CASCADE DELETE)"
)
def delete_project(
    project_id: int,
    db: Session = Depends(get_db)
) -> None:
    """Delete project and all associated data

    WARNING: This will CASCADE DELETE all:
    - Repositories
    - Technologies
    - Research tasks
    - Knowledge entries
    - Webhooks
    - Rate limits
    """
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project with id {project_id} not found"
        )

    db.delete(project)
    db.commit()
