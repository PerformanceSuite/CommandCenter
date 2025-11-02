"""
Project CRUD endpoints for multi-project isolation and project analysis
"""

import os
from pathlib import Path
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
from app.schemas.project_analysis import (
    ProjectAnalysisRequest,
    ProjectAnalysisResult,
    AnalysisStatistics,
)
from app.services.project_analyzer import ProjectAnalyzer

router = APIRouter(prefix="/projects", tags=["projects"])


# Security: Allowed directories for project analysis
# Configure via environment variable or use defaults
ALLOWED_ANALYSIS_DIRS = os.getenv(
    "ALLOWED_ANALYSIS_DIRS", "/projects,/repositories,/tmp/analysis,/workspace"
).split(",")
ALLOWED_ANALYSIS_DIRS = [Path(d.strip()) for d in ALLOWED_ANALYSIS_DIRS if d.strip()]


def validate_project_path(path: str) -> Path:
    """
    Validate project path to prevent path traversal attacks.

    Security: Ensures the project path is within allowed directories
    to prevent unauthorized file system access.

    Args:
        path: User-provided project path

    Returns:
        Resolved Path object if valid

    Raises:
        ValueError: If path is invalid or outside allowed directories
    """
    try:
        project_path = Path(path).resolve()
    except (ValueError, RuntimeError) as e:
        raise ValueError(f"Invalid path format: {path}") from e

    # Check if path exists
    if not project_path.exists():
        raise ValueError(f"Path does not exist: {path}")

    # Check if path is within allowed directories
    is_allowed = any(
        project_path.is_relative_to(allowed_dir)
        for allowed_dir in ALLOWED_ANALYSIS_DIRS
        if allowed_dir.exists()
    )

    if not is_allowed:
        allowed_str = ", ".join(str(d) for d in ALLOWED_ANALYSIS_DIRS)
        raise ValueError(
            f"Path '{path}' is not within allowed analysis directories. " f"Allowed: {allowed_str}"
        )

    return project_path


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


# Project Analysis Endpoints


@router.post(
    "/analyze",
    response_model=ProjectAnalysisResult,
    summary="Analyze project codebase",
    description="Scan project to detect dependencies, technologies, and research gaps",
)
async def analyze_project(
    request: ProjectAnalysisRequest, db: AsyncSession = Depends(get_db)
) -> ProjectAnalysisResult:
    """
    Analyze a project directory.

    Scans codebase to detect:
    - Dependencies and versions
    - Technologies and frameworks
    - Code metrics and complexity
    - Research gaps and upgrade opportunities

    Security: Validates project path to prevent path traversal attacks.
    """
    # Security: Validate path before analysis
    try:
        validated_path = validate_project_path(request.project_path)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid project path: {str(e)}",
        )

    analyzer = ProjectAnalyzer(db)

    try:
        result = await analyzer.analyze_project(
            project_path=str(validated_path), use_cache=request.use_cache
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        )


@router.get(
    "/analysis/{analysis_id}",
    response_model=ProjectAnalysisResult,
    summary="Get cached analysis",
    description="Retrieve previously cached project analysis by ID",
)
async def get_analysis(
    analysis_id: int, db: AsyncSession = Depends(get_db)
) -> ProjectAnalysisResult:
    """Get cached project analysis by ID"""
    analyzer = ProjectAnalyzer(db)
    result = await analyzer.get_analysis_by_id(analysis_id)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Analysis {analysis_id} not found",
        )

    return result


@router.get(
    "/analysis/statistics",
    response_model=AnalysisStatistics,
    summary="Get analysis statistics",
    description="Get aggregate statistics across all project analyses",
)
async def get_analysis_statistics(
    db: AsyncSession = Depends(get_db),
) -> AnalysisStatistics:
    """Get analysis statistics"""
    from app.models.project_analysis import ProjectAnalysis

    # Count total analyses
    total_result = await db.execute(select(func.count(ProjectAnalysis.id)))
    total_analyses = total_result.scalar()

    # Count unique projects
    unique_result = await db.execute(select(func.count(ProjectAnalysis.project_path.distinct())))
    unique_projects = unique_result.scalar()

    # Get all analyses to aggregate stats
    analyses_result = await db.execute(select(ProjectAnalysis))
    analyses = analyses_result.scalars().all()

    # Aggregate counts
    total_deps = 0
    total_techs = 0
    total_gaps = 0
    critical_gaps = 0
    high_gaps = 0
    outdated_deps = 0

    for analysis in analyses:
        if analysis.dependencies:
            deps = analysis.dependencies.get("items", [])
            total_deps += len(deps)
            outdated_deps += sum(1 for dep in deps if dep.get("is_outdated", False))

        if analysis.detected_technologies:
            total_techs += len(analysis.detected_technologies.get("items", []))

        if analysis.research_gaps:
            gaps = analysis.research_gaps.get("items", [])
            total_gaps += len(gaps)
            critical_gaps += sum(1 for gap in gaps if gap.get("severity") == "critical")
            high_gaps += sum(1 for gap in gaps if gap.get("severity") == "high")

    return AnalysisStatistics(
        total_analyses=total_analyses,
        unique_projects=unique_projects,
        total_dependencies=total_deps,
        total_technologies=total_techs,
        total_gaps=total_gaps,
        critical_gaps=critical_gaps,
        high_gaps=high_gaps,
        outdated_dependencies=outdated_deps,
    )
