# Phase 9 — Federation & Ecosystem Mode Implementation Blueprint

**Objective:** Federate multiple project instances (Veria, Performia, ROLLIZR, etc.) into a global, queryable ecosystem graph and expose a VISLZR "Ecosystem Mode" for cross-project insight and control — without breaking instance isolation.

---

## 0) Operating Model

- **Meta Hub (Global):** The existing hub-prototype running in `--scope=meta` mode acts as *observer + launcher*.
- **Project Instances:** Each project runs its own hub in `--scope=project` mode with isolated mesh namespace and graph schema.
- **Federation:** Meta Hub maintains a minimal catalog of projects and aggregates read-only projections (metrics + selected edges) from each instance.

```
[Meta Hub]  ──reads──▶  [Project Hub: Veria]
             └────────▶  [Project Hub: Performia]
             └────────▶  [Project Hub: ROLLIZR]
```

Isolation contract: **Writes** (actions, audits) remain per-instance unless explicitly routed through Federation Actions.

---

## 1) Data Model & Storage

Use a thin **Federation DB** (schema: `commandcenter_fed`) that stores *only* cross-project metadata and summaries.

### 1.1 Tables (Prisma)
- `ProjectCatalog(id, slug, name, status, hubUrl, meshNs, lastSeenAt)`
- `ProjectMetric(id, projectId, key, valueNumber?, valueText?, observedAt)`
- `IntegrationEdge(id, fromProjectId, toProjectId, kind, source, strength, detailsJson)`
- `SurfaceEndpoint(id, projectId, type, url, authKind, lastVerifiedAt)`
- `EcosystemAlert(id, projectId?, severity, title, description, createdAt, status)`

> Instance graphs remain inside each project’s own DB/schema. Federation DB is never a source of truth for code-level nodes.

---

## 2) Mesh Subjects & Discovery

### 2.1 Heartbeat / Presence (from Project Hubs)
- `hub.presence.<hubId>` → `{ projectSlug, meshNs, hubUrl, version, tools[], capabilities[] }`
- `hub.health.<hubId>` → `{ status, latencyMs, degradedReasons[], sampleAt }`

### 2.2 Metrics & Summaries (project → meta)
- `graph.summary.nodes` → `{ projectSlug, counts: { files, symbols, tasks, audits }, ts }`
- `audit.summary.status` → `{ projectSlug, ok, warn, fail, lastRun }`
- `security.summary.status` → `{ projectSlug, vulnsCritical, vulnsHigh, lastScan }`
- `deploy.summary.status` → `{ projectSlug, envs: [dev, staging, prod], versions[], lastDeployedAt }`

### 2.3 Integration Hints
- `integration.edge` → `{ fromProject, toProject, kind[api|queue|shared-schema|secret], strength[0..1], proof:{…} }`

The Meta Hub subscribes to `*.summary.*` and `integration.edge` across all namespaces.

---

## 3) Federation Services (Meta Hub)

### 3.1 Catalog Service
- Maintains `ProjectCatalog` from presence/health signals.
- Verifies `SurfaceEndpoint` (e.g., Graph-Service GraphQL, TaskGraph REST) periodically.

### 3.2 Aggregator Service
- Reduces summary events into `ProjectMetric` rows.
- Derives **risk scores** (e.g., security risk, compliance debt) with simple formulas (v1).

### 3.3 Integration Resolver
- Learns `IntegrationEdge` from hints + manual declarations in `projects.yaml`.
- De-duplicates edges; maintains `strength` and `detailsJson` provenance.

### 3.4 Federation API (read-only)
Expose from Meta Hub:
- `GET /api/fed/projects` → catalog + headline metrics
- `GET /api/fed/graph` → minimal ecosystem node+edge model (projects + integrations)
- `GET /api/fed/metrics/:project` → timeseries (for overlays)
- `GET /api/fed/alerts` → ecosystem alerts

Auth: Meta API key; optional OIDC for UI.

---

## 4) VISLZR — Ecosystem Mode

### 4.1 UX
- **Topology view:** Each project is a node; edges show integrations.
- **Node card:** KPIs (health, audits OK/WARN/FAIL, deploy freshness), quick actions ("Open Instance", "Run Global Security Sweep" → fan-out per instance).
- **Overlays:** Risk heatmap, compliance posture, deployment staleness.
- **Filters:** Domain (Finance/Creative/Infra), status, tags, teams.

### 4.2 Data Flow
VISLZR (meta) queries `GET /api/fed/graph` and `GET /api/fed/projects` and renders. Per-project deep-dives open that instance’s VISLZR in a new pane/window.

### 4.3 Ecosystem Actions (fan-out)
- `fed.audit.security.sweep` → emit `audit.requested.security` into **each** project’s mesh (if permissioned).
- `fed.refresh.summaries` → broadcast `graph.summary.requested` to all.

Safety: Actions are disabled by default; require per-project allowlist.

---

## 5) Config & Conventions

`/config/projects.yaml` (in Meta Hub repo):
```yaml
projects:
  - slug: veria
    name: Veria
    hubUrl: http://127.0.0.1:5401
    meshNs: veria.mesh
    tags: [finance, compliance]
    allowFanout: [audit.security, graph.refresh]
  - slug: performia
    name: Performia
    hubUrl: http://127.0.0.1:5402
    meshNs: performia.mesh
    tags: [creative, realtime]
```

