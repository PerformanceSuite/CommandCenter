# AI Arena - Multi-Model Debate System

## Overview

AI Arena is a multi-model debate system for strategic research and hypothesis validation. It uses Claude, Gemini, and GPT models to debate research questions, reaching consensus through structured rounds.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Frontend (React)                          │
│  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐ │
│  │ HypothesesPage │  │  DebateViewer  │  │  EvidenceExplorer  │ │
│  │   Dashboard    │  │  (Rounds/      │  │  (Filter/Browse    │ │
│  │   StatsBar     │  │   Responses)   │  │   Evidence)        │ │
│  │   CardList     │  │                │  │                    │ │
│  └───────┬────────┘  └───────┬────────┘  └─────────┬──────────┘ │
│          │                   │                     │             │
└──────────┼───────────────────┼─────────────────────┼─────────────┘
           │                   │                     │
           ▼                   ▼                     ▼
    ┌──────────────────────────────────────────────────────┐
    │                REST API (/api/v1/hypotheses)         │
    │  • GET /                - List hypotheses            │
    │  • GET /stats           - Dashboard statistics       │
    │  • GET /costs           - LLM cost tracking          │
    │  • GET /evidence/list   - Browse all evidence        │
    │  • GET /evidence/stats  - Evidence statistics        │
    │  • GET /{id}            - Hypothesis details         │
    │  • POST /{id}/validate  - Start async validation     │
    │  • GET /validation/{id} - Validation task status     │
    │  • GET /validation/{id}/debate - Full debate result  │
    └───────────────────────────┬──────────────────────────┘
                                │
    ┌───────────────────────────▼──────────────────────────┐
    │                  hypothesis_service                   │
    │  • HypothesisService  (CRUD, validation orchestration)│
    │  • ValidationTaskStorage (Redis-backed task state)   │
    └───────────────────────────┬──────────────────────────┘
                                │
    ┌───────────────────────────▼──────────────────────────┐
    │                  libs/ai_arena/                       │
    │  ┌──────────────┐  ┌─────────────┐  ┌──────────────┐ │
    │  │ hypothesis/  │  │  debate/    │  │  agents/     │ │
    │  │  schema.py   │  │ protocol.py │  │ specialist.py│ │
    │  │  registry.py │  │ result.py   │  │ response.py  │ │
    │  │  validator   │  │             │  │              │ │
    │  └──────┬───────┘  └──────┬──────┘  └──────┬───────┘ │
    └─────────┼─────────────────┼─────────────────┼────────┘
              │                 │                 │
              ▼                 ▼                 ▼
    ┌────────────────────────────────────────────────────┐
    │                  libs/llm_gateway/                  │
    │  ┌─────────────┐  ┌─────────────┐  ┌────────────┐  │
    │  │ gateway.py  │  │ providers.py│  │ metrics.py │  │
    │  │ (LiteLLM)   │  │ (claude,gpt,│  │ (Prometheus│  │
    │  │             │  │  gemini)    │  │  counters) │  │
    │  └──────┬──────┘  └─────────────┘  └────────────┘  │
    └─────────┼──────────────────────────────────────────┘
              │
              ▼
    ┌─────────────────────────────────────────────────────┐
    │                External LLM APIs                     │
    │  ┌────────────┐  ┌────────────┐  ┌────────────────┐ │
    │  │   Claude   │  │   Gemini   │  │    GPT-4o      │ │
    │  │ (Anthropic)│  │  (Google)  │  │   (OpenAI)     │ │
    │  └────────────┘  └────────────┘  └────────────────┘ │
    └─────────────────────────────────────────────────────┘
```

## Core Components

### 1. LLM Gateway (`libs/llm_gateway/`)

Unified interface for multiple LLM providers using LiteLLM.

**Files:**
- `gateway.py` - LLMGateway class with async complete/stream methods
- `providers.py` - Provider configurations (claude, gpt, gpt-mini, gemini)
- `metrics.py` - Prometheus metrics and cost tracking

**Usage:**
```python
from libs.llm_gateway import LLMGateway

gateway = LLMGateway()
response = await gateway.complete(
    provider="claude",
    messages=[{"role": "user", "content": "Analyze this hypothesis..."}],
    temperature=0.7,
)
print(response["content"])
```

### 2. AI Arena Core (`libs/ai_arena/`)

Multi-model debate orchestration system.

**Modules:**
- `agents/` - Specialist agents (Analyst, Researcher, Critic, Synthesizer)
- `debate/` - Debate protocol and consensus detection
- `hypothesis/` - Hypothesis schema, registry, validator

**Debate Flow:**
1. Question posed to all agents
2. Each agent provides independent response
3. Agents review each other's responses
4. Process repeats until consensus or max rounds
5. Final synthesis with dissenting views preserved

### 3. Hypothesis Module (`libs/ai_arena/hypothesis/`)

Lean Startup-inspired hypothesis validation framework.

**Schema (`schema.py`):**
```python
class Hypothesis:
    id: str
    statement: str                    # The hypothesis to validate
    category: HypothesisCategory      # customer, problem, solution, etc.
    impact: ImpactLevel               # high, medium, low
    risk: RiskLevel                   # high, medium, low
    testability: TestabilityLevel     # easy, medium, hard
    status: HypothesisStatus          # untested, validating, validated, invalidated
    success_criteria: str             # What would validate this?
    evidence: list[HypothesisEvidence]
    priority: HypothesisPriority      # Calculated from impact × risk × testability
