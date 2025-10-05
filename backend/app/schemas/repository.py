"""
Pydantic schemas for Repository endpoints
"""

from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, ConfigDict, field_validator
import re


class RepositoryBase(BaseModel):
    """Base schema for repository"""
    owner: str = Field(..., min_length=1, max_length=255)
    name: str = Field(..., min_length=1, max_length=255)
    description: Optional[str] = None
    access_token: Optional[str] = None
    is_private: bool = False


class RepositoryCreate(RepositoryBase):
    """Schema for creating a repository"""

    @field_validator('owner', 'name')
    @classmethod
    def validate_github_name(cls, v: str) -> str:
        """Validate GitHub owner/repo names"""
        if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9-]*[a-zA-Z0-9]$', v):
            raise ValueError('Invalid GitHub name format')
        return v

    @field_validator('access_token')
    @classmethod
    def validate_token(cls, v: Optional[str]) -> Optional[str]:
        """Validate GitHub token format"""
        if v and not re.match(r'^(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36,255}$', v):
            raise ValueError('Invalid GitHub token format')
        return v


class RepositoryUpdate(BaseModel):
    """Schema for updating a repository"""
    description: Optional[str] = None
    access_token: Optional[str] = None
    is_private: Optional[bool] = None
    metadata_: Optional[dict] = None


class RepositoryInDB(RepositoryBase):
    """Schema for repository in database"""
    id: int
    full_name: str
    github_id: Optional[int] = None
    url: Optional[str] = None
    clone_url: Optional[str] = None
    default_branch: str
    last_commit_sha: Optional[str] = None
    last_commit_message: Optional[str] = None
    last_commit_author: Optional[str] = None
    last_commit_date: Optional[datetime] = None
    last_synced_at: Optional[datetime] = None
    stars: int
    forks: int
    language: Optional[str] = None
    metadata_: Optional[dict] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RepositoryResponse(RepositoryInDB):
    """Schema for repository API response"""
    pass


class RepositorySyncRequest(BaseModel):
    """Schema for repository sync request"""
    force: bool = Field(default=False, description="Force sync even if recently synced")


class RepositorySyncResponse(BaseModel):
    """Schema for repository sync response"""
    repository_id: int
    synced: bool
    last_commit_sha: Optional[str] = None
    last_commit_message: Optional[str] = None
    last_synced_at: datetime
    changes_detected: bool
