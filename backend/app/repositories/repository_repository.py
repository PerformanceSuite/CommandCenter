"""
Repository-specific data access operations
"""

from typing import Optional, List
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Repository
from .base import BaseRepository


class RepositoryRepository(BaseRepository[Repository]):
    """Repository data access layer"""

    def __init__(self, db: AsyncSession):
        super().__init__(Repository, db)

    async def get_by_full_name(self, full_name: str) -> Optional[Repository]:
        """
        Get repository by full name (owner/name)

        Args:
            full_name: Repository full name

        Returns:
            Repository or None if not found
        """
        return await self.find_one(full_name=full_name)

    async def get_by_owner_and_name(
        self, owner: str, name: str
    ) -> Optional[Repository]:
        """
        Get repository by owner and name

        Args:
            owner: Repository owner
            name: Repository name

        Returns:
            Repository or None if not found
        """
        result = await self.db.execute(
            select(Repository).where(
                Repository.owner == owner, Repository.name == name
            )
        )
        return result.scalar_one_or_none()

    async def list_by_owner(
        self, owner: str, skip: int = 0, limit: int = 100
    ) -> List[Repository]:
        """
        List repositories by owner

        Args:
            owner: Repository owner
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of repositories
        """
        result = await self.db.execute(
            select(Repository)
            .where(Repository.owner == owner)
            .offset(skip)
            .limit(limit)
            .order_by(Repository.updated_at.desc())
        )
        return list(result.scalars().all())

    async def search_by_language(
        self, language: str, skip: int = 0, limit: int = 100
    ) -> List[Repository]:
        """
        Search repositories by programming language

        Args:
            language: Programming language
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of repositories
        """
        result = await self.db.execute(
            select(Repository)
            .where(Repository.language == language)
            .offset(skip)
            .limit(limit)
            .order_by(Repository.stars.desc())
        )
        return list(result.scalars().all())

    async def get_recently_synced(self, limit: int = 10) -> List[Repository]:
        """
        Get recently synced repositories

        Args:
            limit: Maximum number of records to return

        Returns:
            List of repositories
        """
        result = await self.db.execute(
            select(Repository)
            .where(Repository.last_synced_at.isnot(None))
            .order_by(Repository.last_synced_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())
