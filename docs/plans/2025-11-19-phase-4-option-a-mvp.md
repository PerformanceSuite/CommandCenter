# Phase 4 Option A: Minimal Viable UI - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build minimal viable workflow builder UI with drag-and-drop workflow creation and approval interface for high-risk workflow steps.

**Architecture:** React + TypeScript components integrated into existing VISLZR frontend at `frontend/src/components/`. Uses React Flow for visual DAG editing, React Query for data fetching, Axios for API calls.

**Tech Stack:** React 18, TypeScript, React Flow, TailwindCSS (existing), React Query, Axios

**Estimated Time:** 1 week (8 tasks)

---

## MVP Scope

**Workflow Builder (Tasks 21-25):**
- Drag-and-drop agents from palette to canvas
- Connect nodes to define dependencies
- Configure node inputs (basic text fields, no advanced templates)
- Save workflow to backend API
- Load existing workflow from backend API

**Approval Interface (Tasks 26-28):**
- List pending workflow approvals
- View approval details (workflow context, node inputs)
- Approve/reject approval with notes

**Out of Scope (for now):**
- Advanced template editor with autocomplete
- Real-time execution monitoring
- Agent library browser
- Workflow validation/linting
- Undo/redo

---

## Part 1: Workflow Builder (Tasks 21-25)

### Task 21: Setup React Flow and Create Base Structure

**Files:**
- Create: `frontend/src/components/WorkflowBuilder/index.tsx`
- Create: `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`
- Create: `frontend/src/components/WorkflowBuilder/types.ts`
- Create: `frontend/src/hooks/useWorkflows.ts`
- Modify: `frontend/package.json`

**Step 1: Install dependencies**

```bash
cd frontend
npm install reactflow@11.10.1 @tanstack/react-query@5.17.0
```

Expected: Dependencies added to package.json

**Step 2: Create type definitions**

Create `frontend/src/components/WorkflowBuilder/types.ts`:

```typescript
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

export interface WorkflowEdge extends Edge {}

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
```

**Step 3: Create useWorkflows hook**

Create `frontend/src/hooks/useWorkflows.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Workflow } from '../components/WorkflowBuilder/types';

const API_BASE = '/api';

export const useWorkflows = (projectId: number) => {
  return useQuery({
    queryKey: ['workflows', projectId],
    queryFn: async () => {
      const response = await axios.get<Workflow[]>(
        `${API_BASE}/workflows?projectId=${projectId}`
      );
      return response.data;
    },
  });
};

export const useCreateWorkflow = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (workflow: Workflow) => {
      const response = await axios.post<Workflow>(
        `${API_BASE}/workflows`,
        workflow
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
};

export const useUpdateWorkflow = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, workflow }: { id: string; workflow: Partial<Workflow> }) => {
      const response = await axios.patch<Workflow>(
        `${API_BASE}/workflows/${id}`,
        workflow
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflows'] });
    },
  });
};
```

**Step 4: Create basic WorkflowBuilder component**

Create `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`:

```typescript
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

interface WorkflowBuilderProps {
  projectId: number;
  workflowId?: string;
}

export const WorkflowBuilder: React.FC<WorkflowBuilderProps> = ({
  projectId,
  workflowId,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<WorkflowNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<WorkflowEdge>([]);
  const [workflowName, setWorkflowName] = useState('New Workflow');

  const onConnect = React.useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleSave = () => {
    console.log('Save workflow:', { workflowName, nodes, edges });
    // Will implement in Task 24
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
```

**Step 5: Create index export**

Create `frontend/src/components/WorkflowBuilder/index.tsx`:

```typescript
export { WorkflowBuilder } from './WorkflowBuilder';
export type { WorkflowNode, WorkflowEdge, Workflow } from './types';
```

**Step 6: Verify compilation**

```bash
npm run type-check
```

Expected: No TypeScript errors

**Step 7: Commit**

```bash
cd /Users/danielconnolly/Projects/CommandCenter
git add frontend/
git commit -m "feat(vislzr): Add WorkflowBuilder base structure

- React Flow integration for visual DAG editing
- Type definitions for workflow nodes/edges
- useWorkflows hooks for API integration
- Basic toolbar with workflow name and save button

Ref: Phase 10 Phase 4 Option A - MVP"
```

---

### Task 22: Create Custom Agent Node Component

**Files:**
- Create: `frontend/src/components/WorkflowBuilder/nodes/AgentNode.tsx`
- Modify: `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`

