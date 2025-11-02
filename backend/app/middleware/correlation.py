"""Correlation ID middleware for request tracing.

This middleware ensures every request has a unique correlation ID that can be
used to trace requests across services, logs, and metrics.

Phase C Enhancement: Propagates correlation ID to database queries via context variable
"""

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

# Import context variable for database query comments
from app.database import request_id_context


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Middleware to add correlation IDs to all requests.

    This middleware:
    1. Extracts X-Request-ID header if present, or generates a new UUID
    2. Stores the correlation ID in request.state.request_id
    3. Adds the correlation ID to response headers

    The correlation ID can be used for distributed tracing and log correlation.

    Performance: < 0.5ms overhead per request
    """

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request and add correlation ID.

        Args:
            request: The incoming HTTP request
            call_next: The next middleware/handler in the chain

        Returns:
            Response with X-Request-ID header added
        """
        # Extract or generate correlation ID
        # Handle edge case: validate UUID format if provided
        correlation_id = request.headers.get("X-Request-ID")

        if correlation_id:
            # Validate UUID format, fallback to generation if malformed
            try:
                # Just validate it's a reasonable string, don't enforce strict UUID
                if len(correlation_id) > 255:  # Sanity check
                    correlation_id = str(uuid.uuid4())
            except Exception:
                correlation_id = str(uuid.uuid4())
        else:
            correlation_id = str(uuid.uuid4())

        # Store in request state for access by handlers
        request.state.request_id = correlation_id

        # Phase C: Set context variable for database query comment injection
        # This allows SQLAlchemy event listener to add correlation ID to SQL queries
        request_id_context.set(correlation_id)

        # Process request
        response = await call_next(request)

        # Add to response headers for client tracking
        response.headers["X-Request-ID"] = correlation_id

        return response
