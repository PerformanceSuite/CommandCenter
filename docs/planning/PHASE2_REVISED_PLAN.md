# Phase 2 Revised Plan: API Enhancements and Automation Workflows

**Date:** 2025-10-12
**Status:** APPROVED - Ready for Implementation
**Duration:** 3.5 weeks (98 hours)
**Approach:** Option C - Hybrid (API-Complete + MCP, Defer Frontend)
**Prerequisites:** Phase 1 Complete ✅

---

## Executive Summary

**Phase 2 Goal:** Transform CommandCenter from infrastructure to complete API product with automation, integrations, and MCP continuity.

**Scope Decision:** Option C - Hybrid Approach
- ✅ All 7 core API components
- ✅ MCP integration (connects to Phase 1 core)
- ⏳ Frontend components deferred to Phase 2.5 (can be parallel work)

**Why Option C:**
- Delivers complete API surface for programmatic access
- Maintains MCP continuity from Phase 1
- Allows frontend to be built independently or by community
- Realistic 3.5-week timeline (98 hours)
- Reduces risk compared to 4-week full scope

---

## Revised Timeline & Estimates

### Week 1: Foundation (33 hours)

**Sprint 1.1: Async Job System + Migrations (18 hours)**
- Day 1 (6h): Celery setup, database migrations
  - Configure Celery with Redis broker
  - Create Job model and migration
  - Create Schedule model and migration
  - Test migrations in dev environment

- Day 2 (6h): Task infrastructure and job API
  - `backend/app/tasks/__init__.py` (Celery config)
  - `backend/app/tasks/analysis_tasks.py`
  - `backend/app/services/job_service.py`
  - `backend/app/routers/jobs.py`

- Day 3 (6h): WebSocket progress and testing
  - WebSocket endpoint `/ws/jobs/{job_id}`
  - Connection manager with JWT auth
  - Job progress broadcasting
  - 25+ tests for job lifecycle

**Sprint 1.2: Batch Operations (10 hours)**
- Day 4 (6h): Batch analyze endpoints
  - `backend/app/routers/batch.py`
  - `backend/app/services/batch_service.py`
  - Batch job submission

- Day 5 (4h): Bulk import/export and testing
  - Bulk technology import/export
  - Progress tracking
  - 20+ tests

**Sprint 1.3: Observability (5 hours)**
- Day 5 (5h): Health checks and structured logging
  - `backend/app/routers/health.py`
  - Health/ready/live endpoints
  - Dependency health checks (DB, Redis, GitHub)
  - Structured JSON logging
  - 12+ tests

**Week 1 Deliverables:**
- ✅ Celery operational (worker, beat, flower)
- ✅ Job system with WebSocket progress
- ✅ Batch operations API
- ✅ Production health checks
- ✅ 57+ new tests
- ✅ 4 database migrations applied

---

### Week 2: Integrations (43 hours)

**Sprint 2.1: Enhanced Webhooks (4 hours)**
- Day 6 (4h): Outbound webhook delivery
  - Enhance `backend/app/services/webhook_service.py`
  - Add `backend/app/tasks/webhook_tasks.py` (async delivery)
  - Retry logic with exponential backoff
  - Webhook delivery logs
  - 10+ tests (18 total with existing)

**Sprint 2.2: Scheduled Analysis + Markdown Export (15 hours)**
- Day 6-7 (9h): Schedule system
  - Schedule model migration (if not done in Week 1)
  - `backend/app/services/scheduler_service.py`
  - `backend/app/routers/schedules.py`
  - Celery beat integration
  - `backend/app/tasks/scheduled_tasks.py`

- Day 7 (6h): Basic Markdown export
  - `backend/app/exporters/__init__.py`
  - `backend/app/exporters/markdown.py`
  - GitHub-ready markdown reports
  - 15+ tests for scheduling, 10+ for markdown

**Sprint 2.3: External Integrations (16 hours)**
- Day 8-9 (12h): Slack + Jira/Linear
  - Integration model migration
  - `backend/app/integrations/slack.py` (Slack SDK)
  - `backend/app/integrations/jira.py` (Jira REST API)
  - `backend/app/integrations/linear.py` (Linear GraphQL)
  - `backend/app/routers/integrations.py` (OAuth)
  - Attach Markdown reports to notifications

- Day 10 (4h): GitHub Actions
  - `.github/actions/analyze/action.yml`
  - `.github/actions/analyze/README.md`
  - PR comment integration
  - 20+ tests

