# Hub Modules

This directory contains feature modules for the CommandCenter Hub application.

## Structure

```
modules/
├── mrktzr/           # AI Marketing & Partnership Intelligence (ACTIVE)
├── vislzr/           # Visualization module (planned migration)
├── orchestration/    # Agent workflow engine (planned migration)
├── observability/    # Metrics and monitoring (planned migration)
└── graph/            # Code graph service (future)
```

## Active Modules

### MRKTZR

**AI Marketing and Partnership Intelligence** - Automates marketing execution and partnership development.

| Feature | Status | Description |
|---------|--------|-------------|
| Content Generation | Prototype | AI-powered social media posts via Genkit/Gemini |
| Social Scheduling | Planned | Cross-platform post scheduling |
| Analytics | Planned | Engagement tracking and optimization |
| CC Integration | In Progress | Knowledge API + Event Bus connection |

**Quick Start**:
```bash
cd hub/modules/mrktzr
npm install
npm run dev  # Runs on port 3003
```

See [mrktzr/README.md](mrktzr/README.md) for full documentation.

## Planned Migrations

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

## Module Integration Pattern

All modules follow the CommandCenter integration pattern:

```
┌─────────────────┐     ┌─────────────────┐
│  CommandCenter  │────▶│   Module API    │
│   (Knowledge)   │     │   (Express)     │
└─────────────────┘     └─────────────────┘
        │                       │
        ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│  NATS JetStream │◀───▶│  Module Events  │
│   (Event Bus)   │     │                 │
└─────────────────┘     └─────────────────┘
```

---

*Updated: 2025-12-04*
*Part of: CommandCenter Hub*