**Step 1: Create AgentNode component**

Create `frontend/src/components/WorkflowBuilder/nodes/AgentNode.tsx`:

```typescript
import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { AgentNodeData } from '../types';

export const AgentNode: React.FC<NodeProps<AgentNodeData>> = ({
  data,
  selected,
}) => {
  return (
    <div
      style={{
        minWidth: '180px',
        background: 'white',
        border: `2px solid ${selected ? '#2196F3' : '#4CAF50'}`,
        borderRadius: '8px',
        boxShadow: selected
          ? '0 0 0 2px rgba(33, 150, 243, 0.3)'
          : '0 2px 4px rgba(0,0,0,0.1)',
      }}
    >
      <Handle type="target" position={Position.Top} />

      <div
        style={{
          padding: '8px 12px',
          background: '#4CAF50',
          color: 'white',
          borderRadius: '6px 6px 0 0',
          fontWeight: 600,
          fontSize: '14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span>{data.agentName}</span>
        {data.approvalRequired && (
          <span
            style={{
              background: '#FF9800',
              padding: '2px 6px',
              borderRadius: '4px',
              fontSize: '11px',
            }}
          >
            ⚠️ Approval
          </span>
        )}
      </div>

      <div style={{ padding: '12px' }}>
        <div style={{ fontSize: '13px', color: '#666', marginBottom: '4px' }}>
          {data.action}
        </div>
        {Object.keys(data.inputs).length > 0 && (
          <div style={{ fontSize: '11px', color: '#999' }}>
            {Object.keys(data.inputs).length} input(s)
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};
```

**Step 2: Register custom node type**

Modify `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`:

Add at top:
```typescript
import { AgentNode } from './nodes/AgentNode';

const nodeTypes = {
  agent: AgentNode,
};
```

Update ReactFlow component:
```typescript
<ReactFlow
  nodes={nodes}
  edges={edges}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
  onConnect={onConnect}
  nodeTypes={nodeTypes}  // ADD THIS LINE
  fitView
>
```

**Step 3: Verify compilation**

```bash
npm run type-check
```

Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/components/WorkflowBuilder/
git commit -m "feat(vislzr): Add custom AgentNode component

- Visual node component for workflow agents
- Shows agent name, action, approval status
- Color-coded border (green=normal, blue=selected)
- Handles for node connections

Ref: Phase 10 Phase 4 Option A - MVP"
```

---

### Task 23: Add Agent Palette with Drag-and-Drop

**Files:**
- Create: `frontend/src/components/WorkflowBuilder/AgentPalette.tsx`
- Create: `frontend/src/hooks/useAgents.ts`
- Modify: `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`

**Step 1: Create useAgents hook**

Create `frontend/src/hooks/useAgents.ts`:

```typescript
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';

interface Agent {
  id: string;
  projectId: number;
  name: string;
  type: string;
  description?: string;
  capabilities: Array<{
    name: string;
    description?: string;
  }>;
}

const API_BASE = '/api';

export const useAgents = (projectId: number) => {
  return useQuery({
    queryKey: ['agents', projectId],
    queryFn: async () => {
      const response = await axios.get<Agent[]>(
        `${API_BASE}/agents?projectId=${projectId}`
      );
      return response.data;
    },
  });
};
```

**Step 2: Create AgentPalette component**

Create `frontend/src/components/WorkflowBuilder/AgentPalette.tsx`:

```typescript
import React from 'react';
import { useAgents } from '../../hooks/useAgents';

interface Agent {
  id: string;
  name: string;
  type: string;
  description?: string;
  capabilities: Array<{ name: string }>;
}

interface AgentPaletteProps {
  projectId: number;
  onDragStart: (event: React.DragEvent, agent: Agent) => void;
}

