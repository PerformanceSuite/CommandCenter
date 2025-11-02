"""
Technology management endpoints
"""

from typing import Optional
from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import Technology, TechnologyDomain, TechnologyStatus
from app.schemas import (
    TechnologyCreate,
    TechnologyUpdate,
    TechnologyResponse,
    TechnologyListResponse,
)
from app.services import TechnologyService

router = APIRouter(prefix="/technologies", tags=["technologies"])


def get_technology_service(
    db: AsyncSession = Depends(get_db),
) -> TechnologyService:
    """Dependency to get technology service instance"""
    return TechnologyService(db)


@router.get("/", response_model=TechnologyListResponse)
async def list_technologies(
    skip: int = 0,
    limit: int = 50,
    domain: Optional[TechnologyDomain] = None,
    status_filter: Optional[TechnologyStatus] = Query(None, alias="status"),
    search: Optional[str] = None,
    service: TechnologyService = Depends(get_technology_service),
) -> TechnologyListResponse:
    """List technologies with filtering"""
    technologies, total = await service.list_technologies(
        skip=skip,
        limit=limit,
        domain=domain,
        status_filter=status_filter,
        search=search,
    )

    return TechnologyListResponse(
        total=total,
        items=[TechnologyResponse.model_validate(t) for t in technologies],
        page=skip // limit + 1,
        page_size=limit,
    )


@router.get("/{technology_id}", response_model=TechnologyResponse)
async def get_technology(
    technology_id: int,
    service: TechnologyService = Depends(get_technology_service),
) -> Technology:
    """Get technology by ID"""
    return await service.get_technology(technology_id)


@router.post(
    "/", response_model=TechnologyResponse, status_code=status.HTTP_201_CREATED
)
async def create_technology(
    technology_data: TechnologyCreate,
    service: TechnologyService = Depends(get_technology_service),
) -> Technology:
    """Create a new technology"""
    return await service.create_technology(technology_data)


@router.patch("/{technology_id}", response_model=TechnologyResponse)
async def update_technology(
    technology_id: int,
    technology_data: TechnologyUpdate,
    service: TechnologyService = Depends(get_technology_service),
) -> Technology:
    """Update technology"""
    return await service.update_technology(technology_id, technology_data)


@router.delete("/{technology_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_technology(
    technology_id: int,
    service: TechnologyService = Depends(get_technology_service),
) -> None:
    """Delete technology"""
    await service.delete_technology(technology_id)
