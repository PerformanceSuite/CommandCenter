# Wander

**Exploration and Discovery Engine**

Wander is a long-running exploratory agent that discovers unexpected connections, surfaces patterns, and crystallizes insights from CommandCenter's knowledge base.

## Overview

Unlike task-focused agents, Wander **dwells** in the knowledge space. It doesn't try to answer questions—it tries to find interesting questions. Outputs are "Crystals": validated insights with confidence scores.

## Core Concepts

### Resonance
Wander detects when ideas resonate—when disparate pieces of knowledge unexpectedly connect. Resonance is the signal that something interesting exists.

### Dwelling
Wander doesn't rush. It explores an area, sits with it, notices what emerges. This is fundamentally different from task completion.

### Crystals
When resonance is strong enough and validated, it becomes a Crystal—a packaged insight that can be:
- Stored in KnowledgeBeast
- Fed to other modules (MRKTZR, Veria, ROLLIZR)
- Presented to humans for review
- Used to improve prompts and skills

### Attractors and Fences
- **Attractors**: Topics or areas to gravitate toward
- **Fences**: Boundaries to stay within (compliance, scope)

## Architecture

### RLM Pattern (Recursive Language Model)

Wander uses the RLM pattern from arXiv:2512.24601:
- Context stored as REPL variables, NOT in LLM attention window
- Dweller writes Python code to query memory programmatically
- Sub-LLM spawning for chunk analysis
- Enables 10M+ token exploration without context rot

```
┌─────────────────────────────────────────────┐
│              WANDER REPL                    │
│                                             │
│  memory = WanderMemory(knowledge_beast)     │
│  dweller = Dweller(model="claude-sonnet")   │
│                                             │
│  # Dweller writes code to explore:          │
│  chunks = memory.search("prediction markets")│
│  for chunk in chunks:                       │
│      analysis = llm_query(chunk, "extract   │
│                           key patterns")    │
│      if analysis.resonance > 0.7:           │
│          memory.mark_resonant(chunk)        │
│                                             │
│  # Crystallization when ready:              │
│  crystal = dweller.crystallize(resonances)  │
│                                             │
└─────────────────────────────────────────────┘
```

### Mind Map UI (Phase 0)

The first interface is a mind map showing:
- Current exploration area
- Resonant nodes (glowing)
- Crystal candidates
- Attractor/fence boundaries

Human can:
- Nudge exploration direction
- Approve/reject crystal candidates
- Add attractors/fences
- View exploration history

## Integration Points

| Module | Integration |
|--------|-------------|
| KnowledgeBeast | Source of all knowledge to explore |
| AI Arena | Validates crystal candidates |
| Prompt Improver | Crystals improve prompts |
| ROLLIZR | Crystals feed opportunity detection |
| MRKTZR | Crystals inform campaign strategy |
| Veria | Crystals drive trading hypotheses |

## Data Model

```
Exploration
├── id, started_at, status
├── attractor_ids[]
├── fence_ids[]
├── resonances[]
└── crystals[]

Resonance
├── id, exploration_id
├── chunks[] (source materials)
├── strength (0-1)
├── pattern_description
└── created_at

Crystal
├── id, exploration_id
├── resonance_ids[] (sources)
├── insight (the actual content)
├── confidence (0-1)
├── validated_by (ai_arena|human|market)
├── validation_score
└── created_at, validated_at

Attractor
├── id, name, description
├── keywords[], embeddings[]
└── active

Fence
├── id, name, description
├── type (topic|compliance|scope)
├── rules{}
└── active
```

## Actions (VISLZR node)

- start exploration
- view current
- add attractor
- add fence
- review resonances
- crystallize
- history

## Roadmap

- [x] Concept design complete
- [x] Technical spec complete
- [ ] Phase 0: Mind Map UI
- [ ] Phase 1: Basic dwelling loop
- [ ] Phase 2: Resonance detection
- [ ] Phase 3: Crystallization
- [ ] Phase 4: AI Arena validation
- [ ] Phase 5: Continuous background operation
