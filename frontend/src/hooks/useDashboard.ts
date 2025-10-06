import { useState, useEffect, useCallback } from 'react';
import { dashboardApi, DashboardStats, ActivityEvent } from '../services/dashboardApi';

/**
 * Hook to fetch and manage dashboard data
 */
export function useDashboard(activityLimit: number = 10) {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [activity, setActivity] = useState<ActivityEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchStats = useCallback(async () => {
    try {
      const data = await dashboardApi.getStats();
      setStats(data);
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to fetch dashboard stats');
    }
  }, []);

  const fetchActivity = useCallback(async () => {
    try {
      const data = await dashboardApi.getRecentActivity(activityLimit);
      setActivity(data);
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to fetch recent activity');
    }
  }, [activityLimit]);

  const fetchAll = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      await Promise.all([fetchStats(), fetchActivity()]);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch dashboard data'));
    } finally {
      setLoading(false);
    }
  }, [fetchStats, fetchActivity]);

  useEffect(() => {
    fetchAll();

    // Auto-refresh every 5 minutes
    const interval = setInterval(fetchAll, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, [fetchAll]);

  return {
    stats,
    activity,
    loading,
    error,
    refresh: fetchAll,
    refreshStats: fetchStats,
    refreshActivity: fetchActivity,
  };
}
