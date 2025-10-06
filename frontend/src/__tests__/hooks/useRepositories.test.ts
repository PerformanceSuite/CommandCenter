import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useRepositories } from '../../hooks/useRepositories';
import { api } from '../../services/api';
import { mockRepository } from '../../tests/utils';

// Mock the API
vi.mock('../../services/api');

describe('useRepositories', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches repositories on mount', async () => {
    const repos = [mockRepository(), mockRepository({ id: 2 })];
    vi.mocked(api.getRepositories).mockResolvedValue(repos);

    const { result } = renderHook(() => useRepositories());

    // Initially loading
    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.repositories).toEqual(repos);
    expect(result.current.error).toBeNull();
  });

  it('handles fetch error', async () => {
    const error = new Error('Failed to fetch');
    vi.mocked(api.getRepositories).mockRejectedValue(error);

    const { result } = renderHook(() => useRepositories());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.error).toBeTruthy();
    expect(result.current.repositories).toEqual([]);
  });

  it('creates repository', async () => {
    const repos = [mockRepository()];
    const newRepo = mockRepository({ id: 2, name: 'new-repo' });

    vi.mocked(api.getRepositories).mockResolvedValue(repos);
    vi.mocked(api.createRepository).mockResolvedValue(newRepo);

    const { result } = renderHook(() => useRepositories());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const created = await result.current.createRepository({
      owner: 'test',
      name: 'new-repo',
    });

    expect(created).toEqual(newRepo);
    expect(result.current.repositories).toContain(newRepo);
  });

  it('updates repository', async () => {
    const repo = mockRepository();
    const updatedRepo = { ...repo, description: 'Updated' };

    vi.mocked(api.getRepositories).mockResolvedValue([repo]);
    vi.mocked(api.updateRepository).mockResolvedValue(updatedRepo);

    const { result } = renderHook(() => useRepositories());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const updated = await result.current.updateRepository('1', {
      description: 'Updated',
    });

    expect(updated).toEqual(updatedRepo);
    expect(result.current.repositories[0].description).toBe('Updated');
  });

  it('deletes repository', async () => {
    const repos = [mockRepository({ id: 1 }), mockRepository({ id: 2 })];

    vi.mocked(api.getRepositories).mockResolvedValue(repos);
    vi.mocked(api.deleteRepository).mockResolvedValue();

    const { result } = renderHook(() => useRepositories());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await result.current.deleteRepository('1');

    expect(result.current.repositories).toHaveLength(1);
    expect(result.current.repositories[0].id).toBe(2);
  });

  it('syncs repository', async () => {
    const repo = mockRepository();
    const syncedRepo = { ...repo, stars: 200 };

    vi.mocked(api.getRepositories)
      .mockResolvedValueOnce([repo])
      .mockResolvedValueOnce([syncedRepo]);
    vi.mocked(api.syncRepository).mockResolvedValue();

    const { result } = renderHook(() => useRepositories());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await result.current.syncRepository('1');

    await waitFor(() => {
      expect(result.current.repositories[0].stars).toBe(200);
    });
  });

  it('refreshes repositories', async () => {
    const initialRepos = [mockRepository()];
    const refreshedRepos = [mockRepository(), mockRepository({ id: 2 })];

    vi.mocked(api.getRepositories)
      .mockResolvedValueOnce(initialRepos)
      .mockResolvedValueOnce(refreshedRepos);

    const { result } = renderHook(() => useRepositories());

    await waitFor(() => {
      expect(result.current.repositories).toHaveLength(1);
    });

    await result.current.refresh();

    await waitFor(() => {
      expect(result.current.repositories).toHaveLength(2);
    });
  });
});
