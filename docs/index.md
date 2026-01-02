# CommandCenter

**An AI Operating System for Knowledge Work**

CommandCenter is a self-improving intelligence substrate where discoveries feed improvements, which enable better discoveries. It's not a collection of tools—it's a unified system that gets smarter through its own operation.

## The Core Cycle

```
DISCOVER → VALIDATE → IMPROVE → DISCOVER...
```

Every module in CommandCenter participates in this cycle. The system runs whether or not a human is watching.

## Interfaces

CommandCenter has three interfaces to the same underlying system:

| Interface | For | How |
|-----------|-----|-----|
| **VISLZR** | Humans | Visual mind map with interactive nodes, voice input |
| **API** | Agents | REST endpoints, MCP tools, programmatic access |
| **CLI** | Developers | Command-line tools for development and ops |

**VISLZR** is the primary human interface. Everything in CommandCenter—modules, docs, servers, concepts—appears as interactive nodes. Each node has contextual actions (read, run, configure, restart, etc.) generated based on what it represents.

## Modules

| Module | Purpose | Cycle Phase |
|--------|---------|-------------|
| [Wander](modules/wander.md) | Exploration, idea discovery, pattern finding | DISCOVER |
| [Research Hub](modules/research-hub.md) | R&D task tracking, research management | DISCOVER |
| [AI Arena](modules/ai-arena.md) | Multi-model debate, hypothesis validation | VALIDATE |
| [KnowledgeBeast](modules/knowledge-beast.md) | Vector store, RAG, knowledge graph | ALL |
| [MRKTZR](modules/mrktzr.md) | Marketing, CRM, partnerships | ACTION |
| [ROLLIZR](modules/rollizr.md) | Rollup intelligence, consolidation opportunities | DISCOVER |
| [Veria](modules/veria.md) | Financial intelligence, prediction markets | VALIDATE/ACTION |
| [Fractlzr](modules/fractlzr.md) | Fractal encoding, perceptual security | SECURITY |

## Quick Links

- [Architecture](architecture.md) - How it all connects
- [Getting Started](guides/getting-started.md) - Installation and first run
- [API Reference](reference/api.md) - Endpoint documentation
- [Roadmap](roadmap.md) - Where we're going

## Current Status

- **Phase**: Loop Phase 1 - Connect What Exists (20%)
- **Priority**: Wander Phase 0 Mind Map UI
- **Test Suite**: 995 passing, 137 failing
