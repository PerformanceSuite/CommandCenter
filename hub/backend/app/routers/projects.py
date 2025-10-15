"""
Projects API - CRUD operations for CommandCenter projects
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Project
from app.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectStats
from app.services.project_service import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


def get_project_service(db: AsyncSession = Depends(get_db)) -> ProjectService:
    """Dependency to get project service"""
    return ProjectService(db)


@router.get("/stats", response_model=ProjectStats)
async def get_stats(
    service: ProjectService = Depends(get_project_service),
):
    """Get project statistics"""
    return await service.get_stats()


@router.get("/", response_model=List[ProjectResponse])
async def list_projects(
    service: ProjectService = Depends(get_project_service),
):
    """List all CommandCenter projects"""
    return await service.list_projects()


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(
    project_id: int,
    service: ProjectService = Depends(get_project_service),
):
    """Get project by ID"""
    project = await service.get_project(project_id)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project


@router.post("/", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
async def create_project(
    project_data: ProjectCreate,
    service: ProjectService = Depends(get_project_service),
):
    """
    Create new CommandCenter project

    This will:
    1. Create project entry in registry
    2. Clone CommandCenter to project/commandcenter/
    3. Generate .env with unique ports
    4. Configure docker-compose
    """
    return await service.create_project(project_data)


@router.patch("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    project_data: ProjectUpdate,
    service: ProjectService = Depends(get_project_service),
):
    """Update project details"""
    project = await service.update_project(project_id, project_data)
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_project(
    project_id: int,
    delete_files: bool = False,
    service: ProjectService = Depends(get_project_service),
):
    """
    Delete project from registry

    Query Parameters:
    - delete_files: If true, also stops containers and deletes CommandCenter directory

    Examples:
    - DELETE /api/projects/1 - Only remove from registry
    - DELETE /api/projects/1?delete_files=true - Remove from registry AND delete files
    """
    success = await service.delete_project(project_id, delete_files=delete_files)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Project {project_id} not found",
        )
