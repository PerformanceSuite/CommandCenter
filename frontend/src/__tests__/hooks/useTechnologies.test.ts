import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTechnologies } from '../../hooks/useTechnologies';
import { api } from '../../services/api';
import { mockTechnology } from '../../test-utils/mocks';
import React from 'react';

// Mock the API
vi.mock('../../services/api', () => ({
  api: {
    getTechnologies: vi.fn(),
    createTechnology: vi.fn(),
    updateTechnology: vi.fn(),
    deleteTechnology: vi.fn(),
  },
}));

const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);
};

describe('useTechnologies', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('fetches technologies on mount', async () => {
    const mockTechs = [
      mockTechnology({ id: 1, title: 'Python' }),
      mockTechnology({ id: 2, title: 'FastAPI' }),
    ];

    vi.mocked(api.getTechnologies).mockResolvedValue({
      items: mockTechs,
      total: 2,
      page: 1,
      page_size: 20,
    });

    const { result } = renderHook(() => useTechnologies(), {
      wrapper: createWrapper(),
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.technologies).toEqual(mockTechs);
    expect(result.current.total).toBe(2);
    expect(result.current.page).toBe(1);
    expect(api.getTechnologies).toHaveBeenCalledTimes(1);
  });

  it('fetches technologies with filters', async () => {
    const mockTechs = [mockTechnology({ id: 1, title: 'Python', domain: 'ai-ml' })];

    vi.mocked(api.getTechnologies).mockResolvedValue({
      items: mockTechs,
      total: 1,
      page: 1,
      page_size: 20,
    });

    const filters = { domain: 'ai-ml', status: 'discovery' };

    const { result } = renderHook(() => useTechnologies(filters), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.technologies).toEqual(mockTechs);
    expect(api.getTechnologies).toHaveBeenCalledWith(filters);
  });

  it('creates a new technology', async () => {
    const mockTechs = [mockTechnology({ id: 1, title: 'Python' })];
    const newTech = mockTechnology({ id: 2, title: 'FastAPI' });

    vi.mocked(api.getTechnologies).mockResolvedValue({
      items: mockTechs,
      total: 1,
      page: 1,
      page_size: 20,
    });
    vi.mocked(api.createTechnology).mockResolvedValue(newTech);

    const { result } = renderHook(() => useTechnologies(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const createData = {
      title: 'FastAPI',
      vendor: 'Tiangolo',
      domain: 'backend' as const,
      status: 'discovery' as const,
    };

    await result.current.createTechnology(createData);

    expect(api.createTechnology).toHaveBeenCalledWith(createData);
  });

  it('updates a technology', async () => {
    const tech = mockTechnology({ id: 1, title: 'Python' });
    const updatedTech = mockTechnology({ id: 1, title: 'Python 3.12' });

    vi.mocked(api.getTechnologies).mockResolvedValue({
      items: [tech],
      total: 1,
      page: 1,
      page_size: 20,
    });
    vi.mocked(api.updateTechnology).mockResolvedValue(updatedTech);

    const { result } = renderHook(() => useTechnologies(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await result.current.updateTechnology(1, { title: 'Python 3.12' });

    expect(api.updateTechnology).toHaveBeenCalledWith(1, { title: 'Python 3.12' });
  });

  it('deletes a technology', async () => {
    const tech1 = mockTechnology({ id: 1, title: 'Python' });
    const tech2 = mockTechnology({ id: 2, title: 'FastAPI' });

    vi.mocked(api.getTechnologies).mockResolvedValue({
      items: [tech1, tech2],
      total: 2,
      page: 1,
      page_size: 20,
    });
    vi.mocked(api.deleteTechnology).mockResolvedValue(undefined);

    const { result } = renderHook(() => useTechnologies(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await result.current.deleteTechnology(1);

    expect(api.deleteTechnology).toHaveBeenCalledWith(1);
  });

  it('calculates total pages correctly', async () => {
    const mockTechs = [
      mockTechnology({ id: 1, title: 'Tech 1' }),
      mockTechnology({ id: 2, title: 'Tech 2' }),
      mockTechnology({ id: 3, title: 'Tech 3' }),
    ];

    vi.mocked(api.getTechnologies).mockResolvedValue({
      items: mockTechs,
      total: 50,
      page: 1,
      page_size: 20,
    });

    const { result } = renderHook(() => useTechnologies(), {
      wrapper: createWrapper(),
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.totalPages).toBe(3); // ceil(50 / 20) = 3
  });
});
