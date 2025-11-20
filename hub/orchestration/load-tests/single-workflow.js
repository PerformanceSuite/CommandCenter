import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

// Custom metrics
const workflowSuccessRate = new Rate('workflow_success_rate');
const workflowDuration = new Trend('workflow_duration_ms');

export const options = {
  stages: [
    { duration: '30s', target: 5 },   // Ramp up to 5 VUs
    { duration: '1m', target: 5 },    // Stay at 5 VUs
    { duration: '30s', target: 0 },   // Ramp down
  ],
  thresholds: {
    'workflow_success_rate': ['rate>0.99'],  // 99% success rate
    'workflow_duration_ms': ['p(95)<10000'], // p95 < 10s
    'http_req_duration': ['p(95)<2000'],     // API p95 < 2s
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:9002';

export default function () {
  // Create workflow
  const workflowPayload = JSON.stringify({
    name: `load-test-${Date.now()}-${__VU}`,
    trigger: 'MANUAL',
    nodes: [
      {
        id: 'scan',
        agentName: 'security-scanner',
        input: {
          repositoryPath: '/workspace',
          scanType: 'all',
        },
      },
    ],
    edges: [],
  });

  const createRes = http.post(`${BASE_URL}/api/workflows`, workflowPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  check(createRes, {
    'workflow created': (r) => r.status === 201,
  });

  if (createRes.status !== 201) {
    console.error(`Failed to create workflow: ${createRes.status}`);
    return;
  }

  const workflow = JSON.parse(createRes.body);
  const workflowId = workflow.id;

  // Trigger workflow execution
  const triggerRes = http.post(
    `${BASE_URL}/api/workflows/${workflowId}/trigger`,
    JSON.stringify({ input: {} }),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );

  check(triggerRes, {
    'workflow triggered': (r) => r.status === 201,
  });

  if (triggerRes.status !== 201) {
    console.error(`Failed to trigger workflow: ${triggerRes.status}`);
    return;
  }

  const run = JSON.parse(triggerRes.body);
  const runId = run.id;

  // Poll for completion
  const startTime = Date.now();
  let completed = false;
  let finalStatus = 'UNKNOWN';

  for (let i = 0; i < 30; i++) {
    // Max 30s polling
    sleep(1);

    const statusRes = http.get(`${BASE_URL}/api/workflows/${workflowId}/runs/${runId}`);

    if (statusRes.status === 200) {
      const runStatus = JSON.parse(statusRes.body);
      if (runStatus.status === 'SUCCESS' || runStatus.status === 'FAILED') {
        completed = true;
        finalStatus = runStatus.status;
        const duration = Date.now() - startTime;
        workflowDuration.add(duration);
        break;
      }
    }
  }

  // Record success
  const success = completed && finalStatus === 'SUCCESS';
  workflowSuccessRate.add(success);

  check({ completed, finalStatus }, {
    'workflow completed': () => completed,
    'workflow succeeded': () => finalStatus === 'SUCCESS',
  });

  sleep(1);
}
