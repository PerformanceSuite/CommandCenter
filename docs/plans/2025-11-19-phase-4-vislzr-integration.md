# Phase 4: VISLZR Integration - Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a React-based workflow builder UI with drag-and-drop node editing, real-time execution monitoring, approval interface, and agent library browser.

**Architecture:** React + TypeScript frontend integrated with existing VISLZR frontend, using React Flow for visual DAG editing, WebSocket for real-time updates, and REST API for workflow/agent CRUD operations.

**Tech Stack:** React 18, TypeScript, React Flow, TailwindCSS, React Query, WebSocket, Axios

---

## Phase 4 Overview

**Components:**
1. Workflow Builder (Tasks 21-28) - Visual DAG editor with React Flow
2. Execution Monitor (Tasks 29-33) - Real-time workflow status and logs
3. Approval Interface (Tasks 34-37) - Pending approvals with approve/reject
4. Agent Library Browser (Tasks 38-41) - Browse and test registered agents

**Estimated Time:** 2-3 weeks (41 tasks total)

---

## Part 1: Workflow Builder (Tasks 21-28)

### Task 21: Create Workflow Builder Component Structure

**Files:**
- Create: `frontend/src/components/WorkflowBuilder/index.tsx`
- Create: `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`
- Create: `frontend/src/components/WorkflowBuilder/types.ts`
- Create: `frontend/src/components/WorkflowBuilder/WorkflowBuilder.module.css`

**Step 1: Install React Flow dependency**

```bash
cd frontend
npm install reactflow@11.10.1
```

Expected: Dependency added to package.json

**Step 2: Create type definitions**

Create `frontend/src/components/WorkflowBuilder/types.ts`:

```typescript
import { Node, Edge } from 'reactflow';

export interface WorkflowNode extends Node {
  data: {
    agentId: string;
    agentName: string;
    action: string;
    inputs: Record<string, unknown>;
    approvalRequired: boolean;
  };
}

export interface WorkflowEdge extends Edge {
  // Standard React Flow edge
}

export interface Workflow {
  id: string;
  projectId: number;
  name: string;
  description?: string;
  trigger: {
    event: string;
    pattern: string;
  };
  status: 'ACTIVE' | 'DRAFT' | 'ARCHIVED';
  nodes: WorkflowNode[];
  edges: WorkflowEdge[];
}
```

**Step 3: Create basic WorkflowBuilder component**

Create `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`:

```typescript
import React, { useState, useCallback } from 'react';
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
import styles from './WorkflowBuilder.module.css';

interface WorkflowBuilderProps {
  workflowId?: string;
  onSave?: (nodes: WorkflowNode[], edges: WorkflowEdge[]) => void;
}

export const WorkflowBuilder: React.FC<WorkflowBuilderProps> = ({
  workflowId,
  onSave,
}) => {
  const [nodes, setNodes, onNodesChange] = useNodesState<WorkflowNode>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState<WorkflowEdge>([]);

  const onConnect = useCallback(
    (params: Connection | Edge) => setEdges((eds) => addEdge(params, eds)),
    [setEdges]
  );

  const handleSave = () => {
    if (onSave) {
      onSave(nodes, edges);
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.toolbar}>
        <h2>Workflow Builder</h2>
        <button onClick={handleSave} className={styles.saveButton}>
          Save Workflow
        </button>
      </div>
      <div className={styles.canvas}>
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

**Step 4: Create CSS module**

Create `frontend/src/components/WorkflowBuilder/WorkflowBuilder.module.css`:

```css
.container {
  display: flex;
  flex-direction: column;
  height: 100vh;
  width: 100%;
}

.toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem;
  background: #f5f5f5;
  border-bottom: 1px solid #ddd;
}

.toolbar h2 {
  margin: 0;
  font-size: 1.5rem;
}

.saveButton {
  padding: 0.5rem 1rem;
  background: #4CAF50;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
}

.saveButton:hover {
  background: #45a049;
}

.canvas {
  flex: 1;
  position: relative;
}
```

**Step 5: Create index file**

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
git add frontend/src/components/WorkflowBuilder/
git commit -m "feat(vislzr): Add WorkflowBuilder component skeleton

- React Flow integration for visual DAG editing
- Basic toolbar with save button
- Type definitions for workflow nodes/edges
- CSS module for styling

Ref: Phase 10 Phase 4 - VISLZR Integration"
```

---

### Task 22: Add Agent Node Component

**Files:**
- Create: `frontend/src/components/WorkflowBuilder/nodes/AgentNode.tsx`
- Create: `frontend/src/components/WorkflowBuilder/nodes/AgentNode.module.css`
- Modify: `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`

**Step 1: Create AgentNode component**

Create `frontend/src/components/WorkflowBuilder/nodes/AgentNode.tsx`:

