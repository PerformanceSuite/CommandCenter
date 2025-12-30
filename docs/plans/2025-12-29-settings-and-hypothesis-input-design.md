# AI Arena Settings & Hypothesis Input Design

**Date:** 2025-12-29
**Status:** Approved
**Author:** Claude (via brainstorming session)

## Overview

Add UI for managing LLM providers, API keys, and agent configurations, plus a quick hypothesis input form.

## Requirements

1. **Provider Management** - Add, edit, remove LLM providers with any LiteLLM-compatible model
2. **API Key Storage** - Persistent encrypted storage in local SQLite (local service, showing keys is acceptable)
3. **Agent Configuration** - Assign providers to each debate agent role via dropdowns
4. **Hypothesis Input** - Quick text input to create and validate hypotheses in one action

## Data Model

### New Tables (SQLite)

```sql
CREATE TABLE providers (
    id TEXT PRIMARY KEY,
    alias TEXT UNIQUE NOT NULL,
    model_id TEXT NOT NULL,           -- LiteLLM format: "anthropic/claude-sonnet-4"
    api_base TEXT,                    -- Custom endpoint (e.g., Z.AI)
    api_key_env TEXT,                 -- Env var name (optional)
    api_key_encrypted TEXT,           -- Encrypted stored key (optional)
    cost_input REAL DEFAULT 0,        -- Cost per 1M input tokens
    cost_output REAL DEFAULT 0,       -- Cost per 1M output tokens
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE agent_configs (
    role TEXT PRIMARY KEY,            -- analyst, researcher, strategist, critic, chairman
    provider_alias TEXT NOT NULL,
    FOREIGN KEY (provider_alias) REFERENCES providers(alias)
);
```

### Encryption

- API keys encrypted with Fernet symmetric encryption
- Machine key stored in `~/.commandcenter/secret.key`
- Generated on first run if not present

### Default Seeding

On first run (empty tables), seed with current static providers:

| Alias | Model ID | Cost (in/out per 1M) |
|-------|----------|----------------------|
| claude | anthropic/claude-sonnet-4-20250514 | $3.00 / $15.00 |
| gemini | gemini/gemini-2.5-flash | $0.15 / $0.60 |
| gpt | openai/gpt-4o | $2.50 / $10.00 |
| gpt-mini | openai/gpt-4o-mini | $0.15 / $0.60 |
| zai | openai/glm-4.7 | $0.50 / $2.00 |
| zai-flash | openai/glm-4.5-flash | $0.05 / $0.20 |

## API Endpoints

### New Router: `/api/v1/settings/`

```
Providers:
  GET    /providers              List all providers
  POST   /providers              Create provider
  PATCH  /providers/{alias}      Update provider
  DELETE /providers/{alias}      Delete provider
  POST   /providers/{alias}/test Test provider connection
  GET    /providers/{alias}/reveal-key  Get unmasked API key

Agent Configuration:
  GET    /agents                 Get all agent role configs
  PATCH  /agents/{role}          Update agent's provider assignment

Utilities:
  GET    /models/suggest?prefix= Suggest models for provider prefix
```

### Response Schemas

```typescript
interface Provider {
  alias: string;
  model_id: string;
  api_base: string | null;
  api_key_env: string | null;
  api_key_set: boolean;        // Is key configured?
  api_key_masked: string;      // "sk-ant-***xyz"
  cost_input: number;
  cost_output: number;
  is_active: boolean;
}

interface AgentConfig {
  role: 'analyst' | 'researcher' | 'strategist' | 'critic' | 'chairman';
  provider_alias: string;
}
```

## Frontend UI

### Settings Tab

Add 4th tab to HypothesesPage: "Settings"

```
┌─────────────────────────────────────────────────────┐
│ PROVIDERS                              [+ Add New]  │
│ ┌─────────────────────────────────────────────────┐ │
│ │ claude          anthropic/claude-sonnet-4  ✓ 🔑 │ │
│ │ gemini          gemini/gemini-2.5-flash    ✓ 🔑 │ │
│ │ gpt             openai/gpt-4o              ✗    │ │
│ └─────────────────────────────────────────────────┘ │
│   ✓ = active, 🔑 = key configured                   │
│                                                     │
│ AGENT CONFIGURATION                                 │
│ ┌─────────────────────────────────────────────────┐ │
│ │ Analyst     [claude     ▼]                      │ │
│ │ Researcher  [gemini     ▼]                      │ │
│ │ Strategist  [gpt        ▼]                      │ │
│ │ Critic      [gemini     ▼]                      │ │
│ │ Chairman    [claude     ▼]                      │ │
│ └─────────────────────────────────────────────────┘ │
│                              [Save Configuration]   │
└─────────────────────────────────────────────────────┘
```

