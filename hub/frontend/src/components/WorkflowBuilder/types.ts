import { Node, Edge } from 'reactflow';

export interface AgentNodeData {
  agentId: string;
  agentName: string;
  action: string;
  inputs: Record<string, string>;
  approvalRequired: boolean;
}

export interface WorkflowNode extends Node {
  type: 'agent';
  data: AgentNodeData;
}

export type WorkflowEdge = Edge;

export interface Workflow {
  id?: string;
  projectId: number;
  name: string;
  description?: string;
  trigger: {
    event: string;
    pattern: string;
  };
  status: 'ACTIVE' | 'DRAFT' | 'ARCHIVED';
  nodes: Array<{
    agentId: string;
    action: string;
    inputsJson: Record<string, string>;
    dependsOn: string[];
    approvalRequired: boolean;
  }>;
}
