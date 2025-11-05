# Phase 7–8: Graph‑Service + VISLZR Integration Plan (CommandCenter)

**Goal**: Deliver a VISLZR‑style interactive mind map of each project and the full ecosystem, fed by live Graph/Task data, with clickable nodes that trigger code reviews, security checks, health probes, and build/deploy automations.

---

## 0) High‑Level Architecture

```
┌─────────────┐      ┌───────────────────┐      ┌───────────────────────┐
│ Repos/Files │ ───▶ │ Ingestion Pipelines│ ───▶ │ Graph‑Service (Prisma) │
└─────────────┘      └───────────────────┘      └───────────┬───────────┘
       ▲                         ▲                           │
       │                         │                           │
       │                  ┌──────┴──────┐                    │
       │                  │ TaskGraph    │ ◀───── MCP Agents │
       │                  │ (Tasks/Plans)│                    │
       │                  └──────┬──────┘                    │
       │                         │                           │
       │     ┌───────────────────┴──────────────────┐        │
       └────▶│ NATS Mesh (hub.presence / hub.health)│◀───────┘
             └───────────────┬──────────────────────┘
                             │
                     ┌───────┴────────┐
                     │ VISLZR Frontend │  (React/Next + Tailwind + Framer)
                     └─────────────────┘
```

- **Graph‑Service**: Canonical knowledge graph (code entities, services, dependencies, specs) stored via Prisma ORM.
- **TaskGraph‑Service**: Planned and in‑flight work (PRDs, TODOs, blueprints, issues) mapped to graph nodes.
- **NATS Mesh**: Presence, health, audit results, and action execution events.
- **VISLZR**: Real‑time visualization + control surface.

---

## 1) Data Model (Prisma)

> One database (schema `commandcenter_graph`) with two logical modules: `graph` and `tasks`.

### 1.1 Core Entities
- `Project(id, name, rootPath, repoUrl, status)`
- `Repo(id, projectId, provider, defaultBranch)`
- `File(id, repoId, path, lang, hash, size, lastIndexedAt)`
- `Symbol(id, fileId, kind[Module|Class|Function|Type|Var|Test], name, signature, rangeStart, rangeEnd, exports:boolean)`
- `Dependency(id, fromSymbolId, toSymbolId, type[import|call|extends|uses])`
- `Service(id, projectId, name, type[api|job|db|queue|mcp|mesh], endpoint, healthUrl)`
- `Event(id, subject, payloadJson, createdAt)` — mirror of select NATS events for queryability.
- `SpecItem(id, projectId, source[file|doc|canvas], ref, title, description, priority, status[planned|inProgress|done|blocked])`
- `Task(id, projectId, specItemId?, title, description, status, assignee, kind[feature|bug|chore|review|security], labels, createdAt, updatedAt)`
- `Link(id, fromEntity, fromId, toEntity, toId, type)` — generic typed edges (e.g., File→SpecItem, Service→Repo, Task→Symbol).
- `HealthSample(id, serviceId, status[up|down|degraded], latencyMs, detailsJson, observedAt)`
- `Audit(id, targetEntity, targetId, kind[codeReview|security|license|compliance], status[pending|ok|warn|fail], summary, reportPath, createdAt)`

### 1.2 Derived / Virtual Nodes
- **GhostNode** (not stored as a table): materialized view from `SpecItem`/`Task` where no backing `File`/`Symbol` exists.
- **Cluster**: visualization group (by folder, service, domain, or tag) computed at query time.

---

## 2) Ingestion Pipelines

### 2.1 Repo Indexer (CLI + Worker)
- Scan repo roots; parse AST per language (TS/JS, Go, Rust, Python, SQL, JSON/YAML).
- Emit `File`, `Symbol`, and `Dependency` upserts.
- Extract `TODO|FIXME|@planned|@spec` comments into `SpecItem` or link to existing.
- Store artifact hashes for incremental runs.

**CLI**: `pnpm graph:ingest --project <id> [--since <git-ref>] [--lang ts,py]`

### 2.2 MCP / Tool Adapters
- Codex/LLM review agent → writes `Audit` rows (and report artifact paths).
- SCA/SAST (Snyk/semgrep/trivy) adapters → `Audit(kind=security|license)`.
- Test runners (Vitest/Jest/Go test) → map to `Task(kind=review)` plus `Audit` w/ pass/fail.

