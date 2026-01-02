# CommandCenter: Unified AI Operating System Architecture

**Status**: Design Vision
**Created**: 2026-01-02

**See also**: [The Loop](./TheLoop.md) - The self-improving cycle that this architecture enables

---

## Core Thesis

CommandCenter is not a collection of tools. It is a **unified AI Operating System for Knowledge Work** where:

1. **All capabilities are composable building blocks**
2. **Agents are the primary consumers AND builders**
3. **Intent is a first-class architectural concern**
4. **Knowledge flows between all components**

The UI may present different "apps" (AI Arena, Wander, Veria), but underneath they share infrastructure, knowledge, and design principles.

---

## The Three Layers

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER INTERFACE                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │
│  │ AI Arena │ │  Wander  │ │  Veria   │ │ Research │ │  Agents  │  │
│  │   View   │ │   View   │ │   View   │ │   Hub    │ │  Console │  │
│  └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘ └────┬─────┘  │
│       └────────────┴────────────┴────────────┴────────────┘         │
│                              │                                       │
├──────────────────────────────┼───────────────────────────────────────┤
│                              ▼                                       │
│  LAYER 1: RESEARCH (Understanding)                                   │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                  ││
│  │  AI Arena          Wander           External Signals             ││
│  │  • Model compare   • Idea explore   • Polymarket                 ││
│  │  • Benchmark       • Pattern find   • HackerNews                 ││
│  │  • Capability map  • Resonances     • arXiv, SEC                 ││
│  │           │              │                │                      ││
│  │           └──────────────┼────────────────┘                      ││
│  │                          ▼                                       ││
│  │              ┌─────────────────────┐                             ││
│  │              │   KnowledgeBeast    │                             ││
│  │              │   (unified store)   │                             ││
│  │              │   • Vectors + Graph │                             ││
│  │              │   • All knowledge   │                             ││
│  │              └─────────────────────┘                             ││
│  │                                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                       │
│                              ▼                                       │
├──────────────────────────────────────────────────────────────────────┤
│  LAYER 2: INTENT (Clarification)                                     │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                  ││
│  │  ┌─────────────────────────────────────────────────────────┐    ││
│  │  │              INTENT ENGINE                               │    ││
│  │  │                                                          │    ││
│  │  │  Prompt Improver (Intent-Aware)                          │    ││
│  │  │  • Detect ambiguity → trigger disambiguation             │    ││
│  │  │  • Extract explicit intent (goals, constraints, risks)   │    ││
│  │  │  • Enrich with Wander crystals + KnowledgeBeast          │    ││
│  │  │  • Simulate consequences before execution                │    ││
│  │  │  • Route to appropriate model/agent                      │    ││
│  │  │                                                          │    ││
│  │  │  Produces: Intent Artifact                               │    ││
│  │  │  {                                                       │    ││
│  │  │    goals: [...],                                         │    ││
│  │  │    constraints: [...],                                   │    ││
│  │  │    failure_modes: [...],                                 │    ││
│  │  │    trade_offs: [...],                                    │    ││
│  │  │    confidence: 0.X,                                      │    ││
│  │  │    needs_clarification: [...]                            │    ││
│  │  │  }                                                       │    ││
│  │  └─────────────────────────────────────────────────────────┘    ││
│  │                                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                       │
│                              ▼                                       │
├──────────────────────────────────────────────────────────────────────┤
│  LAYER 3: EXECUTION (Action)                                         │
│  ┌─────────────────────────────────────────────────────────────────┐│
│  │                                                                  ││
│  │  Agent Executor       Veria Trading      Tool Orchestration      ││
│  │  • E2B sandboxes     • Prediction mkts  • MCP servers           ││
│  │  • Persona routing   • Risk management  • Filesystem            ││
│  │  • Code generation   • Human approval   • GitHub, APIs          ││
│  │                                                                  ││
│  │  All execution receives Intent Artifact, not raw prompt          ││
│  │  All execution feeds results back to Research Layer              ││
│  │                                                                  ││
│  └─────────────────────────────────────────────────────────────────┘│
│                              │                                       │
│                              ▼                                       │
│                     FEEDBACK TO RESEARCH                             │
│                 (Results → KnowledgeBeast → Wander)                  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Component Integration

### AI Arena → KnowledgeBeast → Wander

```
AI Arena Session: "Compare Claude vs GPT-5 on code generation"
         │
         ▼
Results stored in KnowledgeBeast:
  - Benchmark scores
  - Qualitative observations
  - Code samples
         │
         ▼
Wander explores:
  - Finds pattern: "Claude better at X when Y"
  - Resonance forms across multiple comparisons
  - Crystal: "Route code refactoring to Claude, greenfield to GPT-5"
         │
         ▼
Intent Engine uses crystal for model routing
```

### Prompt Improver as Intent Engine

The existing Prompt Improver should evolve to apply Intent-Aware principles:

| Current | Enhanced |
|---------|----------|
| "Make this prompt clearer" | Detect ambiguity, ask clarifying questions |
| Add structure | Extract explicit intent artifact |
| Suggest improvements | Pull relevant crystals for context |
| Single output | Produce intent artifact + improved prompt |

