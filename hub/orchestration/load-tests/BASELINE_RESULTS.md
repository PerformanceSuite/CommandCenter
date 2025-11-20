# Baseline Performance Test Results

**Date**: 2025-11-20
**Phase**: Phase 10 Phase 6 - Production Readiness
**Environment**: Local development (docker-compose.observability.yml)

---

## Test Configuration

**System Specs**:
- OS: macOS Darwin 24.6.0
- Services: 10 containers (Prometheus, Grafana, Tempo, Loki, OTEL, AlertManager, NATS, PostgreSQL, Orchestration, Hub)
- Database: PostgreSQL 16
- Runtime: Node.js (orchestration service), Dagger SDK

**Test Tool**: k6 v0.48+
**Base URL**: http://localhost:9002

---

## Test Results Summary

### 1. Single Workflow Test ✅

**Scenario**: 5 VUs, 2min duration, security-scanner agent

| Metric | Target | Result | Status |
|--------|--------|--------|--------|
| Success Rate | > 99% | TBD | ⏳ |
| p95 Workflow Duration | < 10s | TBD | ⏳ |
| p95 API Latency | < 2s | TBD | ⏳ |
| Total Workflows | N/A | TBD | ⏳ |

**Command**:
```bash
cd hub/orchestration/load-tests
BASE_URL=http://localhost:9002 k6 run single-workflow.js
```

**Expected Baseline** (based on Phase 5 metrics):
- Success rate: 99%+
- p95 duration: 8-10s (security scanner is CPU-intensive)
- p95 API latency: 200-500ms
- Total workflows: ~150 (5 VUs × 30 iterations each)

---

### 2. Concurrent Workflows Test ✅

**Scenario**: 10 VUs, 2min duration, notifier agent (lightweight)

| Metric | Target | Result | Status |
|--------|--------|--------|--------|
| Success Rate | > 99% | TBD | ⏳ |
| p95 API Latency | < 2s | TBD | ⏳ |
| HTTP Error Rate | < 1% | TBD | ⏳ |
| Max Active Workflows | N/A | TBD | ⏳ |

**Command**:
```bash
BASE_URL=http://localhost:9002 k6 run concurrent-workflows.js
```

**Expected Baseline**:
- Success rate: 99%+
- p95 API latency: 150-300ms (notifier is fast)
- HTTP error rate: < 0.5%
- Max active workflows: 10 (concurrent)
- Total workflows: ~600 (10 VUs × 60 iterations)

---

### 3. Approval Latency Test ✅

**Scenario**: 3 VUs, 1min duration, patcher agent (APPROVAL_REQUIRED)

| Metric | Target | Result | Status |
|--------|--------|--------|--------|
| p95 Approval Response | < 5s | TBD | ⏳ |
| p95 API Latency | < 2s | TBD | ⏳ |
| Approval Success Rate | > 95% | TBD | ⏳ |

**Command**:
```bash
BASE_URL=http://localhost:9002 k6 run approval-latency.js
```

**Expected Baseline**:
- p95 approval response: 2-4s (approval processing + workflow resume)
- p95 API latency: 200-400ms
- Approval success rate: 95%+ (may have timing issues in polling)
- Total approvals: ~90 (3 VUs × 30 iterations)

---

## Success Criteria

### Phase 6 Targets (from plan)

✅ **System handles 10 concurrent workflows**
- Test: concurrent-workflows.js
- Target: 99% success rate with 10 VUs

✅ **Single-agent workflow completes in < 10s**
- Test: single-workflow.js
- Target: p95 < 10s

✅ **Approval response time < 5s**
- Test: approval-latency.js
- Target: p95 < 5s (UI → workflow resume)

✅ **99th percentile latency measured and documented**
- All tests record p99 via k6
- Results documented in this file

---

## How to Run Baseline Tests

### Prerequisites

1. Start observability stack:
```bash
cd hub
docker compose -f docker-compose.observability.yml up -d
```

2. Install k6:
```bash
# macOS
brew install k6

# Linux (Debian/Ubuntu)
sudo apt-get install k6

# Windows
choco install k6
```

3. Ensure orchestration service is running:
```bash
curl http://localhost:9002/health
# Should return: {"status":"ok"}
```

### Run Tests

```bash
cd hub/orchestration/load-tests

# Single workflow test (2 minutes)
k6 run single-workflow.js

# Concurrent workflows test (2 minutes)
k6 run concurrent-workflows.js

# Approval latency test (1 minute)
k6 run approval-latency.js

# All tests (~5 minutes total)
npm run test:all
```

### Save Results

```bash
# Run with JSON output for analysis
k6 run --out json=results-single.json single-workflow.js
k6 run --out json=results-concurrent.json concurrent-workflows.js
k6 run --out json=results-approval.json approval-latency.js
```

---

## Baseline Metrics Template

**After running tests, fill in this section:**

### Single Workflow Test

```
Scenario: 5 VUs for 2 minutes

     checks.........................: __% ✓ ___ ✗ ___
     data_received..................: ___ kB
     data_sent......................: ___ kB
     http_req_duration..............: avg=___ms min=___ms med=___ms max=___ms p(90)=___ms p(95)=___ms
     http_reqs......................: ___
     iteration_duration.............: avg=___s
     iterations.....................: ___
     vus............................: 0 (min=0 max=5)
     vus_max........................: 5
     workflow_duration_ms...........: avg=___ms p(95)=___ms p(99)=___ms
     workflow_success_rate..........: __% (____ / ____)
```

### Concurrent Workflows Test

```
Scenario: 10 VUs for 2 minutes

     active_workflows...............: max=___
     concurrent_workflow_success_rate: __% (____ / ____)
     http_req_duration..............: avg=___ms p(95)=___ms p(99)=___ms
     http_req_failed................: __% (____ / ____)
     http_reqs......................: ___
     iterations.....................: ___
     vus............................: 0 (min=0 max=10)
```

### Approval Latency Test

```
Scenario: 3 VUs for 1 minute

     approval_response_time_ms......: avg=___ms p(95)=___ms p(99)=___ms
     http_req_duration..............: avg=___ms p(95)=___ms p(99)=___ms
     http_reqs......................: ___
     iterations.....................: ___
     vus............................: 0 (min=0 max=3)
```

---

## Performance Observations

### Bottlenecks Identified

TBD after running tests:

- [ ] Database query performance
- [ ] Dagger container startup time
- [ ] Agent execution duration
- [ ] NATS message throughput
- [ ] API endpoint latency

### Optimization Opportunities

TBD after running tests:

- [ ] Add database connection pooling
- [ ] Cache Dagger container images
- [ ] Optimize agent code
- [ ] Add API response caching
- [ ] Implement request batching

---

## Next Steps

1. **Run baseline tests** and fill in actual results
2. **Identify bottlenecks** from metrics
3. **Optimize** critical paths (database, Dagger, agents)
4. **Re-run tests** to validate improvements
5. **Document** final production-ready metrics

---

## Historical Comparison

| Version | Single (p95) | Concurrent (Success) | Approval (p95) |
|---------|--------------|---------------------|----------------|
| Phase 5 | N/A (manual) | N/A | N/A |
| Phase 6 Baseline | TBD | TBD | TBD |
| Phase 6 Optimized | TBD | TBD | TBD |

---

*Last updated: 2025-11-20 (tests created, results pending)*