### 2.3 Mesh Signals
- `hub.presence.<hubId>` → links `Service` and updates status.
- `hub.health.<hubId>` → `HealthSample` rows.
- `audit.result.*` → completes `Audit` records.

---

## 3) Graph‑Service API

Expose both **GraphQL** (for VISLZR) and **REST** (for tools/CLIs). All endpoints gated by API key (mesh‑internal) + signed HMAC.

### 3.1 Queries
- `projectGraph(projectId, depth?, filters?)` → returns nodes/edges (Files, Symbols, Services, Tasks, SpecItems, Health, Audits).
- `dependencies(symbolId, direction, depth)`
- `ghostNodes(projectId, filters?)`
- `search(query, scope)` — code + spec + task unified search.

### 3.2 Mutations / Actions
- `triggerAudit(targetEntity, targetId, kind)` → emits `audit.requested` on NATS.
- `createTask(specItemId?, title, kind, labels)`
- `link(fromEntity, fromId, toEntity, toId, type)`
- `refreshProject(projectId, modes[])` (reindex, health, audits)

**NATS Subjects**
- `audit.requested.<kind>`
- `audit.result.<kind>`
- `graph.ingest.requested` / `graph.ingest.completed`
- `hub.presence.*` / `hub.health.*`

---

## 4) VISLZR Frontend (Phase 8)

### 4.1 Stack
- **Next.js 14**, **React 18**, **Zustand**, **Tailwind**, **Framer Motion**.
- Layout engine: **elkjs** (layered) + **force simulation** for decluttering.
- Virtualization: canvas/WebGL rendering for >10k nodes (pixi.js optional).

### 4.2 Node/Edge Taxonomy
- **Node types**: Project, Repo, Folder, File, Symbol (module/class/function), Service, SpecItem, Task, Audit, HealthSample, GhostNode.
- **Edge types**: contains, imports, calls, dependsOn, implements, plannedFor, satisfies, observedBy, producedBy.

### 4.3 Visual Semantics
- Color by **category** (code/design/infra/ai/compliance).
- Border by **state**: ✅ implemented, 🟡 in progress, 🔴 missing (ghost), ⚠️ failing audit, 🧪 test‑failing.
- Badges: coverage %, open tasks count, recent health status.
- Filters: scope by service, folder, filetype, risk, owner, label.
- Time slider: show deltas (last 24h/7d) with animatable transitions.

### 4.4 Interactions
- Click node → **Action Drawer** with tabs: *Overview, Code, Tasks, Audits, Health, Links*.
- One‑click actions:
  - **Run Code Review** → `audit.requested.codeReview`
  - **Run Security Check** → `audit.requested.security`
  - **Open in Editor** (VS Code URL, local file path)
  - **Generate Implementation** (for GhostNode → scaffold via Codex/CLI)
  - **Create Task** (prepopulates with context)
- Multi‑select: bulk audits or refactor plans.

### 4.5 UX Details
- Breadcrumbs + mini‑map.
- Progressive disclosure (cluster→expand→file→symbol).
- Pin/focus mode; "follow live" (auto‑focus nodes with recent events).

---

## 5) Actions & Agents

### 5.1 Action Runtime
- VISLZR → Graph‑Service (mutation) → NATS event → specific **Agent** consumes.
- Agents: CodeReview (LLM + rules), Security (semgrep/trivy/snyk), License, Compliance (Veria rules), Infra (k8s/liveness), Test Runner.

### 5.2 Artifacts
- Each action writes **artifact files** under `/snapshots/audits/<project>/<timestamp>/…` and stores pointer in `Audit.reportPath`.
- Reports are viewable in the Action Drawer.

---

## 6) Security & Access Control
- Mesh‑internal services authenticate with an **HMAC header** + rotating API keys.
- Frontend uses user auth (GitHub/GCP OIDC). Server enforces **row‑level** filters by project membership.
- Artifact paths sandboxed under project root; signed URLs for downloads.

---

## 7) Implementation Plan & Milestones

### Milestone 1 — Graph‑Service MVP (2 weeks)
- Prisma schema + migrations.
- REST/GraphQL read endpoints: `projectGraph`, `dependencies`, `ghostNodes`.
- Repo Indexer CLI (TS) for TS/JS + JSON/YAML.
- NATS subjects and basic consumers.

