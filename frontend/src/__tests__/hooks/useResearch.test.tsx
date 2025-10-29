import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useResearchTasks } from '../../hooks/useResearchTasks';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { researchApi } from '../../services/researchApi';
import type { ResearchTask } from '../../types/researchTask';
import React, { ReactNode } from 'react';

// Mock the research API
vi.mock('../../services/researchApi', () => ({
  researchApi: {
    getTasks: vi.fn(),
    getTaskById: vi.fn(),
    createTask: vi.fn(),
    updateTask: vi.fn(),
    deleteTask: vi.fn(),
  },
}));

// Helper to create wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('useResearchTasks', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('handles empty results gracefully', async () => {
    // Mock API to return empty array
    vi.mocked(researchApi.getTasks).mockResolvedValue([]);

    const { result } = renderHook(() => useResearchTasks(), {
      wrapper: createWrapper(),
    });

    // Initially loading
    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should have empty array
    expect(result.current.data).toEqual([]);
    expect(result.current.error).toBeNull();
    expect(researchApi.getTasks).toHaveBeenCalledTimes(1);
  });

  it('handles loading states correctly', async () => {
    // Mock API with delay to test loading state
    const mockTask: ResearchTask = {
      id: 1,
      title: 'Test Task',
      description: 'Test Description',
      status: 'pending' as const,
      priority: 'medium' as const,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    vi.mocked(researchApi.getTasks).mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(() => resolve([mockTask]), 100);
        })
    );

    const { result } = renderHook(() => useResearchTasks(), {
      wrapper: createWrapper(),
    });

    // Should start with loading true
    expect(result.current.isLoading).toBe(true);
    expect(result.current.data).toBeUndefined();

    // Wait for data to load
    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    // Should have data
    expect(result.current.data).toHaveLength(1);
    expect(result.current.data?.[0]).toEqual(mockTask);
    expect(result.current.error).toBeNull();
  });
});
