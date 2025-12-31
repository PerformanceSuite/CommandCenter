"""
Agent Persona Router - CRUD API for managing agent personas.

Provides endpoints to create, read, update, and delete agent personas
stored in the database. These personas define the behavior and configuration
of agents in the unified agent framework.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent_persona import AgentPersona
from app.schemas.agent_persona import (
    AgentPersonaCreate,
    AgentPersonaListResponse,
    AgentPersonaResponse,
    AgentPersonaUpdate,
)

router = APIRouter(prefix="/agents", tags=["agents"])


@router.get("/personas", response_model=AgentPersonaListResponse)
async def list_personas(
    category: str | None = None,
    is_active: bool | None = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db),
) -> AgentPersonaListResponse:
    """
    List all agent personas with optional filtering.

    Args:
        category: Optional category filter (assessment, coding, verification, custom)
        is_active: Optional filter for active/inactive personas
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return

    Returns:
        List of personas matching the filters
    """
    query = select(AgentPersona)

    # Apply filters
    if category is not None:
        query = query.where(AgentPersona.category == category)
    if is_active is not None:
        query = query.where(AgentPersona.is_active == is_active)

    # Apply pagination and ordering
    query = query.order_by(AgentPersona.name).offset(skip).limit(limit)

    result = await db.execute(query)
    personas = result.scalars().all()

    # Get total count
    count_query = select(AgentPersona)
    if category is not None:
        count_query = count_query.where(AgentPersona.category == category)
    if is_active is not None:
        count_query = count_query.where(AgentPersona.is_active == is_active)

    from sqlalchemy import func

    count_result = await db.execute(select(func.count()).select_from(count_query.subquery()))
    total = count_result.scalar() or 0

    return AgentPersonaListResponse(personas=personas, total=total)


@router.get("/personas/{name}", response_model=AgentPersonaResponse)
async def get_persona(
    name: str,
    db: AsyncSession = Depends(get_db),
) -> AgentPersonaResponse:
    """
    Get a specific agent persona by name.

    Args:
        name: Unique persona name

    Returns:
        Persona details

    Raises:
        HTTPException: 404 if persona not found
    """
    query = select(AgentPersona).where(AgentPersona.name == name)
    result = await db.execute(query)
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona '{name}' not found")

    return persona


@router.post("/personas", response_model=AgentPersonaResponse, status_code=201)
async def create_persona(
    persona_data: AgentPersonaCreate,
    db: AsyncSession = Depends(get_db),
) -> AgentPersonaResponse:
    """
    Create a new agent persona.

    Args:
        persona_data: Persona configuration data

    Returns:
        Created persona

    Raises:
        HTTPException: 400 if persona with name already exists
    """
    # Create new persona
    persona = AgentPersona(
        name=persona_data.name,
        display_name=persona_data.display_name,
        description=persona_data.description,
        category=persona_data.category,
        system_prompt=persona_data.system_prompt,
        model=persona_data.model,
        temperature=persona_data.temperature,
        requires_sandbox=persona_data.requires_sandbox,
        tags=persona_data.tags,
        is_active=persona_data.is_active,
    )

    db.add(persona)

    try:
        await db.commit()
        await db.refresh(persona)
        return persona
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail=f"Persona with name '{persona_data.name}' already exists")


@router.put("/personas/{name}", response_model=AgentPersonaResponse)
async def update_persona(
    name: str,
    persona_data: AgentPersonaUpdate,
    db: AsyncSession = Depends(get_db),
) -> AgentPersonaResponse:
    """
    Update an existing agent persona.

    Args:
        name: Unique persona name
        persona_data: Updated persona data (only provided fields are updated)

    Returns:
        Updated persona

    Raises:
        HTTPException: 404 if persona not found
    """
    # Get existing persona
    query = select(AgentPersona).where(AgentPersona.name == name)
    result = await db.execute(query)
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona '{name}' not found")

    # Update fields that were provided
    update_data = persona_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(persona, field, value)

    try:
        await db.commit()
        await db.refresh(persona)
        return persona
    except IntegrityError as e:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Failed to update persona")


@router.delete("/personas/{name}", status_code=204)
async def delete_persona(
    name: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an agent persona.

    Args:
        name: Unique persona name

    Raises:
        HTTPException: 404 if persona not found
    """
    # Get existing persona
    query = select(AgentPersona).where(AgentPersona.name == name)
    result = await db.execute(query)
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(status_code=404, detail=f"Persona '{name}' not found")

    await db.delete(persona)
    await db.commit()
