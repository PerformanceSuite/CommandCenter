# Service Level Objectives (SLOs)

**Purpose**: Define measurable reliability targets for CommandCenter orchestration service.

**Review Cycle**: Monthly review of SLO compliance, quarterly target adjustments.

---

## 1. Workflow Success Rate

**Objective**: Ensure workflows complete successfully without errors.

**Target**: ≥ 99.0% of workflows succeed within 30 days

**Measurement**:
```promql
sum(rate(workflow_runs_total{status="SUCCESS"}[30d]))
/
sum(rate(workflow_runs_total[30d]))
```

**Rationale**: Workflow failures directly impact automation reliability and user trust.

**Error Budget**: 1% = ~430 failed workflows per 30 days (assumes 1,440 workflows/day)

**Alerting**:
- **Warning**: Success rate < 99% for 1 hour
- **Critical**: Success rate < 95% for 5 minutes

**Remediation**:
1. Review failed workflow logs in Grafana
2. Identify failing agents via Agent Performance dashboard
3. Check for infrastructure issues (DB, network)
4. Roll back recent workflow changes if pattern emerges

---

## 2. API Availability

**Objective**: Ensure orchestration service is responsive and available.

**Target**: ≥ 99.9% uptime within 30 days

**Measurement**:
```promql
avg_over_time(up{job="orchestration-service"}[30d])
```

**Rationale**: Service downtime blocks all automation and manual interactions.

**Error Budget**: 0.1% = ~43 minutes downtime per 30 days

**Alerting**:
- **Critical**: Service down for 1 minute

**Remediation**:
1. Check service health: `docker ps | grep orchestration`
2. Review service logs: `docker logs hub-orchestration`
3. Verify database connectivity
4. Restart service if necessary
5. Escalate to on-call if restart fails

---

## 3. Workflow Latency (p95)

**Objective**: Ensure workflows complete in a reasonable time.

**Target**: ≥ 95% of workflows complete within 120 seconds (p95 latency < 120s)

**Measurement**:
```promql
histogram_quantile(0.95, rate(workflow_duration_bucket[7d])) < 120000
```

**Rationale**: Slow workflows reduce automation effectiveness and user experience.

**Error Budget**: 5% of workflows can exceed 120s = ~360 slow workflows per 7 days

**Alerting**:
- **Warning**: p95 latency > 300s (5 minutes) for 10 minutes

**Remediation**:
1. Identify slow workflows in Workflow Overview dashboard
2. Check for slow agents via duration heatmap
3. Review agent execution logs for bottlenecks
4. Optimize agent logic or increase timeout limits
5. Scale infrastructure if resource-constrained

---

## 4. Agent Success Rate

**Objective**: Ensure individual agents execute reliably.

**Target**: ≥ 98.0% of agent executions succeed within 7 days

**Measurement**:
```promql
sum(rate(agent_runs_total{status="SUCCESS"}[7d]))
/
sum(rate(agent_runs_total[7d]))
```

**Rationale**: Agent failures cascade to workflow failures and reduce automation trust.

**Error Budget**: 2% = ~240 failed agent runs per 7 days (assumes 1,200 runs/day)

**Alerting**:
- **Warning**: Success rate < 98% for 1 hour per agent type

**Remediation**:
1. Identify failing agent in Agent Performance dashboard
2. Review agent logs and error messages
3. Check agent dependencies (APIs, credentials)
4. Test agent in isolation
5. Deploy fix or disable agent temporarily

---

## 5. Event Loop Lag (Performance)

**Objective**: Ensure Node.js event loop remains responsive.

**Target**: ≥ 95% of time with event loop lag < 50ms

**Measurement**:
```promql
avg_over_time(process_runtime_nodejs_event_loop_lag_seconds[5m]) < 0.05
```

**Rationale**: High event loop lag indicates CPU saturation and degrades all operations.

**Error Budget**: 5% = ~2 hours of high lag per 30 days

**Alerting**:
- **Warning**: Lag > 100ms for 5 minutes

**Remediation**:
1. Identify CPU-intensive operations in traces
2. Review recent code changes
3. Check for blocking I/O or synchronous operations
4. Increase service replicas or scale vertically
5. Optimize hot paths identified in profiling

---

## 6. Memory Usage (Resource)

**Objective**: Prevent memory exhaustion and OOM crashes.

**Target**: < 80% heap memory usage (average over 5 minutes)

**Measurement**:
```promql
(
  process_runtime_nodejs_memory_heap_bytes
  /
  process_runtime_nodejs_memory_heap_max_bytes
) < 0.8
```

**Rationale**: Memory leaks or excessive allocation lead to service crashes.

**Error Budget**: 20% headroom for spikes and gradual leaks

**Alerting**:
- **Warning**: Memory > 80% for 5 minutes
- **Critical**: Memory > 90% for 2 minutes

**Remediation**:
1. Check for memory leaks via heap snapshots
2. Review recent code changes for unbounded growth
3. Analyze traces for excessive object allocation
4. Restart service if leak confirmed
5. Increase heap size if legitimate growth

---

## SLO Dashboard

**Grafana Dashboard**: `SLO Overview` (auto-provisioned)

**Panels**:
1. **Workflow Success Rate** (30d rolling window)
   - Gauge: Current percentage
   - Timeseries: Trend over 30 days
   - Error budget: Remaining failures before SLO breach

2. **API Availability** (30d rolling window)
   - Gauge: Current uptime percentage
   - Timeseries: Uptime percentage over 30 days
   - Error budget: Remaining downtime minutes

3. **Workflow Latency** (7d rolling window)
   - Gauge: Current p95 latency
   - Timeseries: p50/p95/p99 latencies
   - Error budget: Percentage of workflows exceeding target

4. **Agent Success Rate** (7d rolling window)
   - Table: Success rate per agent type
   - Timeseries: Agent success rates
   - Error budget: Remaining failures per agent

5. **Event Loop Lag** (5m rolling window)
   - Gauge: Current lag
   - Timeseries: Lag over time
   - Threshold line at 50ms

6. **Memory Usage** (5m rolling window)
   - Gauge: Current heap usage percentage
   - Timeseries: Heap usage over time
   - Threshold lines at 80% (warning) and 90% (critical)

---

## SLO Review Process

**Monthly Review** (First Monday of month):
1. Review SLO compliance for previous 30 days
2. Analyze error budget consumption
3. Identify patterns in SLO violations
4. Document incidents and root causes
5. Update remediation procedures if needed

**Quarterly Adjustment** (First Monday of quarter):
1. Evaluate if SLO targets are appropriate
2. Adjust targets based on business needs
3. Update error budgets and alerting thresholds
4. Communicate changes to stakeholders

**On-Call Escalation**:
- **Critical SLO breach**: Immediate page to on-call engineer
- **Warning SLO trend**: Slack notification to team channel
- **Error budget exhausted**: Block new feature deployments until fixed

---

## Error Budget Policy

**When Error Budget Exhausted**:
1. **Freeze feature deployments** (focus on reliability)
2. **Mandatory incident retrospective** within 48 hours
3. **Reliability improvements required** before next deploy
4. **Executive review** if budget exhausted 2+ months in row

**Error Budget Tracking**:
- Grafana dashboard: Real-time error budget consumption
- Weekly email: Error budget status for all SLOs
- Monthly report: SLO compliance summary

---

*Last Updated*: 2025-11-19
*Owner*: Platform Engineering Team
*Review Cycle*: Monthly
