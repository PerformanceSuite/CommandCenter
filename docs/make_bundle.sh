#!/usr/bin/env bash
set -euo pipefail

# === Configuration (absolute paths as requested) ===
DEST_DIR="/Users/danielconnolly/Projects/CommandCenter/docs"
ROOT_DIR="$DEST_DIR/mrktzr-integration"
QUIET=0
FORCE=0
RENDER=1

log() {
  if [ "$QUIET" -eq 0 ]; then
    echo "$@"
  fi
}

usage() {
  cat <<USAGE
Usage: bash make_bundle.sh [--force] [--no-render] [--quiet]

Options:
  --force       Rebuild even if mrktzr-integration/ already exists (no prompt)
  --no-render   Skip Mermaid PNG rendering (keeps .mmd only)
  --quiet       Suppress informational output
USAGE
}

for arg in "$@"; do
  case "$arg" in
    --force) FORCE=1 ;;
    --no-render) RENDER=0 ;;
    --quiet) QUIET=1 ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown flag: $arg"; usage; exit 1 ;;
  esac
done

log "🚀 Building MRKTZR ↔ CommandCenter Integration docs into:"
log "   $ROOT_DIR"
mkdir -p "$DEST_DIR"

if [ -d "$ROOT_DIR" ]; then
  if [ "$FORCE" -eq 1 ]; then
    rm -rf "$ROOT_DIR"
  else
    read -p "mrktzr-integration/ exists. Rebuild and overwrite? [y/N] " ans
    case "$ans" in
      y|Y|yes|YES) rm -rf "$ROOT_DIR" ;;
      *) echo "Aborted."; exit 1 ;;
    esac
  fi
fi

# === Create folders ===
mkdir -p "$ROOT_DIR"/{01_STRATEGY,02_TECH_BLUEPRINT,03_ROADMAP,04_AGENTIC_AUTOMATION,05_APPENDIX}

# === Root README ===
cat > "$ROOT_DIR/README.md" <<'MD'
# MRKTZR ↔ CommandCenter Integration (v1)

This module documents the technical integration between **MRKTZR** (marketing execution layer) and **CommandCenter** (knowledge intelligence layer). It includes architecture, API/event contracts, security, observability, a phased roadmap, and a full agentic automation design.

**Folders**
- `01_STRATEGY/` – improvement analyses and integration concept
- `02_TECH_BLUEPRINT/` – architecture, OpenAPI/AsyncAPI, schema & infra, security
- `03_ROADMAP/` – phases, milestones, ownership, KPIs
- `04_AGENTIC_AUTOMATION/` – agent responsibilities, task graph, prompts, learning loop
- `05_APPENDIX/` – stack comparison, future opportunities, credits

See `VALIDATE.md` for a quick post-install checklist.
MD

# === VALIDATE.md ===
cat > "$ROOT_DIR/VALIDATE.md" <<'MD'
# MRKTZR ↔ CommandCenter Integration — Post-Install Validation

## ✅ 1. Directory Structure
Ensure:
```
mrktzr-integration/
├── README.md
├── VALIDATE.md
├── install_mrktzr_integration.sh
├── 01_STRATEGY/
├── 02_TECH_BLUEPRINT/
├── 03_ROADMAP/
├── 04_AGENTIC_AUTOMATION/
└── 05_APPENDIX/
```

## ✅ 2. Diagram Render
If you passed default flags (render enabled), confirm:
```
02_TECH_BLUEPRINT/Integration_Architecture.png
```
If missing, install mermaid-cli then re-run:
```bash
npm install -g @mermaid-js/mermaid-cli
bash make_bundle.sh --force
```

## ✅ 3. Docs Index Link
Check `../README.md` contains:
```
- [MRKTZR Integration](./mrktzr-integration/README.md)
```

## ✅ 4. API Spec Preview
Preview locally with Docker:
```bash
docker run -p 8080:8080 -v $(pwd)/mrktzr-integration/02_TECH_BLUEPRINT/OpenAPI.yaml:/api.yaml swaggerapi/swagger-ui
docker run -p 8081:8080 -v $(pwd)/mrktzr-integration/02_TECH_BLUEPRINT/AsyncAPI.yaml:/asyncapi.yaml asyncapi/studio
```

