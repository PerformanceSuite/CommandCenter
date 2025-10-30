import { useState, useEffect, useCallback } from 'react';
import { researchApi } from '../services/researchApi';
import type { ResearchSummaryResponse } from '../types/research';

/**
 * Hook to fetch and manage research summary data with auto-refresh
 */
export function useResearchSummary(refreshInterval: number = 10000) {
  const [summary, setSummary] = useState<ResearchSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchSummary = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await researchApi.getResearchSummary();
      setSummary(data);
    } catch (err) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to load summary';
      setError(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let isMounted = true;

    const loadData = async () => {
      try {
        const data = await researchApi.getResearchSummary();
        if (isMounted) {
          setSummary(data);
          setError(null);
        }
      } catch (err) {
        if (isMounted) {
          const errorMessage = err instanceof Error ? err.message : 'Failed to load summary';
          setError(errorMessage);
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadData();

    // Refresh at specified interval
    const interval = setInterval(loadData, refreshInterval);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [refreshInterval]);

  return {
    summary,
    loading,
    error,
    refetch: fetchSummary,
  };
}
