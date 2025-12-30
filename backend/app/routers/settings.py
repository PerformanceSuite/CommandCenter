"""
Settings Router - API Key Management

Provides endpoints to view and update API keys stored in the .env file.
Keys are masked when returned for security.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.config import settings as app_settings

router = APIRouter(prefix="/settings", tags=["settings"])

# Path to .env file (relative to backend directory)
ENV_FILE = Path(__file__).parent.parent.parent / ".env"

# API keys we manage
API_KEY_FIELDS = {
    "ANTHROPIC_API_KEY": "Anthropic (Claude)",
    "OPENAI_API_KEY": "OpenAI (GPT)",
    "GOOGLE_API_KEY": "Google (Gemini)",
    "OPENROUTER_API_KEY": "OpenRouter",
    "ZAI_API_KEY": "Z.AI (GLM)",
    "GITHUB_TOKEN": "GitHub",
}


class ApiKeyInfo(BaseModel):
    """Information about an API key"""

    key: str = Field(..., description="Environment variable name")
    name: str = Field(..., description="Human-readable provider name")
    configured: bool = Field(..., description="Whether the key is set")
    masked_value: Optional[str] = Field(None, description="Last 4 chars if set")


class ApiKeysResponse(BaseModel):
    """Response containing all API key statuses"""

    keys: list[ApiKeyInfo]
    env_file_path: str


class ApiKeyUpdate(BaseModel):
    """Update request for a single API key"""

    key: str = Field(..., description="Environment variable name")
    value: str = Field(..., description="New API key value (empty string to remove)")


class ApiKeysUpdateRequest(BaseModel):
    """Request to update multiple API keys"""

    updates: list[ApiKeyUpdate]


def mask_key(value: str) -> str:
    """Mask an API key, showing only last 4 characters"""
    if len(value) <= 4:
        return "****"
    return f"{'*' * (len(value) - 4)}{value[-4:]}"


def read_env_file() -> dict[str, str]:
    """Read the .env file and return key-value pairs"""
    env_vars = {}
    if ENV_FILE.exists():
        with open(ENV_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    # Remove quotes if present
                    value = value.strip().strip("'\"")
                    env_vars[key.strip()] = value
    return env_vars


def write_env_file(env_vars: dict[str, str]) -> None:
    """Write key-value pairs to the .env file, preserving comments and structure"""
    existing_lines = []
    existing_keys = set()

    # Read existing file structure
    if ENV_FILE.exists():
        with open(ENV_FILE, "r") as f:
            for line in f:
                original_line = line.rstrip("\n")
                stripped = line.strip()

                if stripped and not stripped.startswith("#") and "=" in stripped:
                    key, _, _ = stripped.partition("=")
                    key = key.strip()
                    existing_keys.add(key)

                    if key in env_vars:
                        # Update existing key
                        value = env_vars[key]
                        if value:  # Only write non-empty values
                            existing_lines.append(f"{key}={value}")
                        # Skip empty values (effectively removing the key)
                    else:
                        # Keep other keys unchanged
                        existing_lines.append(original_line)
                else:
                    # Keep comments and empty lines
                    existing_lines.append(original_line)

    # Add new keys that weren't in the file
    for key, value in env_vars.items():
        if key not in existing_keys and value:
            existing_lines.append(f"{key}={value}")

    # Write the file
    with open(ENV_FILE, "w") as f:
        f.write("\n".join(existing_lines))
        if existing_lines and not existing_lines[-1] == "":
            f.write("\n")


@router.get("/api-keys", response_model=ApiKeysResponse)
async def get_api_keys() -> ApiKeysResponse:
    """
    Get status of all API keys.

    Returns masked values for security - only shows last 4 characters.
    """
    env_vars = read_env_file()

    keys = []
    for key, name in API_KEY_FIELDS.items():
        # Check both .env file and environment variables
        value = env_vars.get(key) or os.environ.get(key)
        configured = bool(value)

        keys.append(
            ApiKeyInfo(
                key=key,
                name=name,
                configured=configured,
                masked_value=mask_key(value) if configured else None,
            )
        )

    return ApiKeysResponse(keys=keys, env_file_path=str(ENV_FILE.absolute()))


@router.put("/api-keys")
async def update_api_keys(request: ApiKeysUpdateRequest) -> dict:
    """
    Update API keys in the .env file.

    Pass an empty string as value to remove a key.
    """
    # Validate keys
    valid_keys = set(API_KEY_FIELDS.keys())
    for update in request.updates:
        if update.key not in valid_keys:
            raise HTTPException(
                status_code=400,
                detail=f"Unknown API key: {update.key}. Valid keys: {list(valid_keys)}",
            )

    # Read current env file
    env_vars = read_env_file()

    # Apply updates
    updated_keys = []
    for update in request.updates:
        if update.value:
            env_vars[update.key] = update.value
            # Also update environment for immediate use
            os.environ[update.key] = update.value
            updated_keys.append(update.key)
        else:
            # Remove key
            env_vars.pop(update.key, None)
            os.environ.pop(update.key, None)
            updated_keys.append(f"{update.key} (removed)")

    # Write back
    write_env_file(env_vars)

    return {
        "status": "ok",
        "updated": updated_keys,
        "message": "API keys updated. Restart server for full effect.",
    }


@router.get("/providers")
async def get_providers() -> dict:
    """
    Get list of available LLM providers and their configuration status.
    """
    from libs.llm_gateway.providers import COSTS, PROVIDER_CONFIGS

    providers = []
    env_vars = read_env_file()

    for alias, config in PROVIDER_CONFIGS.items():
        # Determine which API key this provider needs
        if config.api_key_env:
            api_key_name = config.api_key_env
        elif "anthropic" in config.model_id:
            api_key_name = "ANTHROPIC_API_KEY"
        elif "openai" in config.model_id and not config.api_base:
            api_key_name = "OPENAI_API_KEY"
        elif "gemini" in config.model_id:
            api_key_name = "GOOGLE_API_KEY"
        else:
            api_key_name = "OPENROUTER_API_KEY"

        # Check if configured
        value = env_vars.get(api_key_name) or os.environ.get(api_key_name)
        configured = bool(value)

        cost = COSTS.get(alias)

        providers.append(
            {
                "alias": alias,
                "model_id": config.model_id,
                "api_key_required": api_key_name,
                "configured": configured,
                "cost_per_1m_input": cost.input if cost else None,
                "cost_per_1m_output": cost.output if cost else None,
            }
        )

    return {"providers": providers}


# ============================================================================
# Agent Configuration Endpoints (Database-backed)
# ============================================================================


def get_sync_session():
    """Get a sync database session for settings operations."""
    # Use sync engine for settings (simple CRUD, not performance critical)
    sync_url = app_settings.database_url.replace("+aiosqlite", "").replace("+asyncpg", "")
    engine = create_engine(sync_url)
    Session = sessionmaker(bind=engine)
    return Session()


class AgentConfigRequest(BaseModel):
    """Request to update agent's provider and model"""

    provider: str = Field(..., description="Provider name (anthropic, openai, google, zai)")
    model_id: str = Field(..., description="LiteLLM model ID")