export const AgentPalette: React.FC<AgentPaletteProps> = ({
  projectId,
  onDragStart,
}) => {
  const { data: agents, isLoading } = useAgents(projectId);

  if (isLoading) {
    return (
      <div style={{ width: '280px', padding: '2rem', textAlign: 'center' }}>
        Loading agents...
      </div>
    );
  }

  return (
    <div
      style={{
        width: '280px',
        background: 'white',
        borderRight: '1px solid #ddd',
        overflowY: 'auto',
      }}
    >
      <h3
        style={{
          padding: '1rem',
          margin: 0,
          fontSize: '1.1rem',
          borderBottom: '1px solid #ddd',
          background: '#f9f9f9',
        }}
      >
        Available Agents
      </h3>
      <div style={{ padding: '0.5rem' }}>
        {agents?.map((agent) => (
          <div
            key={agent.id}
            draggable
            onDragStart={(e) => onDragStart(e, agent)}
            style={{
              display: 'flex',
              gap: '12px',
              padding: '12px',
              marginBottom: '8px',
              background: '#f5f5f5',
              border: '1px solid #ddd',
              borderRadius: '6px',
              cursor: 'grab',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#e8f5e9';
              e.currentTarget.style.borderColor = '#4CAF50';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#f5f5f5';
              e.currentTarget.style.borderColor = '#ddd';
            }}
          >
            <div style={{ fontSize: '24px' }}>🤖</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontWeight: 600,
                  fontSize: '14px',
                  marginBottom: '2px',
                }}
              >
                {agent.name}
              </div>
              <div
                style={{
                  fontSize: '11px',
                  color: '#666',
                  textTransform: 'uppercase',
                }}
              >
                {agent.type}
              </div>
              {agent.description && (
                <div
                  style={{
                    fontSize: '12px',
                    color: '#888',
                    marginTop: '4px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {agent.description}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

**Step 3: Integrate palette into WorkflowBuilder**

Modify `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`:

Add imports:
```typescript
import { AgentPalette } from './AgentPalette';
import { WorkflowNode } from './types';
```

Add drag-and-drop handlers:
```typescript
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

    setNodes((nds) => nds.concat(newNode));
  },
  [setNodes]
);

const onDragStart = React.useCallback((event: React.DragEvent, agent: any) => {
  event.dataTransfer.setData('application/json', JSON.stringify(agent));
  event.dataTransfer.effectAllowed = 'move';
}, []);
```

Update JSX structure:
```typescript
return (
  <div style={{ display: 'flex', flexDirection: 'column', height: '100vh' }}>
    <div style={{ /* toolbar styles */ }}>
      {/* toolbar content */}
    </div>
    <div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
      <AgentPalette projectId={projectId} onDragStart={onDragStart} />
      <div
        style={{ flex: 1, position: 'relative' }}
        onDrop={onDrop}
        onDragOver={onDragOver}
      >
        <ReactFlow ...>
        </ReactFlow>
      </div>
    </div>
  </div>
);
```

**Step 4: Verify compilation**

```bash
npm run type-check
```

Expected: No errors

**Step 5: Commit**

```bash
git add frontend/
git commit -m "feat(vislzr): Add agent palette with drag-and-drop

- Sidebar showing available agents from API
- Drag agent from palette to canvas
- Creates agent node on drop with default action
- useAgents hook for fetching registered agents

Ref: Phase 10 Phase 4 Option A - MVP"
```

---

### Task 24: Add Node Configuration Panel

**Files:**
- Create: `frontend/src/components/WorkflowBuilder/NodeConfigPanel.tsx`
- Modify: `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`

**Step 1: Create NodeConfigPanel component**

Create `frontend/src/components/WorkflowBuilder/NodeConfigPanel.tsx`:

```typescript
import React from 'react';
import { WorkflowNode } from './types';

interface NodeConfigPanelProps {
  node: WorkflowNode | null;
  onUpdate: (nodeId: string, updates: Partial<WorkflowNode['data']>) => void;
  onClose: () => void;
}

export const NodeConfigPanel: React.FC<NodeConfigPanelProps> = ({
  node,
  onUpdate,
  onClose,
}) => {
  if (!node) return null;

  const [inputs, setInputs] = React.useState(node.data.inputs);
  const [action, setAction] = React.useState(node.data.action);
  const [approvalRequired, setApprovalRequired] = React.useState(
    node.data.approvalRequired
  );

  const handleSave = () => {
    onUpdate(node.id, {
      action,
      inputs,
      approvalRequired,
    });
    onClose();
  };

  const handleAddInput = () => {
    const key = prompt('Input key:');
    if (key) {
      setInputs({ ...inputs, [key]: '' });
    }
  };

  const handleInputChange = (key: string, value: string) => {
    setInputs({ ...inputs, [key]: value });
  };

  const handleRemoveInput = (key: string) => {
    const newInputs = { ...inputs };
    delete newInputs[key];
    setInputs(newInputs);
  };

  return (
    <div
      style={{
        width: '320px',
        background: 'white',
        borderLeft: '1px solid #ddd',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div
        style={{
          padding: '1rem',
          borderBottom: '1px solid #ddd',
          background: '#f9f9f9',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Configure Node</h3>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '20px',
            cursor: 'pointer',
            padding: '0 8px',
          }}
        >
          ×
        </button>
      </div>

      <div style={{ padding: '1rem', flex: 1 }}>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', fontWeight: 600, marginBottom: '4px' }}>
            Agent
          </label>
          <div style={{ color: '#666' }}>{node.data.agentName}</div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label
            style={{ display: 'block', fontWeight: 600, marginBottom: '4px' }}
            htmlFor="action"
          >
            Action
          </label>
          <input
            id="action"
            type="text"
            value={action}
            onChange={(e) => setAction(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '14px',
            }}
          />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '8px',
            }}
          >
            <label style={{ fontWeight: 600 }}>Inputs</label>
            <button
              onClick={handleAddInput}
              style={{
                padding: '4px 8px',
                background: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
              }}
            >
              + Add Input
            </button>
          </div>
          <div>
            {Object.entries(inputs).map(([key, value]) => (
              <div
                key={key}
                style={{
                  marginBottom: '8px',
                  padding: '8px',
                  background: '#f5f5f5',
                  borderRadius: '4px',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '4px',
                  }}
                >
                  <span style={{ fontWeight: 600, fontSize: '13px' }}>{key}</span>
                  <button
                    onClick={() => handleRemoveInput(key)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#f44336',
                      cursor: 'pointer',
                      fontSize: '12px',
                    }}
                  >
                    Remove
                  </button>
                </div>
                <input
                  type="text"
                  value={value}
                  onChange={(e) => handleInputChange(key, e.target.value)}
                  placeholder="Value or template (e.g., {{ context.foo }})"
                  style={{
                    width: '100%',
                    padding: '6px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '13px',
                  }}
                />
              </div>
            ))}
            {Object.keys(inputs).length === 0 && (
              <div style={{ color: '#999', fontSize: '13px', fontStyle: 'italic' }}>
                No inputs configured
              </div>
            )}
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={approvalRequired}
              onChange={(e) => setApprovalRequired(e.target.checked)}
              style={{ marginRight: '8px' }}
            />
            <span style={{ fontWeight: 600 }}>Require approval before execution</span>
          </label>
        </div>
      </div>

      <div
        style={{
          padding: '1rem',
          borderTop: '1px solid #ddd',
          display: 'flex',
          gap: '8px',
        }}
      >
        <button
          onClick={handleSave}
          style={{
            flex: 1,
            padding: '10px',
            background: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          Save
        </button>
        <button
          onClick={onClose}
          style={{
            padding: '10px 20px',
            background: '#f5f5f5',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
};
```

**Step 2: Integrate panel into WorkflowBuilder**

Modify `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`:

Add import:
```typescript
import { NodeConfigPanel } from './NodeConfigPanel';
```

Add state:
```typescript
const [selectedNode, setSelectedNode] = useState<WorkflowNode | null>(null);
```

Add node click handler:
```typescript
const onNodeClick = React.useCallback(
  (_event: React.MouseEvent, node: WorkflowNode) => {
    setSelectedNode(node);
  },
  []
);
```

Add update handler:
```typescript
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
```

Update ReactFlow:
```typescript
<ReactFlow
  nodes={nodes}
  edges={edges}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
  onConnect={onConnect}
  onNodeClick={onNodeClick}  // ADD THIS
  nodeTypes={nodeTypes}
  fitView
>
```

Add panel to JSX:
```typescript
<div style={{ flex: 1, display: 'flex', overflow: 'hidden' }}>
  <AgentPalette projectId={projectId} onDragStart={onDragStart} />
  <div
    style={{ flex: 1, position: 'relative' }}
    onDrop={onDrop}
    onDragOver={onDragOver}
  >
    <ReactFlow ...>
    </ReactFlow>
  </div>
  <NodeConfigPanel  {/* ADD THIS */}
    node={selectedNode}
    onUpdate={onNodeUpdate}
    onClose={() => setSelectedNode(null)}
  />
</div>
```

**Step 3: Verify compilation**

```bash
npm run type-check
```

Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/components/WorkflowBuilder/
git commit -m "feat(vislzr): Add node configuration panel

- Click node to open config panel
- Edit action name
- Add/edit/remove input key-value pairs
- Toggle approval requirement
- Save updates to node data

Ref: Phase 10 Phase 4 Option A - MVP"
```

---

### Task 25: Implement Save/Load Workflow

**Files:**
- Modify: `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`
- Modify: `frontend/src/components/WorkflowBuilder/types.ts`

**Step 1: Add workflow conversion helpers**

Add to `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`:

```typescript
// Add after imports
import { useCreateWorkflow, useUpdateWorkflow, useWorkflows } from '../../hooks/useWorkflows';
import { Workflow } from './types';

// Add helper functions before component
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

  workflow.nodes.forEach((node, index) => {
    const nodeId = `node-${index}`;
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

    node.dependsOn.forEach((depIndex) => {
      edges.push({
        id: `edge-${depIndex}-${nodeId}`,
        source: `node-${depIndex}`,
        target: nodeId,
      });
    });
  });

  return { nodes, edges };
};
```

**Step 2: Add workflow mutations**

Update WorkflowBuilder component:

```typescript
// Add hooks
const createWorkflow = useCreateWorkflow();
const updateWorkflow = useUpdateWorkflow();

// Update handleSave
const handleSave = async () => {
  const workflowData: Workflow = {
    projectId,
    name: workflowName,
    description: `Created via workflow builder`,
    trigger: {
      event: 'manual',
      pattern: 'manual',
    },
    status: 'DRAFT',
    nodes: convertNodesToBackend(nodes, edges),
  };

  try {
    if (workflowId) {
      await updateWorkflow.mutateAsync({
        id: workflowId,
        workflow: workflowData,
      });
      alert('Workflow updated successfully!');
    } else {
      const created = await createWorkflow.mutateAsync(workflowData);
      alert(`Workflow created with ID: ${created.id}`);
    }
  } catch (error: any) {
    alert(`Failed to save workflow: ${error.message}`);
  }
};
```

**Step 3: Add workflow loading**

Update component:

```typescript
// Add inside component, before return
const { data: workflows } = useWorkflows(projectId);

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
```

**Step 4: Verify compilation**

```bash
npm run type-check
```

Expected: No errors

**Step 5: Test save functionality**

Manual test: Open the WorkflowBuilder, drag some nodes, connect them, configure inputs, click Save.

Expected: Success alert with workflow ID

**Step 6: Commit**

```bash
git add frontend/src/components/WorkflowBuilder/ frontend/src/hooks/
git commit -m "feat(vislzr): Implement save/load workflow

- Convert React Flow nodes/edges to backend format
- Save new workflow or update existing
- Load existing workflow and reconstruct canvas
- Success/error notifications

Ref: Phase 10 Phase 4 Option A - MVP"
```

---

## Part 2: Approval Interface (Tasks 26-28)

### Task 26: Create Approval Queue Component

**Files:**
- Create: `frontend/src/components/ApprovalQueue/index.tsx`
- Create: `frontend/src/components/ApprovalQueue/ApprovalQueue.tsx`
- Create: `frontend/src/components/ApprovalQueue/ApprovalCard.tsx`
- Create: `frontend/src/hooks/useApprovals.ts`

**Step 1: Create useApprovals hook**

Create `frontend/src/hooks/useApprovals.ts`:

```typescript
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

interface Approval {
  id: string;
  workflowRunId: string;
  nodeId: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  requestedAt: string;
  respondedAt?: string;
  respondedBy?: string;
  notes?: string;
}

const API_BASE = '/api';

export const useApprovals = (status?: string) => {
  return useQuery({
    queryKey: ['approvals', status],
    queryFn: async () => {
      const params = status ? `?status=${status}` : '';
      const response = await axios.get<Approval[]>(
        `${API_BASE}/approvals${params}`
      );
      return response.data;
    },
    refetchInterval: 5000, // Poll every 5 seconds
  });
};

export const useApproveWorkflow = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ approvalId, notes }: { approvalId: string; notes?: string }) => {
      const response = await axios.post(
        `${API_BASE}/approvals/${approvalId}/approve`,
        { notes }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
    },
  });
};

export const useRejectWorkflow = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ approvalId, notes }: { approvalId: string; notes: string }) => {
      const response = await axios.post(
        `${API_BASE}/approvals/${approvalId}/reject`,
        { notes }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
    },
  });
};
```

**Step 2: Create ApprovalCard component**

Create `frontend/src/components/ApprovalQueue/ApprovalCard.tsx`:

```typescript
import React from 'react';

