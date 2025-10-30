# Production Foundations Design

**Author**: Claude + Developer
**Date**: 2025-10-29
**Status**: Approved for Implementation
**Related Issues**: Ecosystem Integration Roadmap, Habit Coach Feature Request

## Executive Summary

This design document outlines a **sequential component hardening** approach to build production-grade infrastructure foundations for CommandCenter. The work focuses on hardening existing infrastructure (not building new features) to support future ecosystem integration and Habit Coach capabilities.

### Key Objectives

1. **Dagger Production Hardening**: Bring orchestration to production-grade quality
2. **Automated Knowledge Ingestion**: Build automated pipelines for knowledge collection
3. **Observability Layer**: Add comprehensive monitoring, logging, and alerting

### Timeline

- **Total Duration**: 9 weeks (3 weeks per phase)
- **Approach**: Complete each phase 100% before moving to next
- **Flexibility**: Iterative, no hard deadline

### Success Criteria

Production-grade foundations in place before building Habit Coach or ecosystem features, ensuring:
- Robust container orchestration with full visibility
- Automated knowledge gathering from multiple sources
- Comprehensive monitoring and alerting infrastructure

---

## Current State Assessment

### Infrastructure Maturity Analysis

| Component | Status | Maturity | Assessment |
|-----------|--------|----------|------------|
| **Dagger Orchestration** | 🟡 Partial | Basic | Works for development, lacks production features (logs, health checks, resource limits) |
| **KnowledgeBeast/RAG** | ✅ Functional | Production | v3.0 with PostgresBackend, ready for use |
| **Scheduled Jobs (Celery)** | ✅ Production | Production | Robust task queue, ready for ingestion tasks |
| **Knowledge Ingestion** | 🔴 Partial | Stub | Manual API only, no automation pipelines |

### Infrastructure Completeness: ~50%

**What We Have**:
- Celery task infrastructure ✅
- RAG/KnowledgeBeast backend ✅
- Basic Dagger orchestration 🟡
- Manual knowledge ingestion 🟡

**What's Missing**:
- Dagger production features (logging, health, resources, security)
- Automated ingestion pipelines (feeds, scrapers, webhooks, file watchers)
- Observability layer (metrics, tracing, alerting, analytics)

### Dependency on Foundations

Both the **Ecosystem Integration Roadmap** and **Habit Coach Feature Request** require:
1. Reliable container orchestration (Dagger hardening needed)
2. Automated knowledge collection (ingestion pipelines needed)
3. Production visibility (observability layer needed)

**Conclusion**: Build foundations first, then features.

---

## Overall Architecture & Sequencing

### Design Philosophy: Sequential Component Hardening

**Approach**: Complete each component to 100% production-grade quality before moving to the next.

**Why Sequential vs. Parallel**:
- **Solo developer + AI**: Context switching overhead is high
- **Quality over speed**: Each component fully tested and documented
- **Clear milestones**: Concrete completion criteria for each phase
- **Risk reduction**: Validate hardening approach before scaling

### Three-Phase Design

```
Phase A (Weeks 1-3)          Phase B (Weeks 4-6)          Phase C (Weeks 7-9)
┌─────────────────────┐     ┌─────────────────────┐     ┌─────────────────────┐
│ Dagger Production   │────▶│ Automated Knowledge │────▶│ Observability       │
│ Hardening           │     │ Ingestion           │     │ Layer               │
│                     │     │                     │     │                     │
│ • Log retrieval     │     │ • Celery tasks      │     │ • Prometheus        │
│ • Health checks     │     │ • Feed scrapers     │     │ • Grafana           │
│ • Resource limits   │     │ • Webhooks          │     │ • Tracing           │
│ • Security          │     │ • File watchers     │     │ • Alerting          │
│ • Error handling    │     │ • Source priorities │     │ • Analytics         │
└─────────────────────┘     └─────────────────────┘     └─────────────────────┘
         ✓                           ✓                           ✓
    100% Complete              100% Complete              100% Complete
```

### Sequencing Rationale

1. **Phase A First**: Dagger orchestration is the foundation for all infrastructure work. Must have visibility and control before building on top.

2. **Phase B Second**: Automated ingestion requires reliable orchestration. Knowledge pipelines will stress-test the hardened Dagger layer.

