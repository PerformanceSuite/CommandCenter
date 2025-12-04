# Phase 10 Phase 6: Production Readiness Implementation Plan

**Created**: 2025-11-20
**Duration**: Week 9-10 (2 weeks estimated)
**Status**: Planning
**Dependencies**: Phase 5 (Observability) ✅ Complete

---

## Overview

Phase 6 focuses on hardening the agent orchestration system for production use through additional agents, load testing, comprehensive documentation, and security auditing.

**Goal**: Production-ready agent orchestration with proven reliability, security, and documentation.

---

## Success Criteria

### Functional
- ✅ 3 additional agents deployed (compliance-checker, patcher, code-reviewer)
- ✅ All agents tested with real workflows
- ✅ Approval system tested with high-risk operations
- ✅ End-to-end workflow execution validated

### Performance
- ✅ System handles 10 concurrent workflows
- ✅ Single-agent workflow completes in < 10s
- ✅ 5-node DAG completes in < 30s
- ✅ Approval response time < 5s (UI → workflow resume)
- ✅ 99th percentile latency measured and documented

### Observability
- ✅ All workflows traced in Tempo/Grafana
- ✅ Metrics dashboards populated with real data
- ✅ Alert rules tested and firing correctly
- ✅ Logs accessible and searchable

### Safety
- ✅ High-risk actions require approval (patcher agent validation)
- ✅ Agents cannot access host filesystem
- ✅ Agents cannot communicate with other containers
- ✅ Secrets never appear in logs or outputs
- ✅ Input validation prevents injection attacks

### Documentation
- ✅ Agent development guide complete
- ✅ Workflow creation guide complete
- ✅ API documentation current
- ✅ Runbooks for common issues
- ✅ Architecture diagrams updated

---

## Implementation Tasks

### Track 1: Additional Agents (Week 9, Days 1-3)

#### Task 1: Compliance Checker Agent
**Estimate**: 4 hours

Create agent that validates code/config against compliance rules.

**Deliverables**:
- `hub/orchestration/agents/compliance-checker/`
  - `agent.ts` - Main agent logic
  - `rules/` - Compliance rule definitions
    - `license-check.ts` - Verify OSS license compatibility
    - `security-headers.ts` - Check HTTP security headers
    - `env-vars.ts` - Ensure no secrets in code
  - `package.json` - Dependencies (eslint, checkov, semgrep)
  - `README.md` - Agent documentation

**Agent Spec**:
```typescript
{
  name: "compliance-checker",
  type: "ANALYSIS",
  riskLevel: "AUTO",
  capabilities: ["license-scanning", "security-headers", "secret-detection"],
  inputs: {
    repositoryPath: string,
    rules: string[] // ["licenses", "security", "secrets"]
  },
  outputs: {
    violations: Array<{
      rule: string,
      severity: "critical" | "warning" | "info",
      file: string,
      line: number,
      message: string
    }>,
    passed: boolean
  }
}
```

**Testing**:
- Test with CommandCenter codebase
- Verify all license violations detected
- Validate secret detection (test .env files)
- Measure execution time (target: < 30s for medium repo)

---

#### Task 2: Patcher Agent
**Estimate**: 6 hours

Create agent that applies code patches with human approval.

**Deliverables**:
- `hub/orchestration/agents/patcher/`
  - `agent.ts` - Patch application logic
  - `validators/` - Patch validation
    - `syntax-check.ts` - Validate patch syntax
    - `conflict-detection.ts` - Detect merge conflicts
    - `backup.ts` - Create backup before patching
  - `package.json` - Dependencies (simple-git, diff)
  - `README.md` - Usage guide

**Agent Spec**:
```typescript
{
  name: "patcher",
  type: "MODIFICATION",
  riskLevel: "APPROVAL_REQUIRED", // Always requires approval
  capabilities: ["git-patch", "file-modification", "backup-restore"],
  inputs: {
    repositoryPath: string,
    patchContent: string, // Unified diff format
    targetBranch: string,
    createBackup: boolean // Default: true
  },
  outputs: {
    applied: boolean,
    filesModified: string[],
    backupPath: string,
    conflicts: Array<{file: string, reason: string}>
  }
}
```

**Safety Features**:
- Always create git backup commit before patching
- Validate patch syntax before applying
- Detect conflicts and abort if found
- Log all file modifications
- Require approval via workflow system

**Testing**:
- Apply simple patch (single file)
- Test conflict detection
- Verify backup/restore functionality
- Test approval workflow integration
- Measure latency (approval → patch applied)

---

#### Task 3: Code Reviewer Agent
**Estimate**: 6 hours

Create agent that reviews code changes and provides feedback.

