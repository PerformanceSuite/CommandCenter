---
name: infrastructure-decisions
description: Guidelines for choosing between infrastructure approaches (Dagger vs YAML, programmatic vs declarative). Use during design phases when containerization, CI/CD, or orchestration decisions are needed.
---

# Infrastructure Decision Guidelines

Choose the right tool for infrastructure needs.

## Dagger vs Docker Compose

### Use Dagger When:

- **Custom images with extensions** (Postgres + pgvector + ParadeDB)
- **Testing matrices** (test against multiple backends/versions)
- **Programmatic orchestration** (start/stop services via code)
- **Dynamic configuration** (parameters determined at runtime)
- **CI/CD pipelines** (reproducible builds across environments)

### Use docker-compose.yml When:

- **Static service definitions** (standard images, fixed config)
- **Simple local development** (just need services running)
- **No customization needed** (vanilla Postgres, Redis, etc.)
- **Team familiarity** (everyone knows compose)

## Quick Decision Tree

```
Need custom image with extensions?
  YES → Dagger
  NO ↓

Need testing matrix (multiple backends)?
  YES → Dagger
  NO ↓

Need programmatic control (start/stop via API)?
  YES → Dagger
  NO ↓

Just need services running for dev?
  → docker-compose.yml
```

## Dagger Quick Reference

```python
# Basic pattern
import dagger

async with dagger.Connection() as client:
    postgres = (
        client.container()
        .from_("postgres:16")
        .with_env_variable("POSTGRES_PASSWORD", "secret")
        .with_exposed_port(5432)
    )
    service = postgres.as_service()
```

**Key patterns:**
- `container().from_()` - Base image
- `.with_exec()` - Run commands (for custom builds)
- `.with_env_variable()` - Set env vars
- `.as_service()` - Convert to running service
- Order operations from least-changing to most-changing (caching)

## Project Examples

| Project | Approach | Reason |
|---------|----------|--------|
| CommandCenter Hub | Dagger | Orchestrates multiple CC instances programmatically |
| KnowledgeBeast tests | Dagger | Test matrix: ChromaDB vs Postgres backends |
| Local dev environment | Compose | Just need Postgres + Redis running |
| CI/CD pipeline | Dagger | Reproducible across local/CI |

## References

For detailed Dagger implementation patterns, see:
- `docs/UNIVERSAL_DAGGER_PATTERN.md` in CommandCenter
- Dagger docs: https://docs.dagger.io/
