"""
Repository management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Repository
from app.schemas import (
    RepositoryCreate,
    RepositoryUpdate,
    RepositoryResponse,
    RepositorySyncRequest,
    RepositorySyncResponse,
)
from app.services import RepositoryService

router = APIRouter(prefix="/repositories", tags=["repositories"])


def get_repository_service(
    db: AsyncSession = Depends(get_db),
) -> RepositoryService:
    """Dependency to get repository service instance"""
    return RepositoryService(db)


@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    owner: Optional[str] = Query(
        None, description="Filter by repository owner"
    ),
    language: Optional[str] = Query(
        None, description="Filter by programming language"
    ),
    service: RepositoryService = Depends(get_repository_service),
) -> List[Repository]:
    """List all repositories with optional filters"""
    return await service.list_repositories(skip, limit, owner, language)


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: int,
    service: RepositoryService = Depends(get_repository_service),
) -> Repository:
    """Get repository by ID"""
    return await service.get_repository(repository_id)


@router.post(
    "/", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED
)
async def create_repository(
    repository_data: RepositoryCreate,
    service: RepositoryService = Depends(get_repository_service),
) -> Repository:
    """Create a new repository"""
    return await service.create_repository(repository_data)


@router.patch("/{repository_id}", response_model=RepositoryResponse)
async def update_repository(
    repository_id: int,
    repository_data: RepositoryUpdate,
    service: RepositoryService = Depends(get_repository_service),
) -> Repository:
    """Update repository"""
    return await service.update_repository(repository_id, repository_data)


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repository_id: int,
    service: RepositoryService = Depends(get_repository_service),
) -> None:
    """Delete repository"""
    await service.delete_repository(repository_id)


@router.post("/{repository_id}/sync", response_model=RepositorySyncResponse)
async def sync_repository(
    repository_id: int,
    sync_request: RepositorySyncRequest,
    service: RepositoryService = Depends(get_repository_service),
) -> RepositorySyncResponse:
    """Sync repository with GitHub"""
    sync_result = await service.sync_repository(
        repository_id,
        force=sync_request.force if hasattr(sync_request, "force") else False,
    )
    return RepositorySyncResponse(**sync_result)
