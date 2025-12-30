# Settings & Hypothesis Input Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Add UI for managing LLM providers/API keys, agent configuration, and quick hypothesis input.

**Architecture:** New SQLite tables store provider configs and agent assignments. Settings API exposes CRUD. Frontend adds Settings tab and hypothesis input form. LLMGateway reads from DB with static fallback.

**Tech Stack:** FastAPI, SQLAlchemy, Fernet encryption, React, TypeScript, TailwindCSS

---

## Phase 1: Backend Foundation

### Task 1: Crypto Utility for API Key Encryption

**Files:**
- Create: `backend/app/services/crypto.py`
- Test: `backend/tests/test_services/test_crypto.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_services/test_crypto.py
import pytest
from app.services.crypto import encrypt_key, decrypt_key, get_or_create_secret_key


def test_encrypt_decrypt_roundtrip():
    """Encrypted key can be decrypted back to original."""
    original = "sk-ant-api03-test-key-12345"
    encrypted = encrypt_key(original)
    decrypted = decrypt_key(encrypted)
    assert decrypted == original


def test_encrypted_differs_from_original():
    """Encrypted value is not the same as original."""
    original = "sk-ant-api03-test-key-12345"
    encrypted = encrypt_key(original)
    assert encrypted != original


def test_encrypt_empty_string():
    """Empty string encrypts and decrypts correctly."""
    encrypted = encrypt_key("")
    assert decrypt_key(encrypted) == ""


def test_get_or_create_secret_key_creates_file(tmp_path, monkeypatch):
    """Secret key file is created if it doesn't exist."""
    key_path = tmp_path / "secret.key"
    monkeypatch.setenv("COMMANDCENTER_KEY_PATH", str(key_path))

    key = get_or_create_secret_key()

    assert key_path.exists()
    assert len(key) == 44  # Fernet key is 44 chars base64
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_services/test_crypto.py -v`
Expected: FAIL with "No module named 'app.services.crypto'"

**Step 3: Create test directory if needed**

```bash
mkdir -p backend/tests/test_services
touch backend/tests/test_services/__init__.py
```

**Step 4: Write implementation**

```python
# backend/app/services/crypto.py
"""Encryption utilities for storing API keys securely."""

import os
from pathlib import Path

from cryptography.fernet import Fernet

# Default key path - can be overridden via env var
DEFAULT_KEY_PATH = Path.home() / ".commandcenter" / "secret.key"


def get_key_path() -> Path:
    """Get the path to the secret key file."""
    env_path = os.environ.get("COMMANDCENTER_KEY_PATH")
    if env_path:
        return Path(env_path)
    return DEFAULT_KEY_PATH


def get_or_create_secret_key() -> str:
    """Get existing secret key or create a new one."""
    key_path = get_key_path()

    if key_path.exists():
        return key_path.read_text().strip()

    # Create directory if needed
    key_path.parent.mkdir(parents=True, exist_ok=True)

    # Generate new key
    key = Fernet.generate_key().decode()
    key_path.write_text(key)

    # Secure permissions (owner read/write only)
    key_path.chmod(0o600)

    return key


def get_fernet() -> Fernet:
    """Get Fernet instance with the secret key."""
    key = get_or_create_secret_key()
    return Fernet(key.encode())


def encrypt_key(plaintext: str) -> str:
    """Encrypt an API key for storage."""
    if not plaintext:
        return ""
    f = get_fernet()
    return f.encrypt(plaintext.encode()).decode()


def decrypt_key(ciphertext: str) -> str:
    """Decrypt a stored API key."""
    if not ciphertext:
        return ""
    f = get_fernet()
    return f.decrypt(ciphertext.encode()).decode()


def mask_key(key: str) -> str:
    """Mask an API key for display (show first 7 and last 4 chars)."""
    if not key or len(key) < 12:
        return "***"
    return f"{key[:7]}***{key[-4:]}"
```

**Step 5: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_services/test_crypto.py -v`
Expected: PASS (4 tests)

**Step 6: Commit**

```bash
git add backend/app/services/crypto.py backend/tests/test_services/
git commit -m "feat(settings): add crypto utilities for API key encryption"
```

---

### Task 2: Settings SQLAlchemy Models

**Files:**
- Create: `backend/app/models/settings.py`
- Modify: `backend/app/models/__init__.py`
- Test: `backend/tests/test_models/test_settings.py`

**Step 1: Write the failing test**

```python
# backend/tests/test_models/test_settings.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.settings import Provider, AgentConfig, Base


@pytest.fixture
def db_session():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


def test_create_provider(db_session):
    """Can create a provider with all fields."""
    provider = Provider(
        alias="claude",
        model_id="anthropic/claude-sonnet-4-20250514",
        cost_input=3.0,
        cost_output=15.0,
    )
    db_session.add(provider)
    db_session.commit()

    result = db_session.query(Provider).filter_by(alias="claude").first()
    assert result is not None
    assert result.model_id == "anthropic/claude-sonnet-4-20250514"
    assert result.is_active is True


def test_provider_alias_unique(db_session):
    """Provider alias must be unique."""
    p1 = Provider(alias="gpt", model_id="openai/gpt-4o")
    p2 = Provider(alias="gpt", model_id="openai/gpt-4o-mini")

    db_session.add(p1)
    db_session.commit()

    db_session.add(p2)
    with pytest.raises(Exception):  # IntegrityError
        db_session.commit()