**Deliverables**:
- `hub/orchestration/agents/code-reviewer/`
  - `agent.ts` - Review orchestration
  - `analyzers/`
    - `complexity.ts` - Cyclomatic complexity analysis
    - `style.ts` - Code style violations
    - `security.ts` - Security vulnerability scanning
    - `tests.ts` - Test coverage analysis
  - `templates/` - Review comment templates
  - `package.json` - Dependencies (eslint, complexity-report, bandit)
  - `README.md` - Configuration guide

**Agent Spec**:
```typescript
{
  name: "code-reviewer",
  type: "ANALYSIS",
  riskLevel: "AUTO",
  capabilities: ["complexity-analysis", "style-check", "security-scan", "test-coverage"],
  inputs: {
    repositoryPath: string,
    changedFiles: string[], // Git diff output
    baseline: string // Commit SHA for comparison
  },
  outputs: {
    score: number, // 0-100
    issues: Array<{
      category: "complexity" | "style" | "security" | "testing",
      severity: "blocker" | "critical" | "major" | "minor",
      file: string,
      line: number,
      message: string,
      suggestion: string
    }>,
    metrics: {
      complexityScore: number,
      testCoverage: number,
      securityIssues: number
    }
  }
}
```

**Testing**:
- Review CommandCenter PR (simulate)
- Detect high complexity functions
- Flag security issues (SQL injection test)
- Measure execution time (< 60s for 10 files)

---

#### Task 4: Agent Registration Scripts
**Estimate**: 2 hours

Create scripts to register all 5 agents with the orchestration service.

**Deliverables**:
- `hub/orchestration/scripts/register-all-agents.ts`
  - Reads agent metadata from agent directories
  - Registers via `/api/agents` endpoint
  - Validates registration success
  - Idempotent (can run multiple times)

**Testing**:
- Run script from clean database
- Verify all 5 agents registered
- Confirm idempotency (run twice, no errors)

---

### Track 2: Load Testing (Week 9, Days 4-5)

#### Task 5: Load Test Infrastructure
**Estimate**: 4 hours

Set up load testing framework for workflow execution.

**Deliverables**:
- `hub/orchestration/load-tests/`
  - `k6/` - K6 load test scripts
    - `single-workflow.js` - Single workflow execution
    - `concurrent-workflows.js` - 10 concurrent workflows
    - `dag-execution.js` - Complex 5-node DAG
    - `approval-latency.js` - Approval response time
  - `artillery/` - Artillery HTTP tests
    - `api-endpoints.yml` - API endpoint load tests
  - `scripts/`
    - `run-load-tests.sh` - Execute all tests
    - `analyze-results.sh` - Parse results, check thresholds
  - `README.md` - Test execution guide

**Test Scenarios**:
1. **Single Workflow** (100 requests, 10 RPS)
   - Target: p95 < 10s, p99 < 15s
2. **Concurrent Workflows** (10 parallel, 5 runs)
   - Target: All complete within 60s
3. **Complex DAG** (5 nodes, 20 executions)
   - Target: p95 < 30s, no failures
4. **Approval Latency** (100 approvals)
   - Target: p95 < 5s (UI click → workflow resume)

**Testing**:
- Run tests against local orchestration service
- Collect Prometheus metrics during tests
- Verify no memory leaks (monitor RSS)
- Check database connection pool (no exhaustion)

---

#### Task 6: Performance Baseline Documentation
**Estimate**: 2 hours

Document performance characteristics and capacity limits.

**Deliverables**:
- `hub/orchestration/PERFORMANCE.md`
  - Baseline metrics (latency, throughput)
  - Capacity limits (max concurrent workflows)
  - Resource usage (CPU, memory, database connections)
  - Bottleneck analysis
  - Scaling recommendations

**Metrics to Document**:
- Workflow execution latency (p50, p95, p99)
- Agent execution time by type
- Database query performance
- NATS message throughput
- Memory usage per workflow
- Container startup time

---

### Track 3: Security Audit (Week 10, Days 1-2)

#### Task 7: Input Validation Audit
**Estimate**: 4 hours

Audit and harden all API endpoints for input validation.

**Scope**:
- `/api/agents` (POST, PUT)
- `/api/workflows` (POST, PUT)
- `/api/workflows/:id/trigger` (POST)
- `/api/approvals/:id/respond` (POST)
- `/api/webhooks/alertmanager` (POST)

**Validation Checks**:
- Schema validation (Zod)
- SQL injection prevention (Prisma ORM)
- Command injection prevention (no shell=true)
- Path traversal prevention (validate file paths)
- XXE prevention (JSON only, no XML)
- DoS prevention (rate limiting, size limits)

