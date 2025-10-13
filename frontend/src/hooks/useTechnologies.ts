import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '../services/api';
import type { Technology, TechnologyCreate, TechnologyUpdate } from '../types/technology';

const QUERY_KEY = ['technologies'];

export interface TechnologyFilters {
  page?: number;
  limit?: number;
  domain?: string;
  status?: string;
  search?: string;
}

export interface TechnologyListData {
  technologies: Technology[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

export function useTechnologies(filters?: TechnologyFilters) {
  const queryClient = useQueryClient();

  // Fetch technologies with pagination and filters
  const {
    data,
    isLoading: loading,
    error,
    refetch: refresh,
  } = useQuery({
    queryKey: [...QUERY_KEY, filters],
    queryFn: async () => {
      const response = await api.getTechnologies(filters);
      return {
        technologies: response.items,
        total: response.total,
        page: response.page,
        pageSize: response.page_size,
        totalPages: Math.ceil(response.total / response.page_size),
      } as TechnologyListData;
    },
  });

  // Backwards compatibility - when no filters, return just the array
  const technologies = data?.technologies || [];
  const total = data?.total || 0;
  const page = data?.page || 1;
  const pageSize = data?.pageSize || 20;
  const totalPages = data?.totalPages || 0;

  // Create mutation
  const createMutation = useMutation<
    Technology,
    Error,
    TechnologyCreate,
    { previousQueries?: Array<{ queryKey: ReadonlyArray<unknown>; data: unknown }> }
  >({
    mutationFn: (data: TechnologyCreate) => api.createTechnology(data),
    onMutate: async (newData: TechnologyCreate) => {
      // Cancel any outgoing refetches for all technology queries
      await queryClient.cancelQueries({ queryKey: QUERY_KEY });

      // Snapshot all existing query caches (all filter combinations)
      const previousQueries: Array<{ queryKey: ReadonlyArray<unknown>; data: unknown }> = [];
      queryClient.getQueryCache().findAll({ queryKey: QUERY_KEY }).forEach(query => {
        previousQueries.push({
          queryKey: query.queryKey,
          data: queryClient.getQueryData(query.queryKey),
        });
      });

      // Optimistically update ALL cached queries with pagination structure
      queryClient.getQueryCache().findAll({ queryKey: QUERY_KEY }).forEach(query => {
        queryClient.setQueryData<TechnologyListData>(query.queryKey, (old) => {
          if (!old) return old;

          return {
            ...old,
            technologies: [
              ...old.technologies,
              {
                ...newData,
                id: -Math.floor(Math.random() * 1000000), // Negative ID to distinguish from real IDs
                created_at: new Date().toISOString(),
                updated_at: new Date().toISOString(),
              } as Technology,
            ],
            total: old.total + 1, // Increment total count
          };
        });
      });

      // Return context with all previous query states
      return { previousQueries };
    },
    onError: (_err: Error, _newData: TechnologyCreate, context) => {
      // Rollback all queries on error
      if (context?.previousQueries) {
        context.previousQueries.forEach(({ queryKey, data }) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSuccess: () => {
      // Invalidate and refetch ALL technology queries to get accurate server state
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  // Update mutation
  const updateMutation = useMutation<
    Technology,
    Error,
    { id: number; data: TechnologyUpdate },
    { previousQueries?: Array<{ queryKey: ReadonlyArray<unknown>; data: unknown }> }
  >({
    mutationFn: ({ id, data }: { id: number; data: TechnologyUpdate }) =>
      api.updateTechnology(id, data),
    onMutate: async ({ id, data }: { id: number; data: TechnologyUpdate }) => {
      // Cancel any outgoing refetches for all technology queries
      await queryClient.cancelQueries({ queryKey: QUERY_KEY });

      // Snapshot all existing query caches (all filter combinations)
      const previousQueries: Array<{ queryKey: ReadonlyArray<unknown>; data: unknown }> = [];
      queryClient.getQueryCache().findAll({ queryKey: QUERY_KEY }).forEach(query => {
        previousQueries.push({
          queryKey: query.queryKey,
          data: queryClient.getQueryData(query.queryKey),
        });
      });

      // Optimistically update ALL cached queries with pagination structure
      queryClient.getQueryCache().findAll({ queryKey: QUERY_KEY }).forEach(query => {
        queryClient.setQueryData<TechnologyListData>(query.queryKey, (old) => {
          if (!old) return old;

          return {
            ...old,
            technologies: old.technologies.map((tech: Technology) =>
              tech.id === id ? { ...tech, ...data, updated_at: new Date().toISOString() } : tech
            ),
          };
        });
      });

      // Return context with all previous query states
      return { previousQueries };
    },
    onError: (_err: Error, _variables: { id: number; data: TechnologyUpdate }, context) => {
      // Rollback all queries on error
      if (context?.previousQueries) {
        context.previousQueries.forEach(({ queryKey, data }) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSuccess: () => {
      // Invalidate and refetch ALL technology queries to get accurate server state
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  // Delete mutation
  const deleteMutation = useMutation<
    void,
    Error,
    number,
    { previousQueries?: Array<{ queryKey: ReadonlyArray<unknown>; data: unknown }> }
  >({
    mutationFn: (id: number) => api.deleteTechnology(id),
    onMutate: async (deletedId: number) => {
      // Cancel any outgoing refetches for all technology queries
      await queryClient.cancelQueries({ queryKey: QUERY_KEY });

      // Snapshot all existing query caches (all filter combinations)
      const previousQueries: Array<{ queryKey: ReadonlyArray<unknown>; data: unknown }> = [];
      queryClient.getQueryCache().findAll({ queryKey: QUERY_KEY }).forEach(query => {
        previousQueries.push({
          queryKey: query.queryKey,
          data: queryClient.getQueryData(query.queryKey),
        });
      });

      // Optimistically update ALL cached queries with pagination structure
      queryClient.getQueryCache().findAll({ queryKey: QUERY_KEY }).forEach(query => {
        queryClient.setQueryData<TechnologyListData>(query.queryKey, (old) => {
          if (!old) return old;

          return {
            ...old,
            technologies: old.technologies.filter((tech: Technology) => tech.id !== deletedId),
            total: Math.max(0, old.total - 1), // Decrement total count (prevent negative)
          };
        });
      });

      // Return context with all previous query states
      return { previousQueries };
    },
    onError: (_err: Error, _deletedId: number, context) => {
      // Rollback all queries on error
      if (context?.previousQueries) {
        context.previousQueries.forEach(({ queryKey, data }) => {
          queryClient.setQueryData(queryKey, data);
        });
      }
    },
    onSuccess: () => {
      // Invalidate and refetch ALL technology queries to get accurate server state
      queryClient.invalidateQueries({ queryKey: QUERY_KEY });
    },
  });

  // Composite loading state
  const isMutating = createMutation.isPending || updateMutation.isPending || deleteMutation.isPending;

  return {
    technologies,
    loading,
    error: error as Error | null,
    refresh,
    // Pagination metadata
    total,
    page,
    pageSize,
    totalPages,
    // Mutation functions
    createTechnology: createMutation.mutateAsync,
    updateTechnology: (id: number, data: TechnologyUpdate) =>
      updateMutation.mutateAsync({ id, data }),
    deleteTechnology: deleteMutation.mutateAsync,
    isCreating: createMutation.isPending,
    isUpdating: updateMutation.isPending,
    isDeleting: deleteMutation.isPending,
    isMutating, // Any mutation in progress
    // Mutation error states for components that need them
    createError: createMutation.error,
    updateError: updateMutation.error,
    deleteError: deleteMutation.error,
  };
}