## ✅ 5. Commit
```bash
git add mrktzr-integration
git commit -m "docs: add MRKTZR↔CommandCenter integration (v1)"
git push
```
MD

# === Installer script (absolute path) ===
cat > "$ROOT_DIR/install_mrktzr_integration.sh" <<'SH'
#!/usr/bin/env bash
set -euo pipefail
DEST="/Users/danielconnolly/Projects/CommandCenter/docs"
TARGET_DIR="$DEST/mrktzr-integration"
DOC_INDEX="$DEST/README.md"

echo "📘 Registering integration in docs index..."
mkdir -p "$DEST"
if ! grep -q "MRKTZR Integration" "$DOC_INDEX" 2>/dev/null; then
  echo "- [MRKTZR Integration](./mrktzr-integration/README.md)" >> "$DOC_INDEX"
  echo "✅ Added link to $DOC_INDEX"
else
  echo "ℹ️ Integration already listed in $DOC_INDEX"
fi

echo "🧩 Done. Location: $TARGET_DIR"
SH
chmod +x "$ROOT_DIR/install_mrktzr_integration.sh"

# === 01_STRATEGY files ===
cat > "$ROOT_DIR/01_STRATEGY/MRKTZR_Improvements.md" <<'MD'
# MRKTZR — Improvement Plan (Execution Layer)

- **Service modularization** (NestJS or FastAPI): `content-svc`, `persona-svc`, `scheduler-svc`, `channels-svc`, `analytics-svc`, `compliance-svc`.
- **Experimentation/A-B/n**: Bayesian bandits per channel; automatic winner promotion.
- **Creative Knowledge Graph**: Content ↔ Persona ↔ Topic ↔ Campaign ↔ Outcome (CTR/watchtime/CVR), Postgres + pgvector.
- **Observability**: OpenTelemetry traces from generation → moderation → publish → metrics ingest; Prometheus/Grafana dashboards.
- **DX**: `make` tasks, Docker, `.env` templates, e2e channel simulators, seed data.

See the `02_TECH_BLUEPRINT/` for concrete contracts and infra.
MD

cat > "$ROOT_DIR/01_STRATEGY/CommandCenter_Improvements.md" <<'MD'
# CommandCenter — Improvement Plan (Intelligence Layer)

- **Plugin SDK**: `plugin.manifest.yaml`, hooks: `on_ingest`, `on_enrich`, `on_export`.
- **Unified Graph UI**: first-class node types, saved views, technology/research/insight graph.
- **Observability Phase C**: ingestion rates, freshness index, failed sources, top queries.
- **Semantic Action Layer**: insight → action webhooks (MRKTZR connector by default).
- **Memory tiers**: session, long-term (project), behavioral (Habit Coach).
MD

cat > "$ROOT_DIR/01_STRATEGY/Integration_Concept.md" <<'MD'
# Integration Concept: Inbound Intelligence ↔ Outbound Execution

- **CommandCenter**: collect → analyze → synthesize (*TopicBriefs*)
- **MRKTZR**: create → test → publish (*Campaigns & Posts*)
- **Feedback**: MRKTZR analytics → CommandCenter learning → better next briefs
MD

# === 02_TECH_BLUEPRINT files ===
cat > "$ROOT_DIR/02_TECH_BLUEPRINT/Integration_Architecture.md" <<'MD'
# Integration Architecture (High Level)