**Deliverables**:
- `hub/orchestration/SECURITY_AUDIT.md`
  - Findings by endpoint
  - Remediation actions
  - Test cases for each vulnerability class
- Updated validation middleware
- Integration tests for injection attempts

---

#### Task 8: Secret Management Audit
**Estimate**: 3 hours

Verify secrets are never logged or exposed in outputs.

**Scope**:
- Agent execution logs
- Workflow run outputs
- API responses
- Error messages
- Prometheus metrics
- OpenTelemetry traces

**Checks**:
- No DATABASE_URL in logs
- No API keys in agent outputs
- No secrets in error messages
- No credentials in Grafana traces
- Redaction working correctly

**Deliverables**:
- `hub/orchestration/src/utils/redact.ts` (if needed)
- Tests for secret redaction
- Documentation of safe logging practices

---

#### Task 9: Container Isolation Audit
**Estimate**: 3 hours

Verify agents cannot escape Dagger container sandbox.

**Tests**:
1. **Filesystem Access**
   - Agent attempts to read `/etc/passwd` (host)
   - Should fail (no host mounts)
2. **Network Access**
   - Agent attempts to access other containers
   - Should fail (network isolation)
3. **Resource Limits**
   - Agent consumes > max memory
   - Should be killed by Dagger
4. **Process Spawning**
   - Agent forks excessive processes
   - Should be limited by cgroup

**Deliverables**:
- `hub/orchestration/security-tests/`
  - `filesystem-escape.test.ts`
  - `network-isolation.test.ts`
  - `resource-limits.test.ts`
- Documentation of container security model

---

### Track 4: Documentation (Week 10, Days 3-5)

#### Task 10: Agent Development Guide
**Estimate**: 4 hours

Comprehensive guide for creating custom agents.

**Deliverables**:
- `hub/orchestration/docs/AGENT_DEVELOPMENT.md`
  - Agent structure and conventions
  - Input/output schema design
  - Risk level selection criteria
  - Dagger container configuration
  - Error handling best practices
  - Testing strategies
  - Registration process
  - Example: Building a custom agent from scratch

**Sections**:
1. Agent Anatomy
2. TypeScript Template
3. Container Configuration
4. Input Validation
5. Output Schema
6. Error Handling
7. Logging Best Practices
8. Testing Your Agent
9. Registration
10. Real-World Example

---

#### Task 11: Workflow Creation Guide
**Estimate**: 3 hours

Guide for defining and triggering workflows.

**Deliverables**:
- `hub/orchestration/docs/WORKFLOW_GUIDE.md`
  - Workflow anatomy (DAG structure)
  - Input templating (Mustache syntax)
  - Trigger types (webhook, NATS, manual)
  - Approval gates configuration
  - Error handling and retries
  - VISLZR builder usage
  - YAML workflow definition
  - Example workflows

**Sections**:
1. Workflow Basics
2. DAG Structure
3. Agent Nodes
4. Input Templating
5. Trigger Configuration
6. Approval Gates
7. Error Handling
8. VISLZR Builder
9. YAML Workflows
10. Common Patterns

---

#### Task 12: API Documentation
**Estimate**: 2 hours

Update OpenAPI spec and generate API docs.

**Deliverables**:
- `hub/orchestration/openapi.yaml` (Swagger spec)
- Auto-generated docs at `/docs` endpoint
- Example requests for each endpoint
- Authentication documentation

**Endpoints to Document**:
- Agents: CRUD operations
- Workflows: CRUD + trigger
- Approvals: List + respond
- Webhooks: AlertManager integration
- Health: Service health checks

---

#### Task 13: Runbooks
**Estimate**: 3 hours

Operational runbooks for common issues.

**Deliverables**:
- `hub/orchestration/docs/RUNBOOKS.md`
  - Workflow stuck in "running" state
  - Agent execution timeout
  - Database connection pool exhausted
  - NATS connection lost
  - Prometheus metrics missing
  - High memory usage
  - Approval not triggering
  - Container startup failures

**Format**:
```markdown
## Workflow Stuck in "running" State

**Symptoms**: Workflow status = "running" for > 5 minutes, no agent activity

**Diagnosis**:
1. Check agent_runs table for latest run
2. Review Dagger executor logs
3. Check NATS message queue

**Resolution**:
1. If agent crashed: Retry workflow
2. If Dagger hung: Restart Dagger engine
3. If NATS issue: Reconnect NATS client

**Prevention**: Add workflow timeout (task 14)
```

---

#### Task 14: Architecture Diagrams
**Estimate**: 2 hours

Update architecture diagrams with Phase 10 components.

**Deliverables**:
- `docs/diagrams/phase-10-architecture.mmd` (Mermaid)
  - System overview
  - Workflow execution flow
  - Event-driven triggers
  - Approval workflow
  - Observability stack integration