def test_create_agent_config(db_session):
    """Can create agent config linked to provider."""
    provider = Provider(alias="gemini", model_id="gemini/gemini-2.5-flash")
    db_session.add(provider)
    db_session.commit()

    config = AgentConfig(role="analyst", provider_alias="gemini")
    db_session.add(config)
    db_session.commit()

    result = db_session.query(AgentConfig).filter_by(role="analyst").first()
    assert result.provider_alias == "gemini"
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_models/test_settings.py -v`
Expected: FAIL with "No module named 'app.models.settings'"

**Step 3: Write implementation**

```python
# backend/app/models/settings.py
"""Settings models for LLM provider and agent configuration."""

import uuid
from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, String, Text
from sqlalchemy.orm import relationship

from app.db import Base


def generate_uuid() -> str:
    return str(uuid.uuid4())


class Provider(Base):
    """LLM provider configuration."""

    __tablename__ = "providers"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    alias = Column(String(50), unique=True, nullable=False, index=True)
    model_id = Column(String(200), nullable=False)  # LiteLLM format
    api_base = Column(String(500), nullable=True)   # Custom endpoint
    api_key_env = Column(String(100), nullable=True)  # Env var name
    api_key_encrypted = Column(Text, nullable=True)   # Encrypted stored key
    cost_input = Column(Float, default=0.0)   # Per 1M input tokens
    cost_output = Column(Float, default=0.0)  # Per 1M output tokens
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationship to agent configs
    agent_configs = relationship("AgentConfig", back_populates="provider")

    def __repr__(self):
        return f"<Provider {self.alias}: {self.model_id}>"


class AgentConfig(Base):
    """Agent role to provider mapping."""

    __tablename__ = "agent_configs"

    role = Column(String(50), primary_key=True)  # analyst, researcher, etc.
    provider_alias = Column(
        String(50),
        ForeignKey("providers.alias", onupdate="CASCADE"),
        nullable=False
    )

    # Relationship to provider
    provider = relationship("Provider", back_populates="agent_configs")

    def __repr__(self):
        return f"<AgentConfig {self.role} -> {self.provider_alias}>"
```

**Step 4: Update models __init__.py**

```python
# Add to backend/app/models/__init__.py
from app.models.settings import Provider, AgentConfig
```

**Step 5: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_models/test_settings.py -v`
Expected: PASS (3 tests)

**Step 6: Commit**

```bash
git add backend/app/models/settings.py backend/app/models/__init__.py backend/tests/test_models/
git commit -m "feat(settings): add Provider and AgentConfig models"
```

---

### Task 3: Database Migration

**Files:**
- Create: `backend/alembic/versions/xxxx_add_settings_tables.py`

**Step 1: Generate migration**

```bash
cd backend && uv run alembic revision --autogenerate -m "add_settings_tables"
```

**Step 2: Review generated migration**

Verify it creates `providers` and `agent_configs` tables with correct columns.

**Step 3: Run migration**

```bash
cd backend && uv run alembic upgrade head
```

**Step 4: Verify tables exist**

```bash
cd backend && sqlite3 commandcenter.db ".schema providers"
```

Expected: Shows CREATE TABLE statement

**Step 5: Commit**

```bash
git add backend/alembic/versions/
git commit -m "feat(settings): add database migration for settings tables"
```

---

### Task 4: Settings Service

**Files:**
- Create: `backend/app/services/settings_service.py`
- Test: `backend/tests/test_services/test_settings_service.py`

**Step 1: Write the failing tests**

```python
# backend/tests/test_services/test_settings_service.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.settings import Base, Provider, AgentConfig
from app.services.settings_service import SettingsService


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()


@pytest.fixture
def service(db_session):
    return SettingsService(db_session)


class TestProviderCRUD:
    def test_create_provider(self, service):
        provider = service.create_provider(
            alias="claude",
            model_id="anthropic/claude-sonnet-4",
            cost_input=3.0,
            cost_output=15.0,
        )
        assert provider.alias == "claude"
        assert provider.is_active is True

    def test_list_providers(self, service):
        service.create_provider(alias="a", model_id="model-a")
        service.create_provider(alias="b", model_id="model-b")

        providers = service.list_providers()
        assert len(providers) == 2

    def test_get_provider(self, service):
        service.create_provider(alias="gpt", model_id="openai/gpt-4o")

        provider = service.get_provider("gpt")
        assert provider is not None
        assert provider.model_id == "openai/gpt-4o"

    def test_update_provider(self, service):
        service.create_provider(alias="test", model_id="old-model")

        updated = service.update_provider("test", model_id="new-model")
        assert updated.model_id == "new-model"

    def test_delete_provider(self, service):
        service.create_provider(alias="delete-me", model_id="model")

        success = service.delete_provider("delete-me")
        assert success is True
        assert service.get_provider("delete-me") is None

    def test_set_api_key_encrypts(self, service, monkeypatch, tmp_path):
        # Use temp key path
        key_path = tmp_path / "secret.key"
        monkeypatch.setenv("COMMANDCENTER_KEY_PATH", str(key_path))

        service.create_provider(alias="secure", model_id="model")
        service.set_provider_api_key("secure", "sk-secret-key-123")

        provider = service.get_provider("secure")
        assert provider.api_key_encrypted is not None
        assert provider.api_key_encrypted != "sk-secret-key-123"


class TestAgentConfig:
    def test_get_agent_config(self, service):
        service.create_provider(alias="gemini", model_id="gemini/flash")
        service.set_agent_provider("analyst", "gemini")

        config = service.get_agent_config("analyst")
        assert config.provider_alias == "gemini"

    def test_list_agent_configs(self, service):
        service.create_provider(alias="p1", model_id="m1")
        service.set_agent_provider("analyst", "p1")
        service.set_agent_provider("critic", "p1")

        configs = service.list_agent_configs()
        assert len(configs) == 2


class TestSeeding:
    def test_seed_defaults_when_empty(self, service):
        service.seed_defaults()

        providers = service.list_providers()
        assert len(providers) >= 4  # At least claude, gemini, gpt, gpt-mini

        configs = service.list_agent_configs()
        assert len(configs) == 5  # analyst, researcher, strategist, critic, chairman
```