**Sprint 2.4: MCP Integration (8 hours)**
- Day 10 (8h): MCP resources, tools, prompts
  - MCP resources: `job://`, `schedule://`, `webhook://`
  - MCP tools: `trigger_analysis`, `get_job_status`, `export_analysis`
  - MCP prompts: `analyze_project`, `schedule_analysis`
  - Integration with Phase 1 MCP core
  - 15+ tests

**Week 2 Deliverables:**
- ✅ Outbound webhooks with retry
- ✅ Scheduled analysis operational
- ✅ Slack, Jira, Linear integrations
- ✅ GitHub Action published
- ✅ MCP integration complete
- ✅ 70+ new tests

---

### Week 3: Export & Polish (22 hours)

**Sprint 3.1: Enhanced Export (12 hours)**
- Day 11-12 (9h): SARIF, HTML, CSV/Excel
  - `backend/app/exporters/sarif.py` (SARIF 2.1.0)
  - `backend/app/exporters/html.py` (self-contained HTML)
  - `backend/app/exporters/spreadsheet.py` (CSV/Excel)
  - `backend/app/templates/` (HTML/Markdown templates)

- Day 13 (3h): Export API endpoints
  - `GET /api/v1/export/{analysis_id}/sarif`
  - `GET /api/v1/export/{analysis_id}/markdown`
  - `GET /api/v1/export/{analysis_id}/html`
  - `GET /api/v1/export/{analysis_id}/csv`
  - `POST /api/v1/export/batch`
  - 65+ tests (75 total with markdown from Week 2)

**Sprint 3.2: Integration Testing (6 hours)**
- Day 13-14 (6h): End-to-end workflows
  - Schedule → Analyze → Webhook → Slack
  - Batch operations workflow
  - Export pipeline tests
  - MCP integration tests
  - 10+ E2E tests

**Sprint 3.3: Documentation (4 hours)**
- Day 14 (4h): Comprehensive documentation
  - `docs/API_REFERENCE.md` (complete OpenAPI/Swagger)
  - `docs/INTEGRATIONS_GUIDE.md` (Slack, Jira, Linear, GitHub Actions)
  - `docs/AUTOMATION_GUIDE.md` (scheduling, webhooks, CI/CD)
  - `docs/EXPORT_FORMATS.md` (SARIF, Markdown, HTML, CSV examples)
  - Update MCP documentation with Phase 2 features

**Week 3 Deliverables:**
- ✅ 5 export formats (SARIF, Markdown, HTML, JSON, CSV)
- ✅ Integration test suite
- ✅ Complete API documentation
- ✅ 75+ new tests

---

## Total Phase 2 Deliverables

**Time:** 98 hours (3.5 weeks at 28 hours/week)

**Tests:** 210+ new tests (400+ total)
- Unit tests: 150+
- Integration tests: 50+
- E2E tests: 10+

**New Files:** ~70 files
- Routers: 6 (batch, jobs, webhooks, schedules, integrations, health)
- Services: 4 (batch_service, job_service, webhook_service, scheduler_service)
- Tasks: 4 (analysis_tasks, export_tasks, webhook_tasks, scheduled_tasks)
- Integrations: 3 (slack, jira, linear)
- Exporters: 5 (init, sarif, markdown, html, spreadsheet)
- Observability: 4 (init, metrics, logging, tracing)
- Models: 3 (job, schedule, integration) + webhook enhancements
- MCP: 3 (resources, tools, prompts for Phase 2 features)
- Tests: 21 test files
- Docs: 4 documentation files
- GitHub Actions: 2 files
- Migrations: 4 Alembic migrations

**New Dependencies:**
```txt
celery==5.3.4
flower==2.0.1
celery-redbeat==2.2.0
slack-sdk==3.26.1
jira==3.6.0
openpyxl==3.1.2
python-crontab==3.0.0
sentry-sdk==1.38.0  # Optional
```

**Docker Services Added:**
- celery-worker (with scaling)
- celery-beat
- flower (monitoring UI)
- prometheus (already partially configured)

---

## Component Breakdown (Revised)

### 1. Async Job System (18 hours) ⭐ CRITICAL PATH

**Goal:** Background job processing with progress tracking

**What's New:**
- Celery worker/beat infrastructure
- Job model with status tracking
- WebSocket progress updates
- Job API (list, get, cancel, delete)

