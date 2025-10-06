"""
Command Center FastAPI Application
Main entry point for the backend API
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator
import os

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded

from app.config import settings
from app.database import init_db, close_db
from app.routers import auth, repositories, technologies, dashboard, knowledge
from app.routers import webhooks, github_features, rate_limits, research_tasks
from app.services import redis_service
from app.utils.metrics import setup_custom_metrics
from app.utils.logging import setup_logging
from app.middleware import limiter, add_security_headers, LoggingMiddleware


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for startup and shutdown events
    """
    # Setup logging
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    log_file = os.getenv('LOG_FILE', '/app/logs/commandcenter.log')
    json_logs = os.getenv('JSON_LOGS', 'true').lower() == 'true'

    setup_logging(
        log_level=log_level,
        log_file=log_file if os.getenv('ENVIRONMENT') == 'production' else None,
        json_format=json_logs
    )

    # Startup
    print("Starting Command Center API...")
    await init_db()
    print("Database initialized")

    # Initialize Redis
    await redis_service.connect()
    print("Redis service initialized")

    yield

    # Shutdown
    print("Shutting down Command Center API...")
    await redis_service.disconnect()
    print("Redis service disconnected")
    await close_db()
    print("Database connections closed")


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="Command Center API for Performia - Research and development management",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
)

# Add logging middleware
app.add_middleware(LoggingMiddleware)

# Add rate limiting
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Add security headers middleware
add_security_headers(app)

# Configure CORS with security best practices
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,  # Explicit allowlist from environment
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],  # Explicit methods
    allow_headers=["Authorization", "Content-Type", "Accept"],  # Explicit headers
    max_age=settings.cors_max_age,
)

# Setup Prometheus metrics
instrumentator = Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=True,
    should_instrument_requests_inprogress=True,
    excluded_handlers=["/metrics", "/health"],
    env_var_name="ENABLE_METRICS",
    inprogress_name="http_requests_inprogress",
    inprogress_labels=True,
)
instrumentator.instrument(app)
setup_custom_metrics(app)


# Health check endpoint
@app.get("/health", tags=["health"])
async def health_check() -> JSONResponse:
    """Health check endpoint"""
    return JSONResponse(
        content={
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
        }
    )


# Root endpoint
@app.get("/", tags=["root"])
async def root() -> JSONResponse:
    """Root endpoint with API information"""
    return JSONResponse(
        content={
            "app": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/health",
        }
    )


# Include routers
app.include_router(auth.router, prefix=settings.api_v1_prefix)
app.include_router(repositories.router, prefix=settings.api_v1_prefix)
app.include_router(technologies.router, prefix=settings.api_v1_prefix)
app.include_router(research_tasks.router, prefix=settings.api_v1_prefix)
app.include_router(dashboard.router, prefix=settings.api_v1_prefix)
app.include_router(knowledge.router, prefix=settings.api_v1_prefix)
app.include_router(webhooks.router, prefix=settings.api_v1_prefix)
app.include_router(github_features.router, prefix=settings.api_v1_prefix)
app.include_router(rate_limits.router, prefix=settings.api_v1_prefix)
app.include_router(research_tasks.router, prefix=settings.api_v1_prefix)

# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler for unhandled errors"""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
        }
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
        log_level="info" if settings.debug else "warning",
    )