interface Approval {
  id: string;
  workflowRunId: string;
  nodeId: string;
  requestedAt: string;
}

interface ApprovalCardProps {
  approval: Approval;
  onClick: () => void;
}

export const ApprovalCard: React.FC<ApprovalCardProps> = ({
  approval,
  onClick,
}) => {
  const requestedDate = new Date(approval.requestedAt);
  const timeAgo = Math.floor((Date.now() - requestedDate.getTime()) / 60000);

  return (
    <div
      onClick={onClick}
      style={{
        padding: '16px',
        background: '#fff3e0',
        border: '2px solid #FF9800',
        borderRadius: '8px',
        marginBottom: '12px',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'start',
          marginBottom: '8px',
        }}
      >
        <div style={{ fontWeight: 600, fontSize: '15px' }}>
          ⚠️ Approval Required
        </div>
        <div style={{ fontSize: '12px', color: '#666' }}>
          {timeAgo === 0 ? 'Just now' : `${timeAgo}m ago`}
        </div>
      </div>
      <div style={{ fontSize: '13px', color: '#666', marginBottom: '4px' }}>
        Workflow Run: {approval.workflowRunId.substring(0, 8)}...
      </div>
      <div style={{ fontSize: '13px', color: '#666' }}>
        Node: {approval.nodeId}
      </div>
    </div>
  );
};
```

**Step 3: Create ApprovalQueue component**

Create `frontend/src/components/ApprovalQueue/ApprovalQueue.tsx`:

```typescript
import React, { useState } from 'react';
import { useApprovals } from '../../hooks/useApprovals';
import { ApprovalCard } from './ApprovalCard';

