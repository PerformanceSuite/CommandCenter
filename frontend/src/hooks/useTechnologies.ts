import { useState, useEffect, useCallback } from 'react';
import { api } from '../services/api';
import type { Technology } from '../types/technology';

export function useTechnologies() {
  const [technologies, setTechnologies] = useState<Technology[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<Error | null>(null);

  const fetchTechnologies = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await api.getTechnologies();
      setTechnologies(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch technologies'));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchTechnologies();
  }, [fetchTechnologies]);

  const createTechnology = useCallback(async (data: Partial<Technology>) => {
    try {
      const newTech = await api.createTechnology(data);
      setTechnologies((prev) => [...prev, newTech]);
      return newTech;
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to create technology');
    }
  }, []);

  const updateTechnology = useCallback(async (id: string, data: Partial<Technology>) => {
    try {
      const updated = await api.updateTechnology(id, data);
      setTechnologies((prev) => prev.map((tech) => (tech.id === id ? updated : tech)));
      return updated;
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to update technology');
    }
  }, []);

  const deleteTechnology = useCallback(async (id: string) => {
    try {
      await api.deleteTechnology(id);
      setTechnologies((prev) => prev.filter((tech) => tech.id !== id));
    } catch (err) {
      throw err instanceof Error ? err : new Error('Failed to delete technology');
    }
  }, []);

  return {
    technologies,
    loading,
    error,
    refresh: fetchTechnologies,
    createTechnology,
    updateTechnology,
    deleteTechnology,
  };
}
