import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { researchApi } from '../services/researchApi';
import type {
  ResearchTask,
  ResearchTaskCreate,
  ResearchTaskUpdate,
  ResearchTaskFilter,
  TaskStatus,
} from '../types/researchTask';

const QUERY_KEYS = {
  tasks: 'research-tasks',
  task: (id: number) => ['research-tasks', id],
  statistics: 'research-task-statistics',
  upcoming: 'upcoming-tasks',
  overdue: 'overdue-tasks',
};

/**
 * Hook to fetch all research tasks with optional filters
 */
export function useResearchTasks(filters?: ResearchTaskFilter) {
  return useQuery<ResearchTask[], Error>({
    queryKey: [QUERY_KEYS.tasks, filters],
    queryFn: () => researchApi.getTasks(filters),
  });
}

/**
 * Hook to fetch a single research task by ID
 */
export function useResearchTask(taskId: number) {
  return useQuery<ResearchTask, Error>({
    queryKey: QUERY_KEYS.task(taskId),
    queryFn: () => researchApi.getTaskById(taskId),
    enabled: !!taskId,
  });
}

/**
 * Hook to create a new research task
 */
export function useCreateResearchTask() {
  const queryClient = useQueryClient();

  return useMutation<ResearchTask, Error, ResearchTaskCreate>({
    mutationFn: (data) => researchApi.createTask(data),
    onSuccess: () => {
      // Invalidate tasks list to refetch
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.tasks] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.statistics] });
    },
  });
}

/**
 * Hook to update a research task
 */
export function useUpdateResearchTask() {
  const queryClient = useQueryClient();

  return useMutation<
    ResearchTask,
    Error,
    { taskId: number; data: ResearchTaskUpdate },
    { previousTask?: ResearchTask }
  >({
    mutationFn: ({ taskId, data }) => researchApi.updateTask(taskId, data),
    onMutate: async ({ taskId, data }) => {
      // Cancel any outgoing refetches
      await queryClient.cancelQueries({ queryKey: QUERY_KEYS.task(taskId) });

      // Snapshot the previous value
      const previousTask = queryClient.getQueryData<ResearchTask>(
        QUERY_KEYS.task(taskId)
      );

      // Optimistically update the task
      if (previousTask) {
        queryClient.setQueryData<ResearchTask>(QUERY_KEYS.task(taskId), {
          ...previousTask,
          ...data,
        });
      }

      // Return context with the previous task
      return { previousTask };
    },
    onError: (_err, { taskId }, context) => {
      // Rollback on error
      if (context?.previousTask) {
        queryClient.setQueryData(QUERY_KEYS.task(taskId), context.previousTask);
      }
    },
    onSuccess: (data, { taskId }) => {
      // Update the cache with the server response
      queryClient.setQueryData(QUERY_KEYS.task(taskId), data);
      // Invalidate lists to refetch
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.tasks] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.statistics] });
    },
  });
}

/**
 * Hook to delete a research task
 */
export function useDeleteResearchTask() {
  const queryClient = useQueryClient();

  return useMutation<void, Error, number>({
    mutationFn: (taskId) => researchApi.deleteTask(taskId),
    onSuccess: (_, taskId) => {
      // Remove from cache
      queryClient.removeQueries({ queryKey: QUERY_KEYS.task(taskId) });
      // Invalidate lists to refetch
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.tasks] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.statistics] });
    },
  });
}

/**
 * Hook to update task status
 */
export function useUpdateTaskStatus() {
  const queryClient = useQueryClient();

  return useMutation<
    ResearchTask,
    Error,
    { taskId: number; status: TaskStatus }
  >({
    mutationFn: ({ taskId, status }) =>
      researchApi.updateTaskStatus(taskId, status),
    onSuccess: (data, { taskId }) => {
      queryClient.setQueryData(QUERY_KEYS.task(taskId), data);
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.tasks] });
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.statistics] });
    },
  });
}

/**
 * Hook to update task progress
 */
export function useUpdateTaskProgress() {
  const queryClient = useQueryClient();

  return useMutation<
    ResearchTask,
    Error,
    { taskId: number; progress: number }
  >({
    mutationFn: ({ taskId, progress }) =>
      researchApi.updateTaskProgress(taskId, progress),
    onSuccess: (data, { taskId }) => {
      queryClient.setQueryData(QUERY_KEYS.task(taskId), data);
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.tasks] });
    },
  });
}

/**
 * Hook to upload a document to a task
 */
export function useUploadDocument() {
  const queryClient = useQueryClient();

  return useMutation<ResearchTask, Error, { taskId: number; file: File }>({
    mutationFn: ({ taskId, file }) => researchApi.uploadDocument(taskId, file),
    onSuccess: (data, { taskId }) => {
      // Update the task cache with the new document
      queryClient.setQueryData(QUERY_KEYS.task(taskId), data);
      queryClient.invalidateQueries({ queryKey: [QUERY_KEYS.tasks] });
    },
  });
}

/**
 * Hook to fetch task statistics
 */
export function useTaskStatistics(technologyId?: number, repositoryId?: number) {
  return useQuery({
    queryKey: [QUERY_KEYS.statistics, technologyId, repositoryId],
    queryFn: () => researchApi.getStatistics(technologyId, repositoryId),
  });
}

/**
 * Hook to fetch upcoming tasks
 */
export function useUpcomingTasks(days: number = 7) {
  return useQuery<ResearchTask[], Error>({
    queryKey: [QUERY_KEYS.upcoming, days],
    queryFn: () => researchApi.getUpcomingTasks(days),
  });
}

/**
 * Hook to fetch overdue tasks
 */
export function useOverdueTasks() {
  return useQuery<ResearchTask[], Error>({
    queryKey: [QUERY_KEYS.overdue],
    queryFn: () => researchApi.getOverdueTasks(),
  });
}