3. **Phase C Last**: Observability benefits from real workloads (ingestion tasks) to monitor. Provides visibility into both Dagger and ingestion systems.

---

## Phase A: Dagger Production Hardening

**Duration**: Weeks 1-3
**Status**: Ready to implement
**Prerequisites**: None (foundation layer)

### Goals

Transform basic Dagger orchestration into production-grade container management with full visibility, control, and reliability.

### Current State

**What Exists** (`hub/backend/app/dagger_modules/commandcenter.py`):
- CommandCenterStack class with service definitions
- Basic container lifecycle (start/stop)
- Port mapping and volume mounts
- Environment variable injection

**What's Missing**:
- Log retrieval and streaming
- Health checks and readiness probes
- Resource limits (CPU, memory)
- Security hardening (non-root, secrets)
- Error handling and retries
- Network isolation and service discovery

### Scope

#### 1. Log Retrieval & Streaming

**Requirement**: Real-time access to container logs from Hub UI.

**Implementation**:
- Add `get_logs()` method to CommandCenterStack
- Support streaming mode (follow logs) and snapshot mode
- Filter by service (postgres, redis, backend, frontend)
- Tail last N lines for quick debugging
- Expose via Hub API: `GET /api/projects/{id}/logs/{service}`

**Test Coverage**:
- Unit tests: Log retrieval methods
- Integration tests: Log streaming across services
- Error cases: Container not found, log file missing

#### 2. Health Checks & Readiness Probes

**Requirement**: Know when services are actually ready, not just "running".

**Implementation**:
- Define health check endpoints:
  - Postgres: `pg_isready` command
  - Redis: `redis-cli ping`
  - Backend: `GET /health` (FastAPI)
  - Frontend: HTTP 200 on root path
- Add `health_status()` method returning per-service status
- Implement startup ordering: postgres → redis → backend → frontend
- Add timeout handling (fail after N seconds)
- Expose via Hub API: `GET /api/projects/{id}/health`

**Test Coverage**:
- Unit tests: Health check logic
- Integration tests: Startup ordering
- Failure scenarios: Service crashes, timeouts

#### 3. Resource Limits

**Requirement**: Prevent runaway containers from consuming all host resources.

**Implementation**:
- Define resource limits per service:
  - Postgres: 1 CPU, 2GB memory
  - Redis: 0.5 CPU, 512MB memory
  - Backend: 1 CPU, 1GB memory
  - Frontend: 0.5 CPU, 512MB memory
- Make limits configurable via CommandCenterConfig
- Add resource monitoring (current usage vs. limits)
- Expose via Hub API: `GET /api/projects/{id}/resources`

**Test Coverage**:
- Unit tests: Resource limit configuration
- Integration tests: Limits enforced by Dagger
- Monitoring: Usage reported correctly

#### 4. Security Hardening

**Requirement**: Follow container security best practices.

**Implementation**:
- Run services as non-root users (UID mapping)
- Use read-only filesystems where possible
- Implement secret injection (not environment variables)
- Add network policies (service isolation)
- Scan images for vulnerabilities (Trivy integration)
- Document security configuration in `docs/SECURITY.md`

**Test Coverage**:
- Unit tests: Security configuration applied
- Integration tests: Non-root execution verified
- Audit: Security checklist validation

#### 5. Error Handling & Retries

**Requirement**: Graceful degradation and automatic recovery.

**Implementation**:
- Retry transient failures (network timeouts, temporary errors)
- Exponential backoff for retries (1s, 2s, 4s, 8s)
- Circuit breaker for persistent failures
- Clear error messages with troubleshooting hints
- Log all errors with structured context
- Add `restart_service()` method for recovery

**Test Coverage**:
- Unit tests: Retry logic
- Integration tests: Recovery from failures
- Chaos testing: Simulate network partitions, OOM kills

### Deliverables

1. **Code**: Enhanced CommandCenterStack with all features above
2. **Tests**: 74+ tests → 120+ tests (full coverage of new features)
3. **Documentation**: Updated `docs/DAGGER_ARCHITECTURE.md` with production features
4. **API**: Hub API endpoints for logs, health, resources
5. **UI**: Hub frontend components for log viewing, health dashboard

### Success Criteria

