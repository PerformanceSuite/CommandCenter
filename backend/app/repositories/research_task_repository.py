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

    def __init__(self):
        super().__init__(ResearchTask)

    async def list_by_technology(
        self, db: AsyncSession, technology_id: int, skip: int = 0, limit: int = 100
    ) -> List[ResearchTask]:
        """
        List tasks by technology

        Args:
            db: The database session
            technology_id: Technology ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of research tasks
        """
        result = await db.execute(
            select(ResearchTask)
            .where(ResearchTask.technology_id == technology_id)
            .offset(skip)
            .limit(limit)
            .order_by(ResearchTask.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_repository(
        self, db: AsyncSession, repository_id: int, skip: int = 0, limit: int = 100
    ) -> List[ResearchTask]:
        """
        List tasks by repository

        Args:
            db: The database session
            repository_id: Repository ID
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of research tasks
        """
        result = await db.execute(
            select(ResearchTask)
            .where(ResearchTask.repository_id == repository_id)
            .offset(skip)
            .limit(limit)
            .order_by(ResearchTask.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_status(
        self, db: AsyncSession, status: TaskStatus, skip: int = 0, limit: int = 100
    ) -> List[ResearchTask]:
        """
        List tasks by status

        Args:
            db: The database session
            status: Task status
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of research tasks
        """
        result = await db.execute(
            select(ResearchTask)
            .where(ResearchTask.status == status)
            .offset(skip)
            .limit(limit)
            .order_by(ResearchTask.updated_at.desc())
        )
        return list(result.scalars().all())

    async def list_by_assignee(
        self, db: AsyncSession, assigned_to: str, skip: int = 0, limit: int = 100
    ) -> List[ResearchTask]:
        """
        List tasks by assignee

        Args:
            db: The database session
            assigned_to: Assignee username
            skip: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of research tasks
        """
        result = await db.execute(
            select(ResearchTask)
            .where(ResearchTask.assigned_to == assigned_to)
            .offset(skip)
            .limit(limit)
            .order_by(ResearchTask.updated_at.desc())
        )
        return list(result.scalars().all())

    async def get_overdue(
        self, db: AsyncSession, limit: int = 100
    ) -> List[ResearchTask]:
        """
        Get overdue tasks

        Args:
            db: The database session
            limit: Maximum number of records to return

        Returns:
            List of overdue research tasks
        """
        now = datetime.utcnow()
        result = await db.execute(
            select(ResearchTask)
            .where(
                ResearchTask.due_date < now,
                ResearchTask.status.in_(
                    [TaskStatus.PENDING, TaskStatus.IN_PROGRESS, TaskStatus.BLOCKED]
                ),
            )
            .order_by(ResearchTask.due_date.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def get_upcoming(
        self, db: AsyncSession, days: int = 7, limit: int = 100
    ) -> List[ResearchTask]:
        """
        Get upcoming tasks due within specified days

        Args:
            db: The database session
            days: Number of days to look ahead
            limit: Maximum number of records to return

        Returns:
            List of upcoming research tasks
        """
        from datetime import timedelta

        now = datetime.utcnow()
        future = now + timedelta(days=days)

        result = await db.execute(
            select(ResearchTask)
            .where(
                ResearchTask.due_date.between(now, future),
                ResearchTask.status.in_([TaskStatus.PENDING, TaskStatus.IN_PROGRESS]),
            )
            .order_by(ResearchTask.due_date.asc())
            .limit(limit)
        )
        return list(result.scalars().all())

    async def count_by_status(self, db: AsyncSession) -> dict[str, int]:
        """
        Get count of tasks grouped by status

        Args:
            db: The database session

        Returns:
            Dictionary mapping status to count
        """
        result = await db.execute(
            select(ResearchTask.status, func.count(ResearchTask.id)).group_by(
                ResearchTask.status
            )
        )
        return {status.value: count for status, count in result}

    async def get_statistics(
        self,
        db: AsyncSession,
        technology_id: Optional[int] = None,
        repository_id: Optional[int] = None,
    ) -> dict:
        """
        Get task statistics

        Args:
            db: The database session
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

        result = await db.execute(query)
        status_counts = {status.value: 0 for status in TaskStatus}

        for count, status in result:
            status_counts[status.value] = count

        return {"by_status": status_counts, "total": sum(status_counts.values())}
