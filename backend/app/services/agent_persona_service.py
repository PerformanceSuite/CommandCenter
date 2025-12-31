"""
Agent Persona business logic service
Handles persona operations with transaction management
"""

from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import AgentPersona
from app.schemas import AgentPersonaCreate, AgentPersonaUpdate


class AgentPersonaService:
    """Service layer for agent persona operations"""

    def __init__(self, db: AsyncSession):
        """
        Initialize agent persona service

        Args:
            db: Database session
        """
        self.db = db

    async def list_personas(
        self,
        skip: int = 0,
        limit: int = 50,
        category: Optional[str] = None,
        is_active: Optional[bool] = None,
    ) -> tuple[list[AgentPersona], int]:
        """
        List agent personas with filtering and pagination

        Args:
            skip: Number of records to skip
            limit: Maximum number of records
            category: Optional category filter
            is_active: Optional active status filter

        Returns:
            Tuple of (list of personas, total count)
        """
        # Build query
        query = select(AgentPersona)

        # Apply filters
        if category is not None:
            query = query.where(AgentPersona.category == category)
        if is_active is not None:
            query = query.where(AgentPersona.is_active == is_active)

        # Get total count
        count_query = select(func.count()).select_from(query.subquery())
        total_result = await self.db.execute(count_query)
        total = total_result.scalar_one()

        # Apply pagination and order
        query = query.order_by(AgentPersona.name).offset(skip).limit(limit)

        # Execute query
        result = await self.db.execute(query)
        personas = list(result.scalars().all())

        return personas, total

    async def get_persona(self, persona_id: int) -> AgentPersona:
        """
        Get persona by ID

        Args:
            persona_id: Persona ID

        Returns:
            AgentPersona

        Raises:
            HTTPException: If persona not found
        """
        query = select(AgentPersona).where(AgentPersona.id == persona_id)
        result = await self.db.execute(query)
        persona = result.scalar_one_or_none()

        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona {persona_id} not found",
            )

        return persona

    async def get_persona_by_name(self, name: str) -> AgentPersona:
        """
        Get persona by name

        Args:
            name: Persona name

        Returns:
            AgentPersona

        Raises:
            HTTPException: If persona not found
        """
        query = select(AgentPersona).where(AgentPersona.name == name)
        result = await self.db.execute(query)
        persona = result.scalar_one_or_none()

        if not persona:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Persona '{name}' not found",
            )

        return persona

    async def create_persona(self, persona_data: AgentPersonaCreate) -> AgentPersona:
        """
        Create new agent persona

        Args:
            persona_data: Persona creation data

        Returns:
            Created persona

        Raises:
            HTTPException: If persona with same name exists
        """
        # Check if persona with same name exists
        query = select(AgentPersona).where(AgentPersona.name == persona_data.name)
        result = await self.db.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Persona '{persona_data.name}' already exists",
            )

        # Create persona
        persona = AgentPersona(**persona_data.model_dump())
        self.db.add(persona)

        await self.db.commit()
        await self.db.refresh(persona)

        return persona

    async def update_persona(
        self, name: str, persona_data: AgentPersonaUpdate
    ) -> AgentPersona:
        """
        Update agent persona

        Args:
            name: Persona name
            persona_data: Persona update data

        Returns:
            Updated persona

        Raises:
            HTTPException: If persona not found
        """
        # Fetch persona
        persona = await self.get_persona_by_name(name)

        # Update fields
        update_data = persona_data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(persona, key, value)

        await self.db.commit()
        await self.db.refresh(persona)

        return persona

    async def delete_persona(self, name: str) -> None:
        """
        Delete agent persona

        Args:
            name: Persona name

        Raises:
            HTTPException: If persona not found
        """
        persona = await self.get_persona_by_name(name)
        await self.db.delete(persona)
        await self.db.commit()
