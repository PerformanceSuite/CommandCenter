"""
CommandCenter Hub - Main FastAPI Application
Manages multiple CommandCenter instances
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.database import engine, Base
from app.routers import projects, orchestration, filesystem


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle manager for FastAPI app"""
    # Create database tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Cleanup
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
    allow_origins=["http://localhost:9000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(projects.router, prefix="/api")
app.include_router(orchestration.router, prefix="/api")
app.include_router(filesystem.router, prefix="/api")


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "app": "CommandCenter Hub",
        "version": "1.0.0",
        "status": "running",
    }


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}
