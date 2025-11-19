import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import axios from 'axios';
import { Workflow } from '../components/WorkflowBuilder/types';

const API_BASE = 'http://localhost:9002/api';

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