export const ApprovalQueue: React.FC = () => {
  const { data: approvals, isLoading } = useApprovals('PENDING');
  const [selectedApprovalId, setSelectedApprovalId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        Loading approvals...
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ margin: 0, marginBottom: '8px' }}>Pending Approvals</h2>
        <p style={{ margin: 0, color: '#666' }}>
          {approvals?.length || 0} workflow(s) waiting for approval
        </p>
      </div>

      {approvals && approvals.length === 0 ? (
        <div
          style={{
            padding: '3rem',
            textAlign: 'center',
            background: '#f5f5f5',
            borderRadius: '8px',
            color: '#999',
          }}
        >
          No pending approvals
        </div>
      ) : (
        <div>
          {approvals?.map((approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              onClick={() => setSelectedApprovalId(approval.id)}
            />
          ))}
        </div>
      )}

      {selectedApprovalId && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setSelectedApprovalId(null)}
        >
          <div
            style={{
              background: 'white',
              padding: '2rem',
              borderRadius: '8px',
              maxWidth: '500px',
              width: '90%',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3>Approval Details</h3>
            <p>Approval ID: {selectedApprovalId}</p>
            <p>Full detail view will be implemented in Task 27</p>
            <button
              onClick={() => setSelectedApprovalId(null)}
              style={{
                padding: '8px 16px',
                background: '#f5f5f5',
                border: '1px solid #ccc',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
```

**Step 4: Create index export**

Create `frontend/src/components/ApprovalQueue/index.tsx`:

```typescript
export { ApprovalQueue } from './ApprovalQueue';
```

**Step 5: Verify compilation**

```bash
npm run type-check
```

Expected: No errors

**Step 6: Commit**

```bash
git add frontend/src/components/ApprovalQueue/ frontend/src/hooks/useApprovals.ts
git commit -m "feat(vislzr): Add approval queue component

- List pending workflow approvals
- Auto-refresh every 5 seconds
- Approval cards with time ago
- useApprovals hook with approve/reject mutations
- Placeholder modal for approval details

Ref: Phase 10 Phase 4 Option A - MVP"
```

---

### Task 27: Add Approval Detail View

**Files:**
- Create: `frontend/src/components/ApprovalQueue/ApprovalDetail.tsx`
- Modify: `frontend/src/components/ApprovalQueue/ApprovalQueue.tsx`

**Step 1: Create ApprovalDetail component**

Create `frontend/src/components/ApprovalQueue/ApprovalDetail.tsx`:

```typescript
import React, { useState } from 'react';
import { useApproveWorkflow, useRejectWorkflow } from '../../hooks/useApprovals';

interface ApprovalDetailProps {
  approvalId: string;
  workflowRunId: string;
  nodeId: string;
  onClose: () => void;
}

export const ApprovalDetail: React.FC<ApprovalDetailProps> = ({
  approvalId,
  workflowRunId,
  nodeId,
  onClose,
}) => {
  const [notes, setNotes] = useState('');
  const approveWorkflow = useApproveWorkflow();
  const rejectWorkflow = useRejectWorkflow();

  const handleApprove = async () => {
    if (confirm('Are you sure you want to approve this workflow step?')) {
      try {
        await approveWorkflow.mutateAsync({ approvalId, notes });
        alert('Workflow approved successfully!');
        onClose();
      } catch (error: any) {
        alert(`Failed to approve: ${error.message}`);
      }
    }
  };

  const handleReject = async () => {
    if (!notes.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }

    if (confirm('Are you sure you want to reject this workflow step?')) {
      try {
        await rejectWorkflow.mutateAsync({ approvalId, notes });
        alert('Workflow rejected');
        onClose();
      } catch (error: any) {
        alert(`Failed to reject: ${error.message}`);
      }
    }
  };

  return (
    <div
      style={{
        position: 'fixed',
        top: 0,
        left: 0,
        right: 0,
        bottom: 0,
        background: 'rgba(0,0,0,0.5)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        zIndex: 1000,
      }}
      onClick={onClose}
    >
      <div
        style={{
          background: 'white',
          padding: 0,
          borderRadius: '8px',
          maxWidth: '600px',
          width: '90%',
          maxHeight: '80vh',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            padding: '1.5rem',
            borderBottom: '1px solid #ddd',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <h3 style={{ margin: 0 }}>⚠️ Approval Required</h3>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              padding: '0 8px',
            }}
          >
            ×
          </button>
        </div>

        <div style={{ padding: '1.5rem', flex: 1, overflowY: 'auto' }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ fontWeight: 600, marginBottom: '4px' }}>Workflow Run</div>
            <div
              style={{
                padding: '8px',
                background: '#f5f5f5',
                borderRadius: '4px',
                fontSize: '14px',
                fontFamily: 'monospace',
              }}
            >
              {workflowRunId}
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ fontWeight: 600, marginBottom: '4px' }}>Node ID</div>
            <div
              style={{
                padding: '8px',
                background: '#f5f5f5',
                borderRadius: '4px',
                fontSize: '14px',
                fontFamily: 'monospace',
              }}
            >
              {nodeId}
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label
              style={{ fontWeight: 600, display: 'block', marginBottom: '8px' }}
              htmlFor="notes"
            >
              Notes (optional for approval, required for rejection)
            </label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about your decision..."
              rows={4}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '14px',
                fontFamily: 'inherit',
                resize: 'vertical',
              }}
            />
          </div>

          <div
            style={{
              padding: '12px',
              background: '#fff3e0',
              border: '1px solid #FF9800',
              borderRadius: '4px',
              fontSize: '13px',
            }}
          >
            <strong>⚠️ Important:</strong> Approving this step will allow the workflow to
            continue execution. Rejecting will stop the workflow.
          </div>
        </div>

        <div
          style={{
            padding: '1.5rem',
            borderTop: '1px solid #ddd',
            display: 'flex',
            gap: '12px',
            justifyContent: 'flex-end',
          }}
        >
          <button
            onClick={handleReject}
            disabled={rejectWorkflow.isPending}
            style={{
              padding: '10px 20px',
              background: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: rejectWorkflow.isPending ? 'not-allowed' : 'pointer',
              fontWeight: 600,
              opacity: rejectWorkflow.isPending ? 0.6 : 1,
            }}
          >
            {rejectWorkflow.isPending ? 'Rejecting...' : 'Reject'}
          </button>
          <button
            onClick={handleApprove}
            disabled={approveWorkflow.isPending}
            style={{
              padding: '10px 20px',
              background: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: approveWorkflow.isPending ? 'not-allowed' : 'pointer',
              fontWeight: 600,
              opacity: approveWorkflow.isPending ? 0.6 : 1,
            }}
          >
            {approveWorkflow.isPending ? 'Approving...' : 'Approve'}
          </button>
        </div>
      </div>
    </div>
  );
};
```

**Step 2: Integrate into ApprovalQueue**

Modify `frontend/src/components/ApprovalQueue/ApprovalQueue.tsx`:

Replace modal placeholder with:
```typescript
import { ApprovalDetail } from './ApprovalDetail';

