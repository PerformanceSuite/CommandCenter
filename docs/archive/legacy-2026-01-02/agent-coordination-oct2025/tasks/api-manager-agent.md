# API Key Manager Agent - Task Definition

**Mission:** Build API Key Manager MCP server with multi-provider AI routing
**Worktree:** worktrees/api-manager-agent
**Branch:** feature/api-manager
**Estimated Time:** 15 hours
**Dependencies:** None (Phase 1 - Independent)

---

## Tasks Checklist

### Task 1: Create API Key Manager MCP Server (6 hours)
- [ ] Create `.commandcenter/mcp-servers/api-keys/` directory
- [ ] Implement secure API key storage
- [ ] Add multi-provider configuration
- [ ] Create key validation tools
- [ ] Implement key rotation support
- [ ] Add usage tracking per provider
- [ ] Create cost estimation tools

**Directory Structure:**
```
.commandcenter/mcp-servers/api-keys/
├── __init__.py
├── server.py              # Main MCP server
├── tools/
│   ├── __init__.py
│   ├── manage.py          # Key management
│   ├── validate.py        # Key validation
│   ├── routing.py         # Provider routing
│   └── usage.py           # Usage tracking
├── resources/
│   ├── __init__.py
│   ├── providers.py       # Available providers
│   └── usage_stats.py     # Usage statistics
└── config.py              # Server configuration
```

**Files to Create:**
- `.commandcenter/mcp-servers/api-keys/server.py`
- `.commandcenter/mcp-servers/api-keys/tools/` (4 files)
- `.commandcenter/mcp-servers/api-keys/resources/` (2 files)
- `.commandcenter/mcp-servers/api-keys/config.py`

**Tools to Implement:**
1. `add_api_key` - Add API key for provider
2. `validate_key` - Validate API key
3. `rotate_key` - Rotate API key
4. `get_usage` - Get usage statistics
5. `estimate_cost` - Estimate API cost
6. `route_request` - Route request to best provider

**Resources to Provide:**
1. `api://providers` - Available AI providers
2. `api://usage` - Current usage statistics
3. `api://routing` - Routing configuration

---

### Task 2: Implement Multi-Provider AI Routing (5 hours)
- [ ] Design provider routing configuration
- [ ] Implement task-based routing (code gen, embeddings, analysis)
- [ ] Add fallback provider support
- [ ] Create load balancing logic
- [ ] Implement rate limit handling
- [ ] Add provider health checking
- [ ] Create routing optimization

**Routing Configuration:**
```json
{
  "providers": {
    "anthropic": {
      "enabled": true,
      "api_key_env": "ANTHROPIC_API_KEY",
      "models": ["claude-3-5-sonnet", "claude-3-opus"],
      "rate_limit": 100,
      "cost_per_1k_tokens": 0.015
    },
    "openai": {
      "enabled": true,
      "api_key_env": "OPENAI_API_KEY",
      "models": ["gpt-4", "gpt-3.5-turbo"],
      "rate_limit": 60,
      "cost_per_1k_tokens": 0.03
    },
    "google": {
      "enabled": false,
      "api_key_env": "GOOGLE_API_KEY",
      "models": ["gemini-pro"],
      "rate_limit": 60,
      "cost_per_1k_tokens": 0.001
    },
    "local": {
      "enabled": true,
      "endpoint": "http://localhost:11434",
      "models": ["codellama", "mistral"],
      "cost_per_1k_tokens": 0
    }
  },
  "routing": {
    "code_generation": "anthropic",
    "embeddings": "local",
    "analysis": "openai",
    "chat": "anthropic"
  },
  "fallback_order": ["anthropic", "openai", "google", "local"]
}
```

**Files to Create:**
- `.commandcenter/mcp-servers/api-keys/routing_config.json`
- `.commandcenter/mcp-servers/api-keys/tools/routing.py`

**Implementation:**
- Task-based routing (optimal model per task)
- Automatic fallback on failure
- Cost optimization
- Rate limit awareness
- Health monitoring

---

### Task 3: Add Secure Key Storage (2 hours)
- [ ] Implement encrypted key storage
- [ ] Use existing crypto utils from backend
- [ ] Add key encryption/decryption
- [ ] Create key rotation mechanism
- [ ] Implement key access logging
- [ ] Add key expiration support

**Implementation:**
```python
from app.utils.crypto import encrypt_token, decrypt_token

class APIKeyManager:
    def store_key(self, provider: str, key: str):
        encrypted_key = encrypt_token(key)
        # Store in .commandcenter/mcp-servers/api-keys/.keys.enc

    def get_key(self, provider: str) -> str:
        encrypted_key = # Load from storage
        return decrypt_token(encrypted_key)
```

**Files to Create:**
- `.commandcenter/mcp-servers/api-keys/.keys.enc` (encrypted storage)
- `.commandcenter/mcp-servers/api-keys/tools/storage.py`

**Security:**
- All keys encrypted at rest
- Keys never logged in plaintext
- Automatic key rotation support
- Access audit trail

---

