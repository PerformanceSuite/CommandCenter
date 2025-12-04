# DEPRECATED

> **Warning**: This directory contains legacy code that is being migrated to `hub/`.

## Migration Status

| Component | Target Location | Status |
|-----------|-----------------|--------|
| API Routes | `hub/backend/app/routers/` | Partial |
| Services | `hub/backend/app/services/` | Partial |
| Models | `hub/backend/app/models/` | Partial |
| Schemas | `hub/backend/app/schemas/` | Partial |

## For New Development

**Do NOT add new features to this directory.**

Instead, use:
- `hub/backend/` - FastAPI backend services
- `hub/orchestration/` - Agent workflow engine
- `hub/core/api/` - Shared API utilities (future)

## What's Still Active

Some code in this directory is still in active use:

1. **RAG Service** - Being refactored to use KnowledgeBeast
2. **Graph Indexer** - Python AST parsing utilities
3. **GitHub Integration** - Repository syncing

## Migration Plan

1. Identify active code paths
2. Create equivalents in `hub/`
3. Update imports/references
4. Mark as fully deprecated
5. Archive or remove

## Timeline

- **Target**: Q1 2025
- **Blocker**: Hub backend feature parity
- **Tracking**: See `docs/plans/` for migration plans

---

*Deprecated: 2025-12-03*
*See: docs/ARCHITECTURE.md for current structure*
