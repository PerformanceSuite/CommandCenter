import axios from 'axios';

const API_BASE = process.env.ORCHESTRATION_API || 'http://localhost:9002';

async function triggerWorkflow(workflowId: string, context: any) {
  const response = await axios.post(
    `${API_BASE}/api/workflows/${workflowId}/trigger`,
    { context }
  );

  console.log('Workflow triggered:', response.data);
  return response.data;
}

async function main() {
  const workflowId = process.argv[2];
  const contextJson = process.argv[3] || '{}';

  if (!workflowId) {
    console.error('Usage: npx ts-node trigger-workflow.ts <workflowId> [context]');
    process.exit(1);
  }

  try {
    const context = JSON.parse(contextJson);
    await triggerWorkflow(workflowId, context);
    process.exit(0);
  } catch (error: any) {
    console.error('Trigger failed:', error.response?.data || error.message);
    process.exit(1);
  }
}

main();