```mermaid
flowchart LR
  subgraph CC[CommandCenter]
    CC.Ingest[Ingestion: RSS, GitHub, Docs, FS]
    CC.RAG[KnowledgeBeast RAG]
    CC.Habit[Habit Coach]
    CC.API[(CC REST/GraphQL API)]
    CC.Obs[(Prometheus/OTel)]
  end

  subgraph MR[MRKTZR]
    MR.Content[Content Svc]
    MR.Persona[Persona/Avatar Svc]
    MR.Scheduler[Scheduler Svc]
    MR.Channels[Channels Svc]
    MR.Analytics[Analytics Svc]
    MR.API[(MR REST/API GW)]
    MR.Obs[(Prometheus/OTel)]
  end

  CC.RAG -->|/insights/export| CC.API
  CC.API -->|Topic briefs, trends, citations| MR.Content
  MR.Content --> MR.Scheduler --> MR.Channels
  MR.Channels -->|Publish| Social[(X/LinkedIn/YouTube/...)]
  Social -->|Engagement events| MR.Analytics
  MR.Analytics -->|/metrics/export| MR.API
  MR.API -->|POST /cc/analytics/intake| CC.API
  CC.Habit -->|Proactive triggers| MR.Content
  CC.Obs --- MR.Obs
```
MD

# Mermaid source for PNG rendering
cat > "$ROOT_DIR/02_TECH_BLUEPRINT/Integration_Architecture.mmd" <<'MMD'
flowchart LR
  subgraph CC[CommandCenter]
    CC_Ingest[Ingestion: RSS, GitHub, Docs, FS]
    CC_RAG[KnowledgeBeast RAG]
    CC_Habit[Habit Coach]
    CC_API[(CC REST/GraphQL API)]
    CC_Obs[(Prometheus/OTel)]
  end

  subgraph MR[MRKTZR]
    MR_Content[Content Svc]
    MR_Persona[Persona/Avatar Svc]
    MR_Scheduler[Scheduler Svc]
    MR_Channels[Channels Svc]
    MR_Analytics[Analytics Svc]
    MR_API[(MR REST/API GW)]
    MR_Obs[(Prometheus/OTel)]
  end

  CC_RAG -->|/insights/export| CC_API
  CC_API -->|Topic briefs, trends, citations| MR_Content
  MR_Content --> MR_Scheduler --> MR_Channels
  MR_Channels -->|Publish| Social[(X/LinkedIn/YouTube/...)]
  Social -->|Engagement events| MR_Analytics
  MR_Analytics -->|/metrics/export| MR_API
  MR_API -->|POST /cc/analytics/intake| CC_API
  CC_Habit -->|Proactive triggers| MR_Content
  CC_Obs --- MR_Obs
MMD

cat > "$ROOT_DIR/02_TECH_BLUEPRINT/Schema_and_APIs.md" <<'MD'
# Schema & APIs Overview

- **HTTP (OpenAPI)**: `/insights/export` (CC→MR), `/campaigns/intake` (MR intake), `/analytics/intake` (MR→CC metrics).
- **Events (AsyncAPI, NATS)**: `cc.insight.ready`, `mr.campaign.event`, `mr.analytics.metric`.
- **Relational/Vector Models**:
  - CC: `insights`, `embeddings`
  - MR: `campaigns`, `posts`, `metrics`, `personas`
MD

cat > "$ROOT_DIR/02_TECH_BLUEPRINT/OpenAPI.yaml" <<'YAML'
openapi: 3.0.3
info:
  title: CC↔MR Integration API
  version: 1.0.0
servers:
  - url: https://cc.local/api
    description: CommandCenter API
  - url: https://mr.local/api
    description: MRKTZR API
paths:
  /insights/export:
    get:
      summary: Export aggregated topic briefs for a tenant
      parameters:
        - in: query
          name: tenant_id
          schema: { type: string }
          required: true
        - in: query
          name: since
          description: ISO8601 timestamp filter
          schema: { type: string, format: date-time }
      responses:
        '200':
          description: List of TopicBrief
          content:
            application/json:
              schema:
                type: array
                items:
                  $ref: '#/components/schemas/TopicBrief'
  /campaigns/intake:
    post:
      summary: Ingest topic briefs into MRKTZR to seed campaigns
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                tenant_id: { type: string }
                briefs:
                  type: array
                  items: { $ref: '#/components/schemas/TopicBrief' }
      responses:
        '202': { description: Accepted }
  /analytics/intake:
    post:
      summary: Ingest post/campaign analytics into CommandCenter
      requestBody:
        required: true
        content:
          application/json:
            schema:
              type: object
              properties:
                tenant_id: { type: string }
                metrics:
                  type: array
                  items: { $ref: '#/components/schemas/EngagementMetric' }
      responses:
        '202': { description: Accepted }