class AgentConfigResponse(BaseModel):
    """Response for agent config"""

    role: str
    provider: str
    model_id: str


@router.get("/models")
async def list_models() -> dict:
    """
    List all available models grouped by provider.

    Models are dynamically fetched from LiteLLM's registry.
    """
    import os

    from libs.llm_gateway.providers import get_cached_models

    env_vars = read_env_file()
    available_models = get_cached_models()

    result: dict[str, list[dict]] = {}
    for provider, models in available_models.items():
        result[provider] = []
        for model in models:
            # Check if API key is configured
            api_key_env = model.api_key_env
            configured = (
                bool(env_vars.get(api_key_env) or os.environ.get(api_key_env))
                if api_key_env
                else True
            )

            result[provider].append(
                {
                    "id": model.id,
                    "name": model.name,
                    "cost_per_1m_input": model.cost_input,
                    "cost_per_1m_output": model.cost_output,
                    "configured": configured,
                }
            )

    return {"models": result}


@router.post("/models/refresh")
async def refresh_models() -> dict:
    """
    Force refresh the models cache from LiteLLM.
    """
    from libs.llm_gateway.providers import refresh_models_cache

    models = refresh_models_cache()
    return {"message": "Models cache refreshed", "provider_count": len(models)}


@router.get("/agents")
async def list_agents() -> dict:
    """
    List all agent role configurations.
    """
    from app.services.settings_service import SettingsService

    session = get_sync_session()
    try:
        service = SettingsService(session)
        configs = service.list_agent_configs()
        return {
            "agents": [
                {"role": c.role, "provider": c.provider, "model_id": c.model_id} for c in configs
            ]
        }
    finally:
        session.close()


@router.put("/agents/{role}")
async def set_agent_model(role: str, request: AgentConfigRequest) -> dict:
    """
    Set which provider and model an agent role should use.
    """
    from libs.llm_gateway.providers import get_cached_models

    from app.services.settings_service import SettingsService

    available_models = get_cached_models()

    # Validate provider exists
    if request.provider not in available_models:
        raise HTTPException(
            status_code=400,
            detail=f"Provider '{request.provider}' not found. Available: {list(available_models.keys())}",
        )

    # Validate model exists for provider
    provider_models = available_models[request.provider]
    valid_model_ids = [m.id for m in provider_models]
    if request.model_id not in valid_model_ids:
        raise HTTPException(
            status_code=400,
            detail=f"Model '{request.model_id}' not found for provider '{request.provider}'. Available: {valid_model_ids}",
        )

    session = get_sync_session()
    try:
        service = SettingsService(session)
        config = service.set_agent_model(role, request.provider, request.model_id)
        return {"role": config.role, "provider": config.provider, "model_id": config.model_id}
    finally:
        session.close()


@router.post("/seed")
async def seed_defaults() -> dict:
    """
    Seed default providers and agent configurations.

    Only populates if tables are empty.
    """
    from app.services.settings_service import SettingsService

    session = get_sync_session()
    try:
        service = SettingsService(session)
        service.seed_defaults()
        return {"message": "Seeded default providers and agent configs"}
    finally:
        session.close()
