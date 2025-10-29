import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useKnowledge } from '../../hooks/useKnowledge';
import { knowledgeApi } from '../../services/knowledgeApi';

// Mock the knowledge API
vi.mock('../../services/knowledgeApi', () => ({
  knowledgeApi: {
    query: vi.fn(),
    uploadDocument: vi.fn(),
    deleteDocument: vi.fn(),
    getStatistics: vi.fn(),
    getCollections: vi.fn(),
    getCategories: vi.fn(),
  },
}));

describe('useKnowledge', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('handles query errors gracefully', async () => {
    const networkError = new Error('Network error');
    vi.mocked(knowledgeApi.query).mockRejectedValue(networkError);

    const { result } = renderHook(() => useKnowledge());

    // Should start with no error
    expect(result.current.error).toBeNull();
    expect(result.current.searchResults).toEqual([]);

    // Execute query
    let thrownError: Error | null = null;
    await act(async () => {
      try {
        await result.current.query({ query: 'test query' });
      } catch (err) {
        thrownError = err as Error;
      }
    });

    // Should have error state
    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });

    expect(result.current.error?.message).toContain('Network error');
    expect(result.current.searchResults).toEqual([]);
    expect(result.current.loading).toBe(false);
    expect(thrownError?.message).toContain('Network error');
  });
});