**Implementation:**
- `backend/app/tasks/__init__.py` - Celery config
- `backend/app/models/job.py` - Job model (NEW MIGRATION)
- `backend/app/services/job_service.py` - Job tracking
- `backend/app/routers/jobs.py` - Job API
- `backend/app/tasks/analysis_tasks.py` - Analysis jobs
- WebSocket endpoint: `/ws/jobs/{job_id}`

**Tests:** 25+

**Why Critical:** All other components depend on job system

---

### 2. Batch Operations (10 hours)

**Goal:** Bulk operations for multi-repository analysis

**Features:**
- Batch analyze multiple repositories
- Bulk technology import/export
- Progress tracking via job system

**Implementation:**
- `backend/app/routers/batch.py`
- `backend/app/services/batch_service.py`
- Uses async job system from Component 1

**Endpoints:**
```python
POST   /api/v1/batch/analyze
GET    /api/v1/batch/jobs/{job_id}
POST   /api/v1/batch/export
POST   /api/v1/batch/import
```

**Tests:** 20+

**Dependencies:** Requires Component 1 (Async Jobs)

---

### 3. Enhanced Webhooks (4 hours) ⚡ REDUCED

**Goal:** Outbound webhook delivery for external integrations

**What Exists (70%):**
- ✅ Inbound GitHub webhooks fully implemented
- ✅ Webhook models (WebhookConfig, WebhookEvent)
- ✅ HMAC signature verification
- ✅ Event storage and processing

**What's New (30%):**
- Outbound webhook delivery
- Retry logic with exponential backoff
- Delivery logs
- Generic event system (analysis.complete, etc.)

**Implementation:**
- Enhance `backend/app/services/webhook_service.py`
- Add `backend/app/tasks/webhook_tasks.py` (Celery)
- Add outbound delivery endpoints

**Events:**
- `analysis.complete`
- `repo.synced`
- `research.created`
- `schedule.triggered`

**Tests:** 10+ new (18+ total with existing)

**Time Saved:** -6 hours (from 10h to 4h)

---

### 4. Scheduled Analysis (15 hours)

**Goal:** Automatic periodic repository analysis

**Features:**
- Cron-style schedule configuration
- Celery beat integration
- Analysis comparison (detect changes)
- Notifications via webhooks/Slack

**Implementation:**
- `backend/app/models/schedule.py` (NEW MIGRATION)
- `backend/app/services/scheduler_service.py`
- `backend/app/routers/schedules.py`
- `backend/app/tasks/scheduled_tasks.py`
- Basic Markdown export (for notifications)

**Configuration:**
```json
{
  "schedule": "0 9 * * 1",  // Every Monday at 9am
  "repositories": [1, 2, 3],
  "notify": ["webhook", "slack"],
  "compare_previous": true
}
```

**Endpoints:**
```python
POST   /api/v1/schedules
GET    /api/v1/schedules
PUT    /api/v1/schedules/{id}
DELETE /api/v1/schedules/{id}
POST   /api/v1/schedules/{id}/trigger
```

**Tests:** 15+ (scheduling), 10+ (markdown export)

**Includes:** Basic Markdown export moved from Week 3

---

### 5. External Integrations (16 hours)

**Goal:** Connect with Slack, Jira, Linear, GitHub Actions

**Implementation:**

#### 5.1 Slack Integration (6h)
- `backend/app/integrations/slack.py`
- Post analysis summaries to channels
- Interactive buttons
- Slash commands (/analyze, /search)

#### 5.2 Jira/Linear Integration (6h)
- `backend/app/integrations/jira.py`
- `backend/app/integrations/linear.py`
- Create research tasks as tickets
- Bidirectional status sync
- Link analyses to issues

#### 5.3 GitHub Actions (4h)
- `.github/actions/analyze/action.yml`
- PR comment with analysis summary
- Status checks for quality gates
- Artifact upload

**Endpoints:**
```python
POST   /api/v1/integrations/slack/oauth
POST   /api/v1/integrations/slack/command
POST   /api/v1/integrations/jira/connect
GET    /api/v1/integrations/linear/projects
```

**Tests:** 20+

**Includes:** Integration model migration for storing OAuth tokens

---

### 6. Enhanced Export (12 hours) ⚡ ADJUSTED

**Goal:** Export analysis in standard formats

**Formats:**