```python
class IntentEngine:
    """Evolution of Prompt Improver with Intent-Aware principles."""

    async def process(self, raw_input: str, context: dict) -> IntentArtifact:
        # 1. Detect ambiguity
        ambiguities = await self.detect_ambiguity(raw_input)

        if ambiguities.needs_clarification:
            return IntentArtifact(
                status="needs_clarification",
                questions=ambiguities.questions  # Active disambiguation
            )

        # 2. Extract explicit intent
        intent = await self.extract_intent(raw_input)

        # 3. Enrich with Wander crystals
        relevant_crystals = await self.wander.query_crystals(
            embedding=embed(raw_input),
            min_confidence=0.7
        )
        intent.context_enrichment = relevant_crystals

        # 4. Simulate consequences (for high-stakes)
        if intent.risk_level > 0.5:
            simulation = await self.simulate_consequences(intent)
            intent.simulated_outcomes = simulation

        # 5. Route to appropriate executor
        intent.recommended_executor = self.route(intent)

        return intent
```

### Wander Uses RLM for ALL Knowledge

Wander's RLM pattern applies to the entire knowledge base:

```python
# In WanderREPL, available knowledge sources:
self.globals = {
    # Wander-specific
    'hot_memory': [],
    'resonances': {},

    # Cross-system knowledge (RLM queryable)
    'knowledgebeast': self._query_knowledgebeast,  # All stored knowledge
    'ai_arena_results': self._query_arena,          # Model comparisons
    'project_docs': self._query_docs,               # CommandCenter docs
    'external_signals': self._query_signals,        # Polymarket, etc.

    # Sub-LLM for analysis
    'llm_query': self._llm_query,
}
```

### Veria Receives Intent Artifacts

Trading decisions don't come from raw Wander output - they go through Intent Engine:

```
Wander Crystal: "Regulatory pattern suggests approval likely"
         │
         ▼
Intent Engine:
  - Goals: "Profit from information edge"
  - Constraints: "Max $500, requires 15% edge"
  - Failure modes: "Crystal wrong, liquidity trap"
  - Confidence: 0.72
         │
         ▼
Veria evaluates Intent Artifact, not raw crystal
```

---

## Shared Infrastructure

All components share:

| Infrastructure | Used By |
|---------------|---------|
| **KnowledgeBeast** | AI Arena (store results), Wander (explore), Intent Engine (enrich) |
| **NATS Events** | All components publish/subscribe for real-time updates |
| **pgvector** | Embeddings for all semantic search |
| **RLM Pattern** | Any agent needing large context (Wander, Research, Analysis) |
| **Persona Store** | Agent Executor, Intent Engine (different personas for tasks) |
| **MCP Servers** | All execution (filesystem, GitHub, browser) |

---

## UI Unification

From the user's perspective, these are different "modes" of the same system:

```
┌─────────────────────────────────────────────────────────────────────┐
│  CommandCenter                                    [Search] [Profile] │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  [Research ▼]  [Explore]  [Trade]  [Build]  [Settings]              │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                                                                │  │
│  │   Current view depends on selected mode:                       │  │
│  │                                                                │  │
│  │   Research: AI Arena, benchmark results, model comparisons     │  │
│  │   Explore:  Wander mind map, crystals, resonances              │  │
│  │   Trade:    Veria dashboard, positions, P&L                    │  │
│  │   Build:    Agent console, code generation, GitHub             │  │
│  │                                                                │  │
│  │   But ALL modes can:                                           │  │
│  │   - Access the same knowledge base                             │  │
│  │   - Trigger Intent Engine for clarification                    │  │
│  │   - Spawn agents for execution                                 │  │
│  │   - See relevant crystals/context                              │  │
│  │                                                                │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │  Intent Bar: "What are you trying to accomplish?"              │  │
│  │  [_________________________________________________] [Clarify] │  │
│  │                                                                │  │
│  │  Detected: Goal unclear | Constraints: none specified          │  │
│  │  Suggested: Add time constraint? Specify risk tolerance?       │  │
│  └───────────────────────────────────────────────────────────────┘  │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Implementation Priority

### Phase 1: Knowledge Unification
- [ ] AI Arena results → KnowledgeBeast
- [ ] Research Hub → KnowledgeBeast
- [ ] Wander reads from unified KnowledgeBeast

### Phase 2: Intent Engine
- [ ] Evolve Prompt Improver → Intent Engine
- [ ] Add disambiguation detection
- [ ] Add intent artifact extraction
- [ ] Add crystal enrichment

### Phase 3: Execution Integration
- [ ] Agent Executor receives Intent Artifacts
- [ ] Veria receives Intent Artifacts
- [ ] All execution feeds back to Research layer

### Phase 4: UI Unification
- [ ] Unified navigation between modes
- [ ] Intent Bar in all views
- [ ] Cross-mode context awareness

---

## Key Principles

1. **One Knowledge Base**: Everything goes into KnowledgeBeast, Wander explores it all
2. **Intent Before Execution**: Every action goes through Intent Engine
3. **Feedback Loops**: Execution results feed back to research
4. **Composable Building Blocks**: Each component usable independently, powerful together
5. **Agents as Primary Users**: Design for agent consumption, human oversight

---

## References

- [Intent-Aware Agents](./IntentAware.md) - Framework for reliable agent intent
- [Wander](./Wander.md) - Exploratory agent, RLM pattern
- [Wander-TechSpec](./Wander-TechSpec.md) - RLM implementation details
- [Veria](./Veria.md) - Economic action layer
- [Real-Time Intelligence](./RealTimeIntelligence.md) - External signal integration

---

*This document describes the unified vision. Individual components are documented separately but should be understood as parts of one system.*