- Rendered PNGs via Mermaid CLI

**Diagrams**:
1. **System Overview** - All services and connections
2. **Workflow Execution** - Sequence diagram
3. **Event Flow** - NATS event routing
4. **Approval Process** - State machine
5. **Observability** - Metrics/traces/logs flow

---

### Track 5: End-to-End Testing (Week 10, Day 5)

#### Task 15: Integration Test Suite
**Estimate**: 4 hours

Comprehensive end-to-end tests covering all workflows.

**Deliverables**:
- `hub/orchestration/tests/e2e/`
  - `workflow-execution.e2e.test.ts`
  - `approval-workflow.e2e.test.ts`
  - `multi-agent-dag.e2e.test.ts`
  - `webhook-trigger.e2e.test.ts`
  - `error-handling.e2e.test.ts`

**Test Scenarios**:
1. **Simple Workflow**
   - security-scanner → notifier (2 agents)
   - Verify both execute successfully
   - Check metrics in Prometheus
2. **Approval Workflow**
   - patcher agent requires approval
   - Pause workflow, send approval
   - Resume and verify patch applied
3. **Complex DAG**
   - 5 nodes, multiple paths
   - Verify correct execution order
   - Check all outputs propagated
4. **Webhook Trigger**
   - AlertManager fires alert
   - Workflow triggers automatically
   - Notifier sends message
5. **Error Handling**
   - Agent fails, workflow retries
   - Max retries hit, workflow fails
   - Error visible in VISLZR

---

#### Task 16: Production Smoke Tests
**Estimate**: 2 hours

Quick validation tests for production deployments.

**Deliverables**:
- `hub/orchestration/scripts/smoke-tests.sh`
  - Check all services healthy
  - Trigger test workflow
  - Verify metrics endpoint
  - Check database connectivity
  - Validate NATS connection
  - Exit 0 if pass, 1 if fail

**Usage**:
```bash
./scripts/smoke-tests.sh
# Run after deployment to verify system health
```

---

## Timeline

### Week 9 (Days 1-5)
- **Day 1**: Compliance checker agent
- **Day 2**: Patcher agent
- **Day 3**: Code reviewer agent + registration scripts
- **Day 4**: Load test infrastructure
- **Day 5**: Performance baseline documentation

### Week 10 (Days 1-5)
- **Day 1**: Input validation audit
- **Day 2**: Secret management + container isolation audits
- **Day 3**: Agent development guide + workflow guide
- **Day 4**: API docs + runbooks
- **Day 5**: Architecture diagrams + E2E tests + smoke tests

**Total**: 10 days (2 weeks)

---

## Deliverables Checklist

### Code
- [ ] 3 new agents (compliance, patcher, code-reviewer)
- [ ] Agent registration scripts
- [ ] Load test suite (K6 + Artillery)
- [ ] Security test suite
- [ ] E2E integration tests
- [ ] Smoke test script

### Documentation
- [ ] AGENT_DEVELOPMENT.md
- [ ] WORKFLOW_GUIDE.md
- [ ] PERFORMANCE.md
- [ ] SECURITY_AUDIT.md
- [ ] RUNBOOKS.md
- [ ] OpenAPI spec (openapi.yaml)
- [ ] Architecture diagrams (Mermaid)

### Validation
- [ ] All load tests passing
- [ ] Security audit complete (no critical findings)
- [ ] E2E tests passing
- [ ] Smoke tests passing
- [ ] Performance baselines documented

---

## Success Metrics

### Performance
- ✅ 10 concurrent workflows without degradation
- ✅ p95 latency < 10s (single workflow)
- ✅ p95 latency < 30s (5-node DAG)
- ✅ Approval latency < 5s

### Reliability
- ✅ 0 workflow deadlocks during load tests
- ✅ 0 memory leaks (stable RSS over 1 hour)
- ✅ 0 database connection pool exhaustion
- ✅ 100% workflow completion rate (no hangs)

### Security
- ✅ 0 critical security findings
- ✅ All inputs validated
- ✅ No secrets in logs/traces
- ✅ Container escape attempts fail

### Documentation
- ✅ All guides peer-reviewed
- ✅ API docs auto-generated and current
- ✅ Runbooks validated with real issues
- ✅ Diagrams reflect current architecture

---

## Next Phase

**Phase 11**: Graph Service + KnowledgeBeast Integration
- Workflow visualization in graph
- Agent dependency tracking
- Cross-project intelligence
- Federated catalog enhancements

---

**Status**: Ready to start (Phase 5 complete)
**Estimated Effort**: 2 weeks (80 hours)
**Priority**: High (production readiness)
