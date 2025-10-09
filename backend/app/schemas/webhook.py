"""
Webhook schemas for request/response validation
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field


class WebhookConfigCreate(BaseModel):
    """Schema for creating webhook configuration"""

    repository_id: int
    webhook_url: str
    secret: str
    events: List[str] = Field(default=["push", "pull_request", "issues"])


class WebhookConfigUpdate(BaseModel):
    """Schema for updating webhook configuration"""

    webhook_url: Optional[str] = None
    secret: Optional[str] = None
    events: Optional[List[str]] = None
    active: Optional[bool] = None


class WebhookConfigResponse(BaseModel):
    """Schema for webhook configuration response"""

    id: int
    repository_id: int
    webhook_id: Optional[int]
    webhook_url: str
    events: List[str]
    active: bool
    last_delivery_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class WebhookEventResponse(BaseModel):
    """Schema for webhook event response"""

    id: int
    config_id: Optional[int]
    event_type: str
    delivery_id: str
    payload: Dict[str, Any]
    repository_full_name: Optional[str]
    processed: bool
    processed_at: Optional[datetime]
    error: Optional[str]
    received_at: datetime

    class Config:
        from_attributes = True


class WebhookPayload(BaseModel):
    """Schema for incoming webhook payload"""

    # GitHub sends various payloads depending on event type
    # This is a flexible schema that accepts any structure
    pass

    class Config:
        extra = "allow"


class GitHubRateLimitResponse(BaseModel):
    """Schema for GitHub rate limit status"""

    resource_type: str
    limit: int
    remaining: int
    reset_at: datetime
    percentage_used: float = Field(description="Percentage of rate limit used")

    class Config:
        from_attributes = True


class RateLimitStatusResponse(BaseModel):
    """Schema for overall rate limit status"""

    core: GitHubRateLimitResponse
    search: Optional[GitHubRateLimitResponse] = None
    graphql: Optional[GitHubRateLimitResponse] = None
