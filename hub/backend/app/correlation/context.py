"""Correlation context management using contextvars.

Provides thread-safe correlation ID storage for request tracking.
"""
from contextvars import ContextVar
from typing import Optional


_correlation_id: ContextVar[Optional[str]] = ContextVar(
    'correlation_id',
    default=None
)


def get_correlation_id() -> Optional[str]:
    """Get correlation ID from current context.

    Returns:
        Correlation ID string or None if not set
    """
    return _correlation_id.get()


def set_correlation_id(correlation_id: str) -> None:
    """Set correlation ID in current context.

    Args:
        correlation_id: UUID string for request correlation
    """
    _correlation_id.set(correlation_id)


def clear_correlation_id() -> None:
    """Clear correlation ID from current context."""
    _correlation_id.set(None)
