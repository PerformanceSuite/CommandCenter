import { useState, useEffect } from 'react';
import { TaskStatus } from '../types';

const API_BASE = '/api';

export const useTaskStatus = (taskId: string | null) => {
  const [status, setStatus] = useState<TaskStatus | null>(null);
  const [isPolling, setIsPolling] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!taskId) {
      setIsPolling(false);
      setStatus(null);
      setError(null);
      return;
    }

    setIsPolling(true);
    setError(null);

    const pollStatus = async (): Promise<boolean> => {
      try {
        const response = await fetch(`${API_BASE}/task-status/${taskId}`);

        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`);
        }

        const data: TaskStatus = await response.json();
        setStatus(data);

        // Stop polling when task finishes
        if (['SUCCESS', 'FAILURE', 'REVOKED'].includes(data.state)) {
          setIsPolling(false);
          return true; // Signal to stop interval
        }

        return false; // Continue polling
      } catch (err) {
        console.error('Error polling task status:', err);
        setError(err instanceof Error ? err.message : 'Unknown error');
        setIsPolling(false);
        return true; // Stop on error
      }
    };

    // Poll immediately
    pollStatus();

    // Then poll every 2 seconds
    const interval = setInterval(async () => {
      const shouldStop = await pollStatus();
      if (shouldStop) {
        clearInterval(interval);
      }
    }, 2000);

    return () => {
      clearInterval(interval);
      setIsPolling(false);
    };
  }, [taskId]);

  return { status, isPolling, error };
};
