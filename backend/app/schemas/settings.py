"""Pydantic schemas for settings API."""

from pydantic import BaseModel, ConfigDict, Field


class ProviderBase(BaseModel):
    alias: str = Field(..., min_length=1, max_length=50)
    model_id: str = Field(..., min_length=1, max_length=200)
    api_base: str | None = None
    api_key_env: str | None = None
    cost_input: float = 0.0
    cost_output: float = 0.0
    is_active: bool = True


class ProviderCreate(ProviderBase):
    api_key: str | None = None  # Plain text, will be encrypted


class ProviderUpdate(BaseModel):
    model_id: str | None = None
    api_base: str | None = None
    api_key_env: str | None = None
    api_key: str | None = None
    cost_input: float | None = None
    cost_output: float | None = None
    is_active: bool | None = None


class ProviderResponse(ProviderBase):
    id: str
    api_key_set: bool  # Is a key stored?
    api_key_masked: str  # Masked for display

    model_config = ConfigDict(from_attributes=True)


class ProviderKeyResponse(BaseModel):
    api_key: str


class AgentConfigResponse(BaseModel):
    role: str
    provider_alias: str

    model_config = ConfigDict(from_attributes=True)


class AgentConfigUpdate(BaseModel):
    provider_alias: str


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    model: str | None = None
