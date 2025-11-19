import axios from 'axios';
import * as fs from 'fs';

const API_BASE = process.env.ORCHESTRATION_API || 'http://localhost:9002';

async function createWorkflow(definitionPath: string) {
  const definition = JSON.parse(fs.readFileSync(definitionPath, 'utf-8'));

  // Get agent IDs from names
  const agentsResponse = await axios.get(`${API_BASE}/api/agents?projectId=${definition.projectId}`);
  const agents = agentsResponse.data;

  // Map agent names to IDs
  const agentMap = new Map(agents.map((a: any) => [a.name, a.id]));

  // Transform nodes to use agent IDs
  const nodes = definition.nodes.map((node: any) => ({
    agentId: agentMap.get(node.agentName),
    action: node.action,
    inputsJson: node.inputsJson,
    dependsOn: node.dependsOn,
    approvalRequired: node.approvalRequired,
  }));

  const workflow = {
    projectId: definition.projectId,
    name: definition.name,
    description: definition.description,
    trigger: definition.trigger,
    status: definition.status,
    nodes,
  };

  const response = await axios.post(`${API_BASE}/api/workflows`, workflow);
  console.log('Workflow created:', response.data);
  return response.data;
}

async function main() {
  const definitionPath = process.argv[2] || 'examples/scan-and-notify-workflow.json';

  try {
    await createWorkflow(definitionPath);
    process.exit(0);
  } catch (error: any) {
    console.error('Workflow creation failed:', error.response?.data || error.message);
    process.exit(1);
  }
}

main();
