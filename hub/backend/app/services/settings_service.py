"""Service for managing LLM provider and agent settings (async version)."""

from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import AgentConfig, Provider
from app.services.crypto import decrypt_key, encrypt_key, mask_key

# Default providers to seed
DEFAULT_PROVIDERS: list[dict[str, Any]] = [
    {
        "alias": "claude",
        "model_id": "anthropic/claude-sonnet-4-20250514",
        "cost_input": 3.0,
        "cost_output": 15.0,
    },
    {
        "alias": "gemini",
        "model_id": "gemini/gemini-2.5-flash",
        "cost_input": 0.15,
        "cost_output": 0.60,
    },
    {
        "alias": "gpt",
        "model_id": "openai/gpt-4o",
        "cost_input": 2.50,
        "cost_output": 10.0,
    },
    {
        "alias": "gpt-mini",
        "model_id": "openai/gpt-4o-mini",
        "cost_input": 0.15,
        "cost_output": 0.60,
    },
    {
        "alias": "zai",
        "model_id": "openai/glm-4.7",
        "api_base": "https://api.z.ai/api/paas/v4",
        "api_key_env": "ZAI_API_KEY",
        "cost_input": 0.50,
        "cost_output": 2.0,
    },
    {
        "alias": "zai-flash",
        "model_id": "openai/glm-4.5-flash",
        "api_base": "https://api.z.ai/api/paas/v4",
        "api_key_env": "ZAI_API_KEY",
        "cost_input": 0.05,
        "cost_output": 0.20,
    },
]

# Default agent configurations (provider + model_id)
DEFAULT_AGENT_CONFIGS: list[dict[str, str]] = [
    {"role": "analyst", "provider": "google", "model_id": "gemini/gemini-2.5-flash"},
    {"role": "researcher", "provider": "google", "model_id": "gemini/gemini-2.5-flash"},
    {"role": "strategist", "provider": "openai", "model_id": "openai/gpt-4o"},
    {"role": "critic", "provider": "google", "model_id": "gemini/gemini-2.5-flash"},
    {"role": "chairman", "provider": "anthropic", "model_id": "anthropic/claude-sonnet-4-20250514"},
]


class SettingsService:
    """Manages provider and agent configuration (async)."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # --- Provider CRUD ---

    async def create_provider(
        self,
        alias: str,
        model_id: str,
        api_base: str | None = None,
        api_key_env: str | None = None,
        cost_input: float = 0.0,
        cost_output: float = 0.0,
        is_active: bool = True,
    ) -> Provider:
        """Create a new provider."""
        provider = Provider(
            alias=alias,
            model_id=model_id,
            api_base=api_base,
            api_key_env=api_key_env,
            cost_input=cost_input,
            cost_output=cost_output,
            is_active=is_active,
        )
        self.db.add(provider)
        await self.db.commit()
        await self.db.refresh(provider)
        return provider

    async def list_providers(self, active_only: bool = False) -> list[Provider]:
        """List all providers."""
        query = select(Provider)
        if active_only:
            query = query.filter(Provider.is_active == True)  # noqa: E712
        query = query.order_by(Provider.alias)
        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def get_provider(self, alias: str) -> Provider | None:
        """Get provider by alias."""
        result = await self.db.execute(
            select(Provider).filter(Provider.alias == alias)
        )
        return result.scalar_one_or_none()

    async def update_provider(self, alias: str, **kwargs) -> Provider | None:
        """Update provider fields."""
        provider = await self.get_provider(alias)
        if not provider:
            return None

        for key, value in kwargs.items():
            if hasattr(provider, key) and key not in ("id", "alias", "created_at"):
                setattr(provider, key, value)

        await self.db.commit()
        await self.db.refresh(provider)
        return provider

    async def delete_provider(self, alias: str) -> bool:
        """Delete a provider."""
        provider = await self.get_provider(alias)
        if not provider:
            return False

        await self.db.delete(provider)
        await self.db.commit()
        return True

    async def set_provider_api_key(self, alias: str, api_key: str) -> Provider | None:
        """Set and encrypt API key for provider."""
        provider = await self.get_provider(alias)
        if not provider:
            return None

        provider.api_key_encrypted = encrypt_key(api_key) if api_key else None
        await self.db.commit()
        await self.db.refresh(provider)
        return provider

    async def get_provider_api_key(self, alias: str) -> str | None:
        """Get decrypted API key for provider."""
        provider = await self.get_provider(alias)
        if not provider or not provider.api_key_encrypted:
            return None
        return decrypt_key(provider.api_key_encrypted)

    async def get_provider_api_key_masked(self, alias: str) -> str:
        """Get masked API key for display."""
        key = await self.get_provider_api_key(alias)
        return mask_key(key) if key else ""

    # --- Agent Config ---

    async def set_agent_model(self, role: str, provider: str, model_id: str) -> AgentConfig:
        """Set which provider and model an agent role uses."""
        result = await self.db.execute(
            select(AgentConfig).filter(AgentConfig.role == role)
        )
        config = result.scalar_one_or_none()

        if config:
            config.provider = provider
            config.model_id = model_id
        else:
            config = AgentConfig(role=role, provider=provider, model_id=model_id)
            self.db.add(config)

        await self.db.commit()
        await self.db.refresh(config)
        return config

    async def get_agent_config(self, role: str) -> AgentConfig | None:
        """Get agent config by role."""
        result = await self.db.execute(
            select(AgentConfig).filter(AgentConfig.role == role)
        )
        return result.scalar_one_or_none()

    async def list_agent_configs(self) -> list[AgentConfig]:
        """List all agent configurations."""
        result = await self.db.execute(
            select(AgentConfig).order_by(AgentConfig.role)
        )
        return list(result.scalars().all())

    # --- Seeding ---

    async def seed_defaults(self) -> None:
        """Seed default providers and agent configs if tables are empty."""
        # Check if providers exist
        result = await self.db.execute(select(Provider).limit(1))
        if result.scalar_one_or_none() is None:
            for p in DEFAULT_PROVIDERS:
                cost_in = p.get("cost_input", 0.0)
                cost_out = p.get("cost_output", 0.0)
                await self.create_provider(
                    alias=str(p["alias"]),
                    model_id=str(p["model_id"]),
                    api_base=str(p["api_base"]) if p.get("api_base") else None,
                    api_key_env=str(p["api_key_env"]) if p.get("api_key_env") else None,
                    cost_input=float(cost_in) if cost_in is not None else 0.0,
                    cost_output=float(cost_out) if cost_out is not None else 0.0,
                )

        # Check if agent configs exist
        result = await self.db.execute(select(AgentConfig).limit(1))
        if result.scalar_one_or_none() is None:
            for c in DEFAULT_AGENT_CONFIGS:
                await self.set_agent_model(
                    role=str(c["role"]),
                    provider=str(c["provider"]),
                    model_id=str(c["model_id"]),
                )