#### 6.1 SARIF (4h) - PRIORITY
- Static Analysis Results Interchange Format
- GitHub/GitLab native support
- IDE integration (VS Code)
- Schema: SARIF 2.1.0

#### 6.2 HTML Dashboard (4h)
- Self-contained HTML file
- Interactive charts (Chart.js)
- No server required

#### 6.3 CSV/Excel (4h)
- Technology inventory
- Research task list
- Metrics over time

**Note:** Markdown export moved to Week 2 (Component 4)

**Implementation:**
- `backend/app/exporters/__init__.py`
- `backend/app/exporters/sarif.py`
- `backend/app/exporters/markdown.py` (Week 2)
- `backend/app/exporters/html.py`
- `backend/app/exporters/spreadsheet.py`
- `backend/app/templates/`

**Endpoints:**
```python
GET    /api/v1/export/{analysis_id}/sarif
GET    /api/v1/export/{analysis_id}/markdown
GET    /api/v1/export/{analysis_id}/html
GET    /api/v1/export/{analysis_id}/csv
POST   /api/v1/export/batch
```

**Tests:** 75+ (15 per format + API tests)

**Time Saved:** -3 hours (Markdown moved to Week 2)

---

### 7. Observability (5 hours) ⚡ REDUCED

**Goal:** Production-ready monitoring and health checks

**What Exists (50%):**
- ✅ Prometheus client installed
- ✅ FastAPI instrumentator configured
- ✅ Metrics service exists

**What's New (50%):**
- Health check endpoints
- Dependency health checks
- Structured JSON logging
- Correlation ID tracing

**Implementation:**
- `backend/app/routers/health.py`
- `backend/app/observability/logging.py`
- `backend/app/observability/tracing.py`
- Update `backend/app/observability/metrics.py`

**Endpoints:**
```python
GET    /health                    # Basic health
GET    /health/ready              # Readiness probe
GET    /health/live               # Liveness probe
GET    /metrics                   # Prometheus metrics
GET    /api/v1/debug/performance  # Performance stats
```

**Health Checks:**
- Database connectivity
- Redis connectivity
- Celery worker health
- GitHub API accessibility
- Disk space, memory

**Tests:** 12+

**Time Saved:** -3 hours (Prometheus already configured)

---

### 8. MCP Integration (8 hours) ⭐ NEW

**Goal:** Expose Phase 2 features via MCP protocol

**Why Critical:** Maintains continuity with Phase 1 MCP Core (95 tests)

**Implementation:**

#### 8.1 MCP Resources (3h)
- `job://{job_id}` - Job status and results
- `schedule://{schedule_id}` - Schedule configuration
- `webhook://{webhook_id}` - Webhook logs

#### 8.2 MCP Tools (3h)
- `trigger_analysis` - Start analysis job
- `get_job_status` - Query job progress
- `export_analysis` - Export to format
- `create_schedule` - Setup scheduled analysis

#### 8.3 MCP Prompts (2h)
- `analyze_project` - Guided project analysis
- `schedule_analysis` - Schedule setup wizard
- `review_exports` - Export format selection

**Files:**
- `backend/app/mcp/providers/job_provider.py`
- `backend/app/mcp/providers/schedule_provider.py`
- `backend/app/mcp/tools/phase2_tools.py`
- `backend/app/mcp/prompts/phase2_prompts.py`

**Tests:** 15+

**Integration:** Extends Phase 1 MCP server with Phase 2 capabilities

---

## Database Migrations

**4 New Migrations Required:**

### Migration 1: Job Model
```sql
CREATE TABLE jobs (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    job_type VARCHAR(50) NOT NULL,  -- analysis, export, batch
    status VARCHAR(20) NOT NULL,     -- pending, running, completed, failed
    progress INTEGER DEFAULT 0,
    result JSONB,
    error TEXT,
    created_at TIMESTAMP DEFAULT NOW(),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    INDEX idx_jobs_project_status (project_id, status),
    INDEX idx_jobs_created (created_at)
);
```

### Migration 2: Schedule Model
```sql
CREATE TABLE schedules (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    cron_expression VARCHAR(100) NOT NULL,
    repositories INTEGER[] NOT NULL,
    notify_channels JSONB DEFAULT '[]',
    compare_previous BOOLEAN DEFAULT TRUE,
    active BOOLEAN DEFAULT TRUE,
    last_run_at TIMESTAMP,
    next_run_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_schedules_project_active (project_id, active),
    INDEX idx_schedules_next_run (next_run_at)
);
```