**Acceptance**:
- Ingest CommandCenter repo → query returns >5k nodes with edges in <1.5s.

### Milestone 2 — TaskGraph & Spec Linking (1 week)
- Map TODO/FIXME/@planned to `SpecItem` & `Task`.
- GhostNode materialization.

**Acceptance**:
- Ghost nodes visible for at least 5 planned items without files.

### Milestone 3 — Audits & Health (1–2 weeks)
- `triggerAudit` mutation + event wiring.
- Security/CodeReview agent stubs (semgrep + LLM review baseline).
- Health sampler to poll `Service.healthUrl` and store `HealthSample`.

**Acceptance**:
- From VISLZR, click a file → run security check → see `Audit` row + artifact.

### Milestone 4 — VISLZR UI (2–3 weeks)
- Graph viewer with clustering, filters, node drawer, bulk actions.
- Time slider, mini‑map.

**Acceptance**:
- Render CommandCenter + Veria with smooth pan/zoom; expand from service→file→symbol.

### Milestone 5 — Federation (1–2 weeks)
- Cross‑project edges; ecosystem overview; global filters.

**Acceptance**:
- Visualize Veria↔CommandCenter dependencies and run a global security sweep.

---

## 8) CLIs, Scripts & NATS

### 8.1 Package Scripts (add to `hub/package.json`)
```json
{
  "scripts": {
    "graph:ingest": "tsx ./scripts/graph/ingest.ts",
    "graph:rebuild": "pnpm graph:ingest --project $PROJECT_ID --since main",
    "graph:health": "tsx ./scripts/graph/health-sampler.ts",
    "graph:audit:security": "tsx ./scripts/graph/emit-audit.ts security",
    "graph:audit:review": "tsx ./scripts/graph/emit-audit.ts codeReview"
  }
}
```

### 8.2 NATS Subjects (canonical)
- `graph.ingest.requested`, `graph.ingest.completed`
- `audit.requested.codeReview`, `audit.result.codeReview`
- `audit.requested.security`, `audit.result.security`
- `hub.presence.<hubId>`, `hub.health.<hubId>`

---

## 9) ENV & Config

```
# Graph‑Service
GRAPH_DB_URL=postgres://...
GRAPH_API_KEY=...

# Mesh
NATS_URL=nats://127.0.0.1:4222
MESH_HMAC_KEY=...

# Indexer
PROJECT_ROOT=/Users/danielconnolly/Projects/CommandCenter
INDEX_LANGS=ts,js,py,go

# Agents (optional)
SNYK_TOKEN=...
SEM_GREP_RULES=rules/semgrep
LLM_PROVIDER=...
```

---

## 10) Testing & Observability
- Seed fixtures for a small repo; snapshot tests for `projectGraph()`.
- Benchmarks for query latency & render FPS.
- OTel traces for: ingest, queries, audit runs.
- Grafana dashboard: node counts, ghost ratio, open audits, health status.

---

## 11) Risks & Mitigations
- **Scale**: >50k symbols → use paging + server‑side clustering; WebGL fallback.
- **Noise**: too many edges → edge sampling + semantic filters (only cross‑module imports).
- **AST drift**: language coverage staged; leverage tree‑sitter parsers.
- **Security**: artifact redaction and project‑scoped signed URLs.

---

## 12) Definition of Done (Phase 8)
- From the VISLZR UI, Daniel can:
  1) Open a project → see complete map with ghost nodes.
  2) Filter to a service, expand to a file, inspect a function’s deps.
  3) Click **Run Security Check** and view the report.
  4) Click a ghost node → auto‑generate an implementation scaffold and open a PR draft.
  5) Toggle ecosystem mode and visualize cross‑project links.

---

## 13) Next Steps (Immediate)
1) Create Prisma schema + migrations for entities above.
2) Implement `ingest.ts` (TS/JS + JSON/YAML parsers via tree‑sitter or ts‑morph first).
3) Scaffold Graph‑Service (Fastify/Express + Mercurius GraphQL).
4) Stub VISLZR page with elkjs layout + node drawer.
5) Wire `audit.requested.*` → simple consumers that write stub reports.

> This plan makes the “mind map as control surface” real in Phase 8, with a pragmatic Phase 7 data spine that’s useful from day one.
