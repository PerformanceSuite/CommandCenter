"""
Repository pattern implementations for data access layer
"""

from .base import BaseRepository
from .intelligence_repository import (
    DebateRepository,
    EvidenceRepository,
    HypothesisRepository,
    ResearchFindingRepository,
)
from .repository_repository import RepositoryRepository
from .research_task_repository import ResearchTaskRepository
from .technology_repository import TechnologyRepository

__all__ = [
    "BaseRepository",
    "RepositoryRepository",
    "TechnologyRepository",
    "ResearchTaskRepository",
    # Intelligence Integration
    "HypothesisRepository",
    "EvidenceRepository",
    "DebateRepository",
    "ResearchFindingRepository",
]
