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

  it('initializes with correct default state', () => {
    const { result } = renderHook(() => useKnowledge());

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(result.current.searchResults).toEqual([]);
  });

  it('successfully executes a query', async () => {
    const mockResults = [
      { id: '1', content: 'Test result 1', score: 0.95 },
      { id: '2', content: 'Test result 2', score: 0.87 },
    ];
    vi.mocked(knowledgeApi.query).mockResolvedValue({ results: mockResults });

    const { result } = renderHook(() => useKnowledge());

    await act(async () => {
      await result.current.query({ query: 'test query' });
    });

    await waitFor(() => {
      expect(result.current.searchResults).toEqual(mockResults);
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBeNull();
    expect(knowledgeApi.query).toHaveBeenCalledWith({ query: 'test query' });
    expect(knowledgeApi.query).toHaveBeenCalledTimes(1);
  });

  it('sets loading state during query execution', async () => {
    vi.mocked(knowledgeApi.query).mockImplementation(
      () => new Promise((resolve) => setTimeout(() => resolve({ results: [] }), 100))
    );

    const { result } = renderHook(() => useKnowledge());

    act(() => {
      result.current.query({ query: 'test query' });
    });

    // Should be loading immediately after query starts
    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
  });

  it('successfully uploads a document', async () => {
    const mockDocument = { id: 'doc-123', name: 'test.pdf' };
    vi.mocked(knowledgeApi.uploadDocument).mockResolvedValue(mockDocument);

    const { result } = renderHook(() => useKnowledge());

    const file = new File(['test content'], 'test.pdf', { type: 'application/pdf' });

    await act(async () => {
      await result.current.uploadDocument(file, 'technical', 'docs');
    });

    expect(knowledgeApi.uploadDocument).toHaveBeenCalledWith(file, 'technical', 'docs');
    expect(result.current.error).toBeNull();
  });

  it('successfully fetches statistics', async () => {
    const mockStats = {
      totalDocuments: 42,
      totalCollections: 5,
      storageUsed: 1024000,
    };
    vi.mocked(knowledgeApi.getStatistics).mockResolvedValue(mockStats);

    const { result } = renderHook(() => useKnowledge());

    let stats;
    await act(async () => {
      stats = await result.current.getStatistics();
    });

    expect(stats).toEqual(mockStats);
    expect(knowledgeApi.getStatistics).toHaveBeenCalledTimes(1);
    expect(result.current.error).toBeNull();
  });

  it('clears error state on successful query after error', async () => {
    const { result } = renderHook(() => useKnowledge());

    // First query fails
    vi.mocked(knowledgeApi.query).mockRejectedValueOnce(new Error('Network error'));

    await act(async () => {
      try {
        await result.current.query({ query: 'test' });
      } catch (err) {
        // Expected error
      }
    });

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });

    // Second query succeeds
    vi.mocked(knowledgeApi.query).mockResolvedValueOnce({ results: [] });

    await act(async () => {
      await result.current.query({ query: 'test' });
    });

    await waitFor(() => {
      expect(result.current.error).toBeNull();
    });
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
