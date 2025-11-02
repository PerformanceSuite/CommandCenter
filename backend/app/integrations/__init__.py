"""
External integration services for CommandCenter.

Provides integrations with:
- GitHub: Enhanced repo features, Issues sync, Actions automation
- Generic: Base classes for custom integrations
"""

from app.integrations.base import (
    BaseIntegration,
    IntegrationError,
    IntegrationAuthError,
)
from app.integrations.github_integration import GitHubIntegration

__all__ = [
    "BaseIntegration",
    "IntegrationError",
    "IntegrationAuthError",
    "GitHubIntegration",
]
