"""
Pydantic schemas for Agent Persona endpoints
"""

from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentPersonaBase(BaseModel):
    """Base schema for agent persona"""

    name: str = Field(..., min_length=1, max_length=255, description="Unique persona identifier")
    display_name: str = Field(..., min_length=1, max_length=255, description="Human-readable name")
    description: Optional[str] = Field(None, description="Description of the persona")
    category: str = Field(
        default="custom",
        max_length=100,
        description="Persona category (assessment, verification, coding, synthesis, custom)",
    )
    system_prompt: str = Field(..., min_length=1, description="System prompt for the agent")
    model: str = Field(
        default="claude-sonnet-4-20250514",
        max_length=255,
        description="Model identifier to use",
    )
    temperature: float = Field(
        default=0.7, ge=0.0, le=2.0, description="Temperature for model sampling"
    )
    requires_sandbox: bool = Field(
        default=False, description="Whether the persona requires sandbox execution"
    )
    tags: Optional[dict[str, Any]] = Field(
        None, description="Additional metadata tags (JSON)"
    )
    is_active: bool = Field(default=True, description="Whether the persona is active")


class AgentPersonaCreate(AgentPersonaBase):
    """Schema for creating an agent persona"""


class AgentPersonaUpdate(BaseModel):
    """Schema for updating an agent persona"""

    display_name: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = None
    category: Optional[str] = Field(None, max_length=100)
    system_prompt: Optional[str] = Field(None, min_length=1)
    model: Optional[str] = Field(None, max_length=255)
    temperature: Optional[float] = Field(None, ge=0.0, le=2.0)
    requires_sandbox: Optional[bool] = None
    tags: Optional[dict[str, Any]] = None
    is_active: Optional[bool] = None


class AgentPersonaInDB(AgentPersonaBase):
    """Schema for agent persona in database"""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentPersonaResponse(AgentPersonaInDB):
    """Schema for agent persona API response"""


class AgentPersonaListResponse(BaseModel):
    """Schema for agent persona list response"""

    total: int
    items: list[AgentPersonaResponse]
    page: int = 1
    page_size: int = 50
