"""
Pydantic schemas for NATS heartbeat message validation
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime


class HeartbeatMessage(BaseModel):
    """
    Schema for validating NATS heartbeat messages from hub projects.

    Expected message format:
    {
        "project_slug": "commandcenter",
        "mesh_namespace": "hub.commandcenter",
        "timestamp": "2025-11-18T04:00:00Z",
        "hub_url": "http://localhost:3000"
    }
    """

    project_slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique project identifier (slug)"
    )

    mesh_namespace: Optional[str] = Field(
        None,
        pattern=r"^hub\.[a-z0-9-]+$",
        description="NATS subject namespace (hub.<project_slug>)"
    )

    timestamp: Optional[str] = Field(
        None,
        description="ISO 8601 timestamp of when heartbeat was sent"
    )

    hub_url: Optional[str] = Field(
        None,
        pattern=r"^https?://.*",
        description="Hub's base URL"
    )

    @validator("project_slug")
    def validate_project_slug(cls, v):
        """Ensure project_slug matches URL-safe characters."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError("project_slug must contain only alphanumeric, dash, or underscore")
        return v.lower()

    @validator("mesh_namespace")
    def validate_namespace_matches_slug(cls, v, values):
        """Ensure mesh_namespace matches project_slug."""
        if v and "project_slug" in values:
            expected = f"hub.{values['project_slug']}"
            if v != expected:
                raise ValueError(f"mesh_namespace must be '{expected}', got '{v}'")
        return v

    class Config:
        # Allow extra fields for forward compatibility
        extra = "allow"
        json_schema_extra = {
            "example": {
                "project_slug": "commandcenter",
                "mesh_namespace": "hub.commandcenter",
                "timestamp": "2025-11-18T04:00:00Z",
                "hub_url": "http://localhost:3000"
            }
        }