**Step 2: Run test to verify it fails**

Run: `cd backend && uv run pytest tests/test_services/test_settings_service.py -v`
Expected: FAIL with "No module named 'app.services.settings_service'"

**Step 3: Write implementation**

```python
# backend/app/services/settings_service.py
"""Service for managing LLM provider and agent settings."""

from sqlalchemy.orm import Session

from app.models.settings import AgentConfig, Provider
from app.services.crypto import decrypt_key, encrypt_key, mask_key


# Default providers to seed
DEFAULT_PROVIDERS = [
    {"alias": "claude", "model_id": "anthropic/claude-sonnet-4-20250514", "cost_input": 3.0, "cost_output": 15.0},
    {"alias": "gemini", "model_id": "gemini/gemini-2.5-flash", "cost_input": 0.15, "cost_output": 0.60},
    {"alias": "gpt", "model_id": "openai/gpt-4o", "cost_input": 2.50, "cost_output": 10.0},
    {"alias": "gpt-mini", "model_id": "openai/gpt-4o-mini", "cost_input": 0.15, "cost_output": 0.60},
    {"alias": "zai", "model_id": "openai/glm-4.7", "api_base": "https://api.z.ai/api/paas/v4", "api_key_env": "ZAI_API_KEY", "cost_input": 0.50, "cost_output": 2.0},
    {"alias": "zai-flash", "model_id": "openai/glm-4.5-flash", "api_base": "https://api.z.ai/api/paas/v4", "api_key_env": "ZAI_API_KEY", "cost_input": 0.05, "cost_output": 0.20},
]

# Default agent configurations
DEFAULT_AGENT_CONFIGS = [
    {"role": "analyst", "provider_alias": "gemini"},
    {"role": "researcher", "provider_alias": "gemini"},
    {"role": "strategist", "provider_alias": "gpt"},
    {"role": "critic", "provider_alias": "gemini"},
    {"role": "chairman", "provider_alias": "claude"},
]


class SettingsService:
    """Manages provider and agent configuration."""

    def __init__(self, db: Session):
        self.db = db

    # --- Provider CRUD ---

    def create_provider(
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
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def list_providers(self, active_only: bool = False) -> list[Provider]:
        """List all providers."""
        query = self.db.query(Provider)
        if active_only:
            query = query.filter(Provider.is_active == True)
        return query.order_by(Provider.alias).all()

    def get_provider(self, alias: str) -> Provider | None:
        """Get provider by alias."""
        return self.db.query(Provider).filter(Provider.alias == alias).first()

    def update_provider(self, alias: str, **kwargs) -> Provider | None:
        """Update provider fields."""
        provider = self.get_provider(alias)
        if not provider:
            return None

        for key, value in kwargs.items():
            if hasattr(provider, key) and key not in ("id", "alias", "created_at"):
                setattr(provider, key, value)

        self.db.commit()
        self.db.refresh(provider)
        return provider

    def delete_provider(self, alias: str) -> bool:
        """Delete a provider."""
        provider = self.get_provider(alias)
        if not provider:
            return False

        self.db.delete(provider)
        self.db.commit()
        return True

    def set_provider_api_key(self, alias: str, api_key: str) -> Provider | None:
        """Set and encrypt API key for provider."""
        provider = self.get_provider(alias)
        if not provider:
            return None

        provider.api_key_encrypted = encrypt_key(api_key) if api_key else None
        self.db.commit()
        self.db.refresh(provider)
        return provider

    def get_provider_api_key(self, alias: str) -> str | None:
        """Get decrypted API key for provider."""
        provider = self.get_provider(alias)
        if not provider or not provider.api_key_encrypted:
            return None
        return decrypt_key(provider.api_key_encrypted)

    def get_provider_api_key_masked(self, alias: str) -> str:
        """Get masked API key for display."""
        key = self.get_provider_api_key(alias)
        return mask_key(key) if key else ""

    # --- Agent Config ---

    def set_agent_provider(self, role: str, provider_alias: str) -> AgentConfig:
        """Set which provider an agent role uses."""
        config = self.db.query(AgentConfig).filter(AgentConfig.role == role).first()

        if config:
            config.provider_alias = provider_alias
        else:
            config = AgentConfig(role=role, provider_alias=provider_alias)
            self.db.add(config)

        self.db.commit()
        self.db.refresh(config)
        return config

    def get_agent_config(self, role: str) -> AgentConfig | None:
        """Get agent config by role."""
        return self.db.query(AgentConfig).filter(AgentConfig.role == role).first()

    def list_agent_configs(self) -> list[AgentConfig]:
        """List all agent configurations."""
        return self.db.query(AgentConfig).order_by(AgentConfig.role).all()

    # --- Seeding ---

    def seed_defaults(self) -> None:
        """Seed default providers and agent configs if tables are empty."""
        # Seed providers
        if self.db.query(Provider).count() == 0:
            for p in DEFAULT_PROVIDERS:
                self.create_provider(**p)

        # Seed agent configs
        if self.db.query(AgentConfig).count() == 0:
            for c in DEFAULT_AGENT_CONFIGS:
                self.set_agent_provider(**c)
```