// Replace the modal div with:
{selectedApprovalId && (() => {
  const approval = approvals?.find((a) => a.id === selectedApprovalId);
  return approval ? (
    <ApprovalDetail
      approvalId={approval.id}
      workflowRunId={approval.workflowRunId}
      nodeId={approval.nodeId}
      onClose={() => setSelectedApprovalId(null)}
    />
  ) : null;
})()}
```

**Step 3: Verify compilation**

```bash
npm run type-check
```

Expected: No errors

**Step 4: Commit**

```bash
git add frontend/src/components/ApprovalQueue/
git commit -m "feat(vislzr): Add approval detail view with approve/reject

- Modal with workflow run and node details
- Notes textarea for approval rationale
- Approve button (with optional notes)
- Reject button (requires notes)
- Confirmation dialogs for safety
- Loading states during API calls

Ref: Phase 10 Phase 4 Option A - MVP"
```

---

### Task 28: Add Approval Notification Badge

**Files:**
- Create: `frontend/src/components/ApprovalBadge/index.tsx`
- Create: `frontend/src/components/ApprovalBadge/ApprovalBadge.tsx`

**Step 1: Create ApprovalBadge component**

Create `frontend/src/components/ApprovalBadge/ApprovalBadge.tsx`:

```typescript
import React from 'react';
import { useApprovals } from '../../hooks/useApprovals';

