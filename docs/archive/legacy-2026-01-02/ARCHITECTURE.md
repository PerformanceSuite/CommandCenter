# Architecture

CommandCenter is a unified AI Operating System, not a collection of separate tools. This document describes how everything connects.

## The Self-Improving Cycle

The core insight: **the system improves itself through its own operation.**

```
┌─────────────────────────────────────────────────────────────────┐
│                                                                 │
│         ┌──────────────────────────────────────────┐           │
│         │                                          │           │
│         ▼                                          │           │
│    ┌──────────┐     ┌──────────┐     ┌──────────┐ │           │
│    │ DISCOVER │ ──→ │ VALIDATE │ ──→ │ IMPROVE  │─┘           │
│    └──────────┘     └──────────┘     └──────────┘             │
│                                                                 │
│    Explore          Test            Apply                      │
│    Connect          Compare         Update                     │
│    Pattern-find     Human review    Compound                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

### DISCOVER Phase
- **Wander**: Explores idea space, finds unexpected connections
- **Research Hub**: Tracks research tasks, surfaces what needs exploration
- **Real-Time Intelligence**: Ingests Polymarket, HackerNews, arXiv, SEC
- **ROLLIZR**: Scans for consolidation opportunities

### VALIDATE Phase
- **AI Arena**: Tests models, compares approaches, finds what works
- **Crystals**: Insights that survive scrutiny (from Wander)
- **Human Checkpoints**: Expert review at critical junctures
- **Veria**: Market validation (prediction markets as truth signal)

### IMPROVE Phase
- **Prompt Improver**: Makes prompts better based on learnings
- **Skills**: Rewritten by agents using discoveries
- **Agent Personas**: Refined based on what works

## Three Layers

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: RESEARCH (Understanding)                              │
│                                                                 │
│  Wander          AI Arena         External Signals              │
│  • Explore       • Benchmark      • Polymarket                  │
│  • Pattern-find  • Compare        • HackerNews                  │
│  • Resonate      • Validate       • arXiv, SEC                  │
│                                                                 │
│                    ↓                                            │
│            KnowledgeBeast                                       │
│            (unified store)                                      │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 2: INTENT (Clarification)                                │
│                                                                 │
│  • Detect ambiguity → ask before acting                         │
│  • Extract goals, constraints, failure modes                    │
│  • Crystallize intent over time (not upfront)                   │
│  • Separate interpretation from execution                       │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│  LAYER 3: ACTION (Execution)                                    │
│                                                                 │
│  • MRKTZR: Campaigns, CRM, partnerships                         │
│  • Veria: Prediction market trading                             │
│  • Agent execution with human checkpoints                       │
│  • Audit trail and compliance                                   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## VISLZR: The Human Interface

VISLZR is not a visualization tool—it's **THE interface** for humans to interact with CommandCenter.

Everything is a node:
- Modules, concepts, documents, servers, containers, people, campaigns

Each node has:
- **Center**: Description (what it IS)
- **Action Ring**: Contextual actions based on node type
- **Connections**: Parent, children, siblings

```
                    ┌─────────┐
                    │ Parent  │
                    └────┬────┘
                         │
        ┌────────────────┼────────────────┐
        │                │                │
   ┌────┴────┐    ┌──────┴──────┐   ┌────┴────┐
   │ Sibling │────│    NODE     │───│ Sibling │
   └─────────┘    │ ┌─────────┐ │   └─────────┘
                  │ │  Desc   │ │
                  │ ├─────────┤ │
                  │ │ Actions │ │
                  │ │ 1│2│3│4 │ │
                  │ └─────────┘ │
                  └──────┬──────┘
                         │
                    ┌────┴────┐
                    │  Child  │
                    └─────────┘
```

**Actions are composable and generated:**

| Node Type | Example Actions |
|-----------|-----------------|
| Server | restart, logs, health, stop |
| Document | read, edit, related, history |
| Module | run, configure, test, security scan |
| Person (CRM) | email, call log, deals, notes |
| Campaign | execute, pause, metrics, edit |

**Input modalities:**
- Visual (click/drag)
- Text (search/command)
- Voice (speak commands)

## Design Principles

### Intent-Aware
Agents are smart, fast, and subtly wrong. We handle this by:
- **Ask before acting** when intent is ambiguous
- **Crystallize over time** rather than demanding precision upfront
- **Explicit artifacts** for goals, constraints, trade-offs
- **Checkpoints** separating interpretation from execution

### Composable
Everything is a building block:
- Modules compose into workflows
- Actions compose into automations
- Nodes compose into views
- Agents compose into teams

### Agent-First
AI agents are the primary consumers AND builders:
- APIs designed for programmatic access
- Everything discoverable and queryable
- Skills written by agents, for agents
- Compounding improvement through operation

## Technical Stack

| Layer | Technology |
|-------|------------|
| Database | PostgreSQL + pgvector |
| Cache | Redis |
| Events | NATS JetStream |
| Backend | FastAPI + SQLAlchemy |
| Frontend | React + TypeScript + Vite |
| Containers | Docker + Dagger |
| AI | Claude, GPT-4, Gemini, local models |

## Ports (Development)

| Service | Port |
|---------|------|
| Backend API | 8000 |
| Main Frontend | 3000 |
| Hub Frontend | 9000 |
| PostgreSQL | 5432 |
| Redis | 6379 |
| NATS | 4222 |
