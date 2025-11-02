import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useRepositories } from '../../hooks/useRepositories';
import { api } from '../../services/api';
import { mockRepository } from '../../test-utils/mocks';

// Mock the API
vi.mock('../../services/api', () => ({
  api: {
    getRepositories: vi.fn(),
    createRepository: vi.fn(),
    updateRepository: vi.fn(),
    deleteRepository: vi.fn(),
    syncRepository: vi.fn(),
  },
}));

describe('useRepositories', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches repositories on mount', async () => {
    const mockRepos = [
      mockRepository({ id: '1', name: 'repo1' }),
      mockRepository({ id: '2', name: 'repo2' }),
    ];

    vi.mocked(api.getRepositories).mockResolvedValue(mockRepos);

    const { result } = renderHook(() => useRepositories());

    expect(result.current.loading).toBe(true);
    expect(result.current.repositories).toEqual([]);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.repositories).toEqual(mockRepos);
    expect(result.current.error).toBeNull();
    expect(api.getRepositories).toHaveBeenCalledTimes(1);
  });

  it('handles fetch error', async () => {
    const error = new Error('Failed to fetch');
    vi.mocked(api.getRepositories).mockRejectedValue(error);

    const { result } = renderHook(() => useRepositories());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.repositories).toEqual([]);
    expect(result.current.error).toEqual(error);
  });

  it('creates a new repository', async () => {
    const existingRepos = [mockRepository({ id: '1', name: 'repo1' })];
    const newRepo = mockRepository({ id: '2', name: 'new-repo' });

    vi.mocked(api.getRepositories).mockResolvedValue(existingRepos);
    vi.mocked(api.createRepository).mockResolvedValue(newRepo);

    const { result } = renderHook(() => useRepositories());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const createdRepo = await result.current.createRepository({ name: 'new-repo' });

    expect(createdRepo).toEqual(newRepo);
    await waitFor(() => {
      expect(result.current.repositories).toHaveLength(2);
      expect(result.current.repositories[1]).toEqual(newRepo);
    });
    expect(api.createRepository).toHaveBeenCalledWith({ name: 'new-repo' });
  });

  it('updates an existing repository', async () => {
    const repo1 = mockRepository({ id: '1', name: 'repo1' });
    const repo2 = mockRepository({ id: '2', name: 'repo2' });
    const updatedRepo1 = mockRepository({ id: '1', name: 'updated-repo1' });

    vi.mocked(api.getRepositories).mockResolvedValue([repo1, repo2]);
    vi.mocked(api.updateRepository).mockResolvedValue(updatedRepo1);

    const { result } = renderHook(() => useRepositories());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const updated = await result.current.updateRepository('1', { name: 'updated-repo1' });

    expect(updated).toEqual(updatedRepo1);
    await waitFor(() => {
      expect(result.current.repositories[0]).toEqual(updatedRepo1);
      expect(result.current.repositories[1]).toEqual(repo2);
    });
    expect(api.updateRepository).toHaveBeenCalledWith('1', { name: 'updated-repo1' });
  });

  it('deletes a repository', async () => {
    const repo1 = mockRepository({ id: '1', name: 'repo1' });
    const repo2 = mockRepository({ id: '2', name: 'repo2' });

    vi.mocked(api.getRepositories).mockResolvedValue([repo1, repo2]);
    vi.mocked(api.deleteRepository).mockResolvedValue(undefined);

    const { result } = renderHook(() => useRepositories());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await result.current.deleteRepository('1');

    await waitFor(() => {
      expect(result.current.repositories).toHaveLength(1);
      expect(result.current.repositories[0]).toEqual(repo2);
    });
    expect(api.deleteRepository).toHaveBeenCalledWith('1');
  });

  it('syncs a repository and refreshes list', async () => {
    const mockRepos = [mockRepository({ id: '1', name: 'repo1' })];

    vi.mocked(api.getRepositories).mockResolvedValue(mockRepos);
    vi.mocked(api.syncRepository).mockResolvedValue(undefined);

    const { result } = renderHook(() => useRepositories());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await result.current.syncRepository('1');

    expect(api.syncRepository).toHaveBeenCalledWith('1');
    expect(api.getRepositories).toHaveBeenCalledTimes(2); // Initial + after sync
  });

  it('refreshes repository list', async () => {
    const mockRepos = [mockRepository({ id: '1', name: 'repo1' })];

    vi.mocked(api.getRepositories).mockResolvedValue(mockRepos);

    const { result } = renderHook(() => useRepositories());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await result.current.refresh();

    expect(api.getRepositories).toHaveBeenCalledTimes(2); // Initial + refresh
  });
});