```typescript
import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { WorkflowNode } from '../types';
import styles from './AgentNode.module.css';

export const AgentNode: React.FC<NodeProps<WorkflowNode['data']>> = ({
  data,
  selected,
}) => {
  return (
    <div className={`${styles.node} ${selected ? styles.selected : ''}`}>
      <Handle type="target" position={Position.Top} />

      <div className={styles.header}>
        <div className={styles.agentName}>{data.agentName}</div>
        {data.approvalRequired && (
          <div className={styles.approvalBadge}>⚠️ Approval</div>
        )}
      </div>

      <div className={styles.body}>
        <div className={styles.action}>{data.action}</div>
        {Object.keys(data.inputs).length > 0 && (
          <div className={styles.inputCount}>
            {Object.keys(data.inputs).length} input(s)
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};
```

**Step 2: Create AgentNode styles**

Create `frontend/src/components/WorkflowBuilder/nodes/AgentNode.module.css`:

```css
.node {
  min-width: 180px;
  background: white;
  border: 2px solid #4CAF50;
  border-radius: 8px;
  padding: 0;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
  transition: all 0.2s;
}

.node:hover {
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
}

.node.selected {
  border-color: #2196F3;
  box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.3);
}

.header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #4CAF50;
  color: white;
  border-radius: 6px 6px 0 0;
}

.agentName {
  font-weight: 600;
  font-size: 14px;
}

.approvalBadge {
  background: #FF9800;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 11px;
  font-weight: 600;
}

.body {
  padding: 12px;
}

.action {
  font-size: 13px;
  color: #666;
  margin-bottom: 4px;
}

.inputCount {
  font-size: 11px;
  color: #999;
}
```

**Step 3: Register custom node type**

Modify `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`:

```typescript
// Add import at top
import { AgentNode } from './nodes/AgentNode';

// Add nodeTypes constant before component
const nodeTypes = {
  agent: AgentNode,
};

// Update ReactFlow component props
<ReactFlow
  nodes={nodes}
  edges={edges}
  onNodesChange={onNodesChange}
  onEdgesChange={onEdgesChange}
  onConnect={onConnect}
  nodeTypes={nodeTypes}  // ADD THIS
  fitView
>
```

**Step 4: Verify compilation**

```bash
npm run type-check
```

Expected: No errors

**Step 5: Commit**

```bash
git add frontend/src/components/WorkflowBuilder/
git commit -m "feat(vislzr): Add AgentNode custom component

- Visual node component for agents
- Displays agent name, action, approval status
- Color-coded based on state
- Handles for connections

Ref: Phase 10 Phase 4 - VISLZR Integration"
```

---

### Task 23: Add Agent Palette Sidebar

**Files:**
- Create: `frontend/src/components/WorkflowBuilder/AgentPalette.tsx`
- Create: `frontend/src/components/WorkflowBuilder/AgentPalette.module.css`
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
    inputSchema: object;
    outputSchema: object;
  }>;
}

