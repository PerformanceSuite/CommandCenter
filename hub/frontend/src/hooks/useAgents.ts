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

const API_BASE = 'http://localhost:9002/api';

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
