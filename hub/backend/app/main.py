"""
CommandCenter Hub - Main FastAPI Application
Manages multiple CommandCenter instances
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
import asyncio
import logging

from app.database import engine, Base, AsyncSessionLocal
from app.routers import projects, orchestration, filesystem, logs, tasks, events, health, rpc, federation, services, settings
# Import models to ensure they're registered with Base.metadata
from app.models import settings as settings_models  # noqa: F401
from app.correlation.middleware import correlation_middleware
from app.streaming.sse import router as sse_router
from app.events.bridge import NATSBridge
from app.services.federation_service import FederationService
from app.workers.health_worker import get_health_worker
from app.config import get_nats_url, get_hub_id

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Initialize NATS Bridge
    nats_bridge = NATSBridge(nats_url=get_nats_url())
    try:
        await nats_bridge.connect()
        logger.info("✅ NATS Bridge connected")
    except Exception as e:
        logger.warning(f"Failed to connect NATS Bridge (federation disabled): {e}")
        nats_bridge = None

    # Initialize and start Federation Service
    federation_service = None
    federation_db_session = None
    if nats_bridge:
        # Create long-lived session for federation service
        federation_db_session = AsyncSessionLocal()
        federation_service = FederationService(
            db_session=federation_db_session,
            nats_bridge=nats_bridge
        )
        await federation_service.start()
        logger.info(f"✅ Federation started - Hub ID: {get_hub_id()}")

    # Start health check worker
    health_worker = get_health_worker()
    await health_worker.start()
    logger.info("✅ Health check worker started")

    # Store in app state for access by routers
    app.state.nats_bridge = nats_bridge
    app.state.federation_service = federation_service
    app.state.health_worker = health_worker

    yield

    # Cleanup with timeout for graceful shutdown
    try:
        await asyncio.wait_for(health_worker.stop(), timeout=10.0)
        logger.info("Health check worker stopped gracefully")
    except asyncio.TimeoutError:
        logger.warning("Health check worker shutdown timed out after 10 seconds")
    if federation_service:
        await federation_service.stop()
    if federation_db_session:
        await federation_db_session.close()
    if nats_bridge:
        await nats_bridge.disconnect()
    await engine.dispose()


app = FastAPI(
    title="CommandCenter Hub",
    description="Multi-project launcher and management interface",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:9000", "http://localhost:9003", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add correlation middleware (before route handlers)
app.middleware("http")(correlation_middleware)

# Include routers
app.include_router(health.router)  # Health check endpoints (no prefix)
app.include_router(sse_router)  # SSE streaming endpoints (must be before events router)
app.include_router(events.router)  # Event endpoints
app.include_router(rpc.router)  # JSON-RPC endpoint
app.include_router(federation.router)  # Federation endpoints
app.include_router(services.router)  # Service health and discovery endpoints
app.include_router(projects.router, prefix="/api")
app.include_router(orchestration.router, prefix="/api")
app.include_router(filesystem.router, prefix="/api")
app.include_router(logs.router)
app.include_router(tasks.router)  # Background task endpoints
app.include_router(settings.router, prefix="/api")  # Settings and agent configuration


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "CommandCenter Hub",
        "version": "1.0.0",
        "status": "running",
    }
