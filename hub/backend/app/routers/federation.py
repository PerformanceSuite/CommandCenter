"""Federation API endpoints for Hub discovery and monitoring."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Dict, Any

from app.database import get_db
from app.models.hub_registry import HubRegistry
from app.config import get_hub_id

router = APIRouter(prefix="/api/federation", tags=["federation"])


@router.get("/hubs")
async def list_discovered_hubs(
    db: AsyncSession = Depends(get_db)
) -> Dict[str, Any]:
    """List all discovered Hubs in the federation.

    Returns:
        JSON with count and list of Hub details
    """
    stmt = select(HubRegistry).order_by(HubRegistry.last_seen.desc())
    result = await db.execute(stmt)
    hubs = result.scalars().all()

    return {
        "hub_id": get_hub_id(),
        "count": len(hubs),
        "hubs": [
            {
                "id": hub.id,
                "name": hub.name,
                "version": hub.version,
                "hostname": hub.hostname,
                "project_path": hub.project_path,
                "project_count": hub.project_count,
                "service_count": hub.service_count,
                "uptime_seconds": hub.uptime_seconds,
                "first_seen": hub.first_seen.isoformat() if hub.first_seen else None,
                "last_seen": hub.last_seen.isoformat() if hub.last_seen else None,
            }
            for hub in hubs
        ]
    }


@router.get("/status")
async def federation_status() -> Dict[str, Any]:
    """Get federation service status.

    Returns:
        JSON with Hub ID and federation status
    """
    return {
        "hub_id": get_hub_id(),
        "federation_enabled": True,
        "status": "active"
    }