### Task 4: Implement Usage Tracking and Cost Estimation (1 hour)
- [ ] Track API calls per provider
- [ ] Track token usage
- [ ] Calculate costs per provider
- [ ] Create usage reports
- [ ] Add cost alerts
- [ ] Implement budget limits

**Usage Tracking:**
```json
{
  "providers": {
    "anthropic": {
      "total_requests": 1500,
      "total_tokens": 450000,
      "estimated_cost": 6.75,
      "last_30_days": {
        "requests": 500,
        "tokens": 150000,
        "cost": 2.25
      }
    },
    "openai": {
      "total_requests": 800,
      "total_tokens": 240000,
      "estimated_cost": 7.20,
      "last_30_days": {
        "requests": 300,
        "tokens": 90000,
        "cost": 2.70
      }
    }
  },
  "total_cost": 13.95,
  "budget_limit": 50.00,
  "budget_remaining": 36.05
}
```

**Files to Create:**
- `.commandcenter/mcp-servers/api-keys/usage.json`
- `.commandcenter/mcp-servers/api-keys/tools/usage.py`

---

### Task 5: Add Slash Command Integration (1 hour)
- [ ] Create `.claude/commands/api-config.md` command
- [ ] Create `.claude/commands/api-usage.md` command
- [ ] Create `.claude/commands/api-costs.md` command
- [ ] Map commands to API Manager MCP tools

**Slash Commands to Create:**
1. `/api-config` - Configure API providers
2. `/api-usage` - Show API usage statistics
3. `/api-costs` - Show cost estimates

**Files to Create:**
- `.claude/commands/api-config.md`
- `.claude/commands/api-usage.md`
- `.claude/commands/api-costs.md`

**Command Mapping:**
- `/api-config` → `manage` tools
- `/api-usage` → `get_usage` tool
- `/api-costs` → `estimate_cost` tool

---

## Testing Requirements

### Unit Tests to Write
- [ ] `tests/mcp/test_api_key_manager.py` - Key management
- [ ] `tests/mcp/test_routing.py` - Provider routing
- [ ] `tests/mcp/test_encryption.py` - Key encryption
- [ ] `tests/mcp/test_usage_tracking.py` - Usage tracking

### Integration Tests
- [ ] Test multi-provider routing
- [ ] Test fallback mechanism
- [ ] Test usage tracking accuracy
- [ ] Test cost estimation
- [ ] Test slash command integration

### Security Tests
- [ ] Verify keys encrypted at rest
- [ ] Test key rotation
- [ ] Verify no plaintext key logging
- [ ] Test access audit trail

---

## Review Checklist

Before creating PR, ensure:
- [ ] All tests pass: `pytest tests/mcp/`
- [ ] Keys properly encrypted
- [ ] Multi-provider routing working
- [ ] Usage tracking accurate
- [ ] Slash commands functional
- [ ] Documentation complete
- [ ] Run `/review` until score is 10/10

---

## PR Details

**Title:** "MCP: API Key Manager with multi-provider AI routing"

**Description:**
```markdown
## API Key Manager MCP Server Complete ✅

This PR implements the API Key Manager MCP server with secure key storage and multi-provider AI routing.

### Changes
- ✅ API Key Manager MCP server with 6 core tools
- ✅ Multi-provider AI routing (Anthropic, OpenAI, Google, Local)
- ✅ Encrypted API key storage
- ✅ Usage tracking and cost estimation
- ✅ Slash command integration (3 commands)

### MCP Tools Implemented
1. `add_api_key` - Securely add API keys
2. `validate_key` - Validate API keys
3. `rotate_key` - Rotate API keys
4. `get_usage` - Get usage statistics
5. `estimate_cost` - Estimate API costs
6. `route_request` - Intelligent provider routing

### Supported AI Providers
- **Anthropic** (Claude models) - Primary for code generation
- **OpenAI** (GPT models) - Analysis and chat
- **Google** (Gemini) - Optional fallback
- **Local** (Ollama) - Cost-free embeddings

### Routing Strategy
- Task-based routing (optimal model per task)
- Automatic fallback on failure
- Cost optimization
- Rate limit awareness
- Health monitoring

### Security Features
- All keys encrypted at rest
- No plaintext key logging
- Key rotation support
- Access audit trail

### Slash Commands Added
- `/api-config` - Configure API providers
- `/api-usage` - Show usage statistics
- `/api-costs` - Show cost estimates

### Review Score: 10/10 ✅
```

---

## Success Criteria

- [ ] API Key Manager MCP server operational
- [ ] Multi-provider routing working
- [ ] Secure key storage verified
- [ ] Usage tracking functional
- [ ] Cost estimation accurate
- [ ] Slash commands working
- [ ] All tests passing (>90% coverage)
- [ ] Review score 10/10
- [ ] No merge conflicts
- [ ] PR approved and merged

---

**Reference Documents:**
- `.claude/memory.md` (Session 2 - MCP architecture planning)
- `backend/app/utils/crypto.py` (encryption utilities)
- MCP Protocol Specification