**Step 4: Run test to verify it passes**

Run: `cd backend && uv run pytest tests/test_services/test_settings_service.py -v`
Expected: PASS (9 tests)

**Step 5: Commit**

```bash
git add backend/app/services/settings_service.py backend/tests/test_services/test_settings_service.py
git commit -m "feat(settings): add SettingsService with provider and agent config management"
```

---

### Task 5: Settings API Router

**Files:**
- Create: `backend/app/routers/settings.py`
- Create: `backend/app/schemas/settings.py`
- Modify: `backend/app/main.py` (add router)
- Test: `backend/tests/test_routers/test_settings.py`

**Step 1: Create schemas**

```python
# backend/app/schemas/settings.py
"""Pydantic schemas for settings API."""

from pydantic import BaseModel, Field


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

    class Config:
        from_attributes = True


class ProviderKeyResponse(BaseModel):
    api_key: str


class AgentConfigResponse(BaseModel):
    role: str
    provider_alias: str

    class Config:
        from_attributes = True


class AgentConfigUpdate(BaseModel):
    provider_alias: str


class TestConnectionResponse(BaseModel):
    success: bool
    message: str
    model: str | None = None
```

**Step 2: Write the router**

```python
# backend/app/routers/settings.py
"""Settings API for managing LLM providers and agent configuration."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas.settings import (
    AgentConfigResponse,
    AgentConfigUpdate,
    ProviderCreate,
    ProviderKeyResponse,
    ProviderResponse,
    ProviderUpdate,
    TestConnectionResponse,
)
from app.services.settings_service import SettingsService

router = APIRouter(prefix="/settings", tags=["settings"])


def get_settings_service(db: Session = Depends(get_db)) -> SettingsService:
    return SettingsService(db)


# --- Providers ---

@router.get("/providers", response_model=list[ProviderResponse])
def list_providers(
    active_only: bool = False,
    service: SettingsService = Depends(get_settings_service),
):
    """List all configured providers."""
    providers = service.list_providers(active_only=active_only)
    return [
        ProviderResponse(
            id=p.id,
            alias=p.alias,
            model_id=p.model_id,
            api_base=p.api_base,
            api_key_env=p.api_key_env,
            cost_input=p.cost_input,
            cost_output=p.cost_output,
            is_active=p.is_active,
            api_key_set=bool(p.api_key_encrypted),
            api_key_masked=service.get_provider_api_key_masked(p.alias),
        )
        for p in providers
    ]


@router.post("/providers", response_model=ProviderResponse, status_code=201)
def create_provider(
    data: ProviderCreate,
    service: SettingsService = Depends(get_settings_service),
):
    """Create a new provider."""
    existing = service.get_provider(data.alias)
    if existing:
        raise HTTPException(400, f"Provider '{data.alias}' already exists")

    provider = service.create_provider(
        alias=data.alias,
        model_id=data.model_id,
        api_base=data.api_base,
        api_key_env=data.api_key_env,
        cost_input=data.cost_input,
        cost_output=data.cost_output,
        is_active=data.is_active,
    )

    if data.api_key:
        service.set_provider_api_key(data.alias, data.api_key)

    return ProviderResponse(
        id=provider.id,
        alias=provider.alias,
        model_id=provider.model_id,
        api_base=provider.api_base,
        api_key_env=provider.api_key_env,
        cost_input=provider.cost_input,
        cost_output=provider.cost_output,
        is_active=provider.is_active,
        api_key_set=bool(data.api_key),
        api_key_masked=service.get_provider_api_key_masked(provider.alias),
    )


@router.patch("/providers/{alias}", response_model=ProviderResponse)
def update_provider(
    alias: str,
    data: ProviderUpdate,
    service: SettingsService = Depends(get_settings_service),
):
    """Update a provider."""
    provider = service.get_provider(alias)
    if not provider:
        raise HTTPException(404, f"Provider '{alias}' not found")

    update_data = data.model_dump(exclude_unset=True, exclude={"api_key"})
    if update_data:
        provider = service.update_provider(alias, **update_data)

    if data.api_key is not None:
        service.set_provider_api_key(alias, data.api_key)

    return ProviderResponse(
        id=provider.id,
        alias=provider.alias,
        model_id=provider.model_id,
        api_base=provider.api_base,
        api_key_env=provider.api_key_env,
        cost_input=provider.cost_input,
        cost_output=provider.cost_output,
        is_active=provider.is_active,
        api_key_set=bool(provider.api_key_encrypted),
        api_key_masked=service.get_provider_api_key_masked(alias),
    )


@router.delete("/providers/{alias}", status_code=204)
def delete_provider(
    alias: str,
    service: SettingsService = Depends(get_settings_service),
):
    """Delete a provider."""
    if not service.delete_provider(alias):
        raise HTTPException(404, f"Provider '{alias}' not found")


@router.get("/providers/{alias}/reveal-key", response_model=ProviderKeyResponse)
def reveal_provider_key(
    alias: str,
    service: SettingsService = Depends(get_settings_service),
):
    """Get the full API key (use sparingly)."""
    key = service.get_provider_api_key(alias)
    if key is None:
        raise HTTPException(404, f"No API key set for provider '{alias}'")
    return ProviderKeyResponse(api_key=key)


@router.post("/providers/{alias}/test", response_model=TestConnectionResponse)
async def test_provider_connection(
    alias: str,
    service: SettingsService = Depends(get_settings_service),
):
    """Test provider connection with a simple completion."""
    provider = service.get_provider(alias)
    if not provider:
        raise HTTPException(404, f"Provider '{alias}' not found")

    # For now, just validate the provider exists
    # TODO: Actually test the connection with LLMGateway
    return TestConnectionResponse(
        success=True,
        message="Provider configuration is valid",
        model=provider.model_id,
    )


# --- Agent Configs ---

@router.get("/agents", response_model=list[AgentConfigResponse])
def list_agent_configs(
    service: SettingsService = Depends(get_settings_service),
):
    """List all agent configurations."""
    return service.list_agent_configs()


@router.patch("/agents/{role}", response_model=AgentConfigResponse)
def update_agent_config(
    role: str,
    data: AgentConfigUpdate,
    service: SettingsService = Depends(get_settings_service),
):
    """Update which provider an agent role uses."""
    # Validate provider exists
    provider = service.get_provider(data.provider_alias)
    if not provider:
        raise HTTPException(400, f"Provider '{data.provider_alias}' not found")

    config = service.set_agent_provider(role, data.provider_alias)
    return config
```