- [ ] All services have health checks with accurate status reporting
- [ ] Logs retrievable via API for all services
- [ ] Resource limits enforced and monitored
- [ ] Security checklist 100% complete
- [ ] Error recovery demonstrated (automatic restarts work)
- [ ] Test coverage >90% for orchestration code
- [ ] Documentation complete and reviewed

---

## Phase B: Automated Knowledge Ingestion

**Duration**: Weeks 4-6
**Status**: Pending Phase A completion
**Prerequisites**: Phase A (Dagger hardening complete)

### Goals

Build automated pipelines to continuously gather knowledge from multiple sources without manual intervention.

### Current State

**What Exists**:
- KnowledgeBeast RAG backend (production-ready)
- Celery task infrastructure (production-ready)
- Manual ingestion API (`POST /api/knowledge/documents`)

**What's Missing**:
- Scheduled scrapers (RSS, blogs, docs sites)
- Webhook receivers (GitHub, external sources)
- File system watchers (local document folders)
- Source priority configuration
- Ingestion monitoring and error handling

### Scope

#### 1. Celery Ingestion Tasks

**Requirement**: Background tasks for knowledge collection and processing.

**Implementation**:
- Create `backend/app/tasks/ingestion_tasks.py`:
  - `scrape_rss_feed(feed_url, project_id)`
  - `scrape_documentation(doc_url, project_id)`
  - `process_github_webhook(payload, project_id)`
  - `watch_file_directory(path, project_id)`
  - `bulk_import_documents(source, project_id)`
- Integrate with existing Celery worker
- Add task scheduling (cron-style)
- Implement task chaining (scrape → process → embed → store)
- Add retry logic with exponential backoff

**Test Coverage**:
- Unit tests: Task logic isolated
- Integration tests: End-to-end ingestion flows
- Celery tests: Scheduling and chaining

#### 2. Feed Scrapers (RSS, Atom, JSON Feed)

**Requirement**: Monitor RSS feeds for new content.

**Implementation**:
- Add `FeedScraperService` in `backend/app/services/`
- Support RSS 2.0, Atom, JSON Feed formats
- Parse metadata (title, author, date, tags)
- Deduplicate based on URL/GUID
- Extract article content (full text, not just summary)
- Handle authentication (HTTP Basic, API keys)
- Schedule scraping (configurable intervals: hourly, daily, weekly)

**Test Coverage**:
- Unit tests: Feed parsing logic
- Integration tests: Scrape → RAG storage
- Mock feeds: Test various formats

#### 3. Documentation Scrapers

**Requirement**: Clone and index documentation sites.

**Implementation**:
- Add `DocumentationScraperService`
- Support common doc systems:
  - Docusaurus
  - MkDocs
  - Sphinx
  - GitBook
- Respect robots.txt
- Follow sitemap.xml for efficient crawling
- Extract structured content (headings, code blocks)
- Handle version-specific docs (e.g., v1.0, v2.0)

**Test Coverage**:
- Unit tests: URL parsing, content extraction
- Integration tests: Scrape public docs (test mode)
- Mock servers: Test doc system parsers

#### 4. Webhook Receivers

**Requirement**: Accept push notifications from external sources.

**Implementation**:
- Add webhook endpoints in `backend/app/routers/webhooks.py`:
  - `POST /api/webhooks/github` (repo updates)
  - `POST /api/webhooks/generic` (custom sources)
- Verify webhook signatures (security)
- Queue ingestion tasks asynchronously
- Return 200 OK immediately (non-blocking)
- Add webhook configuration UI (URLs, secrets)

**Test Coverage**:
- Unit tests: Webhook validation
- Integration tests: GitHub webhook → ingestion
- Security tests: Signature verification

#### 5. File System Watchers

**Requirement**: Monitor local directories for new documents.

**Implementation**:
- Add `FileWatcherService` using `watchdog` library
- Monitor configured paths (e.g., `~/Documents/Research`)
- Trigger ingestion on file changes (create, modify)
- Filter by file type (PDF, MD, TXT, DOCX)
- Debounce events (avoid duplicate processing)
- Respect `.gitignore`-style exclusion rules

**Test Coverage**:
- Unit tests: File event handling
- Integration tests: File changes → ingestion
- Edge cases: Rapid file changes, large files

