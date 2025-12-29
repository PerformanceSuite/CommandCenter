# AI Arena Implementation Plan

**Date**: 2025-12-29
**Status**: Ready for Implementation
**Priority**: High
**Estimated Effort**: 4-6 weeks

---

## Overview

Build a multi-model AI debate system ("AI Arena") for strategic research and hypothesis validation. The system will use Claude, Gemini, and GPT models to debate research questions, reaching consensus through structured rounds.

---

## Phase 1: LiteLLM Integration (Week 1)

### Objectives
- Add LiteLLM as unified multi-provider LLM gateway
- Configure Claude, Gemini, and GPT providers
- Add cost tracking and observability

### Tasks

```
[ ] 1.1 Add litellm dependency to backend/pyproject.toml
[ ] 1.2 Create backend/libs/llm_gateway/ module
[ ] 1.3 Implement LLMGateway class with unified interface
[ ] 1.4 Add provider configuration (env vars for API keys)
[ ] 1.5 Implement cost tracking hooks
[ ] 1.6 Add Prometheus metrics for LLM calls
[ ] 1.7 Write unit tests for gateway
[ ] 1.8 Integration test with all three providers
```

### Files to Create

```
backend/libs/llm_gateway/
├── __init__.py
├── gateway.py          # LLMGateway class
├── providers.py        # Provider configurations
├── cost_tracking.py    # Cost calculation and logging
├── metrics.py          # Prometheus metrics
└── tests/
    ├── test_gateway.py
    └── test_providers.py
```

### Key Code (gateway.py sketch)

```python
from litellm import completion
from typing import List, Dict, Any
import os

class LLMGateway:
    """Unified interface for multiple LLM providers."""

    PROVIDERS = {
        "claude": "anthropic/claude-sonnet-4-20250514",
        "gemini": "gemini/gemini-2.5-flash",
        "gpt": "openai/gpt-4o",
        "gpt-mini": "openai/gpt-4o-mini",
    }

    def __init__(self):
        self._validate_api_keys()

    async def complete(
        self,
        provider: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4096,
    ) -> Dict[str, Any]:
        """Send completion request to specified provider."""
        model = self.PROVIDERS.get(provider)
        if not model:
            raise ValueError(f"Unknown provider: {provider}")

        response = await completion(
            model=model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        # Track costs
        self._track_cost(provider, response)

        return {
            "content": response.choices[0].message.content,
            "model": model,
            "usage": response.usage,
        }
```

---

## Phase 2: Agent Framework (Week 2)

### Objectives
- Create base Agent class with confidence scoring
- Implement specialized agent roles
- Build agent registry and lifecycle management

### Tasks

```
[ ] 2.1 Create backend/libs/ai_arena/ module
[ ] 2.2 Implement BaseAgent class
[ ] 2.3 Add confidence scoring mechanism
[ ] 2.4 Create specialized agents (Analyst, Researcher, Strategist, Critic)
[ ] 2.5 Implement AgentRegistry for managing agents
[ ] 2.6 Add agent prompt templates
[ ] 2.7 Write unit tests
```

### Files to Create

```
backend/libs/ai_arena/
├── __init__.py
├── agents/
│   ├── __init__.py
│   ├── base.py           # BaseAgent class
│   ├── analyst.py        # Claude-based analyst
│   ├── researcher.py     # Gemini-based researcher
│   ├── strategist.py     # GPT-based strategist
│   └── critic.py         # Claude-based devil's advocate
├── registry.py           # AgentRegistry
├── prompts/
│   ├── analyst.md
│   ├── researcher.md
│   ├── strategist.md
│   └── critic.md
└── tests/
```

### Key Code (base.py sketch)

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional
import json

@dataclass
class AgentResponse:
    """Structured response from an agent."""
    answer: str
    reasoning: str
    confidence: int  # 0-100
    evidence: list[str]
    agent_name: str
    model: str

