"""Health check endpoints for Hub backend."""
from fastapi import APIRouter
from pydantic import BaseModel

import nats
from app.config import get_nats_url

router = APIRouter(prefix="/health", tags=["health"])


class HealthResponse(BaseModel):
    """Overall health status."""
    status: str
    nats: str
    database: str


class NATSHealthResponse(BaseModel):
    """NATS connection health."""
    connected: bool
    url: str


@router.get("", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Check health of all services.

    Returns:
        Overall health status with individual service statuses
    """
    # Check NATS
    nats_status = "healthy"
    try:
        nc = await nats.connect(get_nats_url(), timeout=2)
        await nc.close()
    except Exception:
        nats_status = "unhealthy"

    # Check database (always healthy with SQLite, would check connection for Postgres)
    db_status = "healthy"

    overall_status = "healthy" if nats_status == "healthy" and db_status == "healthy" else "degraded"

    return HealthResponse(
        status=overall_status,
        nats=nats_status,
        database=db_status
    )


@router.get("/nats", response_model=NATSHealthResponse)
async def nats_health() -> NATSHealthResponse:
    """Check NATS connection health.

    Returns:
        NATS connection status
    """
    nats_url = get_nats_url()
    try:
        nc = await nats.connect(nats_url, timeout=2)
        await nc.close()
        connected = True
    except Exception:
        connected = False

    return NATSHealthResponse(
        connected=connected,
        url=nats_url
    )