Per-project instance exports a small capability manifest at `GET /api/capabilities`:
```json
{
  "project": "veria",
  "tools": ["vislzr", "vault", "compliance"],
  "endpoints": {"graph": "/api/graph", "task": "/api/task"},
  "events": ["graph.summary.nodes", "audit.summary.status"],
  "version": "0.9.0"
}
```

---

## 6) CLI & Scripts

Add to Meta Hub `package.json`:
```json
{
  "scripts": {
    "fed:serve": "tsx ./services/fed/server.ts",
    "fed:verify": "tsx ./services/fed/verify-endpoints.ts",
    "fed:refresh": "tsx ./services/fed/refresh.ts",
    "fed:vislzr": "next dev -p 5500 -r ./tools/vislzr-meta"
  }
}
```

Project Instance additions:
```json
{
  "scripts": {
    "summary:emit": "tsx ./scripts/emit-summaries.ts",
    "summary:health": "tsx ./scripts/emit-health.ts",
    "summary:integrations": "tsx ./scripts/emit-integrations.ts"
  }
}
```

---

## 7) Endpoints — Minimal Schemas

### 7.1 `GET /api/fed/projects`
```ts
 type FedProject = {
   slug: string;
   name: string;
   status: 'online'|'offline'|'degraded';
   lastSeenAt: string;
   hubUrl: string;
   tags: string[];
   kpis: {
     auditsOk: number; auditsWarn: number; auditsFail: number;
     deployFreshnessDays: number; healthLatencyMs: number;
   };
 }
```

### 7.2 `GET /api/fed/graph`
```ts
 type EcosystemGraph = {
   nodes: { id: string; label: string; tags: string[]; risk: number }[];
   edges: { id: string; from: string; to: string; kind: string; strength: number }[];
 }
```

---

## 8) Security & Isolation

- **Read-only by default:** Federation API never writes into project DBs.
- **Fan-out actions:** Require explicit allowlist per project; signed with `MESH_HMAC_KEY` and validated per instance.
- **Secrets:** No secrets leave instances; only metrics/summaries flow to meta.
- **Network:** Meta Hub connects to instance endpoints via mTLS (future) or IP allowlist in local dev.

---

## 9) Implementation Steps

### 9.1 Meta Hub
1) **DB**: Add `commandcenter_fed` schema + Prisma models.
2) **Services**: Implement `catalog`, `aggregator`, `integration-resolver`.
3) **API**: Expose `/api/fed/projects`, `/api/fed/graph`, `/api/fed/metrics/:project`, `/api/fed/alerts`.
4) **NATS**: Subscribe to `*.summary.*`, `hub.presence.*`, `hub.health.*`, `integration.edge` across namespaces.
5) **Verifier**: Poll instance `GET /api/capabilities` + known endpoints; update `SurfaceEndpoint`.

### 9.2 Project Instances (template changes)
1) Emit summary events on interval (60–120s) via `scripts/emit-summaries.ts`.
2) Serve `GET /api/capabilities` with tool list + endpoints.
3) (Optional) Emit `integration.edge` events from configured sources (e.g., gateway proxy logs, shared schema references).

### 9.3 VISLZR (meta tool)
1) New route: `/ecosystem` (Ecosystem Mode).
2) Graph rendering (projects as nodes, `IntegrationEdge` as edges).
3) Node cards + quick actions; overlays for risk, compliance, freshness.

---

## 10) Acceptance Criteria

- From Meta VISLZR:
  1. See all **online** projects with KPIs and last-seen timestamps.
  2. Toggle overlays (Risk, Compliance, Freshness) and see edges filter by strength.
  3. Click **Open Instance** → deep-link into project VISLZR.
  4. Trigger **Global Security Sweep** (if allowed) → observe fan-out events; each instance registers an `Audit` run.

- From CLI:
  - `pnpm fed:verify` reports reachable endpoints and summarizes capabilities.
  - `pnpm fed:refresh` pulls latest metrics into `ProjectMetric`.

Performance:
- Ecosystem graph renders < 300ms for ≤ 50 projects.
- Metric aggregation windowing prevents DB bloat (TTL 30 days by default).

---

## 11) Observability

- OTel spans: `fed.catalog.update`, `fed.aggregate.metrics`, `fed.verify.endpoint`.
- Grafana dashboard: online projects, risk heatmap, last audit sweep times.
- Alerts: create `EcosystemAlert` for offline projects (>10m), and for security failure spikes.

---

## 12) Deliverables Checklist

- [ ] Prisma models + migrations for Federation DB
- [ ] NATS subscriptions in Meta Hub
- [ ] Aggregator + Catalog services
- [ ] Federation API (read-only)
- [ ] Instance capability endpoint + summary emitters
- [ ] VISLZR Ecosystem Mode UI
- [ ] CLI scripts (`fed:*`, `summary:*`)
- [ ] Docs: `/docs/phase9-federation.md`

---

## 13) Rollout Plan

1) Enable Meta Hub in dev alongside 2–3 project instances.
2) Verify presence, summaries, and ecosystem graph rendering.
3) Roll out fan-out actions with a single allowed action (`graph.refresh`) and audit logging.
4) Gradually allow `audit.security` sweep after guardrails verified.

> Phase 9 ships a safe, read-first federation with optional controlled write-through actions — unlocking the global view without compromising per-project isolation.