**Step 3: Register router in main.py**

Add to `backend/app/main.py`:

```python
from app.routers import settings

app.include_router(settings.router, prefix="/api/v1")
```

**Step 4: Write integration tests**

```python
# backend/tests/test_routers/test_settings.py
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


class TestProvidersAPI:
    def test_list_providers_empty(self, client):
        response = client.get("/api/v1/settings/providers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_create_provider(self, client):
        response = client.post("/api/v1/settings/providers", json={
            "alias": "test-provider",
            "model_id": "openai/gpt-4o",
            "cost_input": 2.5,
            "cost_output": 10.0,
        })
        assert response.status_code == 201
        data = response.json()
        assert data["alias"] == "test-provider"
        assert data["api_key_set"] is False

    def test_create_duplicate_fails(self, client):
        # Create first
        client.post("/api/v1/settings/providers", json={
            "alias": "dup-test",
            "model_id": "model",
        })
        # Try duplicate
        response = client.post("/api/v1/settings/providers", json={
            "alias": "dup-test",
            "model_id": "model2",
        })
        assert response.status_code == 400


class TestAgentConfigsAPI:
    def test_list_agent_configs(self, client):
        response = client.get("/api/v1/settings/agents")
        assert response.status_code == 200
```

**Step 5: Run tests**

Run: `cd backend && uv run pytest tests/test_routers/test_settings.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add backend/app/routers/settings.py backend/app/schemas/settings.py backend/app/main.py backend/tests/test_routers/test_settings.py
git commit -m "feat(settings): add settings API router with provider and agent config endpoints"
```

---

## Phase 2: Dynamic Provider Integration

### Task 6: Dynamic Provider Registry

**Files:**
- Modify: `backend/libs/llm_gateway/providers.py`
- Test: `backend/libs/llm_gateway/tests/test_providers.py`

**Step 1: Add DynamicProviderRegistry class**

Add to `backend/libs/llm_gateway/providers.py`:

```python
class DynamicProviderRegistry:
    """
    Provider registry that reads from database with static fallback.

    Usage:
        registry = DynamicProviderRegistry(db_session)
        config = registry.get_config("claude")
    """

    def __init__(self, db: "Session | None" = None):
        self.db = db
        self._cache: dict[str, ProviderConfig] = {}

    def get_config(self, alias: str) -> ProviderConfig:
        """Get provider config, checking DB first then static defaults."""
        # Check cache
        if alias in self._cache:
            return self._cache[alias]

        # Try database
        if self.db:
            from app.models.settings import Provider
            provider = self.db.query(Provider).filter(
                Provider.alias == alias,
                Provider.is_active == True
            ).first()

            if provider:
                config = ProviderConfig(
                    model_id=provider.model_id,
                    api_base=provider.api_base,
                    api_key_env=provider.api_key_env,
                )
                self._cache[alias] = config
                return config

        # Fall back to static
        return get_provider_config(alias)

    def list_providers(self) -> list[str]:
        """List all available provider aliases."""
        aliases = set(PROVIDERS.keys())

        if self.db:
            from app.models.settings import Provider
            db_aliases = self.db.query(Provider.alias).filter(
                Provider.is_active == True
            ).all()
            aliases.update(a[0] for a in db_aliases)

        return sorted(aliases)

    def clear_cache(self):
        """Clear the config cache."""
        self._cache.clear()
```

**Step 2: Run existing tests to ensure no regression**

Run: `cd backend && uv run pytest libs/llm_gateway/tests/ -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/libs/llm_gateway/providers.py
git commit -m "feat(llm-gateway): add DynamicProviderRegistry with DB support"
```

---

### Task 7: Wire LLMGateway to Use Dynamic Registry

**Files:**
- Modify: `backend/libs/llm_gateway/gateway.py`

**Step 1: Update LLMGateway to accept registry**

Modify constructor and `complete` method to optionally use DynamicProviderRegistry:

```python
# In LLMGateway.__init__:
def __init__(self, registry: "DynamicProviderRegistry | None" = None) -> None:
    """Initialize LLM Gateway."""
    litellm.set_verbose = False
    self.registry = registry
    logger.info("llm_gateway_initialized", providers=list_providers())

# In complete method, replace:
#   config = get_provider_config(provider)
# With:
    if self.registry:
        config = self.registry.get_config(provider)
    else:
        config = get_provider_config(provider)
```

**Step 2: Run tests**

Run: `cd backend && uv run pytest libs/llm_gateway/tests/ -v`
Expected: PASS

**Step 3: Commit**

```bash
git add backend/libs/llm_gateway/gateway.py
git commit -m "feat(llm-gateway): wire LLMGateway to use DynamicProviderRegistry"
```

