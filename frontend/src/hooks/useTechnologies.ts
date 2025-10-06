import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Technology, TechnologyCreate, TechnologyUpdate } from '../types/technology';

const QUERY_KEY = ['technologies'];

export function useTechnologies() {
  const queryClient = useQueryClient();

  // Fetch all technologies
  const {
    data: technologies = [],
    isLoading: loading,
    error,
    refetch: refresh,
  } = useQuery({
    queryKey: QUERY_KEY,
    queryFn: () => api.getTechnologies(),
  });

  // Create mutation
  const createMutation = useMutation({
    mutationFn: (data: TechnologyCreate) => api.createTechnology(data),
    onSuccess: (newTechnology) => {
      // Optimistically update the cache
      queryClient.setQueryData<Technology[]>(QUERY_KEY, (old = []) => [...old, newTechnology]);
    },
  });

  // Update mutation
  const updateMutation = useMutation({
    mutationFn: ({ id, data }: { id: number; data: TechnologyUpdate }) =>
      api.updateTechnology(id, data),
    onSuccess: (updated) => {
      // Optimistically update the cache
      queryClient.setQueryData<Technology[]>(QUERY_KEY, (old = []) =>
        old.map((tech) => (tech.id === updated.id ? updated : tech))
      );
    },
  });

  // Delete mutation
  const deleteMutation = useMutation({
    mutationFn: (id: number) => api.deleteTechnology(id),
    onSuccess: (_, deletedId) => {
      // Optimistically update the cache
      queryClient.setQueryData<Technology[]>(QUERY_KEY, (old = []) =>
        old.filter((tech) => tech.id !== deletedId)
      );
    },
  });

  return {
    technologies,
    loading,
    error: error as Error | null,
    refresh,
    createTechnology: createMutation.mutateAsync,
    updateTechnology: (id: number, data: TechnologyUpdate) =>
      updateMutation.mutateAsync({ id, data }),
    deleteTechnology: deleteMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
  };
}