### Migration 3: Integration Model
```sql
CREATE TABLE integrations (
    id SERIAL PRIMARY KEY,
    project_id INTEGER NOT NULL REFERENCES projects(id) ON DELETE CASCADE,
    integration_type VARCHAR(50) NOT NULL,  -- slack, jira, linear
    name VARCHAR(255) NOT NULL,
    config JSONB NOT NULL,                  -- OAuth tokens, API keys (encrypted)
    active BOOLEAN DEFAULT TRUE,
    last_sync_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    INDEX idx_integrations_project_type (project_id, integration_type)
);
```

### Migration 4: Enhance WebhookConfig
```sql
ALTER TABLE webhook_configs ADD COLUMN delivery_mode VARCHAR(20) DEFAULT 'inbound';
ALTER TABLE webhook_configs ADD COLUMN retry_count INTEGER DEFAULT 3;
ALTER TABLE webhook_configs ADD COLUMN retry_delay INTEGER DEFAULT 60;
ALTER TABLE webhook_configs ADD COLUMN last_error TEXT;

CREATE INDEX idx_webhooks_delivery_mode ON webhook_configs(delivery_mode);
```

**Migration Strategy:**
1. Create migrations on Day 1 (Sprint 1.1)
2. Test in development environment
3. Create rollback scripts
4. Document migration process
5. Apply during Sprint 1.1

---

## Docker Compose Changes

```yaml
# Add to docker-compose.yml

services:
  celery-worker:
    build: ./backend
    command: celery -A app.tasks worker --loglevel=info --concurrency=4
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    volumes:
      - ./backend:/app

  celery-beat:
    build: ./backend
    command: celery -A app.tasks beat --loglevel=info
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - DATABASE_URL=${DATABASE_URL}
    depends_on:
      - redis
      - postgres
    restart: unless-stopped
    volumes:
      - ./backend:/app

  flower:
    build: ./backend
    command: celery -A app.tasks flower --port=5555
    ports:
      - "5555:5555"
    environment:
      - CELERY_BROKER_URL=redis://redis:6379/0
      - CELERY_RESULT_BACKEND=redis://redis:6379/0
    depends_on:
      - redis
    restart: unless-stopped

  prometheus:
    image: prom/prometheus:latest
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
    restart: unless-stopped

volumes:
  prometheus_data:
```

**Setup Time:** 2 hours (included in Sprint 1.1)

---

## Success Criteria

### Functional Requirements
- [x] Async job system operational
- [x] Batch API handles 20+ repositories
- [x] Webhooks with retry and 99% delivery success
- [x] Scheduled analysis runs on time (±1 min)
- [x] 2+ external integrations (Slack + Jira/Linear)
- [x] 4+ export formats (SARIF, Markdown, HTML, CSV)
- [x] MCP integration with Phase 1 core
- [x] Health checks pass in production

### Quality Requirements
- [x] 210+ new tests (total: 420+ tests)
- [x] 95%+ test coverage on new code
- [x] API response time <200ms (p95)
- [x] Job processing <5min for typical repo
- [x] Zero critical security issues
- [x] Complete API documentation
- [x] WebSocket connections stable

### Integration Requirements
- [x] GitHub Action works in CI/CD
- [x] Slack notifications delivered <10s
- [x] Scheduled jobs execute reliably
- [x] MCP tools accessible from Claude Desktop
- [x] All exports validated against schemas

---

## What's Deferred to Phase 2.5

**Frontend Components (10 hours):**
- Job monitoring dashboard with live updates
- Schedule manager UI
- Webhook configuration wizard
- Integration setup wizards (OAuth flows)
- Export format selection UI

**Why Deferred:**
- API surface is complete and usable programmatically
- MCP provides alternative UI via Claude Desktop
- Frontend can be built independently without blocking
- Allows community contribution opportunity
- Reduces Phase 2 risk and timeline

**Phase 2.5 can run in parallel with Phase 3 planning**

---

## Risk Mitigation

### Risk: Database Migration Failures
**Mitigation:**
- Test migrations in dev environment first
- Create rollback scripts for each migration
- Backup database before applying migrations
- Apply during Sprint 1.1 (early in Phase 2)

### Risk: Celery Worker Scaling
**Mitigation:**
- Start with 2 workers, scale horizontally as needed
- Implement queue monitoring (Flower dashboard)
- Add job priorities (analysis > export > webhooks)
- Worker health checks in observability

