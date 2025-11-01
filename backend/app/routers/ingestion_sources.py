"""
API endpoints for managing ingestion sources
"""

import logging
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.models.ingestion_source import IngestionSource, SourceType
from app.schemas.ingestion import (
    IngestionSourceCreate,
    IngestionSourceUpdate,
    IngestionSourceResponse,
    IngestionSourceList,
)
from app.tasks.ingestion_tasks import (
    scrape_rss_feed,
    scrape_documentation,
    process_webhook_payload,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/ingestion", tags=["ingestion"])


@router.post(
    "/sources",
    response_model=IngestionSourceResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_source(
    source: IngestionSourceCreate, db: AsyncSession = Depends(get_db)
):
    """
    Create a new ingestion source.
    """
    db_source = IngestionSource(**source.model_dump())
    db.add(db_source)
    await db.commit()
    await db.refresh(db_source)

    logger.info(f"Created ingestion source: {db_source.name} (ID: {db_source.id})")

    return db_source


@router.get("/sources", response_model=IngestionSourceList)
async def list_sources(
    project_id: Optional[int] = Query(None),
    type: Optional[SourceType] = Query(None),
    enabled: Optional[bool] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    """
    List ingestion sources with optional filters.
    """
    from sqlalchemy import func

    query = select(IngestionSource)

    if project_id:
        query = query.filter(IngestionSource.project_id == project_id)

    if type:
        query = query.filter(IngestionSource.type == type)

    if enabled is not None:
        query = query.filter(IngestionSource.enabled == enabled)

    # Get total count (before pagination)
    count_query = select(func.count()).select_from(query.subquery())
    count_result = await db.execute(count_query)
    total = count_result.scalar()

    # Order by priority descending and apply pagination
    query = query.order_by(IngestionSource.priority.desc())
    query = query.offset(skip).limit(limit)

    result = await db.execute(query)
    sources = result.scalars().all()

    return IngestionSourceList(sources=list(sources), total=total)


@router.get("/sources/{source_id}", response_model=IngestionSourceResponse)
async def get_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """
    Get ingestion source by ID.
    """
    result = await db.execute(
        select(IngestionSource).filter(IngestionSource.id == source_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Ingestion source not found")

    return source


@router.put("/sources/{source_id}", response_model=IngestionSourceResponse)
async def update_source(
    source_id: int,
    source_update: IngestionSourceUpdate,
    db: AsyncSession = Depends(get_db),
):
    """
    Update ingestion source.
    """
    result = await db.execute(
        select(IngestionSource).filter(IngestionSource.id == source_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Ingestion source not found")

    # Update fields
    update_data = source_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(source, field, value)

    await db.commit()
    await db.refresh(source)

    logger.info(f"Updated ingestion source: {source.name} (ID: {source.id})")

    return source


@router.delete("/sources/{source_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_source(source_id: int, db: AsyncSession = Depends(get_db)):
    """
    Delete ingestion source.
    """
    result = await db.execute(
        select(IngestionSource).filter(IngestionSource.id == source_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Ingestion source not found")

    await db.delete(source)
    await db.commit()

    logger.info(f"Deleted ingestion source: {source.name} (ID: {source_id})")

    return None


@router.post("/sources/{source_id}/run", status_code=status.HTTP_202_ACCEPTED)
async def trigger_manual_run(source_id: int, db: AsyncSession = Depends(get_db)):
    """
    Manually trigger ingestion source run.
    """
    result = await db.execute(
        select(IngestionSource).filter(IngestionSource.id == source_id)
    )
    source = result.scalar_one_or_none()

    if not source:
        raise HTTPException(status_code=404, detail="Ingestion source not found")

    if not source.enabled:
        raise HTTPException(status_code=400, detail="Source is disabled")

    # Trigger appropriate task based on source type
    task = None

    if source.type == SourceType.RSS:
        task = scrape_rss_feed.delay(source_id)
    elif source.type == SourceType.DOCUMENTATION:
        task = scrape_documentation.delay(source_id)
    elif source.type == SourceType.WEBHOOK:
        raise HTTPException(
            status_code=400, detail="Webhook sources cannot be triggered manually"
        )
    elif source.type == SourceType.FILE_WATCHER:
        raise HTTPException(
            status_code=400, detail="File watcher sources run automatically"
        )

    logger.info(f"Triggered manual run for source: {source.name} (task_id: {task.id})")

    return {"task_id": task.id, "source_id": source_id, "source_name": source.name}