#### 6. Source Priority & Configuration

**Requirement**: Control which sources are active and their importance.

**Implementation**:
- Add `IngestionSource` model in database:
  - type (RSS, docs, webhook, file)
  - url/path
  - schedule (cron expression)
  - priority (1-10)
  - enabled (boolean)
  - last_run (timestamp)
- UI for managing sources (`Settings → Knowledge Sources`)
- Priority affects RAG retrieval (higher priority = higher relevance)
- Admin can pause sources without deleting

**Test Coverage**:
- Unit tests: Source CRUD operations
- Integration tests: Priority in RAG queries
- UI tests: Source management flows

### Deliverables

1. **Code**: Ingestion services, Celery tasks, webhook endpoints, file watchers
2. **Tests**: 50+ new tests covering all ingestion flows
3. **Documentation**: `docs/KNOWLEDGE_INGESTION.md` with setup instructions
4. **UI**: Settings page for source management
5. **Database**: New tables for ingestion sources and job tracking

### Success Criteria

- [ ] RSS feeds scraped automatically on schedule
- [ ] Documentation sites indexed successfully
- [ ] GitHub webhooks trigger ingestion
- [ ] File watchers detect and process new documents
- [ ] Source priority reflected in RAG results
- [ ] Error handling logs failures without crashing
- [ ] Test coverage >85% for ingestion code
- [ ] Documentation complete with examples

---

## Phase C: Observability Layer

**Duration**: Weeks 7-9
**Status**: Pending Phases A & B completion
**Prerequisites**: Phases A & B (real workloads to observe)

### Goals

Add comprehensive monitoring, logging, tracing, and alerting to provide full visibility into production systems.

### Current State

**What Exists**:
- Basic application logs (stdout)
- Docker Compose logs (ephemeral)
- No metrics collection
- No distributed tracing
- No alerting

**What's Missing**:
- Prometheus metrics collection
- Grafana dashboards
- Distributed tracing (Jaeger/Tempo)
- Centralized logging (Loki)
- Alert manager and notification channels
- Analytics and reporting

### Scope

#### 1. Prometheus Metrics

**Requirement**: Collect and store time-series metrics.

**Implementation**:
- Add Prometheus to docker-compose stack
- Instrument backend with `prometheus_client`:
  - Request rate, latency, error rate (RED metrics)
  - Database connection pool usage
  - Celery queue depth and task duration
  - RAG query performance (retrieval time, result count)
- Instrument frontend with custom metrics:
  - Page load time
  - API response time
  - Component render time
- Add `/metrics` endpoint to backend
- Configure scrape targets in Prometheus

**Test Coverage**:
- Unit tests: Metric registration
- Integration tests: Metrics scraped by Prometheus
- Load tests: Metrics under stress

#### 2. Grafana Dashboards

**Requirement**: Visualize metrics in real-time dashboards.

**Implementation**:
- Add Grafana to docker-compose stack
- Create pre-configured dashboards:
  - **System Overview**: CPU, memory, disk, network
  - **Application Health**: Request rate, latency, errors
  - **Celery Tasks**: Queue depth, task duration, failure rate
  - **RAG Performance**: Query latency, result quality, cache hit rate
  - **Ingestion Pipeline**: Sources active, documents processed, errors
- Import dashboards automatically on startup
- Add alerting rules in Grafana

**Test Coverage**:
- Integration tests: Dashboards load correctly
- Visual tests: Screenshots of dashboards (regression)

#### 3. Distributed Tracing

**Requirement**: Trace requests across services for debugging.

**Implementation**:
- Add Jaeger or Tempo to stack
- Instrument backend with OpenTelemetry:
  - Trace FastAPI requests
  - Trace database queries
  - Trace Celery task execution
  - Trace RAG retrieval pipeline
- Propagate trace context across services
- Add trace ID to logs (correlation)
- UI for viewing traces in Jaeger

**Test Coverage**:
- Integration tests: Traces captured end-to-end
- Performance tests: Tracing overhead <5%

#### 4. Centralized Logging (Loki)

**Requirement**: Aggregate logs from all services in one place.

