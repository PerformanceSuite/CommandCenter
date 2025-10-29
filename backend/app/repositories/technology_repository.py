"""
Technology-specific data access operations
"""

from typing import Optional, List
from sqlalchemy import select, func, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Technology, TechnologyDomain, TechnologyStatus
from .base import BaseRepository


class TechnologyRepository(BaseRepository[Technology]):
    """Technology data access layer"""

    def __init__(self):
        super().__init__(Technology)

    async def get_by_title(self, db: AsyncSession, title: str) -> Optional[Technology]:
        """
        Get technology by title

        Args:
            db: The database session
            title: Technology title

        Returns:
            Technology or None if not found
        """
        result = await db.execute(select(Technology).where(Technology.title == title))
        return result.scalar_one_or_none()

    async def list_by_domain(
        self, db: AsyncSession, domain: TechnologyDomain, skip: int = 0, limit: int = 100
    ) -> List[Technology]:
        """
        List technologies by domain

        Args:
            db: The database session
            domain: Technology domain
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of technologies
        """
        result = await db.execute(
            select(Technology)
            .where(Technology.domain == domain)
            .offset(skip)
            .limit(limit)
            .order_by(Technology.priority.desc(), Technology.relevance_score.desc())
        )
        return list(result.scalars().all())

    async def list_by_status(
        self, db: AsyncSession, status: TechnologyStatus, skip: int = 0, limit: int = 100
    ) -> List[Technology]:
        """
        List technologies by status

        Args:
            db: The database session
            status: Technology status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of technologies
        """
        result = await db.execute(
            select(Technology)
            .where(Technology.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(Technology.priority.desc(), Technology.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_with_filters(
        self,
        db: AsyncSession,
        skip: int = 0,
        limit: int = 100,
        search_term: Optional[str] = None,
        domain: Optional[TechnologyDomain] = None,
        status: Optional[TechnologyStatus] = None,
    ) -> tuple[List[Technology], int]:
        """
        List technologies with optional filters (consolidates all list/search methods)

        Args:
            db: The database session
            skip: Number of records to skip
            limit: Maximum number of records to return
            search_term: Optional search term for title, description, tags
            domain: Optional domain filter
            status: Optional status filter

        Returns:
            Tuple of (list of technologies, total count)
        """
        # Build base query
        query = select(Technology)

        # Apply search filter
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.where(
                or_(
                    Technology.title.ilike(search_pattern),
                    Technology.description.ilike(search_pattern),
                    Technology.tags.ilike(search_pattern),
                )
            )

        # Apply domain filter
        if domain:
            query = query.where(Technology.domain == domain)

        # Apply status filter
        if status:
            query = query.where(Technology.status == status)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = (
            query.offset(skip)
            .limit(limit)
            .order_by(
                Technology.priority.desc(),
                Technology.relevance_score.desc(),
                Technology.updated_at.desc(),
            )
        )

        result = await db.execute(query)
        technologies = list(result.scalars().all())

        return technologies, total

    async def search(
        self,
        db: AsyncSession,
        search_term: str,
        domain: Optional[TechnologyDomain] = None,
        status: Optional[TechnologyStatus] = None,
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[Technology], int]:
        """
        Search technologies with filters (delegates to list_with_filters)

        Args:
            db: The database session
            search_term: Search term for title, description, tags
            domain: Optional domain filter
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            Tuple of (list of technologies, total count)
        """
        return await self.list_with_filters(
            db=db,
            skip=skip,
            limit=limit,
            search_term=search_term,
            domain=domain,
            status=status,
        )

    async def get_high_priority(
        self, db: AsyncSession, min_priority: int = 4, limit: int = 10
    ) -> List[Technology]:
        """
        Get high priority technologies

        Args:
            db: The database session
            min_priority: Minimum priority level
            limit: Maximum number of records to return

        Returns:
            List of high priority technologies
        """
        result = await db.execute(
            select(Technology)
            .where(Technology.priority >= min_priority)
            .order_by(Technology.priority.desc(), Technology.relevance_score.desc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self, db: AsyncSession) -> dict[str, int]:
        """
        Get count of technologies grouped by status

        Args:
            db: The database session

        Returns:
            Dictionary mapping status to count
        """
        result = await db.execute(
            select(Technology.status, func.count(Technology.id))
            .group_by(Technology.status)
        )
        return {status.value: count for status, count in result}

    async def count_by_domain(self, db: AsyncSession) -> dict[str, int]:
        """
        Get count of technologies grouped by domain

        Args:
            db: The database session

        Returns:
            Dictionary mapping domain to count
        """
        result = await db.execute(
            select(Technology.domain, func.count(Technology.id))
            .group_by(Technology.domain)
        )
        return {domain.value: count for domain, count in result}
