import React, { useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  addEdge,
  Connection,
  Edge,
  useNodesState,
  useEdgesState,
} from 'reactflow';
import 'reactflow/dist/style.css';
import { WorkflowNode, WorkflowEdge, Workflow } from './types';
import { AgentNode } from './nodes/AgentNode';
import { AgentPalette } from './AgentPalette';
import { NodeConfigPanel } from './NodeConfigPanel';
import { useCreateWorkflow, useUpdateWorkflow, useWorkflows } from '../../hooks/useWorkflows';

const nodeTypes = {
  agent: AgentNode,
};

// Helper functions
const convertNodesToBackend = (
  nodes: WorkflowNode[],
  edges: WorkflowEdge[]
): Workflow['nodes'] => {
  return nodes.map((node) => {
    const dependencies = edges
      .filter((edge) => edge.target === node.id)
      .map((edge) => edge.source);

    return {
      agentId: node.data.agentId,
      action: node.data.action,
      inputsJson: node.data.inputs,
      dependsOn: dependencies,
      approvalRequired: node.data.approvalRequired,
    };
  });
};

const convertNodesFromBackend = (
  workflow: Workflow
): { nodes: WorkflowNode[]; edges: WorkflowEdge[] } => {
  const nodes: WorkflowNode[] = [];
  const edges: WorkflowEdge[] = [];
  const nodeIdMap = new Map<number, string>();

  workflow.nodes.forEach((node, index) => {
    const nodeId = `node-${index}`;
    nodeIdMap.set(index, nodeId);

    nodes.push({
      id: nodeId,
      type: 'agent',
      position: { x: 100 + index * 250, y: 100 },
      data: {
        agentId: node.agentId,
        agentName: node.agentId.split('-').pop() || 'agent',
        action: node.action,
        inputs: node.inputsJson,
        approvalRequired: node.approvalRequired,
      },
    });

    node.dependsOn.forEach((depNodeId) => {
      const sourceNodeId = nodeIdMap.get(parseInt(depNodeId));
      if (sourceNodeId) {
        edges.push({
          id: `edge-${sourceNodeId}-${nodeId}`,
          source: sourceNodeId,
          target: nodeId,
        });
      }
    });
  });

  return { nodes, edges };
};

interface WorkflowBuilderProps {
  projectId: number;
  workflowId?: string;
  onSave?: (workflowId: string) => void;
}

export const WorkflowBuilder: React.FC<WorkflowBuilderProps> = ({
  projectId,
  workflowId,
  onSave,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<WorkflowNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<WorkflowEdge>([]);
  const [workflowName, setWorkflowName] = useState('New Workflow');
  const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);

  const createWorkflow = useCreateWorkflow();
  const updateWorkflow = useUpdateWorkflow();
  const { data: workflows } = useWorkflows(projectId);

  // Load existing workflow if workflowId provided
  React.useEffect(() => {
    if (workflowId && workflows) {
      const workflow = workflows.find((w) => w.id === workflowId);
      if (workflow) {
        setWorkflowName(workflow.name);
        const { nodes: loadedNodes, edges: loadedEdges } =
          convertNodesFromBackend(workflow);
        setNodes(loadedNodes);
        setEdges(loadedEdges);
      }
    }
  }, [workflowId, workflows, setNodes, setEdges]);

  const onConnect = React.useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const onDragOver = React.useCallback((event: React.DragEvent) => {
    event.preventDefault();
    event.dataTransfer.dropEffect = 'move';
  }, []);

  const onDrop = React.useCallback(
    (event: React.DragEvent) => {
      event.preventDefault();

      const agentData = event.dataTransfer.getData('application/json');
      if (!agentData) return;

      const agent = JSON.parse(agentData);
      const reactFlowBounds = event.currentTarget.getBoundingClientRect();
      const position = {
        x: event.clientX - reactFlowBounds.left - 90,
        y: event.clientY - reactFlowBounds.top - 50,
      };

      const newNode: WorkflowNode = {
        id: `${agent.name}-${Date.now()}`,
        type: 'agent',
        position,
        data: {
          agentId: agent.id,
          agentName: agent.name,
          action: agent.capabilities[0]?.name || 'execute',
          inputs: {},
          approvalRequired: false,
        },
      };

      setNodes((nds) => [...nds, newNode]);
    },
    [setNodes]
  );

  const onDragStart = React.useCallback((event: React.DragEvent, agent: any) => {
    event.dataTransfer.setData('application/json', JSON.stringify(agent));
    event.dataTransfer.effectAllowed = 'move';
  }, []);

  const onNodeClick = React.useCallback(
    (_event: React.MouseEvent, node: any) => {
      setSelectedNode(node as WorkflowNode);
    },
    []
  );

  const onNodeUpdate = React.useCallback(
    (nodeId: string, updates: Partial<WorkflowNode['data']>) => {
      setNodes((nds) =>
        nds.map((node) =>
          node.id === nodeId
            ? { ...node, data: { ...node.data, ...updates } }
            : node
        )
      );
    },
    [setNodes]
  );

  const handleSave = async () => {
    const workflowData: Workflow = {
      projectId,
      name: workflowName,
      description: `Created via workflow builder`,
      trigger: {
        event: 'manual',
        pattern: 'manual',
      },
      status: 'ACTIVE',
      nodes: convertNodesToBackend(nodes as WorkflowNode[], edges),
    };

    try {
      if (workflowId) {
        await updateWorkflow.mutateAsync({
          id: workflowId,
          workflow: workflowData,
        });
        if (onSave) {
          onSave(workflowId);
        }
      } else {
        const created = await createWorkflow.mutateAsync(workflowData);
        if (onSave && created.id) {
          onSave(created.id);
        }
      }
    } catch (error: any) {
      alert(`Failed to save workflow: ${error.message}`);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
      <div style={{
        padding: '1rem',
        background: '#f5f5f5',
        borderBottom: '1px solid #ddd',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
      }}>
        <input
          type="text"
          value={workflowName}
          onChange={(e) => setWorkflowName(e.target.value)}
          style={{
            padding: '0.5rem',
            fontSize: '1.2rem',
            border: '1px solid #ccc',
            borderRadius: '4px',
            width: '300px',
          }}
        />
        <button
          onClick={handleSave}
          style={{
            padding: '0.5rem 1rem',
            background: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontSize: '1rem',
          }}
        >
          Save Workflow
        </button>
      </div>
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
        <AgentPalette projectId={projectId} onDragStart={onDragStart} />
        <div
          style={{ flex: 1, position: 'relative' }}
          onDrop={onDrop}
          onDragOver={onDragOver}
        >
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onConnect={onConnect}
            onNodeClick={onNodeClick}
            nodeTypes={nodeTypes}
            fitView
          >
            <Background />
            <Controls />
            <MiniMap />
          </ReactFlow>
        </div>
        <NodeConfigPanel
          node={selectedNode}
          onUpdate={onNodeUpdate}
          onClose={() => setSelectedNode(null)}
        />
      </div>
    </div>
  );
};