**Implementation**:
- Add Loki to stack for log aggregation
- Configure Promtail to ship logs from containers
- Structure logs as JSON (easier querying)
- Add log labels (service, environment, level)
- Query logs from Grafana (unified view with metrics)
- Implement log retention policy (30 days)

**Test Coverage**:
- Integration tests: Logs shipped to Loki
- Query tests: Find specific log entries

#### 5. Alerting & Notifications

**Requirement**: Proactive alerts for issues before users notice.

**Implementation**:
- Configure Alertmanager (Prometheus ecosystem)
- Define alert rules:
  - High error rate (>1% of requests)
  - High latency (p95 >500ms)
  - Celery queue backlog (>100 tasks)
  - Disk usage (>80%)
  - Service down (health check failures)
- Notification channels:
  - Email (SMTP)
  - Slack (webhook)
  - PagerDuty (critical alerts)
- Alert grouping and deduplication

**Test Coverage**:
- Unit tests: Alert rule evaluation
- Integration tests: Alerts triggered correctly
- End-to-end tests: Notifications delivered

#### 6. Analytics & Reporting

**Requirement**: Track usage patterns and system health over time.

**Implementation**:
- Add analytics database (PostgreSQL with TimescaleDB)
- Track key metrics:
  - Daily active users
  - Knowledge queries per day
  - Most searched topics
  - Ingestion source effectiveness
  - System uptime and availability
- Generate weekly reports (automated)
- Export data for business intelligence tools

**Test Coverage**:
- Unit tests: Analytics data collection
- Integration tests: Reports generated
- Data validation: Metrics accurate

### Deliverables

1. **Code**: Prometheus, Grafana, Jaeger, Loki, Alertmanager integration
2. **Tests**: 40+ tests for observability components
3. **Documentation**: `docs/OBSERVABILITY.md` with setup and usage guide
4. **Dashboards**: 5+ Grafana dashboards (pre-configured)
5. **Alerts**: 10+ alert rules for common issues
6. **Runbooks**: Troubleshooting guides for each alert

### Success Criteria

- [ ] Prometheus collecting metrics from all services
- [ ] Grafana dashboards displaying real-time data
- [ ] Distributed tracing showing request flows
- [ ] Centralized logging with full-text search
- [ ] Alerts triggering for simulated failures
- [ ] Test coverage >80% for observability code
- [ ] Documentation complete with runbooks
- [ ] Analytics reports generated automatically

---

## Success Criteria (Overall)

### Technical Milestones

- [ ] **Phase A Complete**: Dagger orchestration production-ready
- [ ] **Phase B Complete**: Automated ingestion running continuously
- [ ] **Phase C Complete**: Full observability in place

### Quality Metrics

- [ ] Test coverage >85% across all three phases
- [ ] Zero P0/P1 bugs in hardened infrastructure
- [ ] Documentation complete for all new features
- [ ] Code review approval on all implementation PRs

### Operational Readiness

- [ ] Runbooks created for common operational tasks
- [ ] Disaster recovery plan documented and tested
- [ ] Monitoring alerts configured and validated
- [ ] Performance benchmarks established (baselines)

### Validation

- [ ] Each phase demonstrates 100% completion before moving to next
- [ ] End-to-end smoke test passes (all systems working together)
- [ ] Load testing shows acceptable performance under stress
- [ ] Security audit passes (no critical vulnerabilities)

---

## Timeline & Dependencies

### Phase A: Weeks 1-3 (Dagger Hardening)

**Week 1: Logging & Health Checks**
- Days 1-2: Log retrieval implementation
- Days 3-4: Health check system
- Day 5: Testing and documentation

**Week 2: Resources & Security**
- Days 1-2: Resource limits and monitoring
- Days 3-4: Security hardening
- Day 5: Testing and documentation

**Week 3: Error Handling & Polish**
- Days 1-2: Retry logic and circuit breakers
- Days 3-4: Hub UI updates
- Day 5: End-to-end validation

### Phase B: Weeks 4-6 (Ingestion)

**Week 4: Feed Scrapers**
- Days 1-2: Feed scraper service
- Days 3-4: Documentation scraper
- Day 5: Testing

**Week 5: Webhooks & Watchers**
- Days 1-2: Webhook receivers
- Days 3-4: File system watchers
- Day 5: Testing

