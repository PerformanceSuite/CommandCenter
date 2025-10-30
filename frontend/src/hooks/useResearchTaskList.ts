import { useState, useEffect, useCallback } from 'react';
import { researchApi } from '../services/researchApi';
import type { ResearchTask } from '../types/research';

/**
 * Hook to manage research task list with polling for status updates
 */
export function useResearchTaskList(pollInterval: number = 3000) {
  const [tasks, setTasks] = useState<Map<string, ResearchTask>>(new Map());
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const addTask = useCallback(async (taskId: string) => {
    try {
      setError(null);
      const task = await researchApi.getResearchTaskStatus(taskId);
      setTasks(prev => new Map(prev).set(taskId, task));
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Unknown error';
      setError(`Failed to add task: ${errorMessage}`);
    }
  }, []);

  const removeTask = useCallback((taskId: string) => {
    setTasks(prev => {
      const next = new Map(prev);
      next.delete(taskId);
      return next;
    });
    if (expandedTaskId === taskId) {
      setExpandedTaskId(null);
    }
  }, [expandedTaskId]);

  const refreshTasks = useCallback(async () => {
    if (tasks.size === 0) return;

    try {
      setRefreshing(true);
      const promises = Array.from(tasks.keys()).map(taskId =>
        researchApi.getResearchTaskStatus(taskId)
      );
      const updated = await Promise.all(promises);

      const newTasks = new Map(tasks);
      updated.forEach(task => {
        newTasks.set(task.task_id, task);
      });
      setTasks(newTasks);
      setError(null);
    } catch (err) {
      console.error('Failed to refresh tasks:', err);
      setError('Failed to refresh tasks');
    } finally {
      setRefreshing(false);
    }
  }, [tasks]);

  const toggleExpand = useCallback((taskId: string) => {
    setExpandedTaskId(prev => (prev === taskId ? null : taskId));
  }, []);

  useEffect(() => {
    // Poll for task updates at specified interval
    const interval = setInterval(() => {
      if (tasks.size > 0) {
        refreshTasks();
      }
    }, pollInterval);

    return () => clearInterval(interval);
  }, [pollInterval, tasks, refreshTasks]);

  return {
    tasks,
    expandedTaskId,
    refreshing,
    error,
    addTask,
    removeTask,
    refreshTasks,
    toggleExpand,
  };
}
