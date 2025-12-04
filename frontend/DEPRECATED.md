# DEPRECATED

> **Warning**: This directory contains legacy code that is being migrated to `hub/frontend/`.

## Migration Status

| Component | Target Location | Status |
|-----------|-----------------|--------|
| Pages | `hub/frontend/src/pages/` | Partial |
| Components | `hub/frontend/src/components/` | Partial |
| Hooks | `hub/frontend/src/hooks/` | Partial |
| Services | `hub/frontend/src/services/` | Partial |

## For New Development

**Do NOT add new features to this directory.**

Instead, use:
- `hub/frontend/` - React UI application
- `hub/core/ui/` - Shared React components (future)

## What's Still Active

Some code in this directory may still be referenced:

1. **Dashboard Components** - Legacy dashboard views
2. **Settings Pages** - Configuration UI
3. **API Client** - Axios wrapper

## Migration Plan

1. Audit component usage
2. Create equivalents in `hub/frontend/`
3. Update routing and imports
4. Remove legacy components
5. Archive directory

## Timeline

- **Target**: Q1 2025
- **Blocker**: Hub frontend feature parity
- **Tracking**: See `docs/plans/` for migration plans

---

*Deprecated: 2025-12-03*
*See: docs/ARCHITECTURE.md for current structure*
