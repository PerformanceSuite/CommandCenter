"""
Settings Router - Provider and Agent Configuration

Provides endpoints to manage LLM providers and agent model assignments.
"""

import os
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/v1/settings", tags=["settings"])

# Path to .env file
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


@router.get("/providers")
async def get_providers(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Get list of available LLM providers and their configuration status.
    """
    try:
        from libs.llm_gateway.providers import COSTS, PROVIDER_CONFIGS
    except ImportError:
        # Fallback if llm_gateway not available
        PROVIDER_CONFIGS = {}
        COSTS = {}

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
# Agent Configuration Endpoints
# ============================================================================


class AgentConfigRequest(BaseModel):
    """Request to update agent's provider and model"""

    provider: str = Field(..., description="Provider name (anthropic, openai, google, zai)")
    model_id: str = Field(..., description="LiteLLM model ID")


@router.get("/models")
async def list_models() -> dict:
    """
    List all available models grouped by provider.

    Models are dynamically fetched from LiteLLM's registry.
    """
    try:
        from libs.llm_gateway.providers import get_cached_models
        available_models = get_cached_models()
    except ImportError:
        # Fallback if llm_gateway not available
        available_models = {}

    env_vars = read_env_file()

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
    try:
        from libs.llm_gateway.providers import refresh_models_cache
        models = refresh_models_cache()
        return {"message": "Models cache refreshed", "provider_count": len(models)}
    except ImportError:
        return {"message": "LLM gateway not available", "provider_count": 0}


@router.get("/agents")
async def list_agents(db: AsyncSession = Depends(get_db)) -> dict:
    """
    List all agent role configurations.
    """
    service = SettingsService(db)
    configs = await service.list_agent_configs()
    return {
        "agents": [
            {"role": c.role, "provider": c.provider, "model_id": c.model_id} for c in configs
        ]
    }


@router.put("/agents/{role}")
async def set_agent_model(
    role: str,
    request: AgentConfigRequest,
    db: AsyncSession = Depends(get_db)
) -> dict:
    """
    Set which provider and model an agent role should use.
    """
    try:
        from libs.llm_gateway.providers import get_cached_models
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
    except ImportError:
        # Allow any model if llm_gateway not available
        pass

    service = SettingsService(db)
    config = await service.set_agent_model(role, request.provider, request.model_id)
    return {"role": config.role, "provider": config.provider, "model_id": config.model_id}


@router.post("/seed")
async def seed_defaults(db: AsyncSession = Depends(get_db)) -> dict:
    """
    Seed default providers and agent configurations.

    Only populates if tables are empty.
    """
    service = SettingsService(db)
    await service.seed_defaults()
    return {"message": "Seeded default providers and agent configs"}
