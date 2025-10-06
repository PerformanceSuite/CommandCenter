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

    def __init__(self, db: AsyncSession):
        super().__init__(Technology, db)

    async def get_by_title(self, title: str) -> Optional[Technology]:
        """
        Get technology by title

        Args:
            title: Technology title

        Returns:
            Technology or None if not found
        """
        return await self.find_one(title=title)

    async def list_by_domain(
        self,
        domain: TechnologyDomain,
        skip: int = 0,
        limit: int = 100
    ) -> List[Technology]:
        """
        List technologies by domain

        Args:
            domain: Technology domain
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of technologies
        """
        result = await self.db.execute(
            select(Technology)
            .where(Technology.domain == domain)
            .offset(skip)
            .limit(limit)
            .order_by(
                Technology.priority.desc(),
                Technology.relevance_score.desc()
            )
        )
        return list(result.scalars().all())

    async def list_by_status(
        self,
        status: TechnologyStatus,
        skip: int = 0,
        limit: int = 100
    ) -> List[Technology]:
        """
        List technologies by status

        Args:
            status: Technology status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of technologies
        """
        result = await self.db.execute(
            select(Technology)
            .where(Technology.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(
                Technology.priority.desc(),
                Technology.updated_at.desc()
            )
        )
        return list(result.scalars().all())

    async def search(
        self,
        search_term: str,
        domain: Optional[TechnologyDomain] = None,
        status: Optional[TechnologyStatus] = None,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Technology], int]:
        """
        Search technologies with filters

        Args:
            search_term: Search term for title, description, tags
            domain: Optional domain filter
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records to return

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
                    Technology.tags.ilike(search_pattern)
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
        total_result = await self.db.execute(count_query)
        total = total_result.scalar() or 0

        # Apply pagination and ordering
        query = query.offset(skip).limit(limit).order_by(
            Technology.priority.desc(),
            Technology.relevance_score.desc(),
            Technology.updated_at.desc()
        )

        result = await self.db.execute(query)
        technologies = list(result.scalars().all())

        return technologies, total

    async def get_high_priority(
        self,
        min_priority: int = 4,
        limit: int = 10
    ) -> List[Technology]:
        """
        Get high priority technologies

        Args:
            min_priority: Minimum priority level
            limit: Maximum number of records to return

        Returns:
            List of high priority technologies
        """
        result = await self.db.execute(
            select(Technology)
            .where(Technology.priority >= min_priority)
            .order_by(
                Technology.priority.desc(),
                Technology.relevance_score.desc()
            )
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        """
        Get count of technologies grouped by status

        Returns:
            Dictionary mapping status to count
        """
        counts = {}
        for status in TechnologyStatus:
            count = await self.count(status=status)
            counts[status.value] = count
        return counts

    async def count_by_domain(self) -> dict[str, int]:
        """
        Get count of technologies grouped by domain

        Returns:
            Dictionary mapping domain to count
        """
        counts = {}
        for domain in TechnologyDomain:
            count = await self.count(domain=domain)
            counts[domain.value] = count
        return counts
