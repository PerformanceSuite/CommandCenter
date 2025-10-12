# Agent 6: Frontend MCP Integration

**Agent Name**: frontend-mcp-integration
**Phase**: 3 (UI/UX & Integration)
**Branch**: agent/frontend-mcp-integration
**Duration**: 8-10 hours
**Dependencies**: Agent 4 (project-manager-mcp), Agent 5 (research-orchestrator-mcp)

---

## Mission

Build the frontend UI components and integration layer for the MCP architecture, enabling users to interact with project analysis, workflow orchestration, and agent execution monitoring through a rich, real-time dashboard.

You are creating the visual interface that brings the MCP architecture to life for end users.

---

## Deliverables

### 1. Project Analysis Dashboard (`frontend/src/components/ProjectAnalysis/`)
- **ProjectAnalysisDashboard.tsx**: Main dashboard component
- **ProjectSelector.tsx**: Dropdown to select or add projects
- **AnalysisResults.tsx**: Display detected technologies, research gaps
- **AnalysisTrigger.tsx**: Button/form to trigger new analysis
- **TechnologyMatrix.tsx**: Visual matrix of detected vs recommended technologies
- **ResearchGapsList.tsx**: Filterable list of research gaps with priority badges

### 2. MCP Server Configuration UI (`frontend/src/components/Settings/MCPConfig/`)
- **MCPServerList.tsx**: List all available MCP servers with status indicators
- **ServerDetailsCard.tsx**: Server info (name, version, capabilities)
- **ResourceExplorer.tsx**: Browse available resources (tree view)
- **ToolExecutor.tsx**: Form to execute MCP tools with argument inputs
- **PromptViewer.tsx**: View and test prompt templates

### 3. Real-time Workflow Progress View (`frontend/src/components/WorkflowExecution/`)
- **WorkflowDashboard.tsx**: Main workflow monitoring dashboard
- **WorkflowList.tsx**: List of workflows (active, completed, failed)
- **WorkflowTimeline.tsx**: Visual timeline of workflow execution
- **TaskProgressCard.tsx**: Individual task status with progress bar
- **AgentStatusGrid.tsx**: Grid showing all agent statuses
- **LiveLogViewer.tsx**: Real-time streaming logs from agents

### 4. Research Workflow Visualization (`frontend/src/components/WorkflowVisualization/`)
- **DependencyGraph.tsx**: Interactive graph showing task dependencies
- **TaskNodeComponent.tsx**: Visual representation of a task (status, model, priority)
- **ExecutionFlowChart.tsx**: Flowchart of execution order
- **ParallelExecutionView.tsx**: Show concurrent tasks running
- **WorkflowStatistics.tsx**: Stats (total tasks, completed, time elapsed, cost)

### 5. Agent Execution Monitoring (`frontend/src/components/AgentMonitoring/`)
- **AgentDashboard.tsx**: Overview of all agents
- **AgentCard.tsx**: Single agent status (running/idle/failed)
- **ModelUsageStats.tsx**: Breakdown of model usage (Claude vs GPT-4)
- **CostTracker.tsx**: Real-time cost tracking for API usage
- **ResultsViewer.tsx**: Display agent results with markdown rendering

### 6. Interactive Result Explorer (`frontend/src/components/ResultsExplorer/`)
- **ResultsBrowser.tsx**: Browse all workflow results
- **ResultDetailView.tsx**: Detailed view of single result
- **ComparisonView.tsx**: Side-by-side comparison of results
- **ExportButton.tsx**: Export results as PDF/Markdown
- **ShareButton.tsx**: Generate shareable link

### 7. API Integration Layer (`frontend/src/services/mcp.ts`)
- `MCPService` class with methods:
  - `listServers()`: Get all MCP servers
  - `getServerResources(serverName: string)`: List resources
  - `readResource(serverName: string, uri: string)`: Read specific resource
  - `executeTool(serverName: string, toolName: string, args: any)`: Execute tool
  - `getPrompts(serverName: string)`: List prompts
  - `generateWorkflow(projectId: number)`: Generate workflow
  - `executeWorkflow(workflowId: string)`: Start workflow
  - `getWorkflowStatus(workflowId: string)`: Get workflow status
  - `subscribeToWorkflowUpdates(workflowId: string, callback: Function)`: WebSocket subscription

