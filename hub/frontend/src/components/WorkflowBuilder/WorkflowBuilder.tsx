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
import { WorkflowNode, WorkflowEdge } from './types';
import { AgentNode } from './nodes/AgentNode';

const nodeTypes = {
  agent: AgentNode,
};

interface WorkflowBuilderProps {
  projectId: number;
  workflowId?: string;
}

export const WorkflowBuilder: React.FC<WorkflowBuilderProps> = ({
  projectId,
}) => {
  const [nodes, , onNodesChange] = useNodesState<WorkflowNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<WorkflowEdge>([]);
  const [workflowName, setWorkflowName] = useState('New Workflow');

  const onConnect = React.useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleSave = () => {
    console.log('Save workflow:', { workflowName, nodes, edges });
    // Will implement in Task 25
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
      <div style={{ flex: 1 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </div>
  );
};
