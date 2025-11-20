import http from 'k6/http';
import { check, sleep } from 'k6';
import { Trend } from 'k6/metrics';

// Custom metrics
const approvalResponseTime = new Trend('approval_response_time_ms');

export const options = {
  vus: 3,
  duration: '1m',
  thresholds: {
    'approval_response_time_ms': ['p(95)<5000'], // p95 < 5s
    'http_req_duration': ['p(95)<2000'],
  },
};

const BASE_URL = __ENV.BASE_URL || 'http://localhost:9002';

export default function () {
  // Create workflow with APPROVAL_REQUIRED agent (patcher)
  const workflowPayload = JSON.stringify({
    name: `approval-test-${Date.now()}-${__VU}`,
    trigger: 'MANUAL',
    nodes: [
      {
        id: 'patch',
        agentName: 'patcher',
        input: {
          repositoryPath: '/workspace',
          patchType: 'config-update',
          target: '.test-config',
          changes: {
            content: 'test=true',
          },
          dryRun: true,
        },
      },
    ],
    edges: [],
  });

  const createRes = http.post(`${BASE_URL}/api/workflows`, workflowPayload, {
    headers: { 'Content-Type': 'application/json' },
  });

  if (createRes.status !== 201) {
    return;
  }

  const workflow = JSON.parse(createRes.body);
  const workflowId = workflow.id;

  // Trigger workflow
  const triggerRes = http.post(
    `${BASE_URL}/api/workflows/${workflowId}/trigger`,
    JSON.stringify({ input: {} }),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );

  if (triggerRes.status !== 201) {
    return;
  }

  const run = JSON.parse(triggerRes.body);
  const runId = run.id;

  // Wait for workflow to reach PENDING_APPROVAL
  let approvalId = null;
  for (let i = 0; i < 10; i++) {
    sleep(1);

    const statusRes = http.get(`${BASE_URL}/api/workflows/${workflowId}/runs/${runId}`);

    if (statusRes.status === 200) {
      const runStatus = JSON.parse(statusRes.body);
      if (runStatus.status === 'PENDING_APPROVAL') {
        // Get approval ID
        const approvalsRes = http.get(
          `${BASE_URL}/api/workflows/${workflowId}/runs/${runId}/approvals`
        );

        if (approvalsRes.status === 200) {
          const approvals = JSON.parse(approvalsRes.body);
          if (approvals.length > 0) {
            approvalId = approvals[0].id;
            break;
          }
        }
      }
    }
  }

  if (!approvalId) {
    console.error('Workflow did not reach PENDING_APPROVAL state');
    return;
  }

  // Approve workflow and measure response time
  const approvalStartTime = Date.now();

  const approveRes = http.post(
    `${BASE_URL}/api/workflows/${workflowId}/runs/${runId}/approvals/${approvalId}/approve`,
    JSON.stringify({ comment: 'Load test approval' }),
    {
      headers: { 'Content-Type': 'application/json' },
    }
  );

  check(approveRes, {
    'approval submitted': (r) => r.status === 200,
  });

  // Wait for workflow to resume and complete
  let completed = false;
  for (let i = 0; i < 10; i++) {
    sleep(1);

    const statusRes = http.get(`${BASE_URL}/api/workflows/${workflowId}/runs/${runId}`);

    if (statusRes.status === 200) {
      const runStatus = JSON.parse(statusRes.body);
      if (runStatus.status === 'SUCCESS' || runStatus.status === 'FAILED') {
        completed = true;
        const responseTime = Date.now() - approvalStartTime;
        approvalResponseTime.add(responseTime);
        break;
      }
    }
  }

  check({ completed }, {
    'workflow resumed after approval': () => completed,
  });

  sleep(2);
}
