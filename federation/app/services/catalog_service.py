from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from datetime import datetime, timedelta
from app.models.project import Project, ProjectStatus


class CatalogService:
    """Manages project catalog with heartbeat tracking."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def register_project(
        self,
        slug: str,
        name: str,
        hub_url: str,
        mesh_namespace: str,
        tags: List[str]
    ) -> Project:
        """
        Register or update project in catalog.

        Uses upsert pattern: Creates new project if slug doesn't exist,
        updates metadata if it does.
        """
        stmt = select(Project).where(Project.slug == slug)
        result = await self.db.execute(stmt)
        project = result.scalar_one_or_none()

        if project:
            # Update existing
            project.name = name
            project.hub_url = hub_url
            project.mesh_namespace = mesh_namespace
            project.tags = tags
            project.updated_at = datetime.utcnow()
        else:
            # Create new
            project = Project(
                slug=slug,
                name=name,
                hub_url=hub_url,
                mesh_namespace=mesh_namespace,
                tags=tags,
                status=ProjectStatus.OFFLINE
            )
            self.db.add(project)

        await self.db.commit()
        await self.db.refresh(project)
        return project

    async def update_heartbeat(self, slug: str) -> None:
        """
        Update last_heartbeat_at and set status to online.

        Called by heartbeat worker when NATS message received.
        """
        stmt = (
            update(Project)
            .where(Project.slug == slug)
            .values(
                last_heartbeat_at=datetime.utcnow(),
                status=ProjectStatus.ONLINE,
                updated_at=datetime.utcnow()
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def get_projects(
        self,
        status_filter: Optional[ProjectStatus] = None
    ) -> List[Project]:
        """
        List all projects, optionally filtered by status.

        Args:
            status_filter: ProjectStatus enum value or None (all)
        """
        stmt = select(Project)
        if status_filter:
            stmt = stmt.where(Project.status == status_filter)

        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def get_project(self, slug: str) -> Optional[Project]:
        """Get single project by slug."""
        stmt = select(Project).where(Project.slug == slug)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_stale_projects(self) -> int:
        """
        Mark projects as offline if no heartbeat in 90 seconds.

        Returns number of projects marked stale.
        """
        stale_threshold = datetime.utcnow() - timedelta(seconds=90)

        stmt = (
            update(Project)
            .where(
                Project.status == ProjectStatus.ONLINE,
                Project.last_heartbeat_at < stale_threshold
            )
            .values(
                status=ProjectStatus.OFFLINE,
                updated_at=datetime.utcnow()
            )
        )
        result = await self.db.execute(stmt)
        await self.db.commit()

        return result.rowcount
