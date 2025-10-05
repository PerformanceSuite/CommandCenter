"""
Repository management endpoints
"""

from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models import Repository
from app.schemas import (
    RepositoryCreate,
    RepositoryUpdate,
    RepositoryResponse,
    RepositorySyncRequest,
    RepositorySyncResponse,
)
from app.services import GitHubService

router = APIRouter(prefix="/repositories", tags=["repositories"])


@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
) -> List[Repository]:
    """List all repositories"""
    result = await db.execute(
        select(Repository)
        .offset(skip)
        .limit(limit)
        .order_by(Repository.updated_at.desc())
    )
    return result.scalars().all()


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: int,
    db: AsyncSession = Depends(get_db)
) -> Repository:
    """Get repository by ID"""
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {repository_id} not found"
        )

    return repository


@router.post("/", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    repository_data: RepositoryCreate,
    db: AsyncSession = Depends(get_db)
) -> Repository:
    """Create a new repository"""
    # Check if repository already exists
    full_name = f"{repository_data.owner}/{repository_data.name}"
    result = await db.execute(
        select(Repository).where(Repository.full_name == full_name)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository {full_name} already exists"
        )

    # Create repository
    repository = Repository(
        **repository_data.model_dump(),
        full_name=full_name
    )

    db.add(repository)
    await db.commit()
    await db.refresh(repository)

    return repository


@router.patch("/{repository_id}", response_model=RepositoryResponse)
async def update_repository(
    repository_id: int,
    repository_data: RepositoryUpdate,
    db: AsyncSession = Depends(get_db)
) -> Repository:
    """Update repository"""
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {repository_id} not found"
        )

    # Update fields
    update_data = repository_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(repository, field, value)

    await db.commit()
    await db.refresh(repository)

    return repository


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repository_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete repository"""
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {repository_id} not found"
        )

    await db.delete(repository)
    await db.commit()


@router.post("/{repository_id}/sync", response_model=RepositorySyncResponse)
async def sync_repository(
    repository_id: int,
    sync_request: RepositorySyncRequest,
    db: AsyncSession = Depends(get_db)
) -> RepositorySyncResponse:
    """Sync repository with GitHub"""
    result = await db.execute(
        select(Repository).where(Repository.id == repository_id)
    )
    repository = result.scalar_one_or_none()

    if not repository:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Repository {repository_id} not found"
        )

    # Initialize GitHub service
    github_service = GitHubService(access_token=repository.access_token)

    try:
        # Sync with GitHub
        sync_info = await github_service.sync_repository(
            owner=repository.owner,
            name=repository.name,
            last_known_sha=repository.last_commit_sha
        )

        # Update repository with sync info
        repository.last_commit_sha = sync_info.get("last_commit_sha")
        repository.last_commit_message = sync_info.get("last_commit_message")
        repository.last_commit_author = sync_info.get("last_commit_author")
        repository.last_commit_date = sync_info.get("last_commit_date")
        repository.last_synced_at = sync_info.get("last_synced_at")
        repository.stars = sync_info.get("stars", 0)
        repository.forks = sync_info.get("forks", 0)
        repository.language = sync_info.get("language")

        await db.commit()
        await db.refresh(repository)

        return RepositorySyncResponse(
            repository_id=repository.id,
            synced=sync_info["synced"],
            last_commit_sha=sync_info.get("last_commit_sha"),
            last_commit_message=sync_info.get("last_commit_message"),
            last_synced_at=sync_info["last_synced_at"],
            changes_detected=sync_info["changes_detected"]
        )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to sync repository: {str(e)}"
        )
