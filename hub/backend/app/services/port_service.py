"""
Port allocation service - Manages port assignment for CC instances
"""

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from app.models import Project
from app.schemas import PortSet


class PortService:
    """Service for allocating ports to CommandCenter instances"""

    # Base ports for first instance
    BASE_BACKEND = 8000
    BASE_FRONTEND = 3000
    BASE_POSTGRES = 5432
    BASE_REDIS = 6379

    # Port increment for each instance
    INCREMENT = 10

    def __init__(self, db: AsyncSession):
        self.db = db

    async def allocate_ports(self) -> PortSet:
        """
        Allocate next available port set

        Returns PortSet with non-conflicting ports
        Note: Starts at +10 offset to avoid Hub ports (9000/9001)
        """
        # Get count of existing projects
        result = await self.db.execute(select(func.count(Project.id)))
        project_count = result.scalar() or 0

        # Calculate next port set (start at offset 10 to avoid Hub)
        # First project: 8010, 3010, 5442, 6389
        # Second project: 8020, 3020, 5452, 6399
        offset = (project_count + 1) * self.INCREMENT

        return PortSet(
            backend=self.BASE_BACKEND + offset,
            frontend=self.BASE_FRONTEND + offset,
            postgres=self.BASE_POSTGRES + offset,
            redis=self.BASE_REDIS + offset,
        )

    async def get_ports_for_project(self, project_id: int) -> PortSet:
        """Get ports for existing project"""
        result = await self.db.execute(select(Project).where(Project.id == project_id))
        project = result.scalar_one_or_none()

        if not project:
            raise ValueError(f"Project {project_id} not found")

        return PortSet(
            backend=project.backend_port,
            frontend=project.frontend_port,
            postgres=project.postgres_port,
            redis=project.redis_port,
        )
