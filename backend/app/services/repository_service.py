"""
Repository business logic service
Handles repository operations with transaction management
"""

from typing import Any, Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Repository
from app.repositories import RepositoryRepository
from app.schemas import RepositoryCreate, RepositoryUpdate

from .github_async import GitHubAsyncService


class RepositoryService:
    """Service layer for repository operations"""

    def __init__(self, db: AsyncSession):
        """
        Initialize repository service

        Args:
            db: Database session
        """
        self.db = db
        self.repo = RepositoryRepository()

    async def list_repositories(
        self,
        skip: int = 0,
        limit: int = 100,
        owner: Optional[str] = None,
        language: Optional[str] = None,
    ) -> List[Repository]:
        """
        List repositories with optional filters

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            owner: Optional owner filter
            language: Optional language filter

        Returns:
            List of repositories
        """
        if owner:
            return await self.repo.list_by_owner(self.db, owner, skip, limit)
        elif language:
            return await self.repo.search_by_language(self.db, language, skip, limit)
        else:
            return await self.repo.get_all(self.db, skip=skip, limit=limit)

    async def get_repository(self, repository_id: int) -> Repository:
        """
        Get repository by ID

        Args:
            repository_id: Repository ID

        Returns:
            Repository

        Raises:
            HTTPException: If repository not found
        """
        repository = await self.repo.get(self.db, repository_id)

        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository {repository_id} not found",
            )

        return repository

    async def get_repository_by_full_name(self, full_name: str) -> Optional[Repository]:
        """
        Get repository by full name

        Args:
            full_name: Repository full name (owner/name)

        Returns:
            Repository or None if not found
        """
        return await self.repo.get_by_full_name(self.db, full_name)

    async def create_repository(
        self, repository_data: RepositoryCreate, project_id: int
    ) -> Repository:
        """
        Create new repository

        Args:
            repository_data: Repository creation data
            project_id: Project ID for isolation (REQUIRED - must come from authenticated context)

        Returns:
            Created repository

        Raises:
            HTTPException: If repository already exists
            ValueError: If project_id is None or invalid

        Note:
            Multi-tenant isolation: project_id is required and must come from authenticated
            user context. See app.auth.project_context for the roadmap to full multi-tenant
            support with User-Project relationships.
        """
        if not project_id or project_id <= 0:
            raise ValueError("project_id is required and must be a positive integer")

        # Check if repository already exists
        full_name = f"{repository_data.owner}/{repository_data.name}"
        existing = await self.repo.get_by_full_name(self.db, full_name)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Repository {full_name} already exists",
            )

        # Create repository
        repository = await self.repo.create(
            **repository_data.model_dump(), full_name=full_name, project_id=project_id
        )

        await self.db.commit()
        await self.db.refresh(repository)

        return repository

    async def update_repository(
        self, repository_id: int, repository_data: RepositoryUpdate
    ) -> Repository:
        """
        Update repository

        Args:
            repository_id: Repository ID
            repository_data: Repository update data

        Returns:
            Updated repository

        Raises:
            HTTPException: If repository not found
        """
        repository = await self.get_repository(repository_id)

        # Update fields
        update_data = repository_data.model_dump(exclude_unset=True)
        repository = await self.repo.update(repository, **update_data)

        await self.db.commit()
        await self.db.refresh(repository)

        return repository

    async def delete_repository(self, repository_id: int) -> None:
        """
        Delete repository

        Args:
            repository_id: Repository ID

        Raises:
            HTTPException: If repository not found
        """
        repository = await self.get_repository(repository_id)
        await self.repo.delete(repository)
        await self.db.commit()

    async def sync_repository(self, repository_id: int, force: bool = False) -> Dict[str, Any]:
        """
        Sync repository with GitHub

        Args:
            repository_id: Repository ID
            force: Force sync even if no changes detected

        Returns:
            Sync result information

        Raises:
            HTTPException: If repository not found or sync fails
        """
        repository = await self.get_repository(repository_id)

        # Initialize async GitHub service
        async with GitHubAsyncService(access_token=repository.access_token) as github_service:
            try:
                # Sync with GitHub
                sync_info = await github_service.sync_repository(
                    owner=repository.owner,
                    name=repository.name,
                    last_known_sha=repository.last_commit_sha,
                )

                # Update repository with sync info
                update_fields = {
                    "last_commit_sha": sync_info.get("last_commit_sha"),
                    "last_commit_message": sync_info.get("last_commit_message"),
                    "last_commit_author": sync_info.get("last_commit_author"),
                    "last_commit_date": sync_info.get("last_commit_date"),
                    "last_synced_at": sync_info.get("last_synced_at"),
                    "stars": sync_info.get("stars", 0),
                    "forks": sync_info.get("forks", 0),
                    "language": sync_info.get("language"),
                    "description": sync_info.get("description"),
                }

                repository = await self.repo.update(repository, **update_fields)
                await self.db.commit()
                await self.db.refresh(repository)

                return {
                    "repository_id": repository.id,
                    "synced": sync_info["synced"],
                    "last_commit_sha": sync_info.get("last_commit_sha"),
                    "last_commit_message": sync_info.get("last_commit_message"),
                    "last_synced_at": sync_info["last_synced_at"],
                    "changes_detected": sync_info["changes_detected"],
                }

            except Exception as e:
                await self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to sync repository: {str(e)}",
                )

    async def import_from_github(
        self, owner: str, name: str, project_id: int, access_token: Optional[str] = None
    ) -> Repository:
        """
        Import repository from GitHub

        Args:
            owner: Repository owner
            name: Repository name
            project_id: Project ID for isolation (REQUIRED - must come from authenticated context)
            access_token: Optional access token

        Returns:
            Imported repository

        Raises:
            HTTPException: If import fails
            ValueError: If project_id is None or invalid
        """
        if not project_id or project_id <= 0:
            raise ValueError("project_id is required and must be a positive integer")
        # Check if already exists
        full_name = f"{owner}/{name}"
        existing = await self.repo.get_by_full_name(self.db, full_name)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Repository {full_name} already exists",
            )

        # Fetch from GitHub
        async with GitHubAsyncService(access_token=access_token) as github_service:
            try:
                repo_info = await github_service.get_repository_info(owner, name)

                # Create repository
                repository = await self.repo.create(
                    owner=repo_info["owner"],
                    name=repo_info["name"],
                    full_name=repo_info["full_name"],
                    description=repo_info.get("description"),
                    url=repo_info.get("url"),
                    clone_url=repo_info.get("clone_url"),
                    default_branch=repo_info.get("default_branch", "main"),
                    is_private=repo_info.get("is_private", False),
                    stars=repo_info.get("stars", 0),
                    forks=repo_info.get("forks", 0),
                    language=repo_info.get("language"),
                    github_id=repo_info.get("github_id"),
                    access_token=access_token,
                    project_id=project_id,
                )

                await self.db.commit()
                await self.db.refresh(repository)

                return repository

            except Exception as e:
                await self.db.rollback()
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Failed to import repository: {str(e)}",
                )

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get repository statistics

        Returns:
            Dictionary with statistics
        """
        total = await self.repo.count(self.db)
        recently_synced = await self.repo.get_recently_synced(self.db, limit=5)

        return {
            "total": total,
            "recently_synced": [
                {
                    "id": r.id,
                    "full_name": r.full_name,
                    "last_synced_at": r.last_synced_at,
                }
                for r in recently_synced
            ],
        }
