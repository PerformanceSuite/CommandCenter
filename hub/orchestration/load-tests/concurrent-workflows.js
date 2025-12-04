import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Counter } from 'k6/metrics';

// Custom metrics
const workflowSuccessRate = new Rate('concurrent_workflow_success_rate');
const activeWorkflows = new Counter('active_workflows');

export const options = {
  scenarios: {
    concurrent_load: {
      executor: 'constant-vus',
      vus: 10,
      duration: '2m',
    },
  },
  thresholds: {
    'concurrent_workflow_success_rate': ['rate>0.99'],
    'http_req_duration': ['p(95)<2000'],
    'http_req_failed': ['rate<0.01'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:9002';

export default function () {
  // Create and trigger workflow
  const workflowPayload = JSON.stringify({
    name: `concurrent-test-${Date.now()}-${__VU}-${__ITER}`,
    trigger: 'MANUAL',
    nodes: [
      {
        id: 'notify',
        agentName: 'notifier',
        input: {
          channel: 'console',
          severity: 'info',
          message: `Load test from VU ${__VU}`,
        },
      },
    ],
    edges: [],
  });

  const createRes = http.post(`${BASE_URL}/api/workflows`, workflowPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  const createSuccess = check(createRes, {
    'workflow created': (r) => r.status === 201,
  });

  if (!createSuccess) {
    return;
  }

  const workflow = JSON.parse(createRes.body);
  const workflowId = workflow.id;

  // Trigger
  const triggerRes = http.post(
    `${BASE_URL}/api/workflows/${workflowId}/trigger`,
    JSON.stringify({ input: {} }),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );

  const triggerSuccess = check(triggerRes, {
    'workflow triggered': (r) => r.status === 201,
  });

  if (!triggerSuccess) {
    return;
  }

  const run = JSON.parse(triggerRes.body);
  const runId = run.id;

  activeWorkflows.add(1);

  // Poll for completion (shorter timeout for notifier)
  let completed = false;
  for (let i = 0; i < 10; i++) {
    sleep(0.5);

    const statusRes = http.get(`${BASE_URL}/api/workflows/${workflowId}/runs/${runId}`);

    if (statusRes.status === 200) {
      const runStatus = JSON.parse(statusRes.body);
      if (runStatus.status === 'SUCCESS' || runStatus.status === 'FAILED') {
        completed = true;
        const success = runStatus.status === 'SUCCESS';
        workflowSuccessRate.add(success);
        activeWorkflows.add(-1);
        break;
      }
    }
  }

  if (!completed) {
    activeWorkflows.add(-1);
  }

  sleep(1);
}
