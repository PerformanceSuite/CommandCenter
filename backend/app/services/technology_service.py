"""
Technology business logic service
Handles technology operations with transaction management
"""

from typing import Any, Dict, List, Optional

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
        self.repo = TechnologyRepository()

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
        # Use consolidated list_with_filters method (Rec 2.3: eliminates redundant queries)
        return await self.repo.list_with_filters(
            self.db,
            skip=skip,
            limit=limit,
            search_term=search,
            domain=domain,
            status=status_filter,
        )

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
        technology = await self.repo.get(self.db, technology_id)

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
        return await self.repo.get_by_title(self.db, title)

    async def create_technology(
        self, technology_data: TechnologyCreate, project_id: int
    ) -> Technology:
        """
        Create new technology

        Args:
            technology_data: Technology creation data
            project_id: Project ID for isolation (REQUIRED - must come from authenticated context)

        Returns:
            Created technology

        Raises:
            HTTPException: If technology with same title exists or invalid project_id
            ValueError: If project_id is None or invalid

        Note:
            Multi-tenant isolation: project_id is required and must come from authenticated
            user context. See app.auth.project_context for the roadmap to full multi-tenant
            support with User-Project relationships.
        """
        if not project_id or project_id <= 0:
            raise ValueError("project_id is required and must be a positive integer")

        # Check if technology with same title exists
        existing = await self.repo.get_by_title(self.db, technology_data.title)

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Technology '{technology_data.title}' already exists",
            )

        # Create technology with project_id
        tech_data = technology_data.model_dump()
        tech_data["project_id"] = project_id
        technology = await self.repo.create(self.db, obj_in=tech_data)

        return technology

    async def update_technology(
        self, technology_id: int, technology_data: TechnologyUpdate
    ) -> Technology:
        """
        Update technology (optimized to reduce redundant DB calls - Rec 2.5)

        Args:
            technology_id: Technology ID
            technology_data: Technology update data

        Returns:
            Updated technology

        Raises:
            HTTPException: If technology not found or title conflict
        """
        # Fetch technology once
        technology = await self.repo.get(self.db, technology_id)
        if not technology:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Technology {technology_id} not found",
            )

        # Check if title is being changed and new title already exists
        if technology_data.title and technology_data.title != technology.title:
            existing = await self.repo.get_by_title(self.db, technology_data.title)
            if existing:
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Technology '{technology_data.title}' already exists",
                )

        # Update fields directly using repository method
        update_data = technology_data.model_dump(exclude_unset=True)
        technology = await self.repo.update(self.db, db_obj=technology, obj_in=update_data)

        return technology

    async def delete_technology(self, technology_id: int) -> None:
        """
        Delete technology

        Args:
            technology_id: Technology ID

        Raises:
            HTTPException: If technology not found
        """
        # Verify technology exists (raises 404 if not found)
        await self.get_technology(technology_id)
        await self.repo.remove(self.db, id=technology_id)

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
        technology = await self.repo.update(
            self.db, db_obj=technology, obj_in={"status": new_status}
        )

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
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Priority must be between 1 and 5",
            )

        technology = await self.get_technology(technology_id)
        technology = await self.repo.update(
            self.db, db_obj=technology, obj_in={"priority": new_priority}
        )

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
        technology = await self.repo.update(
            self.db, db_obj=technology, obj_in={"relevance_score": new_score}
        )

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
        return await self.repo.get_high_priority(self.db, min_priority, limit)

    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get technology statistics

        Returns:
            Dictionary with statistics
        """
        total = await self.repo.count(self.db)
        by_status = await self.repo.count_by_status(self.db)
        by_domain = await self.repo.count_by_domain(self.db)
        high_priority = await self.repo.get_high_priority(self.db, min_priority=4, limit=5)

        return {
            "total": total,
            "by_status": by_status,
            "by_domain": by_domain,
            "high_priority": [
                {
                    "id": t.id,
                    "title": t.title,
                    "priority": t.priority,
                    "status": t.status.value,
                }
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
            self.db, search_term=query, domain=domain, status=status, skip=skip, limit=limit
        )