class BaseAgent(ABC):
    """Base class for all AI Arena agents."""

    def __init__(
        self,
        name: str,
        provider: str,
        gateway: "LLMGateway",
        system_prompt: str,
    ):
        self.name = name
        self.provider = provider
        self.gateway = gateway
        self.system_prompt = system_prompt

    async def respond(
        self,
        question: str,
        context: Optional[str] = None,
        previous_responses: Optional[list[AgentResponse]] = None,
    ) -> AgentResponse:
        """Generate a response to a question."""
        messages = self._build_messages(question, context, previous_responses)

        response = await self.gateway.complete(
            provider=self.provider,
            messages=messages,
        )

        return self._parse_response(response["content"])

    def _parse_response(self, content: str) -> AgentResponse:
        """Parse structured response from LLM output."""
        # Expect JSON with answer, reasoning, confidence, evidence
        data = json.loads(content)
        return AgentResponse(
            answer=data["answer"],
            reasoning=data["reasoning"],
            confidence=data["confidence"],
            evidence=data.get("evidence", []),
            agent_name=self.name,
            model=self.provider,
        )
```

---

## Phase 3: Debate Protocol (Week 3)

### Objectives
- Implement multi-round debate orchestration
- Build consensus detection algorithm
- Add discussion prompt generation

### Tasks

```
[ ] 3.1 Create DebateOrchestrator class
[ ] 3.2 Implement round management
[ ] 3.3 Build consensus detection algorithm
[ ] 3.4 Create discussion prompt templates
[ ] 3.5 Add debate state persistence
[ ] 3.6 Implement timeout and error handling
[ ] 3.7 Write integration tests
```

### Files to Create

```
backend/libs/ai_arena/
├── debate/
│   ├── __init__.py
│   ├── orchestrator.py   # DebateOrchestrator
│   ├── consensus.py      # Consensus detection
│   ├── prompts.py        # Discussion prompt generation
│   └── state.py          # Debate state management
```

### Key Code (orchestrator.py sketch)

```python
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional

class ConsensusLevel(Enum):
    STRONG = "strong"      # All agree, high confidence
    WEAK = "weak"          # Majority agrees
    DEADLOCK = "deadlock"  # No consensus

@dataclass
class DebateRound:
    round_number: int
    responses: list[AgentResponse]
    consensus_level: Optional[ConsensusLevel]

@dataclass
class DebateResult:
    question: str
    rounds: list[DebateRound]
    final_answer: str
    final_confidence: float
    consensus_level: ConsensusLevel
    dissenting_views: list[AgentResponse]

class DebateOrchestrator:
    """Orchestrates multi-round debates between agents."""

    def __init__(
        self,
        agents: list[BaseAgent],
        max_rounds: int = 3,
        consensus_threshold: float = 0.8,
    ):
        self.agents = agents
        self.max_rounds = max_rounds
        self.consensus_threshold = consensus_threshold

    async def debate(
        self,
        question: str,
        context: Optional[str] = None,
    ) -> DebateResult:
        """Run a full debate on a question."""
        rounds = []

        for round_num in range(self.max_rounds):
            # Get responses from all agents
            responses = await self._collect_responses(
                question=question,
                context=context,
                previous_rounds=rounds,
            )

            # Check for consensus
            consensus = self._detect_consensus(responses)

            round_result = DebateRound(
                round_number=round_num,
                responses=responses,
                consensus_level=consensus,
            )
            rounds.append(round_result)

            # Stop if consensus reached
            if consensus == ConsensusLevel.STRONG:
                break

        return self._compile_result(question, rounds)