### 8. Tests (`frontend/src/components/**/__tests__/`)
- Component rendering tests (React Testing Library)
- API integration tests (mock responses)
- User interaction tests (clicks, form submissions)
- WebSocket subscription tests
- Snapshot tests for visual consistency

---

## Technical Specifications

### Component Architecture

```
frontend/src/components/
├── ProjectAnalysis/
│   ├── ProjectAnalysisDashboard.tsx
│   ├── ProjectSelector.tsx
│   ├── AnalysisResults.tsx
│   ├── TechnologyMatrix.tsx
│   └── ResearchGapsList.tsx
├── Settings/
│   └── MCPConfig/
│       ├── MCPServerList.tsx
│       ├── ResourceExplorer.tsx
│       ├── ToolExecutor.tsx
│       └── PromptViewer.tsx
├── WorkflowExecution/
│   ├── WorkflowDashboard.tsx
│   ├── WorkflowList.tsx
│   ├── WorkflowTimeline.tsx
│   ├── TaskProgressCard.tsx
│   └── LiveLogViewer.tsx
├── WorkflowVisualization/
│   ├── DependencyGraph.tsx
│   ├── TaskNodeComponent.tsx
│   ├── ExecutionFlowChart.tsx
│   └── WorkflowStatistics.tsx
├── AgentMonitoring/
│   ├── AgentDashboard.tsx
│   ├── AgentCard.tsx
│   ├── ModelUsageStats.tsx
│   └── CostTracker.tsx
└── ResultsExplorer/
    ├── ResultsBrowser.tsx
    ├── ResultDetailView.tsx
    ├── ComparisonView.tsx
    └── ExportButton.tsx
```

### State Management

```typescript
// Use React Context for global MCP state
interface MCPState {
  servers: MCPServer[];
  activeWorkflow: Workflow | null;
  workflowHistory: Workflow[];
  selectedProject: Project | null;
  realTimeUpdates: WorkflowUpdate[];
}

const MCPContext = React.createContext<MCPState | null>(null);

export const useMCPContext = () => {
  const context = useContext(MCPContext);
  if (!context) {
    throw new Error("useMCPContext must be used within MCPProvider");
  }
  return context;
};
```

### Real-time Updates (WebSocket)

```typescript
// WebSocket service for live workflow updates
class WorkflowWebSocketService {
  private ws: WebSocket | null = null;
  private subscribers: Map<string, Set<Function>> = new Map();

  connect(workflowId: string) {
    const wsUrl = `ws://localhost:8000/api/v1/workflows/${workflowId}/stream`;
    this.ws = new WebSocket(wsUrl);

    this.ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      this.notifySubscribers(workflowId, update);
    };
  }

  subscribe(workflowId: string, callback: Function) {
    if (!this.subscribers.has(workflowId)) {
      this.subscribers.set(workflowId, new Set());
    }
    this.subscribers.get(workflowId)!.add(callback);
  }

  unsubscribe(workflowId: string, callback: Function) {
    this.subscribers.get(workflowId)?.delete(callback);
  }

  private notifySubscribers(workflowId: string, update: any) {
    this.subscribers.get(workflowId)?.forEach(callback => callback(update));
  }
}
```

---

## Implementation Guidelines

### 1. Project Analysis Dashboard (`ProjectAnalysisDashboard.tsx`)

```typescript
import React, { useState, useEffect } from 'react';
import { MCPService } from '../../services/mcp';
import ProjectSelector from './ProjectSelector';
import AnalysisResults from './AnalysisResults';
import TechnologyMatrix from './TechnologyMatrix';
import ResearchGapsList from './ResearchGapsList';

interface ProjectAnalysis {
  projectId: number;
  technologies: Technology[];
  researchGaps: ResearchGap[];
  analyzedAt: string;
}

