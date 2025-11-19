// hub/orchestration/src/metrics/workflow-metrics.ts
import { metrics } from '@opentelemetry/api';

const meter = metrics.getMeter('orchestration-service');

// Workflow metrics
export const workflowRunCounter = meter.createCounter('workflow.runs.total', {
  description: 'Total number of workflow runs',
  unit: '1',
});

export const workflowDuration = meter.createHistogram('workflow.duration', {
  description: 'Workflow execution time',
  unit: 'ms',
});

export const activeWorkflows = meter.createUpDownCounter('workflows.active', {
  description: 'Number of currently running workflows',
  unit: '1',
});

export const workflowApprovalWaitTime = meter.createHistogram('workflow.approval.wait_time', {
  description: 'Time spent waiting for approval',
  unit: 'ms',
});

// Agent metrics
export const agentRunCounter = meter.createCounter('agent.runs.total', {
  description: 'Total number of agent executions',
  unit: '1',
});

export const agentDuration = meter.createHistogram('agent.duration', {
  description: 'Agent execution time',
  unit: 'ms',
});

export const agentErrorCounter = meter.createCounter('agent.errors.total', {
  description: 'Total agent execution failures',
  unit: '1',
});

export const agentRetryCounter = meter.createCounter('agent.retry.count', {
  description: 'Number of agent retry attempts',
  unit: '1',
});
