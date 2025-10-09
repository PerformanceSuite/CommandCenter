"""
ProjectContextMiddleware - Extract and validate project context from requests.

Extracts project_id from (in priority order):
1. X-Project-ID header (highest priority)
2. JWT token 'project_id' claim
3. Query parameter '?project_id=123' (fallback)

Attaches project_id to request.state for use by services/routers.
"""

from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
import logging

logger = logging.getLogger(__name__)

# Public endpoints that don't require project_id
PUBLIC_ENDPOINTS = {
    "/",
    "/health",
    "/docs",
    "/redoc",
    "/openapi.json",
    "/metrics",
    "/api/v1/auth/login",
    "/api/v1/auth/register",
    "/api/v1/projects",  # Can list projects without project context
}


class ProjectContextMiddleware(BaseHTTPMiddleware):
    """Extract project_id from requests and attach to request state"""

    async def dispatch(self, request: Request, call_next):
        # Skip public endpoints
        if request.url.path in PUBLIC_ENDPOINTS or request.url.path.startswith("/static"):
            return await call_next(request)

        # Extract project_id from various sources
        project_id = None

        # Priority 1: X-Project-ID header
        if "X-Project-ID" in request.headers:
            try:
                project_id = int(request.headers["X-Project-ID"])
                logger.debug(f"Project ID from header: {project_id}")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid X-Project-ID header: must be integer"
                )

        # Priority 2: JWT token claim (if authenticated)
        if not project_id and hasattr(request.state, "user"):
            user_data = request.state.user
            if isinstance(user_data, dict):
                project_id = user_data.get("project_id")
                if project_id:
                    logger.debug(f"Project ID from JWT: {project_id}")

        # Priority 3: Query parameter (fallback)
        if not project_id and "project_id" in request.query_params:
            try:
                project_id = int(request.query_params["project_id"])
                logger.debug(f"Project ID from query param: {project_id}")
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail="Invalid project_id query parameter: must be integer"
                )

        # If still no project_id, reject request
        if not project_id:
            raise HTTPException(
                status_code=400,
                detail="project_id required (provide via X-Project-ID header, JWT token, or ?project_id= query param)"
            )

        # TODO: Validate that project exists and user has access
        # For now, just attach to request state

        request.state.project_id = project_id
        logger.info(f"Request for project {project_id}: {request.method} {request.url.path}")

        response = await call_next(request)

        # Optionally add project_id to response headers for debugging
        response.headers["X-Project-ID"] = str(project_id)

        return response
