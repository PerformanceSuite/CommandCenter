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