```

**Registry (`registry.py`):**
- CRUD operations for hypotheses
- Priority-based ordering
- Evidence management
- Status tracking

**Validator (`validator.py`):**
- Orchestrates multi-model debates
- Collects evidence from agent responses
- Updates hypothesis status based on consensus

### 4. REST API (`app/routers/hypotheses.py`)

**Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/hypotheses/` | List hypotheses with filtering |
| GET | `/hypotheses/stats` | Dashboard statistics |
| GET | `/hypotheses/costs` | LLM cost tracking |
| GET | `/hypotheses/evidence/list` | Browse all evidence |
| GET | `/hypotheses/evidence/stats` | Evidence statistics |
| GET | `/hypotheses/{id}` | Hypothesis details |
| POST | `/hypotheses/{id}/validate` | Start async validation |
| GET | `/hypotheses/{id}/validation-status` | Current validation status |
| GET | `/hypotheses/validation/{task_id}` | Task status by ID |
| GET | `/hypotheses/validation/{task_id}/debate` | Full debate result |

### 5. Frontend Components

**HypothesesPage** (`hub/frontend/src/pages/HypothesesPage.tsx`):
- Tabbed interface for Hypotheses, Evidence, Costs
- Main entry point for AI Arena UI

**HypothesisDashboard** (`hub/frontend/src/components/HypothesisDashboard/`):
- Statistics bar with counts by status
- Hypothesis cards with priority scores
- Validation modal for starting debates

**DebateViewer** (`hub/frontend/src/components/DebateViewer/`):
- Round-by-round debate visualization
- Agent responses with confidence levels
- Consensus progression

**EvidenceExplorer** (`hub/frontend/src/components/EvidenceExplorer/`):
- Filter by supporting/contradicting
- Source type breakdown
- Confidence distribution

**CostDashboard** (`hub/frontend/src/components/CostDashboard/`):
- Total cost tracking
- Provider breakdown (Claude, GPT, Gemini)
- Token usage statistics

## Configuration

### Environment Variables

```bash
# Required for AI Arena
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Optional: Redis for task state persistence
REDIS_URL=redis://localhost:6379
```

### Provider Models

| Provider | Model | Use Case |
|----------|-------|----------|
| claude | claude-sonnet-4-20250514 | Primary analysis |
| gpt | gpt-4o | Cross-validation |
| gpt-mini | gpt-4o-mini | Cost-effective tasks |
| gemini | gemini-2.5-flash | Speed-optimized |

## Validation Workflow

1. **Create Hypothesis**
   ```python
   hypothesis = registry.create(HypothesisCreate(
       statement="Enterprise customers will pay $2K/month for X",
       category=HypothesisCategory.REVENUE,
       impact=ImpactLevel.HIGH,
       risk=RiskLevel.HIGH,
       testability=TestabilityLevel.MEDIUM,
       success_criteria="5 of 10 prospects confirm willingness to pay"
   ))
   ```

2. **Start Validation**
   ```
   POST /api/v1/hypotheses/{id}/validate
   {
     "max_rounds": 3,
     "agents": ["analyst", "researcher", "critic"]
   }
   ```

3. **Poll for Status**
   ```
   GET /api/v1/hypotheses/{id}/validation-status
   ```

4. **Get Debate Result**
   ```
   GET /api/v1/hypotheses/validation/{task_id}/debate
   ```

## Cost Tracking

The system tracks LLM costs via Prometheus metrics:

- `llm_request_total` - Request counts by provider/status
- `llm_tokens_total` - Token usage by provider/type
- `llm_cost_usd_total` - Cumulative cost by provider

Access via `/api/v1/hypotheses/costs` endpoint.

## Testing

```bash
# Run AI Arena unit tests
cd backend
pytest libs/ai_arena/tests/ -v

# Run integration tests
pytest tests/integration/test_hypotheses_api.py -v

# Run all AI Arena related tests
pytest -k "hypothesis or arena or debate" -v
```

## Metrics & Observability

Prometheus metrics exposed at `/metrics`:
- LLM request latency
- Token usage by provider
- Cost accumulation
- Debate completion rate
- Consensus achievement rate

## Future Enhancements

1. **Persistent Storage**: Move from in-memory to database-backed hypothesis storage
2. **Streaming Responses**: Real-time debate updates via WebSocket
3. **Custom Agents**: User-defined specialist agents
4. **Evidence Integration**: Link to external data sources (RAG, databases)
5. **Batch Validation**: Validate multiple hypotheses in parallel
