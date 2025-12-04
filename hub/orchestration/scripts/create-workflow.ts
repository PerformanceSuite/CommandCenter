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

  // Create a map of node symbolic IDs to their index (for dependency resolution)
  const nodeIdMap = new Map(definition.nodes.map((node: any, index: number) => [node.id, index]));

  // Transform nodes to use agent IDs and resolve symbolic dependencies to node indices
  const nodes = definition.nodes.map((node: any, index: number) => ({
    agentId: agentMap.get(node.agentName),
    action: node.action,
    inputsJson: node.inputsJson,
    dependsOn: node.dependsOn.map((depId: string) => {
      const depIndex = nodeIdMap.get(depId);
      if (depIndex === undefined) {
        throw new Error(`Invalid dependency: node "${node.id}" depends on unknown node "${depId}"`);
      }
      return `node-${depIndex}`; // Temporary placeholder - will be replaced with actual IDs after creation
    }),
    approvalRequired: node.approvalRequired,
    _symbolicId: node.id, // Preserve for later reference
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
