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
    fetchSummary(); // Initial load

    // Refresh at specified interval
    const interval = setInterval(fetchSummary, refreshInterval);

    return () => {
      clearInterval(interval);
    };
  }, [refreshInterval, fetchSummary]);

  return {
    summary,
    loading,
    error,
    refetch: fetchSummary,
  };
}
