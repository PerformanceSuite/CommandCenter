"""Pydantic schemas for Agent Persona API."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AgentPersonaBase(BaseModel):
    """Base schema for AgentPersona with shared fields."""

    name: str = Field(..., min_length=1, max_length=100, description="Unique identifier name")
    display_name: str = Field(..., min_length=1, max_length=200, description="Human-readable name")
    description: str | None = Field(None, description="Description of the persona")
    category: str = Field(
        default="custom", max_length=50, description="Category (assessment, coding, verification, custom)"
    )
    system_prompt: str = Field(..., min_length=1, description="System prompt for the agent")
    model: str = Field(
        default="claude-sonnet-4-20250514", max_length=100, description="LLM model identifier"
    )
    temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="Temperature for LLM generation")
    requires_sandbox: bool = Field(default=False, description="Whether agent requires sandbox execution")
    tags: list[str] = Field(default_factory=list, description="Tags for categorization")
    is_active: bool = Field(default=True, description="Whether the persona is active")


class AgentPersonaCreate(AgentPersonaBase):
    """Schema for creating a new AgentPersona."""

    pass


class AgentPersonaUpdate(BaseModel):
    """Schema for updating an existing AgentPersona."""

    display_name: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = None
    category: str | None = Field(None, max_length=50)
    system_prompt: str | None = Field(None, min_length=1)
    model: str | None = Field(None, max_length=100)
    temperature: float | None = Field(None, ge=0.0, le=2.0)
    requires_sandbox: bool | None = None
    tags: list[str] | None = None
    is_active: bool | None = None


class AgentPersonaResponse(AgentPersonaBase):
    """Schema for AgentPersona responses."""

    id: int
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AgentPersonaListResponse(BaseModel):
    """Schema for listing multiple personas."""

    personas: list[AgentPersonaResponse]
    total: int
