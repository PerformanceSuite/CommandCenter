import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import type { Repository } from '../types/repository';

export function useRepositories() {
  const [repositories, setRepositories] = useState<Repository[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchRepositories = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getRepositories();
      setRepositories(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch repositories'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchRepositories();
  }, [fetchRepositories]);

  const createRepository = useCallback(async (data: Partial<Repository>) => {
    try {
      const newRepo = await api.createRepository(data);
      setRepositories((prev) => [...prev, newRepo]);
      return newRepo;
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to create repository');
    }
  }, []);

  const updateRepository = useCallback(async (id: string, data: Partial<Repository>) => {
    try {
      const updated = await api.updateRepository(id, data);
      setRepositories((prev) => prev.map((repo) => (repo.id === id ? updated : repo)));
      return updated;
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to update repository');
    }
  }, []);

  const deleteRepository = useCallback(async (id: string) => {
    try {
      await api.deleteRepository(id);
      setRepositories((prev) => prev.filter((repo) => repo.id !== id));
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to delete repository');
    }
  }, []);

  const syncRepository = useCallback(async (id: string) => {
    try {
      await api.syncRepository(id);
      await fetchRepositories(); // Refresh list after sync
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to sync repository');
    }
  }, [fetchRepositories]);

  return {
    repositories,
    loading,
    error,
    refresh: fetchRepositories,
    createRepository,
    updateRepository,
    deleteRepository,
    syncRepository,
  };
}