const ProjectAnalysisDashboard: React.FC = () => {
  const [selectedProject, setSelectedProject] = useState<number | null>(null);
  const [analysis, setAnalysis] = useState<ProjectAnalysis | null>(null);
  const [loading, setLoading] = useState(false);
  const mcpService = new MCPService();

  useEffect(() => {
    if (selectedProject) {
      loadAnalysis(selectedProject);
    }
  }, [selectedProject]);

  const loadAnalysis = async (projectId: number) => {
    setLoading(true);
    try {
      // Read project analysis from MCP server
      const result = await mcpService.readResource(
        'project-manager',
        `analysis://${projectId}`
      );
      setAnalysis(JSON.parse(result.contents[0].text));
    } catch (error) {
      console.error('Failed to load analysis:', error);
    } finally {
      setLoading(false);
    }
  };

  const triggerAnalysis = async (projectPath: string) => {
    setLoading(true);
    try {
      // Execute analyze_project tool
      const result = await mcpService.executeTool(
        'project-manager',
        'analyze_project',
        { project_path: projectPath, force_rescan: true }
      );

      if (result.success) {
        await loadAnalysis(result.project_id);
      }
    } catch (error) {
      console.error('Analysis failed:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="project-analysis-dashboard">
      <h1>Project Analysis</h1>

      <ProjectSelector
        selectedProject={selectedProject}
        onSelect={setSelectedProject}
      />

      {loading && <LoadingSpinner />}

      {analysis && (
        <>
          <AnalysisResults
            technologies={analysis.technologies}
            researchGaps={analysis.researchGaps}
            analyzedAt={analysis.analyzedAt}
          />

          <TechnologyMatrix technologies={analysis.technologies} />

          <ResearchGapsList
            gaps={analysis.researchGaps}
            onGenerateWorkflow={(gapIds) => handleGenerateWorkflow(gapIds)}
          />
        </>
      )}

      <button
        onClick={() => {
          const path = prompt('Enter project path:');
          if (path) triggerAnalysis(path);
        }}
        disabled={loading}
      >
        Analyze New Project
      </button>
    </div>
  );
};

export default ProjectAnalysisDashboard;
```

### 2. Workflow Dashboard (`WorkflowDashboard.tsx`)

```typescript
import React, { useState, useEffect } from 'react';
import { MCPService } from '../../services/mcp';
import WorkflowList from './WorkflowList';
import WorkflowTimeline from './WorkflowTimeline';
import TaskProgressCard from './TaskProgressCard';
import LiveLogViewer from './LiveLogViewer';

interface Workflow {
  id: string;
  projectId: number;
  status: string;
  tasks: AgentTask[];
  progress: number; // 0-100
}

const WorkflowDashboard: React.FC = () => {
  const [workflows, setWorkflows] = useState<Workflow[]>([]);
  const [selectedWorkflow, setSelectedWorkflow] = useState<Workflow | null>(null);
  const mcpService = new MCPService();

  useEffect(() => {
    loadWorkflows();
    const interval = setInterval(loadWorkflows, 5000); // Poll every 5s
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (selectedWorkflow) {
      // Subscribe to real-time updates
      const unsubscribe = mcpService.subscribeToWorkflowUpdates(
        selectedWorkflow.id,
        (update: any) => {
          setSelectedWorkflow(prev => ({ ...prev!, ...update }));
        }
      );

      return unsubscribe;
    }
  }, [selectedWorkflow?.id]);

  const loadWorkflows = async () => {
    try {
      // List workflows from MCP server
      const result = await mcpService.readResource(
        'research-orchestrator',
        'workflow://list'
      );
      const workflowList = JSON.parse(result.contents[0].text);
      setWorkflows(workflowList);
    } catch (error) {
      console.error('Failed to load workflows:', error);
    }
  };

  const generateWorkflow = async (projectId: number) => {
    try {
      const result = await mcpService.executeTool(
        'research-orchestrator',
        'generate_workflow',
        { project_id: projectId, max_concurrent: 3 }
      );

      if (result.workflow_id) {
        await loadWorkflows();
        // Auto-select new workflow
        const newWorkflow = workflows.find(w => w.id === result.workflow_id);
        if (newWorkflow) setSelectedWorkflow(newWorkflow);
      }
    } catch (error) {
      console.error('Workflow generation failed:', error);
    }
  };

  const executeWorkflow = async (workflowId: string) => {
    try {
      await mcpService.executeTool(
        'research-orchestrator',
        'execute_workflow',
        { workflow_id: workflowId }
      );

      // Workflow will update via WebSocket
    } catch (error) {
      console.error('Workflow execution failed:', error);
    }
  };

  return (
    <div className="workflow-dashboard">
      <h1>Research Workflows</h1>

      <div className="workflow-layout">
        <aside className="workflow-sidebar">
          <WorkflowList
            workflows={workflows}
            selectedWorkflow={selectedWorkflow}
            onSelect={setSelectedWorkflow}
            onGenerate={generateWorkflow}
          />
        </aside>

        <main className="workflow-main">
          {selectedWorkflow && (
            <>
              <WorkflowHeader
                workflow={selectedWorkflow}
                onExecute={() => executeWorkflow(selectedWorkflow.id)}
              />

              <WorkflowTimeline tasks={selectedWorkflow.tasks} />

              <div className="task-grid">
                {selectedWorkflow.tasks.map(task => (
                  <TaskProgressCard key={task.id} task={task} />
                ))}
              </div>

              <LiveLogViewer workflowId={selectedWorkflow.id} />
            </>
          )}
        </main>
      </div>
    </div>
  );
};

export default WorkflowDashboard;
```

### 3. Dependency Graph Visualization (`DependencyGraph.tsx`)

```typescript
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';

interface DependencyGraphProps {
  tasks: AgentTask[];
  width?: number;
  height?: number;
}

const DependencyGraph: React.FC<DependencyGraphProps> = ({
  tasks,
  width = 800,
  height = 600
}) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current) return;

    // Convert tasks to D3 graph format
    const nodes = tasks.map(task => ({
      id: task.id,
      name: task.title,
      status: task.status,
      type: task.type
    }));

    const links = tasks.flatMap(task =>
      task.dependencies.map(depId => ({
        source: depId,
        target: task.id
      }))
    );

    // Create D3 force simulation
    const simulation = d3.forceSimulation(nodes)
      .force('link', d3.forceLink(links).id((d: any) => d.id))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2));

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove(); // Clear previous

    // Draw links
    const link = svg.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', '#999')
      .attr('stroke-width', 2)
      .attr('marker-end', 'url(#arrowhead)');

    // Draw nodes
    const node = svg.append('g')
      .selectAll('circle')
      .data(nodes)
      .join('circle')
      .attr('r', 20)
      .attr('fill', (d: any) => getStatusColor(d.status))
      .call(drag(simulation) as any);

    // Add labels
    const label = svg.append('g')
      .selectAll('text')
      .data(nodes)
      .join('text')
      .text((d: any) => d.name)
      .attr('font-size', 12)
      .attr('dx', 25)
      .attr('dy', 5);

    // Update positions on simulation tick
    simulation.on('tick', () => {
      link
        .attr('x1', (d: any) => d.source.x)
        .attr('y1', (d: any) => d.source.y)
        .attr('x2', (d: any) => d.target.x)
        .attr('y2', (d: any) => d.target.y);

      node
        .attr('cx', (d: any) => d.x)
        .attr('cy', (d: any) => d.y);

      label
        .attr('x', (d: any) => d.x)
        .attr('y', (d: any) => d.y);
    });

    // Define arrow marker
    svg.append('defs').append('marker')
      .attr('id', 'arrowhead')
      .attr('viewBox', '-0 -5 10 10')
      .attr('refX', 30)
      .attr('refY', 0)
      .attr('orient', 'auto')
      .attr('markerWidth', 6)
      .attr('markerHeight', 6)
      .append('path')
      .attr('d', 'M 0,-5 L 10,0 L 0,5')
      .attr('fill', '#999');

    return () => {
      simulation.stop();
    };
  }, [tasks, width, height]);

  const getStatusColor = (status: string) => {
    const colors: { [key: string]: string } = {
      pending: '#ccc',
      running: '#4CAF50',
      completed: '#2196F3',
      failed: '#f44336'
    };
    return colors[status] || '#ccc';
  };

  const drag = (simulation: any) => {
    function dragstarted(event: any) {
      if (!event.active) simulation.alphaTarget(0.3).restart();
      event.subject.fx = event.subject.x;
      event.subject.fy = event.subject.y;
    }

    function dragged(event: any) {
      event.subject.fx = event.x;
      event.subject.fy = event.y;
    }

    function dragended(event: any) {
      if (!event.active) simulation.alphaTarget(0);
      event.subject.fx = null;
      event.subject.fy = null;
    }

    return d3.drag()
      .on('start', dragstarted)
      .on('drag', dragged)
      .on('end', dragended);
  };

  return (
    <div className="dependency-graph">
      <h2>Task Dependency Graph</h2>
      <svg ref={svgRef} width={width} height={height} />
    </div>
  );
};

