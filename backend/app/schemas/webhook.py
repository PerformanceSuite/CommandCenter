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


class WebhookDeliveryCreate(BaseModel):
    """Schema for creating webhook delivery"""

    config_id: int
    event_type: str
    payload: Dict[str, Any]
    target_url: Optional[str] = None


class WebhookDeliveryResponse(BaseModel):
    """Schema for webhook delivery response"""

    id: int
    project_id: int
    config_id: int
    event_type: str
    payload: Dict[str, Any]
    target_url: str
    attempt_number: int
    status: str
    http_status_code: Optional[int]
    response_body: Optional[str]
    error_message: Optional[str]
    scheduled_for: datetime
    attempted_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration_ms: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class WebhookDeliveryListResponse(BaseModel):
    """Schema for list of webhook deliveries with pagination"""

    deliveries: List[WebhookDeliveryResponse]
    total: int
    page: int
    page_size: int


class WebhookStatisticsResponse(BaseModel):
    """Schema for webhook statistics"""

    total_configs: int
    total_deliveries: int
    successful_deliveries: int
    failed_deliveries: int
    success_rate: float
