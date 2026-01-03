# Roadmap

## Current Phase: Connect What Exists

**Status**: 45% complete

We're connecting existing components into a coherent system before building new features.

### Active Work
- [x] Document Intelligence backend (graph entities, ingestion API)
- [x] Document Intelligence agent personas (5 YAML files)
- [x] Sprint 4: Real-time Subscriptions (SSE)

### This Week
- [ ] End-to-end test: Document Intelligence pipeline
- [ ] Wire KnowledgeBeast → Document Intelligence pipeline
- [ ] VISLZR Sprint 3: Agent parity

### This Month
- [ ] VISLZR Sprint 3: Agent parity
- [ ] Voice input prototype
- [ ] Phase 3 skill improvements (5 PRs pending)

### This Quarter
- [ ] Wander crystallization
- [ ] MRKTZR CRM foundation
- [ ] Veria Polymarket integration

## Implementation Phases

### Phase 1: Connect What Exists (Current)
- Wire existing modules together
- Unified data flow through KnowledgeBeast
- VISLZR as primary human interface

### Phase 2: Close the Loop (Q1-Q2 2026)
- Wander → AI Arena → Prompt Improver flow
- Automatic improvement from operation
- Skills written back by agents

### Phase 3: Accelerate (Q2-Q3 2026)
- Background operation (runs while you sleep)
- Multi-agent coordination
- Self-healing infrastructure

### Phase 4: Economic Action (Q3-Q4 2026)
- Veria trading live
- MRKTZR campaigns autonomous
- Revenue generation

### Phase 5: Train the Substrate (2026-2027)
- Custom model training (nanochat-inspired)
- The Loop trains the models it runs on
- True self-improvement

## Module Status

| Module | Status | Priority |
|--------|--------|----------|
| KnowledgeBeast | ✅ Working | Maintenance |
| AI Arena | ✅ Working | Maintenance |
| Research Hub | ✅ Working | Maintenance |
| Wander | 📋 Designed | **HIGH** |
| VISLZR | 🔄 Partial | **HIGH** |
| MRKTZR | 📋 Planned | Medium |
| ROLLIZR | 📋 Planned | Medium |
| Veria | 📋 Planned | Medium |
| Fractlzr | 🧪 Experimental | Low |

**Legend**: ✅ Working | 🔄 In Progress | 📋 Planned | 🧪 Experimental

## Technical Debt

- [ ] Consolidate service/repository patterns
- [ ] Complete test suite (currently 1700+ pass)
- [x] Graph Service completion
- [ ] Federation service activation

## Recently Completed

- ✅ **Sprint 4: Real-time Subscriptions** (Jan 3, 2026)
  - SSE endpoint: `backend/app/routers/sse.py`
  - Subscription manager: `backend/app/services/subscription_manager.py`
  - Frontend hooks: `useGraphSubscription`, `useRealtimeGraph`
  - UI integration with live connection status
- ✅ **Document Intelligence Pipeline** (Jan 2, 2026)
  - Graph entity types: `GraphDocument`, `GraphConcept`, `GraphRequirement`
  - Ingestion API: `POST /api/v1/graph/document-intelligence/ingest`
  - 15 integration tests
  - Pipeline template YAML
- ✅ **Skills Integration** - Moved 6 skills into CommandCenter repo
- ✅ **Linting Cleanup** - Fixed 49 linting errors across backend
- ✅ **App Factory Refactor** - `create_app()` with comprehensive docstring
- ✅ TheLoop architecture defined
- ✅ AI Arena multi-model debate working
- ✅ Settings and provider configuration
- ✅ LLM Gateway with cost tracking
