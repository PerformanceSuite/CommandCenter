"""FastAPI middleware for automatic correlation ID injection.

Middleware extracts or generates correlation IDs for request tracing.
"""
import logging
from uuid import uuid4, UUID
from fastapi import Request
from app.correlation.context import set_correlation_id, clear_correlation_id

logger = logging.getLogger(__name__)


async def correlation_middleware(request: Request, call_next):
    """Auto-inject correlation IDs into all requests.

    Flow:
    1. Extract X-Correlation-ID header (if present)
    2. Validate UUID format
    3. Generate new UUID if missing/invalid
    4. Store in request.state and context variable
    5. Process request
    6. Add correlation ID to response headers

    Args:
        request: FastAPI request object
        call_next: Next middleware/route handler

    Returns:
        Response with X-Correlation-ID header
    """
    try:
        correlation_id = request.headers.get("X-Correlation-ID")

        # Validate format if provided
        if correlation_id:
            try:
                UUID(correlation_id)  # Validate UUID format
            except ValueError:
                logger.warning(
                    f"Invalid correlation ID format: {correlation_id}, generating new"
                )
                correlation_id = str(uuid4())
        else:
            correlation_id = str(uuid4())

        # Store in context for access anywhere in request lifecycle
        set_correlation_id(correlation_id)
        request.state.correlation_id = correlation_id

        # Process request
        response = await call_next(request)

        # Add to response headers
        response.headers["X-Correlation-ID"] = correlation_id
        return response

    except Exception as e:
        # Middleware should never break request - log and continue
        logger.error(f"Correlation middleware error: {e}", exc_info=True)
        return await call_next(request)
    finally:
        # Clear context after request
        clear_correlation_id()
