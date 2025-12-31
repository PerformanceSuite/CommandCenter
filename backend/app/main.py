"""
Command Center FastAPI Application
Main entry point for the backend API
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_client import make_asgi_app
from prometheus_fastapi_instrumentator import Instrumentator
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import close_db, get_db, init_db
from app.middleware import LoggingMiddleware, add_security_headers, limiter
from app.middleware.correlation import CorrelationIDMiddleware
from app.nats_client import init_nats_client, shutdown_nats_client
from app.routers import (
    agents,
    alerts,
    auth,
    batch,
    dashboard,
    export,
    github_features,
    graph,
    hypotheses,
    ingestion_sources,
    intelligence,
    jobs,
    knowledge,
    mcp,
    projects,
    prompts,
    rate_limits,
    repositories,
    research_orchestration,
    research_tasks,
    schedules,
)
from app.routers import settings as settings_router
from app.routers import technologies, webhooks, webhooks_ingestion
from app.services import redis_service
from app.services.federation_heartbeat import FederationHeartbeat
from app.utils.logging import setup_logging
from app.utils.metrics import error_counter, setup_custom_metrics


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """
    Lifespan context manager for startup and shutdown events
    """
    # Setup logging
    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_file = os.getenv("LOG_FILE", "/app/logs/commandcenter.log")
    json_logs = os.getenv("JSON_LOGS", "true").lower() == "true"

    setup_logging(
        log_level=log_level,
        log_file=log_file if os.getenv("ENVIRONMENT") == "production" else None,
        json_format=json_logs,
    )

    # Startup
    print("Starting Command Center API...")
    await init_db()
    print("Database initialized")

    # Initialize Redis
    await redis_service.connect()
    print("Redis service initialized")

    # Initialize MCP server
    await mcp.initialize_mcp_server()
    print("MCP server initialized")

    # Initialize NATS (Phase 7: Graph Service events)
    app.state.heartbeat = None
    heartbeat_task = None
    try:
        await init_nats_client(settings.nats_url)
        print(f"NATS client initialized ({settings.nats_url})")

        # Start federation heartbeat (Phase 9: Federation)
        app.state.heartbeat = FederationHeartbeat()
        heartbeat_task = asyncio.create_task(app.state.heartbeat.start_heartbeat_loop())
        print("Federation heartbeat started")
    except Exception as e:
        # NATS is optional - continue without it
        print(f"Warning: NATS client failed to initialize: {e}")

    yield

    # Shutdown
    print("Shutting down Command Center API...")

    # Stop heartbeat
    if app.state.heartbeat:
        app.state.heartbeat.stop()
    if heartbeat_task:
        heartbeat_task.cancel()
        try:
            await heartbeat_task
        except asyncio.CancelledError:
            pass
        print("Federation heartbeat stopped")

    await shutdown_nats_client()
    print("NATS client shutdown")
    await mcp.shutdown_mcp_server()
    print("MCP server shutdown")
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

# Add correlation ID middleware (must be first to ensure all requests get IDs)
app.add_middleware(CorrelationIDMiddleware)

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
    allow_methods=[
        "GET",
        "POST",
        "PUT",
        "PATCH",
        "DELETE",
        "OPTIONS",
    ],  # Explicit methods
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


# Health check endpoints
@app.get("/health", tags=["health"])
async def health_check() -> JSONResponse:
    """
    Basic health check endpoint for load balancers.
    Returns 200 if the application is running.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "app": settings.app_name,
            "version": settings.app_version,
        }
    )


@app.get("/health/detailed", tags=["health"])
async def detailed_health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> JSONResponse:
    """
    Detailed health check with component status.
    Checks PostgreSQL, Redis, Celery workers, and Federation heartbeat.

    Returns:
        200: All components healthy
        503: One or more components unhealthy
    """
    from app.services.health_service import health_service

    # Get heartbeat worker from app state
    heartbeat_worker = getattr(request.app.state, "heartbeat", None)
    health_status = await health_service.get_overall_health(db, heartbeat_worker)

    status_code = 200
    if health_status["status"] == "unhealthy":
        status_code = 503
    elif health_status["status"] == "degraded":
        status_code = 200  # Still return 200 for degraded (e.g., Redis disabled)

    return JSONResponse(
        content=health_status,
        status_code=status_code,
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
app.include_router(projects.router, prefix=settings.api_v1_prefix)  # Project isolation
app.include_router(repositories.router, prefix=settings.api_v1_prefix)
app.include_router(technologies.router, prefix=settings.api_v1_prefix)
app.include_router(research_tasks.router, prefix=settings.api_v1_prefix)
app.include_router(research_orchestration.router)  # Phase 2 research workflow
app.include_router(dashboard.router, prefix=settings.api_v1_prefix)
app.include_router(knowledge.router, prefix=settings.api_v1_prefix)
app.include_router(webhooks.router, prefix=settings.api_v1_prefix)
app.include_router(github_features.router, prefix=settings.api_v1_prefix)
app.include_router(rate_limits.router, prefix=settings.api_v1_prefix)
app.include_router(mcp.router)  # MCP (Model Context Protocol) endpoints
app.include_router(jobs.router)  # Jobs API for async task management
app.include_router(batch.router)  # Batch operations API for bulk analysis/import/export
app.include_router(schedules.router)  # Schedule management for recurring tasks
app.include_router(export.router)  # Export API for analysis results (SARIF, HTML, CSV, Excel)
app.include_router(webhooks_ingestion.router)  # Webhook ingestion for knowledge base
app.include_router(ingestion_sources.router)  # Ingestion sources management API
app.include_router(graph.router)  # Phase 7: Graph Service - Code knowledge graph
app.include_router(hypotheses.router, prefix=settings.api_v1_prefix)  # AI Arena hypotheses (legacy)
app.include_router(
    intelligence.router, prefix=settings.api_v1_prefix
)  # Research Hub intelligence integration
app.include_router(settings_router.router, prefix=settings.api_v1_prefix)  # Settings & API keys
app.include_router(agents.router, prefix=settings.api_v1_prefix)  # Agent persona management
app.include_router(alerts.router)  # AlertManager webhook integration
app.include_router(prompts.router)  # Prompt analysis and improvement API


# Test endpoints for observability (only in dev/test environments)
if settings.debug or os.getenv("ENVIRONMENT") in ["development", "test"]:

    @app.get("/api/v1/trigger-test-error")
    async def trigger_test_error():
        """Test endpoint that raises an exception for error tracking verification.

        This endpoint is only available in development/test environments.
        Used to verify error tracking, correlation IDs, and metrics.
        """
        raise ValueError("Test error for observability verification")


# Mount Prometheus metrics endpoint
metrics_app = make_asgi_app()
app.mount("/metrics", metrics_app)


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Enhanced global exception handler with correlation tracking and metrics.

    This handler:
    1. Extracts correlation ID from request state
    2. Increments error counter metric with labels
    3. Logs structured error with correlation ID
    4. Returns error response with correlation ID
    """
    # Get logger
    logger = logging.getLogger(__name__)

    # Extract correlation ID from request state
    request_id = getattr(request.state, "request_id", "unknown")

    # Increment error metric with labels
    error_counter.labels(
        endpoint=request.url.path, status_code="500", error_type=type(exc).__name__
    ).inc()

    # Structured error logging with correlation context
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "endpoint": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "error_message": str(exc),
            "user_id": getattr(request.state, "user_id", None),
        },
        exc_info=True,  # Include stack trace
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "detail": str(exc) if settings.debug else "An unexpected error occurred",
            "request_id": request_id,  # Include correlation ID in response
        },
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
