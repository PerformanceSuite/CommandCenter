"""
MCP Authentication Schemas

Pydantic models for MCP token generation and management
"""

from datetime import datetime
from pydantic import BaseModel, Field


class MCPTokenRequest(BaseModel):
    """Request to generate MCP authentication token"""

    project_id: str = Field(
        ..., description="Project identifier for this MCP client", min_length=1
    )
    ttl_hours: int = Field(
        default=24, description="Token time-to-live in hours", ge=1, le=720
    )


class MCPTokenResponse(BaseModel):
    """Response containing MCP authentication token"""

    token: str = Field(..., description="MCP authentication token")
    expires_at: datetime = Field(..., description="Token expiration timestamp (UTC)")
    client_id: str = Field(..., description="Client identifier")


class MCPTokenValidationRequest(BaseModel):
    """Request to validate MCP token"""

    token: str = Field(..., description="MCP token to validate", min_length=1)


class MCPTokenValidationResponse(BaseModel):
    """Response from token validation"""

    valid: bool = Field(..., description="Whether token is valid")
    client_id: str | None = Field(None, description="Client ID if valid")
    message: str = Field(..., description="Validation result message")
