# federation/app/main.py
from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.config import settings
from app.routers import projects_router
from app.workers import HeartbeatWorker
from app.loader import load_projects_from_yaml
import logging

logging.basicConfig(level=settings.LOG_LEVEL.upper())
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    # Startup
    logger.info("Starting Federation Service...")

    # Load projects from config
    await load_projects_from_yaml()

    # Start heartbeat worker
    worker = HeartbeatWorker()
    await worker.start()

    yield

    # Shutdown
    logger.info("Shutting down Federation Service...")
    await worker.stop()


app = FastAPI(
    title="Federation Service",
    version="0.9.0",
    description="Multi-project catalog and orchestration",
    lifespan=lifespan
)

# Include routers
app.include_router(projects_router)


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "ok",
        "service": "federation",
        "version": "0.9.0"
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=settings.SERVICE_PORT)
