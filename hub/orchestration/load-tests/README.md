# Load Testing Suite

Performance and load testing for the orchestration service using k6.

## Prerequisites

Install k6:

```bash
# macOS
brew install k6

# Linux
sudo gpg -k
sudo gpg --no-default-keyring --keyring /usr/share/keyrings/k6-archive-keyring.gpg --keyserver hkp://keyserver.ubuntu.com:80 --recv-keys C5AD17C747E3415A3642D57D77C6C491D6AC1D69
echo "deb [signed-by=/usr/share/keyrings/k6-archive-keyring.gpg] https://dl.k6.io/deb stable main" | sudo tee /etc/apt/sources.list.d/k6.list
sudo apt-get update
sudo apt-get install k6

# Windows
choco install k6
```

## Test Scenarios

### 1. Single Workflow Test (`single-workflow.js`)

**Goal**: Measure single-agent workflow performance under moderate load

**Scenario**:
- 5 virtual users (VUs)
- Each VU creates and executes a security-scanner workflow
- Polls for completion (max 30s)
- Records workflow duration and success rate

**Thresholds**:
- ✅ 99% success rate
- ✅ p95 workflow duration < 10s
- ✅ p95 API latency < 2s

**Run**:
```bash
npm run test:single
# Or with custom URL
BASE_URL=http://localhost:9002 k6 run single-workflow.js
```

**Expected Output**:
```
     ✓ workflow_success_rate.........: 99.00%
     ✓ workflow_duration_ms..........: avg=3.2s p(95)=8.5s
     ✓ http_req_duration.............: avg=150ms p(95)=450ms
```

### 2. Concurrent Workflows Test (`concurrent-workflows.js`)

**Goal**: Test system stability with 10 concurrent workflows

**Scenario**:
- 10 VUs running continuously for 2 minutes
- Each VU creates and triggers a simple notifier workflow
- Measures concurrent workflow handling
- Tracks active workflows counter

**Thresholds**:
- ✅ 99% success rate
- ✅ p95 API latency < 2s
- ✅ < 1% HTTP errors

**Run**:
```bash
npm run test:concurrent
```

**Expected Output**:
```
     ✓ concurrent_workflow_success_rate: 99.50%
     ✓ active_workflows.................: max=10
     ✓ http_req_failed..................: 0.2%
```

### 3. Approval Latency Test (`approval-latency.js`)

**Goal**: Measure approval workflow response time

**Scenario**:
- 3 VUs for 1 minute
- Create workflow with APPROVAL_REQUIRED agent (patcher)
- Wait for PENDING_APPROVAL state
- Approve and measure time to workflow resume
- Records approval response time

**Thresholds**:
- ✅ p95 approval response < 5s
- ✅ p95 API latency < 2s

**Run**:
```bash
npm run test:approval
```

**Expected Output**:
```
     ✓ approval_response_time_ms.....: avg=2.1s p(95)=4.2s
     ✓ http_req_duration.............: avg=180ms p(95)=520ms
```

## Running All Tests

```bash
npm run test:all
```

## Custom Configuration

### Change Base URL

```bash
BASE_URL=http://production:9002 k6 run single-workflow.js
```

### Increase Load

Edit the test file's `options` object:

```javascript
export const options = {
  stages: [
    { duration: '1m', target: 20 },   // 20 VUs instead of 5
    { duration: '5m', target: 20 },
    { duration: '1m', target: 0 },
  ],
};
```

### Change Thresholds

```javascript
thresholds: {
  'workflow_success_rate': ['rate>0.95'],  // 95% instead of 99%
  'workflow_duration_ms': ['p(95)<15000'], // 15s instead of 10s
},
```

## Metrics Collected

### Standard k6 Metrics

- `http_req_duration`: HTTP request latency
- `http_req_failed`: HTTP failure rate
- `http_reqs`: Total HTTP requests
- `vus`: Active virtual users
- `vus_max`: Max virtual users

### Custom Metrics

- `workflow_success_rate`: % of workflows that complete successfully
- `workflow_duration_ms`: Time from trigger to completion
- `concurrent_workflow_success_rate`: Success rate under concurrent load
- `active_workflows`: Number of workflows running simultaneously
- `approval_response_time_ms`: Time from approval to workflow resume

## Interpreting Results

### Success Criteria

✅ **Pass**: All thresholds met
- Single workflow: p95 < 10s, 99% success
- Concurrent: 99% success, < 1% errors
- Approval: p95 response < 5s

❌ **Fail**: Any threshold violated
- Investigate failed checks
- Review orchestration service logs
- Check database connection pool
- Verify Dagger container capacity

### Performance Baselines

Based on Phase 5 observability data:

| Metric | Target | Baseline |
|--------|--------|----------|
| Single workflow (notifier) | < 10s p95 | ~3s avg |
| Single workflow (scanner) | < 10s p95 | ~8s avg |
| Concurrent workflows (10) | 99% success | Expected |
| Approval response | < 5s p95 | ~2s avg |
| API latency | < 2s p95 | ~200ms avg |

### Common Issues

**High latency (> 10s p95)**:
- Check Dagger executor performance
- Review agent container build times
- Verify NATS connection health

**Low success rate (< 99%)**:
- Check orchestration service logs
- Verify database migrations applied
- Test agent executables manually

**Approval timeout**:
- Check workflow approval system
- Verify approval API endpoints
- Review WebSocket connections (if used)

## CI/CD Integration

Add to GitHub Actions:

```yaml
- name: Load Test
  run: |
    cd hub/orchestration/load-tests
    k6 run single-workflow.js --out json=results.json
    k6 run concurrent-workflows.js --out json=results-concurrent.json
```

## Advanced Usage

### Generate HTML Report

```bash
k6 run --out json=results.json single-workflow.js
# Convert to HTML with k6-reporter (install separately)
```

### Cloud Execution

```bash
k6 cloud single-workflow.js
```

### Stress Testing

```bash
k6 run --vus 50 --duration 10m concurrent-workflows.js
```

## Next Steps

1. Run baseline tests and document results
2. Identify bottlenecks from metrics
3. Optimize slow agents or database queries
4. Re-run tests to validate improvements
5. Set up continuous performance monitoring
