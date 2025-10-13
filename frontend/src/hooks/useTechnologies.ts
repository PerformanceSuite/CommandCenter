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
  const createMutation = useMutation<
    Technology,
    Error,
    TechnologyCreate,
    { previousTechnologies?: Technology[] }
  >({
    mutationFn: (data: TechnologyCreate) => api.createTechnology(data),
    onMutate: async (newData: TechnologyCreate) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: QUERY_KEY });

      // Snapshot the previous value
      const previousTechnologies = queryClient.getQueryData<Technology[]>(QUERY_KEY);

      // Optimistically add to cache
      queryClient.setQueryData<Technology[]>(QUERY_KEY, (old = []) => [
        ...old,
        { ...newData, id: Date.now() } as Technology, // Temporary ID
      ]);

      // Return context with the previous state
      return { previousTechnologies };
    },
    onError: (_err: Error, _newData: TechnologyCreate, context) => {
      // Rollback on error
      if (context?.previousTechnologies) {
        queryClient.setQueryData(QUERY_KEY, context.previousTechnologies);
      }
    },
    onSuccess: () => {
      // Invalidate and refetch to get server state
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  // Update mutation
  const updateMutation = useMutation<
    Technology,
    Error,
    { id: number; data: TechnologyUpdate },
    { previousTechnologies?: Technology[] }
  >({
    mutationFn: ({ id, data }: { id: number; data: TechnologyUpdate }) =>
      api.updateTechnology(id, data),
    onMutate: async ({ id, data }: { id: number; data: TechnologyUpdate }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: QUERY_KEY });

      // Snapshot the previous value
      const previousTechnologies = queryClient.getQueryData<Technology[]>(QUERY_KEY);

      // Optimistically update the cache
      queryClient.setQueryData<Technology[]>(QUERY_KEY, (old = []) =>
        old.map((tech: Technology) => (tech.id === id ? { ...tech, ...data } : tech))
      );

      // Return context with the previous state
      return { previousTechnologies };
    },
    onError: (_err: Error, _variables: { id: number; data: TechnologyUpdate }, context) => {
      // Rollback on error
      if (context?.previousTechnologies) {
        queryClient.setQueryData(QUERY_KEY, context.previousTechnologies);
      }
    },
    onSuccess: () => {
      // Invalidate and refetch to get server state
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  // Delete mutation
  const deleteMutation = useMutation<
    void,
    Error,
    number,
    { previousTechnologies?: Technology[] }
  >({
    mutationFn: (id: number) => api.deleteTechnology(id),
    onMutate: async (deletedId: number) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: QUERY_KEY });

      // Snapshot the previous value
      const previousTechnologies = queryClient.getQueryData<Technology[]>(QUERY_KEY);

      // Optimistically remove from cache
      queryClient.setQueryData<Technology[]>(QUERY_KEY, (old = []) =>
        old.filter((tech: Technology) => tech.id !== deletedId)
      );

      // Return context with the previous state
      return { previousTechnologies };
    },
    onError: (_err: Error, _deletedId: number, context) => {
      // Rollback on error
      if (context?.previousTechnologies) {
        queryClient.setQueryData(QUERY_KEY, context.previousTechnologies);
      }
    },
    onSuccess: () => {
      // Invalidate and refetch to get server state
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
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