components:
  schemas:
    TopicBrief:
      type: object
      required: [id, title, summary, topics, sources, guidance]
      properties:
        id: { type: string, format: uuid }
        title: { type: string }
        summary: { type: string }
        topics:
          type: array
          items: { type: string }
        keywords:
          type: array
          items: { type: string }
        persona_hints:
          type: array
          items: { $ref: '#/components/schemas/PersonaHint' }
        sources:
          type: array
          items: { $ref: '#/components/schemas/Citation' }
        guidance:
          type: object
          properties:
            tone: { type: string }
            calls_to_action: { type: array, items: { type: string } }
            channel_recos: { type: array, items: { type: string } }
            compliance_notes: { type: string }
    PersonaHint:
      type: object
      properties:
        persona_id: { type: string }
        name: { type: string }
        demographics: { type: object, additionalProperties: true }
        brand_voice: { type: string }
    Citation:
      type: object
      properties:
        url: { type: string, format: uri }
        title: { type: string }
        snippet: { type: string }
        score: { type: number, format: float }
    EngagementMetric:
      type: object
      required: [id, campaign_id, channel, ts, metrics]
      properties:
        id: { type: string, format: uuid }
        campaign_id: { type: string }
        post_id: { type: string }
        channel: { type: string, enum: [x, linkedin, youtube, tiktok, rss] }
        ts: { type: string, format: date-time }
        metrics:
          type: object
          properties:
            impressions: { type: integer }
            clicks: { type: integer }
            ctr: { type: number, format: float }
            likes: { type: integer }
            comments: { type: integer }
            shares: { type: integer }
            watch_time_ms: { type: integer }
            conversions: { type: integer }
            conversion_value: { type: number, format: float }
YAML

cat > "$ROOT_DIR/02_TECH_BLUEPRINT/AsyncAPI.yaml" <<'YAML'
asyncapi: 2.6.0
info:
  title: CC↔MR Event Contracts
  version: 1.0.0
servers:
  nats:
    url: nats://mesh-bus:4222
    protocol: nats
channels:
  cc.insight.ready:
    description: New topic briefs exported by CC
    subscribe:
      message:
        name: InsightReady
        payload:
          $ref: '#/components/schemas/TopicBrief'
  mr.campaign.event:
    description: Campaign lifecycle and delivery events from MR
    publish:
      message:
        name: CampaignEvent
        payload:
          $ref: '#/components/schemas/CampaignEvent'
  mr.analytics.metric:
    description: Aggregated engagement metrics emitted by MR
    publish:
      message:
        name: EngagementMetric
        payload:
          $ref: '#/components/schemas/EngagementMetric'
components:
  schemas:
    TopicBrief:
      type: object
      properties:
        id: { type: string, format: uuid }
        title: { type: string }
        summary: { type: string }
        topics:
          type: array
          items: { type: string }
        keywords:
          type: array
          items: { type: string }
        persona_hints:
          type: array
          items:
            type: object
            properties:
              persona_id: { type: string }
              name: { type: string }
              brand_voice: { type: string }
        sources:
          type: array
          items:
            type: object
            properties:
              url: { type: string }
              title: { type: string }
              snippet: { type: string }
              score: { type: number }
        guidance:
          type: object
          properties:
            tone: { type: string }
            calls_to_action:
              type: array
              items: { type: string }
            channel_recos:
              type: array
              items: { type: string }
            compliance_notes: { type: string }
    CampaignEvent:
      type: object
      required: [id, campaign_id, type, ts]
      properties:
        id: { type: string, format: uuid }
        campaign_id: { type: string }
        post_id: { type: string }
        type: { type: string, enum: [CREATED, SCHEDULED, PUBLISHED, FAILED, RETRYING] }
        ts: { type: string, format: date-time }
        details: { type: object, additionalProperties: true }
    EngagementMetric:
      type: object
      properties:
        id: { type: string, format: uuid }
        campaign_id: { type: string }
        post_id: { type: string }
        channel: { type: string }
        ts: { type: string, format: date-time }
        metrics: { type: object, additionalProperties: true }