interface ApprovalBadgeProps {
  onClick?: () => void;
}

export const ApprovalBadge: React.FC<ApprovalBadgeProps> = ({ onClick }) => {
  const { data: approvals } = useApprovals('PENDING');
  const count = approvals?.length || 0;

  if (count === 0) return null;

  return (
    <div
      onClick={onClick}
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        background: '#FF9800',
        color: 'white',
        padding: '12px 20px',
        borderRadius: '24px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontWeight: 600,
        fontSize: '14px',
        transition: 'all 0.2s',
        zIndex: 999,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.05)';
        e.currentTarget.style.boxShadow = '0 6px 16px rgba(0,0,0,0.4)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
      }}
    >
      <span style={{ fontSize: '18px' }}>⚠️</span>
      <span>{count} Pending Approval{count !== 1 ? 's' : ''}</span>
    </div>
  );
};
```

**Step 2: Create index export**

Create `frontend/src/components/ApprovalBadge/index.tsx`:

```typescript
export { ApprovalBadge } from './ApprovalBadge';
```

**Step 3: Verify compilation**

```bash
npm run type-check
```

Expected: No errors

**Step 4: Document integration**

Add note to plan:

```markdown
**Integration Note:** The ApprovalBadge component should be added to the main app layout:

```typescript
// In App.tsx or main layout component
import { ApprovalBadge } from './components/ApprovalBadge';

// Add to JSX:
<ApprovalBadge onClick={() => navigate('/approvals')} />
```

