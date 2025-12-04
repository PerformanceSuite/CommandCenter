# Hub Modules

This directory contains feature modules for the CommandCenter Hub application.

## Structure (Target)

```
modules/
├── vislzr/           # Visualization module (planned migration)
├── orchestration/    # Agent workflow engine (planned migration)
├── observability/    # Metrics and monitoring (planned migration)
└── graph/            # Code graph service (future)
```

## Current Status

**Migration Status**: PLANNED

The following modules are candidates for migration into this directory:

| Module | Current Location | Migration Status |
|--------|------------------|------------------|
| vislzr | `hub/vislzr/` | Planned |
| orchestration | `hub/orchestration/` | Planned |
| observability | `hub/observability/` | Planned |

## Migration Plan

1. **Phase 1**: Create symlinks for backward compatibility
2. **Phase 2**: Update import paths across codebase
3. **Phase 3**: Move files to new locations
4. **Phase 4**: Remove symlinks, update documentation

## Why This Structure?

- **Clear Feature Boundaries**: Each module is self-contained
- **Easier Testing**: Modules can be tested in isolation
- **Better Discoverability**: Logical grouping of related functionality
- **Future Scaling**: Easy to add new modules or extract to separate repos

---

*Created: 2025-12-03*
*Part of: Comprehensive Audit & Reorganization*
