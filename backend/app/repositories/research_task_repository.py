"""
ResearchTask-specific data access operations
"""

from typing import Optional, List
from datetime import datetime
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import ResearchTask, TaskStatus
from .base import BaseRepository


class ResearchTaskRepository(BaseRepository[ResearchTask]):
    """ResearchTask data access layer"""

    def __init__(self, db: AsyncSession):
        super().__init__(ResearchTask, db)

    async def list_by_technology(
        self, technology_id: int, skip: int = 0, limit: int = 100
    ) -> List[ResearchTask]:
        """
        List tasks by technology

        Args:
            technology_id: Technology ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of research tasks
        """
        result = await self.db.execute(
            select(ResearchTask)
            .where(ResearchTask.technology_id == technology_id)
            .offset(skip)
            .limit(limit)
            .order_by(ResearchTask.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_repository(
        self, repository_id: int, skip: int = 0, limit: int = 100
    ) -> List[ResearchTask]:
        """
        List tasks by repository

        Args:
            repository_id: Repository ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of research tasks
        """
        result = await self.db.execute(
            select(ResearchTask)
            .where(ResearchTask.repository_id == repository_id)
            .offset(skip)
            .limit(limit)
            .order_by(ResearchTask.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_status(
        self, status: TaskStatus, skip: int = 0, limit: int = 100
    ) -> List[ResearchTask]:
        """
        List tasks by status

        Args:
            status: Task status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of research tasks
        """
        result = await self.db.execute(
            select(ResearchTask)
            .where(ResearchTask.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(ResearchTask.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_assignee(
        self, assigned_to: str, skip: int = 0, limit: int = 100
    ) -> List[ResearchTask]:
        """
        List tasks by assignee

        Args:
            assigned_to: Assignee username
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of research tasks
        """
        result = await self.db.execute(
            select(ResearchTask)
            .where(ResearchTask.assigned_to == assigned_to)
            .offset(skip)
            .limit(limit)
            .order_by(ResearchTask.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_overdue(self, limit: int = 100) -> List[ResearchTask]:
        """
        Get overdue tasks

        Args:
            limit: Maximum number of records to return

        Returns:
            List of overdue research tasks
        """
        now = datetime.utcnow()
        result = await self.db.execute(
            select(ResearchTask)
            .where(
                ResearchTask.due_date < now,
                ResearchTask.status.in_(
                    [
                        TaskStatus.PENDING,
                        TaskStatus.IN_PROGRESS,
                        TaskStatus.BLOCKED,
                    ]
                ),
            )
            .order_by(ResearchTask.due_date.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_upcoming(self, days: int = 7, limit: int = 100) -> List[ResearchTask]:
        """
        Get upcoming tasks due within specified days

        Args:
            days: Number of days to look ahead
            limit: Maximum number of records to return

        Returns:
            List of upcoming research tasks
        """
        from datetime import timedelta

        now = datetime.utcnow()
        future = now + timedelta(days=days)

        result = await self.db.execute(
            select(ResearchTask)
            .where(
                ResearchTask.due_date.between(now, future),
                ResearchTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            )
            .order_by(ResearchTask.due_date.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self) -> dict[str, int]:
        """
        Get count of tasks grouped by status

        Returns:
            Dictionary mapping status to count
        """
        counts = {}
        for status in TaskStatus:
            count = await self.count(status=status)
            counts[status.value] = count
        return counts

    async def get_statistics(
        self,
        technology_id: Optional[int] = None,
        repository_id: Optional[int] = None,
    ) -> dict:
        """
        Get task statistics

        Args:
            technology_id: Optional technology ID filter
            repository_id: Optional repository ID filter

        Returns:
            Dictionary with statistics
        """
        query = select(func.count(), ResearchTask.status)

        if technology_id:
            query = query.where(ResearchTask.technology_id == technology_id)
        if repository_id:
            query = query.where(ResearchTask.repository_id == repository_id)

        query = query.group_by(ResearchTask.status)

        result = await self.db.execute(query)
        status_counts = {status.value: 0 for status in TaskStatus}

        for count, status in result:
            status_counts[status.value] = count

        return {
            "by_status": status_counts,
            "total": sum(status_counts.values()),
        }