export const useAgents = (projectId: number) => {
  return useQuery({
    queryKey: ['agents', projectId],
    queryFn: async () => {
      const response = await axios.get<Agent[]>(
        `/api/agents?projectId=${projectId}`
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
import styles from './AgentPalette.module.css';

interface AgentPaletteProps {
  projectId: number;
  onDragStart: (event: React.DragEvent, agent: any) => void;
}

export const AgentPalette: React.FC<AgentPaletteProps> = ({
  projectId,
  onDragStart,
}) => {
  const { data: agents, isLoading } = useAgents(projectId);

  if (isLoading) {
    return <div className={styles.loading}>Loading agents...</div>;
  }

  return (
    <div className={styles.palette}>
      <h3 className={styles.title}>Available Agents</h3>
      <div className={styles.agentList}>
        {agents?.map((agent) => (
          <div
            key={agent.id}
            className={styles.agentItem}
            draggable
            onDragStart={(e) => onDragStart(e, agent)}
          >
            <div className={styles.agentIcon}>🤖</div>
            <div className={styles.agentInfo}>
              <div className={styles.agentName}>{agent.name}</div>
              <div className={styles.agentType}>{agent.type}</div>
              {agent.description && (
                <div className={styles.agentDesc}>{agent.description}</div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
```

**Step 3: Create AgentPalette styles**

Create `frontend/src/components/WorkflowBuilder/AgentPalette.module.css`:

```css
.palette {
  width: 280px;
  background: white;
  border-right: 1px solid #ddd;
  overflow-y: auto;
}

.title {
  padding: 1rem;
  margin: 0;
  font-size: 1.1rem;
  border-bottom: 1px solid #ddd;
  background: #f9f9f9;
}

.agentList {
  padding: 0.5rem;
}

.agentItem {
  display: flex;
  gap: 12px;
  padding: 12px;
  margin-bottom: 8px;
  background: #f5f5f5;
  border: 1px solid #ddd;
  border-radius: 6px;
  cursor: grab;
  transition: all 0.2s;
}

.agentItem:hover {
  background: #e8f5e9;
  border-color: #4CAF50;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.agentItem:active {
  cursor: grabbing;
}

.agentIcon {
  font-size: 24px;
}

.agentInfo {
  flex: 1;
  min-width: 0;
}

.agentName {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 2px;
}

.agentType {
  font-size: 11px;
  color: #666;
  text-transform: uppercase;
}

.agentDesc {
  font-size: 12px;
  color: #888;
  margin-top: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.loading {
  padding: 2rem;
  text-align: center;
  color: #999;
}
```

**Step 4: Integrate palette into WorkflowBuilder**

Modify `frontend/src/components/WorkflowBuilder/WorkflowBuilder.tsx`:

```typescript
// Add imports
import { AgentPalette } from './AgentPalette';
import { useCallback } from 'react';

// Add inside component
const onDragOver = useCallback((event: React.DragEvent) => {
  event.preventDefault();
  event.dataTransfer.dropEffect = 'move';
}, []);

const onDrop = useCallback(
  (event: React.DragEvent) => {
    event.preventDefault();

    const agentData = event.dataTransfer.getData('application/json');
    if (!agentData) return;

    const agent = JSON.parse(agentData);
    const reactFlowBounds = event.currentTarget.getBoundingClientRect();
    const position = {
      x: event.clientX - reactFlowBounds.left,
      y: event.clientY - reactFlowBounds.top,
    };

    const newNode: WorkflowNode = {
      id: `agent-${Date.now()}`,
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

const onDragStart = useCallback((event: React.DragEvent, agent: any) => {
  event.dataTransfer.setData('application/json', JSON.stringify(agent));
  event.dataTransfer.effectAllowed = 'move';
}, []);

// Update JSX
return (
  <div className={styles.container}>
    <div className={styles.toolbar}>
      <h2>Workflow Builder</h2>
      <button onClick={handleSave} className={styles.saveButton}>
        Save Workflow
      </button>
    </div>
    <div className={styles.content}>  {/* NEW WRAPPER */}
      <AgentPalette projectId={1} onDragStart={onDragStart} />  {/* ADD */}
      <div className={styles.canvas} onDrop={onDrop} onDragOver={onDragOver}>
        <ReactFlow ...>
        </ReactFlow>
      </div>
    </div>  {/* END WRAPPER */}
  </div>
);
```

**Step 5: Update CSS**

Update `frontend/src/components/WorkflowBuilder/WorkflowBuilder.module.css`:

```css
/* Add after .toolbar */
.content {
  flex: 1;
  display: flex;
  overflow: hidden;
}
```

**Step 6: Install React Query if needed**

```bash
npm install @tanstack/react-query@5.0.0
```

**Step 7: Verify compilation**

```bash
npm run type-check
```

**Step 8: Commit**

```bash
git add frontend/src/components/WorkflowBuilder/ frontend/src/hooks/useAgents.ts
git commit -m "feat(vislzr): Add agent palette with drag-and-drop

- Sidebar showing available agents
- Drag-and-drop to add agents to canvas
- useAgents hook for fetching agents
- Creates agent nodes on drop

Ref: Phase 10 Phase 4 - VISLZR Integration"
```

---

**[Plan continues with Tasks 24-41...]**

Due to length constraints, I'll provide a summary of remaining tasks. The full plan would continue with:

**Tasks 24-28: Workflow Builder (continued)**
- Task 24: Add node configuration panel
- Task 25: Add input template editor
- Task 26: Add workflow metadata editor
- Task 27: Implement save/load workflow
- Task 28: Add workflow validation

**Tasks 29-33: Execution Monitor**
- Task 29: Create WorkflowExecutionMonitor component
- Task 30: Add real-time status updates (WebSocket)
- Task 31: Add agent run timeline view
- Task 32: Add log viewer
- Task 33: Add retry/cancel controls

**Tasks 34-37: Approval Interface**
- Task 34: Create ApprovalQueue component
- Task 35: Add approval detail view
- Task 36: Implement approve/reject actions
- Task 37: Add approval notification badge

**Tasks 38-41: Agent Library Browser**
- Task 38: Create AgentLibrary component
- Task 39: Add agent detail view with schema
- Task 40: Add agent test interface
- Task 41: Add agent registration form

---

## Testing Strategy

Each component should have:
1. Unit tests for business logic
2. Integration tests for API interactions
3. E2E tests for critical user flows

**Test Files:**
- `WorkflowBuilder.test.tsx`
- `AgentPalette.test.tsx`
- `ExecutionMonitor.test.tsx`
- `ApprovalQueue.test.tsx`

---

## Success Criteria

- [ ] User can drag agents onto canvas
- [ ] User can connect nodes with edges
- [ ] User can configure node inputs with templates
- [ ] User can save/load workflows
- [ ] User can monitor workflow execution in real-time
- [ ] User can approve/reject pending workflow steps
- [ ] User can browse available agents
- [ ] User can test agents with sample inputs

---

**End of Plan Header**

*Note: This is a partial plan showing the structure and first 3 tasks. The complete plan would have all 41 tasks with similar detail level.*