### Risk: WebSocket Connection Limits
**Mitigation:**
- Limit to 10 clients per job
- 1-hour connection timeout
- Fallback to HTTP polling if WebSocket fails
- Document limitations clearly

### Risk: Integration OAuth Complexity
**Mitigation:**
- Use official SDKs (Slack SDK, Jira library)
- Clear error messages for OAuth failures
- Comprehensive OAuth setup documentation
- Provide test credentials for development

### Risk: Export Format Compatibility
**Mitigation:**
- Use official schemas (SARIF 2.1.0)
- Validation tests for each format
- Examples in documentation
- Schema versioning

---

## Testing Strategy

### Unit Tests (150+)
- Service layer logic
- Export format generation
- Webhook delivery logic
- Schedule parsing
- Job state transitions

### Integration Tests (50+)
- API endpoints
- Celery task execution (eager mode)
- External API mocking (responses library)
- Database operations
- MCP protocol integration

### End-to-End Tests (10+)
- Complete workflows:
  - Schedule → Analyze → Webhook → Slack
  - Batch operations
  - Export pipelines
  - MCP tool invocation

### Performance Tests
- Batch analysis of 50+ repos
- Concurrent job execution
- Webhook delivery under load
- Export generation time
- WebSocket connection handling

**Testing Infrastructure:**
- Celery eager mode for synchronous testing
- FastAPI test client for WebSocket testing
- `responses` library for HTTP mocking
- Fixtures for common test data

---

## Documentation Deliverables

1. **API Reference** (`docs/API_REFERENCE.md`)
   - Complete OpenAPI/Swagger documentation
   - All endpoints with examples
   - Authentication and error handling
   - Rate limiting documentation

2. **Integrations Guide** (`docs/INTEGRATIONS_GUIDE.md`)
   - Slack setup with OAuth flow
   - Jira/Linear configuration
   - GitHub Actions usage
   - Webhook configuration
   - Troubleshooting common issues

3. **Automation Guide** (`docs/AUTOMATION_GUIDE.md`)
   - Scheduling analysis tasks
   - Webhook event handling
   - CI/CD integration patterns
   - Batch operations guide

4. **Export Formats** (`docs/EXPORT_FORMATS.md`)
   - SARIF format specification
   - Markdown report structure
   - HTML dashboard usage
   - CSV/Excel schemas
   - Format selection guide

5. **MCP Integration** (Update existing docs)
   - Phase 2 MCP resources
   - Phase 2 MCP tools
   - Phase 2 MCP prompts
   - Usage examples from Claude Desktop

---

## Implementation Order

**Critical Path (77 hours):**
1. Async Job System (18h) - MUST complete first
2. Batch Operations (10h)
3. Scheduled Analysis (15h)
4. External Integrations (16h)
5. Enhanced Export (12h)
6. Integration Tests (6h)

**Parallel Work (21 hours):**
- Observability (5h) - Parallel to Sprint 1.1
- Webhooks (4h) - Parallel to Sprint 1.2
- MCP Integration (8h) - Parallel to Sprint 2.3
- Documentation (4h) - Parallel to Sprint 3.1

**Realistic Timeline:** 3.5 weeks (98 hours / 28 hours per week)

---

## Next Steps

**Immediate (Before Sprint 1.1):**
1. ✅ Approve revised plan
2. Setup Celery infrastructure (2h)
   - Add to docker-compose.yml
   - Test basic task execution
3. Design database migrations (1h)
   - Review schemas
   - Plan data migration strategy
4. Document existing webhooks (30min)

**Sprint 1.1 Start (Day 1):**
1. Create 4 database migrations
2. Configure Celery in backend
3. Begin job model implementation
4. Setup test infrastructure

---

## Approval Status

**Plan:** Phase 2 Revised - Option C (Hybrid)
**Estimated Effort:** 98 hours (3.5 weeks)
**Status:** ✅ APPROVED - Ready for Implementation

**Scope:**
- ✅ All 7 core API components
- ✅ MCP integration
- ⏳ Frontend deferred to Phase 2.5

**Next Milestone:** Sprint 1.1 - Async Job System (18 hours)

---

**Last Updated:** 2025-10-12
**Reviewed By:** Claude (Self-Review)
**Approved By:** User
**Target Completion:** 2025-11-05 (3.5 weeks)
