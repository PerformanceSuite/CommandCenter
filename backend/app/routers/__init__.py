"""
API routers for FastAPI endpoints
"""

from app.routers import (
    skills,
    auth,
    batch,
    dashboard,
    hypotheses,
    knowledge,
    repositories,
    research_tasks,
    settings,
    sse,
    technologies,
)

__all__ = [
    "auth",
    "repositories",
    "technologies",
    "dashboard",
    "knowledge",
    "research_tasks",
    "batch",
    "hypotheses",
    "settings",
    "sse",
]