YAML

cat > "$ROOT_DIR/02_TECH_BLUEPRINT/Security_Model.md" <<'MD'
# Security Model

- **Isolation**: per-tenant encryption keys; distinct Postgres schemas; separate Docker volumes.
- **Auth**: Mutual mTLS between CC↔MR; OAuth2 client credentials for control plane (scoped per tenant).
- **Secrets**: SOPS- or Vault-managed; ephemeral runtime injection via Dagger.
- **SSRF/XSS**: re-use CommandCenter protections; content moderation guardrails before publish.
- **Idempotency**: `Idempotency-Key` header; store request hashes for 24h.
MD

cat > "$ROOT_DIR/02_TECH_BLUEPRINT/Shared_Infra_Plan.md" <<'MD'
# Shared Infrastructure Plan

- **Orchestration**: Dagger Hub manages tenant-scoped CC & MR instances (ports, volumes, secrets).
- **Message Bus**: NATS (JetStream) for async eventing; HTTP for control plane.
- **Observability**: Prometheus/Grafana with shared labels; OTel traces with W3C headers.
- **SLOs**: freshness <24h (99%); publish success >99.5%; e2e latency <2h (95%) for daily cadence.
MD

# === 03_ROADMAP files ===
cat > "$ROOT_DIR/03_ROADMAP/Phase_Plan.md" <<'MD'
# Phase Plan

**I — API Bridge (Weeks 1–3)**: `/insights/export`, `/campaigns/intake`, bridge worker, idempotency.  
**II — Feedback Loop (Weeks 4–6)**: `/analytics/intake`, metrics schema, basic bandits, Grafana.  
**III — Unified UI (Weeks 7–10)**: Next.js dashboard combining insights + outcomes.  
**IV — Agentic Automation (Weeks 11–16)**: Research/Creative/Scheduler/Feedback agents.  
**V — Observability Integration (Weeks 17–18)**: OTel traces, SLOs, alerting.
MD

cat > "$ROOT_DIR/03_ROADMAP/Milestones_Timeline.md" <<'MD'
# Milestones & Timeline

- M1: Contracts merged + smoke tests green
- M2: CC→MR bridge live with daily briefs
- M3: MR metrics → CC dashboards
- M4: Unified UI MVP
- M5: Agentic loop closed (learn→create→measure)
- M6: SLOs green two consecutive weeks
MD

cat > "$ROOT_DIR/03_ROADMAP/Team_Roles_and_Ownership.md" <<'MD'
# Roles & Ownership (RACI)

- **Architect** (A/R): contracts, security, tenancy map
- **Backend CC** (R): `/insights/export`, analytics intake
- **Backend MR** (R): `/campaigns/intake`, channels adapters
- **Data/ML** (R): bandits, uplift modeling, priors
- **SRE** (R): Dagger pipelines, observability, SLOs
- **PM** (A): roadmap, KPIs, acceptance
MD

cat > "$ROOT_DIR/03_ROADMAP/KPIs_and_Metrics.md" <<'MD'
# KPIs & Metrics

