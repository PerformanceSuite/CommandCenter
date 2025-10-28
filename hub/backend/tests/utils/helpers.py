"""
Test helper functions for Hub

Provides utility functions for common test operations.
"""

from typing import Optional
from unittest.mock import AsyncMock, MagicMock


def create_mock_dagger_response(success: bool = True, message: str = "Success"):
    """Create mock Dagger operation response"""
    return {
        "success": success,
        "message": message,
        "services": {
            "postgres": {"port": 5432},
            "redis": {"port": 6379},
            "backend": {"port": 8000},
            "frontend": {"port": 3000},
        },
    }


def create_mock_dagger_stack(
    start_result: Optional[dict] = None,
    stop_result: Optional[dict] = None,
    status_result: Optional[dict] = None,
):
    """Create mock CommandCenterStack for testing"""
    stack = AsyncMock()
    stack.__aenter__ = AsyncMock(return_value=stack)
    stack.__aexit__ = AsyncMock(return_value=None)

    stack.start = AsyncMock(
        return_value=start_result or create_mock_dagger_response()
    )
    stack.stop = AsyncMock(
        return_value=stop_result
        or {"success": True, "message": "Stack stopped successfully"}
    )
    stack.status = AsyncMock(
        return_value=status_result
        or {"status": "running", "health": "healthy", "containers": []}
    )

    return stack


def create_port_conflict_mock(conflicting_ports: list[int]):
    """
    Create a mock for port checking that simulates port conflicts

    Args:
        conflicting_ports: List of port numbers that should appear in use

    Returns:
        Mock socket context manager
    """

    def connect_ex_side_effect(address):
        """Return 0 (in use) for conflicting ports, 1 (available) for others"""
        host, port = address
        return 0 if port in conflicting_ports else 1

    mock_sock = MagicMock()
    mock_sock.connect_ex.side_effect = connect_ex_side_effect
    mock_sock.__enter__ = MagicMock(return_value=mock_sock)
    mock_sock.__exit__ = MagicMock(return_value=None)

    return mock_sock


async def create_test_project(db_session, **kwargs):
    """
    Helper to create a test project in the database

    Usage:
        project = await create_test_project(
            db_session,
            name="MyProject",
            status="running"
        )
    """
    from app.models import Project

    defaults = {
        "name": "TestProject",
        "slug": "test-project",
        "path": "/tmp/test-project",
        "status": "stopped",
        "backend_port": 8010,
        "frontend_port": 3010,
        "postgres_port": 5442,
        "redis_port": 6389,
        "is_configured": True,
    }

    defaults.update(kwargs)
    project = Project(**defaults)

    db_session.add(project)
    await db_session.commit()
    await db_session.refresh(project)

    return project
