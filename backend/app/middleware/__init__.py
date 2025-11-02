"""
Middleware for security, rate limiting, logging, and other cross-cutting concerns
"""

# Existing middleware
from app.middleware.logging import LoggingMiddleware
from app.middleware.rate_limit import limiter, RateLimitExceeded
from app.middleware.security_headers import add_security_headers

# Phase C: Correlation ID middleware
from app.middleware.correlation import CorrelationIDMiddleware

__all__ = [
    "LoggingMiddleware",
    "limiter",
    "RateLimitExceeded",
    "add_security_headers",
    "CorrelationIDMiddleware",  # Phase C addition
]