```

---

## Phase 4: Hypothesis Validation Workflow (Week 4) ✅ COMPLETED

### Objectives
- Build hypothesis-specific debate workflow
- Integrate with CommandCenter task system
- Add evidence storage to KnowledgeBeast

### Tasks

```
[x] 4.1 Create HypothesisValidator class
[x] 4.2 Define hypothesis schema (Pydantic models)
[x] 4.3 Integrate with Task service (via HypothesisRegistry.linked_task_id)
[x] 4.4 Add evidence storage to KnowledgeBeast (HypothesisEvidenceStorage)
[x] 4.5 Build hypothesis registry
[x] 4.6 Create validation report generator
[x] 4.7 Add NATS event publishing for debate progress
```

### Files Created

```
backend/libs/ai_arena/hypothesis/
├── __init__.py           # Module exports
├── schema.py             # Pydantic models (Hypothesis, Evidence, etc.)
├── validator.py          # HypothesisValidator class
├── registry.py           # HypothesisRegistry for CRUD operations
├── report.py             # ValidationReportGenerator
├── events.py             # NATS event publishing
└── storage.py            # KnowledgeBeast integration

backend/libs/ai_arena/tests/
└── test_hypothesis.py    # Unit tests for Phase 4
```

### Hypothesis Schema

```python
from pydantic import BaseModel
from enum import Enum
from datetime import datetime

class HypothesisStatus(str, Enum):
    UNTESTED = "untested"
    VALIDATING = "validating"
    VALIDATED = "validated"
    INVALIDATED = "invalidated"
    NEEDS_MORE_DATA = "needs_more_data"

class Hypothesis(BaseModel):
    id: str
    statement: str
    category: str  # market, pricing, customer, technical
    impact: str    # high, medium, low
    risk: str      # high, medium, low
    testability: str  # easy, medium, hard
    status: HypothesisStatus
    success_criteria: str
    evidence: list[str]
    debate_result: Optional[DebateResult]
    created_at: datetime
    updated_at: datetime
```

---

## Phase 5: UI Integration (Week 5-6) - IN PROGRESS

### Objectives
- Add AI Arena to Hub frontend
- Build debate visualization component
- Create hypothesis dashboard

### Tasks

```
[x] 5.1 Create AIArena service in frontend (hypothesesApi.ts)
[ ] 5.2 Build DebateViewer component
[x] 5.3 Create HypothesisDashboard
[x] 5.4 Add real-time debate progress (polling, WebSocket later)
[ ] 5.5 Build evidence explorer
[ ] 5.6 Create cost tracking dashboard
```

### Files Created

```
Backend API:
- backend/app/schemas/hypothesis.py       # API request/response models
- backend/app/services/hypothesis_service.py  # Service layer
- backend/app/routers/hypotheses.py       # REST endpoints

Frontend:
- hub/frontend/src/types/hypothesis.ts    # TypeScript types
- hub/frontend/src/services/hypothesesApi.ts  # API client
- hub/frontend/src/components/HypothesisDashboard/
  ├── index.tsx           # Main dashboard container
  ├── HypothesisCard.tsx  # Individual hypothesis card
  ├── StatsBar.tsx        # Statistics summary
  └── ValidationModal.tsx # Validation config/progress modal
- hub/frontend/src/pages/HypothesesPage.tsx  # Page component
```

---

## Environment Variables Required

```bash
# Add to .env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...

# Optional: LiteLLM proxy mode
LITELLM_PROXY_URL=http://localhost:4000
```

---

## Success Metrics

| Metric | Target |
|--------|--------|
| Debate completion rate | > 95% |
| Average consensus rate | > 70% |
| Cost per hypothesis | < $2.00 |
| Time per hypothesis | < 5 minutes |
| Evidence quality score | > 4/5 (user rating) |

---

## Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| API rate limits | Implement backoff, queue debates |
| High costs | Set budget caps, use cheaper models for simple tasks |
| Hallucinations | Cross-check with multiple models, require citations |
| Consensus deadlock | Escalate to human, preserve all viewpoints |
| Model unavailability | Fallback providers, graceful degradation |

---

## Definition of Done

- [ ] All tests passing (unit + integration)
- [ ] Documentation complete
- [ ] Cost tracking verified
- [ ] Observability metrics in Grafana
- [ ] At least 3 Veria hypotheses validated using system
- [ ] Code reviewed and merged to main