---

## Phase 3: Frontend - Settings Tab

### Task 8: Settings API Client

**Files:**
- Create: `hub/frontend/src/services/settingsApi.ts`
- Create: `hub/frontend/src/types/settings.ts`

**Step 1: Create types**

```typescript
// hub/frontend/src/types/settings.ts
export interface Provider {
  id: string;
  alias: string;
  model_id: string;
  api_base: string | null;
  api_key_env: string | null;
  cost_input: number;
  cost_output: number;
  is_active: boolean;
  api_key_set: boolean;
  api_key_masked: string;
}

export interface ProviderCreate {
  alias: string;
  model_id: string;
  api_base?: string;
  api_key_env?: string;
  api_key?: string;
  cost_input?: number;
  cost_output?: number;
  is_active?: boolean;
}

export interface ProviderUpdate {
  model_id?: string;
  api_base?: string | null;
  api_key_env?: string | null;
  api_key?: string;
  cost_input?: number;
  cost_output?: number;
  is_active?: boolean;
}

export interface AgentConfig {
  role: string;
  provider_alias: string;
}

export interface TestConnectionResult {
  success: boolean;
  message: string;
  model: string | null;
}
```

**Step 2: Create API client**

```typescript
// hub/frontend/src/services/settingsApi.ts
import type {
  Provider,
  ProviderCreate,
  ProviderUpdate,
  AgentConfig,
  TestConnectionResult,
} from '../types/settings';

const API_BASE = '/api/v1';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  if (response.status === 204) {
    return undefined as T;
  }

  return response.json();
}

export const settingsApi = {
  // Providers
  listProviders: (activeOnly = false): Promise<Provider[]> =>
    fetchJSON(`${API_BASE}/settings/providers?active_only=${activeOnly}`),

  createProvider: (data: ProviderCreate): Promise<Provider> =>
    fetchJSON(`${API_BASE}/settings/providers`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  updateProvider: (alias: string, data: ProviderUpdate): Promise<Provider> =>
    fetchJSON(`${API_BASE}/settings/providers/${alias}`, {
      method: 'PATCH',
      body: JSON.stringify(data),
    }),

  deleteProvider: (alias: string): Promise<void> =>
    fetchJSON(`${API_BASE}/settings/providers/${alias}`, { method: 'DELETE' }),

  revealKey: (alias: string): Promise<{ api_key: string }> =>
    fetchJSON(`${API_BASE}/settings/providers/${alias}/reveal-key`),

  testConnection: (alias: string): Promise<TestConnectionResult> =>
    fetchJSON(`${API_BASE}/settings/providers/${alias}/test`, { method: 'POST' }),

  // Agent Configs
  listAgentConfigs: (): Promise<AgentConfig[]> =>
    fetchJSON(`${API_BASE}/settings/agents`),

  updateAgentConfig: (role: string, providerAlias: string): Promise<AgentConfig> =>
    fetchJSON(`${API_BASE}/settings/agents/${role}`, {
      method: 'PATCH',
      body: JSON.stringify({ provider_alias: providerAlias }),
    }),
};

export default settingsApi;
```

**Step 3: Commit**

```bash
git add hub/frontend/src/services/settingsApi.ts hub/frontend/src/types/settings.ts
git commit -m "feat(frontend): add settings API client and types"
```

---

### Task 9: SettingsDashboard Component

**Files:**
- Create: `hub/frontend/src/components/SettingsDashboard/index.tsx`
- Create: `hub/frontend/src/components/SettingsDashboard/ProvidersPanel.tsx`
- Create: `hub/frontend/src/components/SettingsDashboard/AgentsPanel.tsx`

**Step 1: Create main component**

```typescript
// hub/frontend/src/components/SettingsDashboard/index.tsx
import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import type { Provider, AgentConfig } from '../../types/settings';
import settingsApi from '../../services/settingsApi';
import { ProvidersPanel } from './ProvidersPanel';
import { AgentsPanel } from './AgentsPanel';

export function SettingsDashboard() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [agentConfigs, setAgentConfigs] = useState<AgentConfig[]>([]);
  const [loading, setLoading] = useState(true);

  const fetchData = useCallback(async () => {
    try {
      const [providersData, configsData] = await Promise.all([
        settingsApi.listProviders(),
        settingsApi.listAgentConfigs(),
      ]);
      setProviders(providersData);
      setAgentConfigs(configsData);
    } catch (err) {
      console.error('Failed to fetch settings:', err);
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  const handleProviderChange = () => {
    fetchData();
  };

  const handleAgentConfigChange = async (role: string, providerAlias: string) => {
    try {
      await settingsApi.updateAgentConfig(role, providerAlias);
      toast.success(`Updated ${role} to use ${providerAlias}`);
      fetchData();
    } catch (err) {
      toast.error(`Failed to update ${role}`);
    }
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <div className="bg-slate-800/30 rounded-lg p-6 animate-pulse">
          <div className="h-6 bg-slate-700 rounded w-1/4 mb-4" />
          <div className="space-y-2">
            {[...Array(4)].map((_, i) => (
              <div key={i} className="h-12 bg-slate-700 rounded" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <ProvidersPanel providers={providers} onChange={handleProviderChange} />
      <AgentsPanel
        configs={agentConfigs}
        providers={providers.filter((p) => p.is_active && p.api_key_set)}
        onChange={handleAgentConfigChange}
      />
    </div>
  );
}

export default SettingsDashboard;
```

**Step 2: Create ProvidersPanel** (simplified - full implementation in actual file)

