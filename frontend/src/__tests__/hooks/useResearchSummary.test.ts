import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useResearchSummary } from '../../hooks/useResearchSummary';
import { researchApi } from '../../services/researchApi';

vi.mock('../../services/researchApi', () => ({
  researchApi: {
    getResearchSummary: vi.fn(),
  },
}));

describe('useResearchSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should return loading state initially', () => {
    vi.mocked(researchApi.getResearchSummary).mockReturnValue(
      new Promise(() => {}) // Never resolves
    );

    const { result } = renderHook(() => useResearchSummary());

    expect(result.current.loading).toBe(true);
    expect(result.current.summary).toBeNull();
    expect(result.current.error).toBeNull();
  });

  it('should fetch and return summary data', async () => {
    const mockSummary = {
      total_tasks: 10,
      completed_tasks: 7,
      failed_tasks: 2,
      agents_deployed: 25,
      total_cost_usd: 1.23,
      avg_execution_time_seconds: 5.5,
    };

    vi.mocked(researchApi.getResearchSummary).mockResolvedValue(mockSummary);

    const { result } = renderHook(() => useResearchSummary());

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.summary).toEqual(mockSummary);
    expect(result.current.error).toBeNull();
  });

  it('should handle API errors', async () => {
    const errorMessage = 'Network error';
    vi.mocked(researchApi.getResearchSummary).mockRejectedValue(
      new Error(errorMessage)
    );

    const { result } = renderHook(() => useResearchSummary());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBe(errorMessage);
    expect(result.current.summary).toBeNull();
  });

  it('should provide refetch function', async () => {
    const mockSummary = {
      total_tasks: 5,
      completed_tasks: 3,
      failed_tasks: 1,
      agents_deployed: 10,
      total_cost_usd: 0.5,
      avg_execution_time_seconds: 2.5,
    };

    vi.mocked(researchApi.getResearchSummary).mockResolvedValue(mockSummary);

    const { result } = renderHook(() => useResearchSummary());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(researchApi.getResearchSummary).toHaveBeenCalledTimes(1);

    // Call refetch
    await result.current.refetch();

    expect(researchApi.getResearchSummary).toHaveBeenCalledTimes(2);
  });
});
