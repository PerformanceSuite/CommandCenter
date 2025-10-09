"""
Technology business logic service
Handles technology operations with transaction management
"""

from typing import Optional, List, Dict, Any
from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Technology, TechnologyDomain, TechnologyStatus
from app.repositories import TechnologyRepository
from app.schemas import TechnologyCreate, TechnologyUpdate


class TechnologyService:
    """Service layer for technology operations"""

    def __init__(self, db: AsyncSession):
        """
        Initialize technology service

        Args:
            db: Database session
        """
        self.db = db
        self.repo = TechnologyRepository(db)

    async def list_technologies(
        self,
        skip: int = 0,
        limit: int = 50,
        domain: Optional[TechnologyDomain] = None,
        status_filter: Optional[TechnologyStatus] = None,
        search: Optional[str] = None,
    ) -> tuple[List[Technology], int]:
        """
        List technologies with filtering and pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            domain: Optional domain filter
            status_filter: Optional status filter
            search: Optional search term

        Returns:
            Tuple of (list of technologies, total count)
        """
        if search:
            return await self.repo.search(
                search_term=search, domain=domain, status=status_filter, skip=skip, limit=limit
            )
        elif domain:
            technologies = await self.repo.list_by_domain(domain, skip, limit)
            total = await self.repo.count(domain=domain)
            return technologies, total
        elif status_filter:
            technologies = await self.repo.list_by_status(status_filter, skip, limit)
            total = await self.repo.count(status=status_filter)
            return technologies, total
        else:
            technologies = await self.repo.get_all(skip, limit)
            total = await self.repo.count()
            return technologies, total

    async def get_technology(self, technology_id: int) -> Technology:
        """
        Get technology by ID

        Args:
            technology_id: Technology ID

        Returns:
            Technology

        Raises:
            HTTPException: If technology not found
        """
        technology = await self.repo.get_by_id(technology_id)

        if not technology:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Technology {technology_id} not found",
            )

        return technology

    async def get_technology_by_title(self, title: str) -> Optional[Technology]:
        """
        Get technology by title

        Args:
            title: Technology title

        Returns:
            Technology or None if not found
        """
        return await self.repo.get_by_title(title)

    async def create_technology(self, technology_data: TechnologyCreate) -> Technology:
        """
        Create new technology

        Args:
            technology_data: Technology creation data

        Returns:
            Created technology

        Raises:
            HTTPException: If technology with same title exists
        """
        # Check if technology with same title exists
        existing = await self.repo.get_by_title(technology_data.title)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Technology '{technology_data.title}' already exists",
            )

        # Create technology
        technology = await self.repo.create(**technology_data.model_dump())

        await self.db.commit()
        await self.db.refresh(technology)

        return technology

    async def update_technology(
        self, technology_id: int, technology_data: TechnologyUpdate
    ) -> Technology:
        """
        Update technology

        Args:
            technology_id: Technology ID
            technology_data: Technology update data

        Returns:
            Updated technology

        Raises:
            HTTPException: If technology not found
        """
        technology = await self.get_technology(technology_id)

        # Check if title is being changed and new title already exists
        if technology_data.title and technology_data.title != technology.title:
            existing = await self.repo.get_by_title(technology_data.title)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Technology '{technology_data.title}' already exists",
                )

        # Update fields
        update_data = technology_data.model_dump(exclude_unset=True)
        technology = await self.repo.update(technology, **update_data)

        await self.db.commit()
        await self.db.refresh(technology)

        return technology

    async def delete_technology(self, technology_id: int) -> None:
        """
        Delete technology

        Args:
            technology_id: Technology ID

        Raises:
            HTTPException: If technology not found
        """
        technology = await self.get_technology(technology_id)
        await self.repo.delete(technology)
        await self.db.commit()

    async def update_status(self, technology_id: int, new_status: TechnologyStatus) -> Technology:
        """
        Update technology status

        Args:
            technology_id: Technology ID
            new_status: New status

        Returns:
            Updated technology

        Raises:
            HTTPException: If technology not found
        """
        technology = await self.get_technology(technology_id)
        technology = await self.repo.update(technology, status=new_status)

        await self.db.commit()
        await self.db.refresh(technology)

        return technology

    async def update_priority(self, technology_id: int, new_priority: int) -> Technology:
        """
        Update technology priority

        Args:
            technology_id: Technology ID
            new_priority: New priority (1-5)

        Returns:
            Updated technology

        Raises:
            HTTPException: If technology not found or invalid priority
        """
        if not 1 <= new_priority <= 5:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Priority must be between 1 and 5"
            )

        technology = await self.get_technology(technology_id)
        technology = await self.repo.update(technology, priority=new_priority)

        await self.db.commit()
        await self.db.refresh(technology)

        return technology

    async def update_relevance_score(self, technology_id: int, new_score: int) -> Technology:
        """
        Update technology relevance score

        Args:
            technology_id: Technology ID
            new_score: New relevance score (0-100)

        Returns:
            Updated technology

        Raises:
            HTTPException: If technology not found or invalid score
        """
        if not 0 <= new_score <= 100:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Relevance score must be between 0 and 100",
            )

        technology = await self.get_technology(technology_id)
        technology = await self.repo.update(technology, relevance_score=new_score)

        await self.db.commit()
        await self.db.refresh(technology)

        return technology

    async def get_high_priority_technologies(
        self, min_priority: int = 4, limit: int = 10
    ) -> List[Technology]:
        """
        Get high priority technologies

        Args:
            min_priority: Minimum priority level
            limit: Maximum number of results

        Returns:
            List of high priority technologies
        """
        return await self.repo.get_high_priority(min_priority, limit)

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get technology statistics

        Returns:
            Dictionary with statistics
        """
        total = await self.repo.count()
        by_status = await self.repo.count_by_status()
        by_domain = await self.repo.count_by_domain()
        high_priority = await self.repo.get_high_priority(min_priority=4, limit=5)

        return {
            "total": total,
            "by_status": by_status,
            "by_domain": by_domain,
            "high_priority": [
                {"id": t.id, "title": t.title, "priority": t.priority, "status": t.status.value}
                for t in high_priority
            ],
        }

    async def search_technologies(
        self,
        query: str,
        domain: Optional[TechnologyDomain] = None,
        status: Optional[TechnologyStatus] = None,
        skip: int = 0,
        limit: int = 50,
    ) -> tuple[List[Technology], int]:
        """
        Search technologies

        Args:
            query: Search query
            domain: Optional domain filter
            status: Optional status filter
            skip: Number of records to skip
            limit: Maximum number of records

        Returns:
            Tuple of (list of technologies, total count)
        """
        return await self.repo.search(
            search_term=query, domain=domain, status=status, skip=skip, limit=limit
        )
