# Concept Index

**Last Updated**: 2026-01-02

## Active Concepts

### Wander System
- [Wander](./Wander.md) - Long-running exploratory agent for idea discovery (concept overview)
- [Wander Technical Spec](./Wander-TechSpec.md) - Database schema, API endpoints, algorithms
- [Fractal Security](./FractalSecurity.md) - Perceptual access control for autonomous agents (experimental)

### Business Platforms
- [Veria](./Veria.md) - Financial intelligence platform
- [MRKTZR](./MRKTZR.md) - Market analysis tools
- [ROLLIZR](./ROLLIZR.md) - Business rollup platform
- [Fractlzr](./Fractlzr.md) - Fractal visualization system

## Implementation Plans

See [docs/plans/](../plans/) for detailed implementation plans:
- [2026-01-02-wander-mindmap-implementation.md](../plans/2026-01-02-wander-mindmap-implementation.md) - Phase 0 mind map UI

## Concept Relationships

```
CommandCenter
├── Wander (exploration/discovery)
│   ├── Uses: KnowledgeBeast (vectors), VISLZR (visualization)
│   ├── Produces: Crystals (insights) for Veria
│   ├── Security: Fractal encoding for economic actions
│   └── Phases: 0 (UI) → 1-5 (engine) → 6-7 (integration) → 8 (fractal)
├── Veria (financial intelligence)
│   └── Consumes: Wander crystals, market data
├── MRKTZR (market tools)
├── ROLLIZR (business rollup)
└── Fractlzr (visualization)

Fractal Security ←──── Novel research direction
└── Enables: Autonomous economic agents with wallet privileges
└── Status: Experimental, needs feasibility experiments
```

## Document Status

| Document | Status | Last Updated |
|----------|--------|--------------|
| Wander.md | ✅ Complete | 2026-01-02 |
| Wander-TechSpec.md | ✅ Complete | 2026-01-02 |
| FractalSecurity.md | 🧪 Experimental | 2026-01-02 |
| Veria.md | 📝 Draft | - |
| MRKTZR.md | 📝 Draft | - |
| ROLLIZR.md | 📝 Draft | - |
| Fractlzr.md | 📝 Draft | - |
