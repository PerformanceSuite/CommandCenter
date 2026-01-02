"""
Repository-specific data access operations
"""

from typing import List, Optional

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Repository

from .base import BaseRepository


class RepositoryRepository(BaseRepository[Repository]):
    """Repository data access layer"""

    def __init__(self):
        super().__init__(Repository)

    async def get_by_full_name(self, db: AsyncSession, full_name: str) -> Optional[Repository]:
        """
        Get repository by full name (owner/name)

        Args:
            db: The database session
            full_name: Repository full name

        Returns:
            Repository or None if not found
        """
        result = await db.execute(select(Repository).where(Repository.full_name == full_name))
        return result.scalar_one_or_none()

    async def get_by_owner_and_name(
        self, db: AsyncSession, owner: str, name: str
    ) -> Optional[Repository]:
        """
        Get repository by owner and name

        Args:
            db: The database session
            owner: Repository owner
            name: Repository name

        Returns:
            Repository or None if not found
        """
        result = await db.execute(
            select(Repository).where(Repository.owner == owner, Repository.name == name)
        )
        return result.scalar_one_or_none()

    async def list_by_owner(
        self, db: AsyncSession, owner: str, skip: int = 0, limit: int = 100
    ) -> List[Repository]:
        """
        List repositories by owner

        Args:
            db: The database session
            owner: Repository owner
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of repositories
        """
        result = await db.execute(
            select(Repository)
            .where(Repository.owner == owner)
            .offset(skip)
            .limit(limit)
            .order_by(Repository.updated_at.desc())
        )
        return list(result.scalars().all())

    async def search_by_language(
        self, db: AsyncSession, language: str, skip: int = 0, limit: int = 100
    ) -> List[Repository]:
        """
        Search repositories by programming language

        Args:
            db: The database session
            language: Programming language
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of repositories
        """
        result = await db.execute(
            select(Repository)
            .where(Repository.language == language)
            .offset(skip)
            .limit(limit)
            .order_by(Repository.stars.desc())
        )
        return list(result.scalars().all())

    async def get_recently_synced(self, db: AsyncSession, limit: int = 10) -> List[Repository]:
        """
        Get recently synced repositories

        Args:
            db: The database session
            limit: Maximum number of records to return

        Returns:
            List of repositories
        """
        result = await db.execute(
            select(Repository)
            .where(Repository.last_synced_at.isnot(None))
            .order_by(Repository.last_synced_at.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count(self, db: AsyncSession) -> int:
        """
        Count total repositories

        Args:
            db: The database session

        Returns:
            Total count of repositories
        """
        result = await db.execute(select(func.count(Repository.id)))
        return result.scalar_one()
