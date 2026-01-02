# CommandCenter Roadmap

**Last Updated**: 2026-01-02

---

## Current State

CommandCenter has achieved **B+ (84%) health score** with:
- Strong backend infrastructure (multiple services, API endpoints)
- Dual React frontends (main port 3000, hub port 9000)
- AI integration (E2B sandboxes, multi-agent framework)
- Graph service with NATS event streaming
- KnowledgeBeast vector RAG system

---

## Active Development Tracks

### Track A: VISLZR (Composable Query Interface)

**Status**: Sprint 3 - Agent Parity

| Phase | Status | Focus |
|-------|--------|-------|
| Sprint 1 | ✅ Complete | Core graph queries |
| Sprint 2 | ✅ Complete | Saved recipes, visualization |
| Sprint 3 | 🔄 Active | Agent executions as entities, NATS events |
| Sprint 4 | 📋 Planned | Ecosystem-wide queries, new entity types |

### Track B: Agent Infrastructure

**Status**: Bootstrap framework validated

| Component | Status |
|-----------|--------|
| Prompt Improver | ✅ Complete |
| YAML Persona Store | ✅ Complete |
| Agent Executor (E2B) | ✅ Complete |
| CLI Runner (cc-agent) | ✅ Complete |
| Long-running agents | 🔄 In Progress |

### Track C: Wander (Exploratory Agent System)

**Status**: Design Complete, Implementation Pending

See: [Wander Concept](./concepts/Wander.md)

| Phase | Status | Focus | Effort |
|-------|--------|-------|--------|
| 0 | 📋 Ready | Mind Map UI (ReactFlow) | 1 day |
| 1 | 📋 Planned | Foundation (DB, models, KB integration) | 1 week |
| 2 | 📋 Planned | Adjacency Finding | 1 week |
| 3 | 📋 Planned | Wander Loop (step, trace, dwelling) | 1 week |
| 4 | 📋 Planned | Resonance & Crystallization | 1 week |
| 5 | 📋 Planned | Constraints & Verification | 1 week |
| 6 | 📋 Planned | VISLZR Integration | 3 days |
| 7 | 📋 Planned | Persistence & Archival | 3 days |
| 8 | 📋 Planned | Fractal Security Layer | 2 weeks |

**Dependency**: Requires long-running agent infrastructure (Track B) before Phase 1.

**Implementation Plan**: [2026-01-02-wander-mindmap-implementation.md](./plans/2026-01-02-wander-mindmap-implementation.md)

---

## Upcoming Milestones

### Q1 2026

1. **Long-Running Agents** - Stable infrastructure for agents that persist across sessions
2. **Wander Phase 0** - Mind map visualization ready with mock data
3. **VISLZR Sprint 4** - Complete ecosystem query capability

### Q2 2026

1. **Wander Phases 1-5** - Core exploration engine
2. **Economic Agent Layer** - Wallet integration for autonomous actions
3. **Fractal Security** - Novel access control mechanism

---

## Strategic Vision

CommandCenter evolves toward an **AI Operating System for Knowledge Work**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMMANDCENTER EVOLUTION                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  NOW                           NEXT                    FUTURE       │
│  ───                           ────                    ──────       │
│  • Multi-project management    • Wander exploration    • Autonomous │
│  • Agent execution (E2B)       • VISLZR ecosystem      • economic   │
│  • Graph service               • Long-running agents     agents     │
│  • Research hub                • Fractal security      • Self-      │
│  • AI Arena                    • Economic layer          improving  │
│                                                          skills     │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

### Core Principle

> Agents are the primary consumers AND builders of the system.
> Everything must be discoverable, queryable, and manipulable programmatically.

---

## Archive

### Completed Phases

- ✅ Phase 1-3: Foundation, core services, basic UI
- ✅ Phase 4: Real-time subscriptions (WebSocket, NATS)
- ✅ Phase 5: Federation prep
- ✅ Phase 6: Health service discovery
- ✅ Phase 7: Graph service
- ✅ Phase 8: Testing infrastructure
- ✅ Phase 9: Federation service
- ✅ Phase 10: Agent orchestration (E2B)

---

*This roadmap is updated when strategic changes occur.*
*For detailed implementation plans, see [docs/plans/](./plans/)*
