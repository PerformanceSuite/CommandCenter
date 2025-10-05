"""
Technology management endpoints
"""

from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from app.database import get_db
from app.models import Technology, TechnologyDomain, TechnologyStatus
from app.schemas import (
    TechnologyCreate,
    TechnologyUpdate,
    TechnologyResponse,
    TechnologyListResponse,
)

router = APIRouter(prefix="/technologies", tags=["technologies"])


@router.get("/", response_model=TechnologyListResponse)
async def list_technologies(
    skip: int = 0,
    limit: int = 50,
    domain: Optional[TechnologyDomain] = None,
    status_filter: Optional[TechnologyStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db)
) -> TechnologyListResponse:
    """List technologies with filtering"""
    # Build query
    query = select(Technology)

    # Apply filters
    if domain:
        query = query.where(Technology.domain == domain)

    if status_filter:
        query = query.where(Technology.status == status_filter)

    if search:
        search_pattern = f"%{search}%"
        query = query.where(
            (Technology.title.ilike(search_pattern)) |
            (Technology.description.ilike(search_pattern)) |
            (Technology.tags.ilike(search_pattern))
        )

    # Get total count
    count_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Apply pagination and ordering
    query = query.offset(skip).limit(limit).order_by(
        Technology.priority.desc(),
        Technology.relevance_score.desc(),
        Technology.updated_at.desc()
    )

    result = await db.execute(query)
    technologies = result.scalars().all()

    return TechnologyListResponse(
        total=total,
        items=[TechnologyResponse.model_validate(t) for t in technologies],
        page=skip // limit + 1,
        page_size=limit
    )


@router.get("/{technology_id}", response_model=TechnologyResponse)
async def get_technology(
    technology_id: int,
    db: AsyncSession = Depends(get_db)
) -> Technology:
    """Get technology by ID"""
    result = await db.execute(
        select(Technology).where(Technology.id == technology_id)
    )
    technology = result.scalar_one_or_none()

    if not technology:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technology {technology_id} not found"
        )

    return technology


@router.post("/", response_model=TechnologyResponse, status_code=status.HTTP_201_CREATED)
async def create_technology(
    technology_data: TechnologyCreate,
    db: AsyncSession = Depends(get_db)
) -> Technology:
    """Create a new technology"""
    # Check if technology with same title exists
    result = await db.execute(
        select(Technology).where(Technology.title == technology_data.title)
    )
    existing = result.scalar_one_or_none()

    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Technology '{technology_data.title}' already exists"
        )

    # Create technology
    technology = Technology(**technology_data.model_dump())

    db.add(technology)
    await db.commit()
    await db.refresh(technology)

    return technology


@router.patch("/{technology_id}", response_model=TechnologyResponse)
async def update_technology(
    technology_id: int,
    technology_data: TechnologyUpdate,
    db: AsyncSession = Depends(get_db)
) -> Technology:
    """Update technology"""
    result = await db.execute(
        select(Technology).where(Technology.id == technology_id)
    )
    technology = result.scalar_one_or_none()

    if not technology:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technology {technology_id} not found"
        )

    # Update fields
    update_data = technology_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(technology, field, value)

    await db.commit()
    await db.refresh(technology)

    return technology


@router.delete("/{technology_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_technology(
    technology_id: int,
    db: AsyncSession = Depends(get_db)
) -> None:
    """Delete technology"""
    result = await db.execute(
        select(Technology).where(Technology.id == technology_id)
    )
    technology = result.scalar_one_or_none()

    if not technology:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Technology {technology_id} not found"
        )

    await db.delete(technology)
    await db.commit()
