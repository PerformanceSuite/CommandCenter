import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

const API_BASE = 'http://localhost:9002/api';

export interface AgentRun {
  id: string;
  agentId: string;
  workflowRunId: string;
  inputJson: any;
  outputJson: any;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'WAITING_APPROVAL';
  error?: string;
  startedAt: string;
  finishedAt?: string;
  durationMs?: number;
  agent: {
    id: string;
    name: string;
    type: string;
    riskLevel: string;
  };
}

export interface WorkflowRun {
  id: string;
  workflowId: string;
  trigger: string;
  contextJson: any;
  status: 'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED' | 'WAITING_APPROVAL';
  startedAt: string;
  finishedAt?: string;
  workflow?: {
    id: string;
    name: string;
    description?: string;
    nodes: any[];
  };
  agentRuns?: AgentRun[];
  approvals?: any[];
}

// List all workflow runs for a workflow
export const useWorkflowRuns = (workflowId: string) => {
  return useQuery({
    queryKey: ['workflow-runs', workflowId],
    queryFn: async () => {
      const response = await axios.get<WorkflowRun[]>(
        `${API_BASE}/workflows/${workflowId}/runs`
      );
      return response.data;
    },
    enabled: !!workflowId,
  });
};

// Get single workflow run with full details (including agent runs and approvals)
export const useWorkflowRun = (workflowId: string, runId: string) => {
  return useQuery({
    queryKey: ['workflow-run', workflowId, runId],
    queryFn: async () => {
      const response = await axios.get<WorkflowRun>(
        `${API_BASE}/workflows/${workflowId}/runs/${runId}`
      );
      return response.data;
    },
    enabled: !!workflowId && !!runId,
    refetchInterval: (query) => {
      // Poll every 2 seconds if workflow is running or pending
      const data = query.state.data;
      if (data && (data.status === 'RUNNING' || data.status === 'PENDING')) {
        return 2000;
      }
      return false;
    },
  });
};

// Get agent runs for a workflow run
export const useAgentRuns = (runId: string) => {
  return useQuery({
    queryKey: ['agent-runs', runId],
    queryFn: async () => {
      const response = await axios.get<AgentRun[]>(
        `${API_BASE}/workflows/runs/${runId}/agent-runs`
      );
      return response.data;
    },
    enabled: !!runId,
    refetchInterval: (query) => {
      // Poll every 2 seconds if any agent is running
      const data = query.state.data;
      if (data && data.some((run: AgentRun) => run.status === 'RUNNING' || run.status === 'PENDING')) {
        return 2000;
      }
      return false;
    },
  });
};

// Retry a failed workflow run
export const useRetryWorkflowRun = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (runId: string) => {
      const response = await axios.post(
        `${API_BASE}/workflows/runs/${runId}/retry`
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate workflow runs list
      queryClient.invalidateQueries({ queryKey: ['workflow-runs'] });
      // Invalidate the specific run
      queryClient.invalidateQueries({ queryKey: ['workflow-run'] });
    },
  });
};

// Trigger a workflow (returns workflow run)
export const useTriggerWorkflow = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ workflowId, contextJson }: { workflowId: string; contextJson: any }) => {
      const response = await axios.post(
        `${API_BASE}/workflows/${workflowId}/trigger`,
        { contextJson }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['workflow-runs'] });
    },
  });
};
