"""
Rate limiting middleware using slowapi
Protects API endpoints from abuse and DoS attacks
"""

from slowapi import Limiter
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

# Create limiter instance
# Uses the client's IP address for rate limiting
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["100/minute", "1000/hour"],
    storage_uri="memory://",  # Use memory storage (consider Redis for production)
    strategy="fixed-window",
)

__all__ = ["limiter", "RateLimitExceeded"]
