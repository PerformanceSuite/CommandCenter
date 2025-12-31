"""
Agent Persona Management API

Provides CRUD endpoints for managing agent personas in the database.
"""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.agent_persona import AgentPersona

router = APIRouter(prefix="/agents", tags=["agents"])


# Pydantic Schemas
class PersonaBase(BaseModel):
    """Base persona schema with common fields"""

    name: str = Field(..., min_length=1, max_length=100)
    display_name: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = None
    category: str = Field(default="custom", max_length=50)
    system_prompt: str = Field(..., min_length=1)
    model: str = Field(default="claude-sonnet-4-20250514", max_length=200)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    requires_sandbox: bool = False
    tags: list[str] = Field(default_factory=list)
    is_active: bool = True


class PersonaCreate(PersonaBase):
    """Schema for creating a new persona"""

    pass


class PersonaUpdate(BaseModel):
    """Schema for updating an existing persona"""

    display_name: Optional[str] = Field(None, min_length=1, max_length=200)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=50)
    system_prompt: Optional[str] = Field(None, min_length=1)
    model: Optional[str] = Field(None, max_length=200)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    requires_sandbox: Optional[bool] = None
    tags: Optional[list[str]] = None
    is_active: Optional[bool] = None


class PersonaResponse(PersonaBase):
    """Schema for persona responses"""

    id: int
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)


class PersonaListResponse(BaseModel):
    """Schema for persona list responses"""

    total: int
    items: list[PersonaResponse]
    page: int
    page_size: int


# API Endpoints
@router.get("/personas", response_model=PersonaListResponse)
async def list_personas(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
) -> PersonaListResponse:
    """
    List all agent personas with optional filtering.

    Args:
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        category: Filter by category (e.g., "assessment", "coding", "verification")
        is_active: Filter by active status
        search: Search in name, display_name, or description
        db: Database session

    Returns:
        PersonaListResponse with paginated results
    """
    # Build query
    query = select(AgentPersona)

    # Apply filters
    if category:
        query = query.where(AgentPersona.category == category)
    if is_active is not None:
        query = query.where(AgentPersona.is_active == is_active)
    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (AgentPersona.name.ilike(search_pattern))
            | (AgentPersona.display_name.ilike(search_pattern))
            | (AgentPersona.description.ilike(search_pattern))
        )

    # Get total count
    count_query = select(AgentPersona.id).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = len(total_result.all())

    # Apply pagination and ordering
    query = query.order_by(AgentPersona.name).offset(skip).limit(limit)

    # Execute query
    result = await db.execute(query)
    personas = result.scalars().all()

    return PersonaListResponse(
        total=total,
        items=[PersonaResponse.model_validate(p) for p in personas],
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/personas/{name}", response_model=PersonaResponse)
async def get_persona(
    name: str,
    db: AsyncSession = Depends(get_db),
) -> PersonaResponse:
    """
    Get a single persona by name.

    Args:
        name: Unique persona name
        db: Database session

    Returns:
        PersonaResponse with persona details

    Raises:
        HTTPException: 404 if persona not found
    """
    query = select(AgentPersona).where(AgentPersona.name == name)
    result = await db.execute(query)
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona not found: {name}",
        )

    return PersonaResponse.model_validate(persona)


@router.post("/personas", response_model=PersonaResponse, status_code=status.HTTP_201_CREATED)
async def create_persona(
    persona_data: PersonaCreate,
    db: AsyncSession = Depends(get_db),
) -> PersonaResponse:
    """
    Create a new agent persona.

    Args:
        persona_data: Persona creation data
        db: Database session

    Returns:
        PersonaResponse with created persona

    Raises:
        HTTPException: 409 if persona with same name already exists
    """
    # Check if persona with same name exists
    query = select(AgentPersona).where(AgentPersona.name == persona_data.name)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Persona with name '{persona_data.name}' already exists",
        )

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
    await db.commit()
    await db.refresh(persona)

    return PersonaResponse.model_validate(persona)


@router.put("/personas/{name}", response_model=PersonaResponse)
async def update_persona(
    name: str,
    persona_data: PersonaUpdate,
    db: AsyncSession = Depends(get_db),
) -> PersonaResponse:
    """
    Update an existing agent persona.

    Args:
        name: Unique persona name
        persona_data: Persona update data
        db: Database session

    Returns:
        PersonaResponse with updated persona

    Raises:
        HTTPException: 404 if persona not found
    """
    # Get existing persona
    query = select(AgentPersona).where(AgentPersona.name == name)
    result = await db.execute(query)
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona not found: {name}",
        )

    # Update fields (only non-None values)
    update_data = persona_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(persona, field, value)

    await db.commit()
    await db.refresh(persona)

    return PersonaResponse.model_validate(persona)


@router.delete("/personas/{name}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_persona(
    name: str,
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete an agent persona.

    Args:
        name: Unique persona name
        db: Database session

    Raises:
        HTTPException: 404 if persona not found
    """
    # Get existing persona
    query = select(AgentPersona).where(AgentPersona.name == name)
    result = await db.execute(query)
    persona = result.scalar_one_or_none()

    if not persona:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Persona not found: {name}",
        )

    await db.delete(persona)
    await db.commit()
