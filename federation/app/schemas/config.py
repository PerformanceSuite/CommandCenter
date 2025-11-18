"""
Pydantic schemas for federation config/projects.yaml validation

Validates the structure and data types of the projects configuration file
before loading into the catalog.
"""

from pydantic import BaseModel, Field, validator, HttpUrl
from typing import List


class ProjectConfig(BaseModel):
    """
    Schema for a single project in projects.yaml

    Example:
        slug: commandcenter
        name: CommandCenter
        hub_url: http://localhost:8000
        mesh_namespace: hub.commandcenter
        tags:
          - python
          - fastapi
        allow_fanout: []
    """

    slug: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Unique project identifier (URL-safe slug)"
    )

    name: str = Field(
        ...,
        min_length=1,
        max_length=200,
        description="Human-readable project name"
    )

    hub_url: str = Field(
        ...,
        pattern=r"^https?://.*",
        description="Hub's base URL (http:// or https://)"
    )

    mesh_namespace: str = Field(
        ...,
        pattern=r"^hub\.[a-z0-9-]+$",
        description="NATS subject namespace (hub.<project_slug>)"
    )

    tags: List[str] = Field(
        default_factory=list,
        description="Project tags/labels for filtering"
    )

    allow_fanout: List[str] = Field(
        default_factory=list,
        description="List of project slugs allowed to receive fanout messages"
    )

    @validator("slug")
    def validate_slug(cls, v):
        """Ensure slug is URL-safe (alphanumeric, dash, underscore only)."""
        if not v.replace("-", "").replace("_", "").isalnum():
            raise ValueError(
                f"slug '{v}' must contain only alphanumeric characters, dash, or underscore"
            )
        return v.lower()

    @validator("mesh_namespace")
    def validate_namespace_matches_slug(cls, v, values):
        """Ensure mesh_namespace matches pattern hub.<slug>."""
        if "slug" in values:
            expected = f"hub.{values['slug']}"
            if v != expected:
                raise ValueError(
                    f"mesh_namespace must be '{expected}', got '{v}'"
                )
        return v

    @validator("tags")
    def validate_tags(cls, v):
        """Ensure tags are non-empty strings."""
        for tag in v:
            if not tag or not tag.strip():
                raise ValueError("tags must be non-empty strings")
        return v

    @validator("allow_fanout")
    def validate_allow_fanout(cls, v):
        """Ensure allow_fanout contains valid slugs."""
        for slug in v:
            if not slug.replace("-", "").replace("_", "").isalnum():
                raise ValueError(
                    f"allow_fanout slug '{slug}' must contain only alphanumeric, dash, or underscore"
                )
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "slug": "commandcenter",
                "name": "CommandCenter",
                "hub_url": "http://localhost:8000",
                "mesh_namespace": "hub.commandcenter",
                "tags": ["python", "fastapi", "rag"],
                "allow_fanout": []
            }
        }


class ProjectsConfig(BaseModel):
    """
    Root schema for config/projects.yaml

    Structure:
        projects:
          - slug: project1
            name: Project 1
            ...
          - slug: project2
            name: Project 2
            ...
    """

    projects: List[ProjectConfig] = Field(
        ...,
        min_items=0,
        description="List of project configurations"
    )

    @validator("projects")
    def validate_unique_slugs(cls, v):
        """Ensure all project slugs are unique."""
        slugs = [p.slug for p in v]
        duplicates = [slug for slug in slugs if slugs.count(slug) > 1]
        if duplicates:
            raise ValueError(f"Duplicate project slugs found: {set(duplicates)}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "projects": [
                    {
                        "slug": "commandcenter",
                        "name": "CommandCenter",
                        "hub_url": "http://localhost:8000",
                        "mesh_namespace": "hub.commandcenter",
                        "tags": ["python", "fastapi"],
                        "allow_fanout": []
                    }
                ]
            }
        }