This will show a floating badge when approvals are pending.
```

**Step 5: Commit**

```bash
git add frontend/src/components/ApprovalBadge/
git commit -m "feat(vislzr): Add floating approval notification badge

- Shows count of pending approvals
- Floating button in bottom-right corner
- Auto-refreshes with useApprovals hook
- Click to navigate to approval queue
- Hides when no approvals pending

Ref: Phase 10 Phase 4 Option A - MVP"
```

---

## Summary of Phase 4 Option A

**Tasks Completed:**
- ✅ Task 21: Setup React Flow and base structure
- ✅ Task 22: Create custom AgentNode component
- ✅ Task 23: Add agent palette with drag-and-drop
- ✅ Task 24: Add node configuration panel
- ✅ Task 25: Implement save/load workflow
- ✅ Task 26: Create approval queue component
- ✅ Task 27: Add approval detail view with approve/reject
- ✅ Task 28: Add approval notification badge

**What Was Built:**
- Visual workflow builder with drag-and-drop
- Agent palette sidebar
- Node configuration panel
- Save/load workflows via API
- Approval queue with pending workflows
- Approval detail modal with approve/reject
- Floating notification badge

**What's Missing (deferred):**
- Execution monitoring UI
- Agent library browser
- Advanced template editor
- Workflow validation
- Undo/redo
- Real-time WebSocket updates

**Estimated Time:** 1 week (8 tasks)

**Next Steps:**
1. Integrate WorkflowBuilder and ApprovalQueue into main VISLZR navigation
2. Test end-to-end workflow creation and approval
3. Consider adding execution monitoring (Option B) if workflows are being actively used

---

**End of Plan**
