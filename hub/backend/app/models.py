"""
Database models for Hub - DEPRECATED

This file is maintained for backward compatibility.
Import from app.models instead.
"""

# Import and re-export from new models package
from app.models import Base, Project, Event

__all__ = ["Base", "Project", "Event"]
