# MRKTZR — Improvement Plan (Execution Layer)

- **Service modularization** (NestJS or FastAPI): `content-svc`, `persona-svc`, `scheduler-svc`, `channels-svc`, `analytics-svc`, `compliance-svc`.
- **Experimentation/A-B/n**: Bayesian bandits per channel; automatic winner promotion.
- **Creative Knowledge Graph**: Content ↔ Persona ↔ Topic ↔ Campaign ↔ Outcome (CTR/watchtime/CVR), Postgres + pgvector.
- **Observability**: OpenTelemetry traces from generation → moderation → publish → metrics ingest; Prometheus/Grafana dashboards.
- **DX**: `make` tasks, Docker, `.env` templates, e2e channel simulators, seed data.

See the `02_TECH_BLUEPRINT/` for concrete contracts and infra.
