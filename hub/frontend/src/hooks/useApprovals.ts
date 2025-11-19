import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';

export interface Approval {
  id: string;
  workflowRunId: string;
  nodeId: string;
  status: 'PENDING' | 'APPROVED' | 'REJECTED';
  requestedAt: string;
  respondedAt?: string;
  respondedBy?: string;
  notes?: string;
  workflowRun?: {
    id: string;
    workflow: {
      id: string;
      name: string;
      description?: string;
    };
  };
  node?: {
    id: string;
    agent: {
      id: string;
      name: string;
      type: string;
    };
  };
}

export interface ApprovalDecision {
  decision: 'APPROVED' | 'REJECTED';
  notes?: string;
  respondedBy: string;
}

const API_BASE = 'http://localhost:9002/api';

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
    refetchInterval: (query) => {
      // Poll every 5 seconds if there are pending approvals
      const data = query.state.data;
      if (data && data.some((approval: Approval) => approval.status === 'PENDING')) {
        return 5000;
      }
      return false;
    },
  });
};

// Get approvals for a specific workflow run
export const useWorkflowRunApprovals = (workflowRunId: string) => {
  return useQuery({
    queryKey: ['approvals', 'workflow-run', workflowRunId],
    queryFn: async () => {
      const response = await axios.get<Approval[]>(
        `${API_BASE}/approvals?workflowRunId=${workflowRunId}`
      );
      return response.data;
    },
    enabled: !!workflowRunId,
  });
};

// Submit approval decision (unified approve/reject endpoint)
export const useApprovalDecision = () => {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ approvalId, decision }: { approvalId: string; decision: ApprovalDecision }) => {
      const response = await axios.post(
        `${API_BASE}/approvals/${approvalId}/decision`,
        decision
      );
      return response.data;
    },
    onSuccess: () => {
      // Invalidate approvals list
      queryClient.invalidateQueries({ queryKey: ['approvals'] });
      // Invalidate workflow runs (status may have changed)
      queryClient.invalidateQueries({ queryKey: ['workflow-runs'] });
      queryClient.invalidateQueries({ queryKey: ['workflow-run'] });
    },
  });
};

// Legacy hooks for backwards compatibility
export const useApproveWorkflow = () => {
  const approvalDecision = useApprovalDecision();

  return {
    ...approvalDecision,
    mutate: ({ approvalId, notes }: { approvalId: string; notes?: string }) => {
      approvalDecision.mutate({
        approvalId,
        decision: {
          decision: 'APPROVED',
          notes,
          respondedBy: 'user', // TODO: Get from auth context
        },
      });
    },
  };
};

export const useRejectWorkflow = () => {
  const approvalDecision = useApprovalDecision();

  return {
    ...approvalDecision,
    mutate: ({ approvalId, notes }: { approvalId: string; notes: string }) => {
      approvalDecision.mutate({
        approvalId,
        decision: {
          decision: 'REJECTED',
          notes,
          respondedBy: 'user', // TODO: Get from auth context
        },
      });
    },
  };
};