```typescript
// hub/frontend/src/components/SettingsDashboard/ProvidersPanel.tsx
import { useState } from 'react';
import toast from 'react-hot-toast';
import type { Provider } from '../../types/settings';
import settingsApi from '../../services/settingsApi';

interface Props {
  providers: Provider[];
  onChange: () => void;
}

export function ProvidersPanel({ providers, onChange }: Props) {
  const [editingAlias, setEditingAlias] = useState<string | null>(null);

  return (
    <div className="bg-slate-800/50 rounded-lg p-6">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-white">Providers</h3>
        <button
          onClick={() => setEditingAlias('__new__')}
          className="px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded"
        >
          + Add New
        </button>
      </div>

      <div className="space-y-2">
        {providers.map((provider) => (
          <div
            key={provider.alias}
            className="flex items-center justify-between p-3 bg-slate-900/50 rounded-lg"
          >
            <div className="flex items-center gap-3">
              <span className={`w-2 h-2 rounded-full ${provider.is_active ? 'bg-green-500' : 'bg-slate-500'}`} />
              <div>
                <div className="text-white font-medium">{provider.alias}</div>
                <div className="text-slate-400 text-sm">{provider.model_id}</div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              {provider.api_key_set && (
                <span className="text-green-400 text-sm">🔑</span>
              )}
              <button
                onClick={() => setEditingAlias(provider.alias)}
                className="px-2 py-1 text-slate-400 hover:text-white text-sm"
              >
                Edit
              </button>
            </div>
          </div>
        ))}
      </div>

      {/* TODO: Add ProviderForm modal for editing */}
    </div>
  );
}
```

**Step 3: Create AgentsPanel**

```typescript
// hub/frontend/src/components/SettingsDashboard/AgentsPanel.tsx
import type { Provider, AgentConfig } from '../../types/settings';

interface Props {
  configs: AgentConfig[];
  providers: Provider[];
  onChange: (role: string, providerAlias: string) => void;
}

const ROLE_LABELS: Record<string, string> = {
  analyst: 'Analyst',
  researcher: 'Researcher',
  strategist: 'Strategist',
  critic: 'Critic',
  chairman: 'Chairman (Synthesis)',
};

export function AgentsPanel({ configs, providers, onChange }: Props) {
  const getConfigForRole = (role: string) =>
    configs.find((c) => c.role === role)?.provider_alias || '';

  return (
    <div className="bg-slate-800/50 rounded-lg p-6">
      <h3 className="text-lg font-medium text-white mb-4">Agent Configuration</h3>
      <p className="text-slate-400 text-sm mb-4">
        Assign which provider each debate agent uses.
      </p>

      <div className="space-y-3">
        {Object.entries(ROLE_LABELS).map(([role, label]) => (
          <div key={role} className="flex items-center justify-between">
            <label className="text-white">{label}</label>
            <select
              value={getConfigForRole(role)}
              onChange={(e) => onChange(role, e.target.value)}
              className="bg-slate-900 border border-slate-700 rounded px-3 py-1.5 text-white min-w-[200px]"
            >
              <option value="">Select provider...</option>
              {providers.map((p) => (
                <option key={p.alias} value={p.alias}>
                  {p.alias}
                </option>
              ))}
            </select>
          </div>
        ))}
      </div>
    </div>
  );
}
```

**Step 4: Commit**

```bash
git add hub/frontend/src/components/SettingsDashboard/
git commit -m "feat(frontend): add SettingsDashboard component with providers and agents panels"
```

---

### Task 10: Add Settings Tab to HypothesesPage

**Files:**
- Modify: `hub/frontend/src/pages/HypothesesPage.tsx`

**Step 1: Import and add tab**

```typescript
// Add import
import { SettingsDashboard } from '../components/SettingsDashboard';

// Update TabType
type TabType = 'hypotheses' | 'evidence' | 'costs' | 'settings';

// Add tab button and content
<TabButton
  active={activeTab === 'settings'}
  onClick={() => setActiveTab('settings')}
>
  <SettingsIcon className="w-4 h-4" />
  Settings
</TabButton>

// Add content
{activeTab === 'settings' && <SettingsDashboard />}

// Add SettingsIcon component
function SettingsIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"
      />
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
    </svg>
  );
}
```

**Step 2: Commit**

```bash
git add hub/frontend/src/pages/HypothesesPage.tsx
git commit -m "feat(frontend): add Settings tab to HypothesesPage"
```

---

## Phase 4: Hypothesis Quick Input

### Task 11: Add Create Hypothesis API

**Files:**
- Modify: `hub/frontend/src/services/hypothesesApi.ts`
- Modify: `hub/frontend/src/types/hypothesis.ts`

**Step 1: Add types**

```typescript
// Add to hub/frontend/src/types/hypothesis.ts
export interface CreateHypothesisRequest {
  statement: string;
  category?: HypothesisCategory;
  context?: string;
}

export interface CreateHypothesisResponse {
  id: string;
  statement: string;
  category: HypothesisCategory;
  status: HypothesisStatus;
}
```

**Step 2: Add API method**

```typescript
// Add to hypothesesApi object in hub/frontend/src/services/hypothesesApi.ts

/**
 * Create a new hypothesis
 */
create: (data: CreateHypothesisRequest): Promise<CreateHypothesisResponse> =>
  fetchJSON(`${API_BASE}/hypotheses/`, {
    method: 'POST',
    body: JSON.stringify(data),
  }),
```

**Step 3: Commit**

```bash
git add hub/frontend/src/services/hypothesesApi.ts hub/frontend/src/types/hypothesis.ts
git commit -m "feat(frontend): add create hypothesis API method"
```