### Provider Form Modal

- Alias (text, unique)
- Model ID (text with autocomplete suggestions)
- API Base URL (optional, for custom endpoints)
- API Key (password input with reveal toggle)
- Cost per 1M tokens: Input / Output
- Active toggle
- [Test Connection] button

### Hypothesis Quick Input

Add above filters in HypothesisDashboard:

```
┌─────────────────────────────────────────────────────┐
│ 💡 Enter a hypothesis to validate...                │
│ [                                              ]    │
│         [Product ▼]              [Validate →]       │
│                               (Save only)           │
└─────────────────────────────────────────────────────┘
```

**Behavior:**
1. User enters hypothesis text
2. Optionally selects category (defaults to "product")
3. Clicks "Validate →"
4. Creates hypothesis via API, then immediately starts validation
5. Opens ValidationModal to show debate progress

## Integration

### Dynamic Provider Registry

Replace static `PROVIDER_CONFIGS` in `llm_gateway/providers.py`:

```python
class DynamicProviderRegistry:
    """Loads provider configs from DB, falls back to static defaults."""

    def get_config(self, alias: str) -> ProviderConfig:
        # Try DB first
        # Fall back to static PROVIDER_CONFIGS if not found

    def list_providers(self) -> list[str]:
        # Merge DB providers with static defaults
```

### Agent Registry Changes

Modify `ai_arena/registry.py` to read agent configs from DB:

```python
def create_default_team(self) -> list[BaseAgent]:
    # Read agent_configs from DB
    # Create agents with configured providers
    # Fall back to current defaults if no config
```

### Orchestrator Changes

Read chairman provider from settings:

```python
# Instead of hardcoded config.chairman_provider
chairman_provider = settings_service.get_agent_config("chairman").provider_alias
```

## File Changes

### New Files

| Path | Purpose |
|------|---------|
| `backend/app/models/settings.py` | SQLAlchemy models for Provider, AgentConfig |
| `backend/app/routers/settings.py` | Settings API endpoints |
| `backend/app/services/settings_service.py` | Business logic, encryption |
| `backend/app/services/crypto.py` | Fernet key management |
| `hub/frontend/src/components/SettingsDashboard/index.tsx` | Main settings component |
| `hub/frontend/src/components/SettingsDashboard/ProvidersPanel.tsx` | Provider list |
| `hub/frontend/src/components/SettingsDashboard/ProviderForm.tsx` | Add/edit modal |
| `hub/frontend/src/components/SettingsDashboard/AgentsPanel.tsx` | Agent config |
| `hub/frontend/src/components/SettingsDashboard/ApiKeyInput.tsx` | Masked input |
| `hub/frontend/src/services/settingsApi.ts` | Settings API client |

### Modified Files

| Path | Changes |
|------|---------|
| `backend/libs/llm_gateway/providers.py` | Add DynamicProviderRegistry |
| `backend/libs/llm_gateway/gateway.py` | Use dynamic registry |
| `backend/libs/ai_arena/registry.py` | Read agent configs from DB |
| `backend/libs/ai_arena/debate/orchestrator.py` | Chairman from settings |
| `hub/frontend/src/pages/HypothesesPage.tsx` | Add Settings tab |
| `hub/frontend/src/components/HypothesisDashboard/index.tsx` | Add quick input |
| `hub/frontend/src/services/hypothesesApi.ts` | Add create endpoint |
| `hub/frontend/src/types/hypothesis.ts` | Add CreateHypothesis type |

## Backward Compatibility

- If `providers` table is empty, system uses static defaults
- If `agent_configs` table is empty, agents use current default providers
- Environment variables still work as fallback for API keys
- No breaking changes to existing API endpoints

## Testing

- Unit tests for crypto/encryption
- Unit tests for settings service
- Integration tests for settings API endpoints
- E2E test: configure provider → assign to agent → run validation