export default DependencyGraph;
```

### 4. MCP Service (`services/mcp.ts`)

```typescript
import axios from 'axios';

export class MCPService {
  private baseUrl = 'http://localhost:8000/api/v1/mcp';
  private wsService = new WorkflowWebSocketService();

  async listServers(): Promise<MCPServer[]> {
    const response = await axios.get(`${this.baseUrl}/servers`);
    return response.data.servers;
  }

  async getServerResources(serverName: string): Promise<Resource[]> {
    const response = await axios.post(
      `${this.baseUrl}/servers/${serverName}/resources`
    );
    return response.data.resources;
  }

  async readResource(serverName: string, uri: string): Promise<any> {
    const response = await axios.post(
      `${this.baseUrl}/servers/${serverName}/resources`,
      { uri }
    );
    return response.data;
  }

  async executeTool(
    serverName: string,
    toolName: string,
    arguments: any
  ): Promise<any> {
    const response = await axios.post(
      `${this.baseUrl}/servers/${serverName}/tools/${toolName}`,
      arguments
    );
    return response.data;
  }

  subscribeToWorkflowUpdates(
    workflowId: string,
    callback: (update: any) => void
  ): () => void {
    this.wsService.connect(workflowId);
    this.wsService.subscribe(workflowId, callback);

    return () => this.wsService.unsubscribe(workflowId, callback);
  }
}
```

---

## Testing Strategy

### Component Tests

```typescript
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import ProjectAnalysisDashboard from '../ProjectAnalysisDashboard';
import { MCPService } from '../../../services/mcp';