- **Insight freshness** (hrs), **coverage** (#briefs/week)
- **Time-to-publish** (min), **variant hit-rate** (% winners)
- **Engagement uplift** (%) vs baseline
- **SLO conformance** (%), **ops toil** (alerts/week)
MD

# === 04_AGENTIC_AUTOMATION files ===
cat > "$ROOT_DIR/04_AGENTIC_AUTOMATION/LLM_Agent_Design.md" <<'MD'
# LLM Agent Design

- **ResearchAgent (CC)**: synthesize TopicBriefs with citations; RAG within tenant corpus only.
- **CreativeAgent (MR)**: generate channel-specific variants; enforce persona+compliance notes.
- **SchedulerAgent (MR)**: optimal posting windows per channel; history + heuristics.
- **FeedbackAgent (MR→CC)**: aggregate metrics; Bayesian updates for uplift per feature.
- **HabitCoach (CC)**: proactive triggers for re-briefs and backlog grooming.
MD

cat > "$ROOT_DIR/04_AGENTIC_AUTOMATION/Prompt_Orchestration.md" <<'MD'
# Prompt Orchestration (Patterns)

- **ResearchAgent**: Summarize top N themes from last 7 days (sources X,Y). Output: title, summary (≤120w), topics[], keywords[], persona_hints[], compliance notes, citations.
- **CreativeAgent**: For each TopicBrief × Persona, generate A/B variants per channel with CTA, alt text, thumbnail prompt.
- **FeedbackAgent**: Given metrics for campaign X, estimate uplift per (topic, format, CTA) with Bayesian update; propose next-cycle adjustments.
MD

cat > "$ROOT_DIR/04_AGENTIC_AUTOMATION/Feedback_Loop_Design.md" <<'MD'
# Feedback Loop Design

- **Bandits**: per-channel Thompson Sampling over creative variants.
- **Cold Start**: seed priors from heuristics; decay over time.
- **Guardrails**: compliance regex/LLM moderation; forbidden topics per tenant.
- **Control**: idempotent publish, retries with backoff, dead-letter queues.
MD

# === 05_APPENDIX files ===
cat > "$ROOT_DIR/05_APPENDIX/Technology_Stack_Comparison.md" <<'MD'
# Stack Comparison

- **CommandCenter**: Python/FastAPI, Celery/Redis, Postgres+pgvector, Docling, sentence-transformers, Dagger, Prometheus/Grafana, OTel.
- **MRKTZR (target)**: Node/NestJS (or FastAPI), BullMQ/Redis, Next.js UI, Postgres+pgvector, LangChain/LlamaIndex, OpenAI/Anthropic adapters, PostHog, OTel.
- **Interop**: HTTP (OpenAPI 3), NATS (AsyncAPI), OTel traces, SOPS/Vault secrets, Dagger pipelines.
MD

cat > "$ROOT_DIR/05_APPENDIX/Future_Opportunities.md" <<'MD'
# Future Opportunities

- **Veria**: compliance gating + content auditing for regulated verticals.
- **Performia**: campaign testing with live A/V hooks.
- **Rollizr**: cross-brand synergy hub and shared analytics.
MD

cat > "$ROOT_DIR/05_APPENDIX/Credits_and_Attributions.md" <<'MD'
# Credits & Attributions

Architecture and contracts authored with AI assistance. Built on open standards: OpenAPI, AsyncAPI, Prometheus, OpenTelemetry.
MD

# === Render Mermaid diagram to PNG (dark) ===
if [ "$RENDER" -eq 1 ]; then
  if command -v mmdc >/dev/null 2>&1; then
    log "🖼  Rendering Mermaid → PNG via mmdc (dark theme)..."
    mmdc -i "$ROOT_DIR/02_TECH_BLUEPRINT/Integration_Architecture.mmd" \
         -o "$ROOT_DIR/02_TECH_BLUEPRINT/Integration_Architecture.png" \
         -t dark >/dev/null 2>&1 || true
  else
    log "⚠️  mermaid-cli (mmdc) not found. Install with:"
    log "   npm install -g @mermaid-js/mermaid-cli"
  fi
fi

# === Ensure index link in docs/README.md ===
DOC_INDEX="$DEST_DIR/README.md"
mkdir -p "$DEST_DIR"
if ! grep -q "MRKTZR Integration" "$DOC_INDEX" 2>/dev/null; then
  echo "- [MRKTZR Integration](./mrktzr-integration/README.md)" >> "$DOC_INDEX"
fi

# === Summary ===
log "✅ Docs written to: $ROOT_DIR"
[ "$RENDER" -eq 1 ] && log "✅ Diagram render attempted (see 02_TECH_BLUEPRINT/Integration_Architecture.png)"
log "🎉 Done. Run 'git add mrktzr-integration && git commit && git push' when ready."
