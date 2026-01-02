# Concept Index

**Last Updated**: 2026-01-02

## Active Concepts

### System Architecture
- [Unified Architecture](./UnifiedArchitecture.md) - **START HERE** - How all components work together as one AI OS

### Design Principles
- [Intent-Aware Agents](./IntentAware.md) - Framework for reliable agent intent (crystallization, disambiguation, verification)

### Wander System (Exploration & Discovery)
- [Wander](./Wander.md) - Long-running exploratory agent for idea discovery
- [Wander Technical Spec](./Wander-TechSpec.md) - Database schema, API endpoints, algorithms
- [Fractal Security](./FractalSecurity.md) - Perceptual access control for autonomous agents

### Intelligence & Action (Veria Ecosystem)
- [Real-Time Intelligence Engine](./RealTimeIntelligence.md) - Information gathering, prediction markets as signals
- [Veria](./Veria.md) - Financial intelligence platform, prediction market trading

### Business Platforms
- [MRKTZR](./MRKTZR.md) - Market analysis and distribution tools
- [ROLLIZR](./ROLLIZR.md) - Business rollup platform
- [Fractlzr](./Fractlzr.md) - Fractal visualization system

## Implementation Plans

See [docs/plans/](../plans/) for detailed implementation plans:
- [2026-01-02-wander-mindmap-implementation.md](../plans/2026-01-02-wander-mindmap-implementation.md) - Phase 0 mind map UI

## System Relationships

```
┌─────────────────────────────────────────────────────────────────────┐
│                    COMMANDCENTER ECOSYSTEM                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  DISCOVERY LAYER                                                     │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Wander ──────────────────────────────────────────────────┐ │   │
│  │  • Explores idea space                                    │ │   │
│  │  • Produces Crystals (validated insights)                 │ │   │
│  │  • Uses KnowledgeBeast, VISLZR                            │ │   │
│  └───────────────────────────────────────────────────────────┼─┘   │
│                                                               │      │
│  INTELLIGENCE LAYER                                           ▼      │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Real-Time Intelligence Engine                              │   │
│  │  • Polymarket, HackerNews, arXiv, SEC                       │   │
│  │  • Feeds signals to Wander                                  │   │
│  │  • Validates Crystals against market prices                 │   │
│  └──────────────────────────────────┬──────────────────────────┘   │
│                                      │                              │
│  ACTION LAYER                        ▼                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Veria                                                       │   │
│  │  • Trades on prediction markets (Polymarket)                 │   │
│  │  • Information arbitrage from Wander Crystals                │   │
│  │  • Compliance & trust layer for regulated assets             │   │
│  └──────────────────────────────────┬──────────────────────────┘   │
│                                      │                              │
│  SECURITY LAYER                      ▼                              │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │  Fractal Security                                            │   │
│  │  • Encodes trade proposals as fractals                       │   │
│  │  • Only authorized agents can decode                         │   │
│  │  • Audit trail embedded in visual record                     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                      │
│  DISTRIBUTION LAYER                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐              │
│  │   MRKTZR     │  │   ROLLIZR    │  │   Fractlzr   │              │
│  │  Marketing   │  │   Rollups    │  │   Visuals    │              │
│  └──────────────┘  └──────────────┘  └──────────────┘              │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘

Data Flow:
  Signals → Wander → Crystals → Veria → Trades → Revenue
     ↑                                              │
     └──────────── Feedback Loop ──────────────────┘
```

## Value Chain

```
Information Sources (Polymarket, HackerNews, arXiv, SEC, etc.)
         │
         ▼
Real-Time Intelligence Engine (signal processing, anomaly detection)
         │
         ▼
Wander (divergent exploration, pattern discovery)
         │
         ▼
Crystals (validated insights with confidence scores)
         │
         ▼
Veria Trading (information arbitrage on prediction markets)
         │
         ▼
Revenue (trading profits fund further development)
         │
         ▼
Compounding: Better models → Better signals → Better trades → More revenue
```

## Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| IntentAware.md | ✅ Complete | 2026-01-02 |
| Wander.md | ✅ Complete | 2026-01-02 |
| Wander-TechSpec.md | ✅ Complete | 2026-01-02 |
| FractalSecurity.md | 🧪 Experimental | 2026-01-02 |
| RealTimeIntelligence.md | ✅ Complete | 2026-01-02 |
| Veria.md | ✅ Updated | 2026-01-02 |
| MRKTZR.md | 📝 Draft | - |
| ROLLIZR.md | 📝 Draft | - |
| Fractlzr.md | 📝 Draft | - |