jest.mock('../../../services/mcp');

describe('ProjectAnalysisDashboard', () => {
  it('renders project selector', () => {
    render(<ProjectAnalysisDashboard />);
    expect(screen.getByText('Project Analysis')).toBeInTheDocument();
  });

  it('loads analysis when project selected', async () => {
    const mockAnalysis = {
      projectId: 1,
      technologies: [{ title: 'React' }],
      researchGaps: []
    };

    (MCPService.prototype.readResource as jest.Mock).mockResolvedValue({
      contents: [{ text: JSON.stringify(mockAnalysis) }]
    });

    render(<ProjectAnalysisDashboard />);

    // Select project
    fireEvent.click(screen.getByRole('combobox'));
    fireEvent.click(screen.getByText('Project 1'));

    await waitFor(() => {
      expect(screen.getByText('React')).toBeInTheDocument();
    });
  });

  it('triggers analysis on button click', async () => {
    const mockExecuteTool = jest.fn().mockResolvedValue({
      success: true,
      project_id: 1
    });

    (MCPService.prototype.executeTool as jest.Mock) = mockExecuteTool;

    render(<ProjectAnalysisDashboard />);

    fireEvent.click(screen.getByText('Analyze New Project'));

    // Enter project path in prompt (mocked)
    // ...

    await waitFor(() => {
      expect(mockExecuteTool).toHaveBeenCalledWith(
        'project-manager',
        'analyze_project',
        expect.any(Object)
      );
    });
  });
});
```

---

## Dependencies

```json
{
  "dependencies": {
    "d3": "^7.8.5",
    "react-markdown": "^9.0.0",
    "recharts": "^2.10.0",
    "react-syntax-highlighter": "^15.5.0"
  },
  "devDependencies": {
    "@types/d3": "^7.4.3"
  }
}
```

---

## Success Criteria

- ✅ All 8 deliverables complete
- ✅ Project analysis dashboard functional
- ✅ MCP server configuration UI working
- ✅ Real-time workflow progress updates
- ✅ Dependency graph visualization
- ✅ Agent monitoring dashboard
- ✅ Results explorer with export
- ✅ WebSocket integration for live updates
- ✅ 80%+ test coverage
- ✅ Responsive design (mobile-friendly)
- ✅ Accessibility compliance (WCAG 2.1)
- ✅ Self-review score: 10/10

---

## Self-Review Checklist

Before marking PR as ready:
- [ ] All 8 deliverables complete
- [ ] Tests pass (npm test)
- [ ] Integration with Agent 4 & 5 verified
- [ ] Linting passes (npm run lint)
- [ ] Type checking passes (npm run type-check)
- [ ] Components documented (JSDoc/TSDoc)
- [ ] Storybook stories created
- [ ] Responsive design verified
- [ ] Accessibility audit passed
- [ ] No console errors or warnings
- [ ] Self-review score: 10/10