---

### Task 12: Hypothesis Quick Input Component

**Files:**
- Create: `hub/frontend/src/components/HypothesisDashboard/QuickInput.tsx`
- Modify: `hub/frontend/src/components/HypothesisDashboard/index.tsx`

**Step 1: Create QuickInput component**

```typescript
// hub/frontend/src/components/HypothesisDashboard/QuickInput.tsx
import { useState } from 'react';
import toast from 'react-hot-toast';
import type { HypothesisCategory, HypothesisSummary } from '../../types/hypothesis';
import { CATEGORY_LABELS } from '../../types/hypothesis';
import hypothesesApi from '../../services/hypothesesApi';

interface Props {
  onCreated: (hypothesis: HypothesisSummary) => void;
  onValidate: (id: string) => void;
}

export function QuickInput({ onCreated, onValidate }: Props) {
  const [statement, setStatement] = useState('');
  const [category, setCategory] = useState<HypothesisCategory>('product');
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (andValidate: boolean) => {
    if (!statement.trim()) {
      toast.error('Please enter a hypothesis');
      return;
    }

    setIsSubmitting(true);
    try {
      const hypothesis = await hypothesesApi.create({
        statement: statement.trim(),
        category,
      });

      toast.success('Hypothesis created');
      setStatement('');
      onCreated(hypothesis as HypothesisSummary);

      if (andValidate) {
        onValidate(hypothesis.id);
      }
    } catch (err) {
      toast.error('Failed to create hypothesis');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-800/50 rounded-lg p-4 mb-6">
      <div className="flex items-center gap-2 text-slate-400 mb-3">
        <span className="text-xl">💡</span>
        <span className="text-sm">Enter a hypothesis to validate...</span>
      </div>

      <div className="flex gap-3">
        <input
          type="text"
          value={statement}
          onChange={(e) => setStatement(e.target.value)}
          placeholder="e.g., Users will pay more for faster delivery"
          className="flex-1 bg-slate-900 border border-slate-700 rounded px-4 py-2 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500"
          disabled={isSubmitting}
          onKeyDown={(e) => e.key === 'Enter' && handleSubmit(true)}
        />

        <select
          value={category}
          onChange={(e) => setCategory(e.target.value as HypothesisCategory)}
          className="bg-slate-900 border border-slate-700 rounded px-3 py-2 text-white"
          disabled={isSubmitting}
        >
          {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
            <option key={value} value={value}>
              {label}
            </option>
          ))}
        </select>

        <button
          onClick={() => handleSubmit(true)}
          disabled={isSubmitting || !statement.trim()}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:cursor-not-allowed text-white font-medium rounded flex items-center gap-2"
        >
          {isSubmitting ? 'Creating...' : 'Validate →'}
        </button>
      </div>

      <div className="mt-2 text-right">
        <button
          onClick={() => handleSubmit(false)}
          disabled={isSubmitting || !statement.trim()}
          className="text-slate-500 hover:text-slate-300 text-sm"
        >
          Save only
        </button>
      </div>
    </div>
  );
}
```

**Step 2: Add to HypothesisDashboard**

```typescript
// In hub/frontend/src/components/HypothesisDashboard/index.tsx

// Add import
import { QuickInput } from './QuickInput';

// Add handler
const handleHypothesisCreated = (hypothesis: HypothesisSummary) => {
  fetchHypotheses();
  fetchStats();
};

// Add component before filters
<QuickInput
  onCreated={handleHypothesisCreated}
  onValidate={handleValidate}
/>
```

**Step 3: Commit**

```bash
git add hub/frontend/src/components/HypothesisDashboard/
git commit -m "feat(frontend): add QuickInput component for hypothesis creation"
```

---

## Phase 5: Final Integration

### Task 13: Seed Defaults on Backend Startup

**Files:**
- Modify: `backend/app/main.py`

**Step 1: Add startup event**

```python
# Add to backend/app/main.py

from app.services.settings_service import SettingsService

@app.on_event("startup")
async def seed_settings():
    """Seed default providers and agent configs on startup."""
    from app.db import SessionLocal
    db = SessionLocal()
    try:
        service = SettingsService(db)
        service.seed_defaults()
    finally:
        db.close()
```

**Step 2: Commit**

```bash
git add backend/app/main.py
git commit -m "feat(settings): seed default providers on backend startup"
```

---

### Task 14: End-to-End Manual Test

**Steps:**

1. Start backend:
   ```bash
   cd backend
   CORS_ORIGINS='["http://localhost:9000"]' uv run uvicorn app.main:app --port 8000 --reload
   ```

2. Start frontend:
   ```bash
   cd hub/frontend
   VITE_API_URL=http://localhost:8000 npm run dev
   ```

3. Open http://localhost:9000/hypotheses

4. Test Settings tab:
   - View seeded providers
   - Add a new provider with API key
   - Assign providers to agents

5. Test Quick Input:
   - Enter a hypothesis
   - Click "Validate →"
   - Verify validation starts

**Step 5: Final commit**

```bash
git add -A
git commit -m "feat: complete settings and hypothesis input feature"
```

---

## Summary

| Phase | Tasks | Description |
|-------|-------|-------------|
| 1 | 1-5 | Backend foundation: crypto, models, migration, service, API |
| 2 | 6-7 | Dynamic provider registry integration |
| 3 | 8-10 | Frontend Settings tab |
| 4 | 11-12 | Hypothesis quick input |
| 5 | 13-14 | Final integration and testing |

**Total: 14 tasks, ~35 steps**