**Week 6: Integration & Configuration**
- Days 1-2: Source management UI
- Days 3-4: Priority system
- Day 5: End-to-end validation

### Phase C: Weeks 7-9 (Observability)

**Week 7: Metrics & Dashboards**
- Days 1-2: Prometheus setup
- Days 3-4: Grafana dashboards
- Day 5: Testing

**Week 8: Tracing & Logging**
- Days 1-2: Distributed tracing
- Days 3-4: Centralized logging
- Day 5: Testing

**Week 9: Alerting & Analytics**
- Days 1-2: Alert rules and notifications
- Days 3-4: Analytics and reporting
- Day 5: Final validation

### Dependencies

**Blockers**:
- Phase B requires Phase A completion (relies on hardened orchestration)
- Phase C requires Phase B completion (needs real workloads to observe)

**External Dependencies**:
- None (all work internal to CommandCenter)

**Resource Dependencies**:
- Solo developer + AI assistance
- No additional hardware required (local development sufficient)

---

## Risk Assessment

### Technical Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Dagger SDK limitations | Medium | High | Investigate SDK capabilities early, have fallback to Docker API |
| Performance degradation from observability overhead | Medium | Medium | Benchmark each addition, optimize hot paths |
| Ingestion pipeline overwhelms RAG backend | Low | High | Implement rate limiting, backpressure mechanisms |
| Security vulnerabilities in scrapers | Medium | High | Regular dependency updates, security scanning |

### Schedule Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Phase extends beyond 3 weeks | Medium | Low | Scope reduction, move non-critical features to follow-up |
| Unexpected complexity in Dagger hardening | Medium | Medium | Incremental delivery, validate approach early |
| Testing takes longer than expected | High | Low | Test continuously during development, not at end |

### Operational Risks

| Risk | Likelihood | Impact | Mitigation |
|------|-----------|--------|------------|
| Observability system becomes too complex | Medium | Medium | Start simple, add complexity only when needed |
| Alert fatigue from too many notifications | High | Medium | Tune alert thresholds carefully, use escalation tiers |
| Documentation falls out of sync with code | High | Low | Update docs in same PR as code changes |

### Risk Response Strategy

- **High Impact Risks**: Address in design phase, validate early
- **High Likelihood Risks**: Monitor closely, have contingency plans
- **Low Impact Risks**: Accept and document

---

## Next Steps

### Immediate Actions

1. ✅ **Design document written** (this document)
2. **Set up git worktree** for implementation isolation
3. **Create detailed implementation plan** using superpowers:writing-plans skill
4. **Begin Phase A implementation** starting with logging system

### Before Starting Phase A

- [ ] Review this design document with stakeholders
- [ ] Set up git worktree: `feature/production-foundations`
- [ ] Create GitHub issue/project board for tracking
- [ ] Write detailed implementation plan (task breakdown)
- [ ] Establish testing strategy for each component

### Definition of Done

**Phase A**: All acceptance criteria met, tests passing, docs complete, code reviewed
**Phase B**: All acceptance criteria met, tests passing, docs complete, code reviewed
**Phase C**: All acceptance criteria met, tests passing, docs complete, code reviewed

**Project**: All three phases complete, end-to-end validation passes, production deployment successful

---

## Appendix

### Related Documents

- `docs/plans/2025-10-29-ecosystem-integration-roadmap.md` - Full feature roadmap
- `docs/plans/2025-10-29-commandcenter-habit-coach-feature-request.md` - Habit Coach design
- `docs/DAGGER_ARCHITECTURE.md` - Current Dagger implementation
- `docs/CLAUDE.md` - Project overview and setup

### Glossary

- **Dagger SDK**: Python SDK for type-safe container orchestration
- **KnowledgeBeast**: Internal RAG library (v3.0) with PostgreSQL backend
- **Sequential Hardening**: Approach of completing each component to 100% before moving on
- **Observability**: Monitoring, logging, tracing, and alerting infrastructure
- **RED Metrics**: Request rate, Error rate, Duration (standard monitoring framework)

### Revision History

| Date | Version | Changes | Author |
|------|---------|---------|--------|
| 2025-10-29 | 1.0 | Initial design document | Claude + Developer |

---

**Status**: ✅ Ready for Implementation
**Next Phase**: Create implementation plan for Phase A
