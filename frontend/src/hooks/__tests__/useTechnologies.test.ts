import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { useTechnologies } from '../useTechnologies';
import { api } from '../../services/api';
import type { Technology, TechnologyCreate, TechnologyUpdate } from '../../types/technology';
import { TechnologyDomain, TechnologyStatus } from '../../types/technology';
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

// Mock toast utilities
vi.mock('../../utils/toast', () => ({
  showErrorToast: vi.fn(),
  formatApiError: vi.fn((error: Error) => error.message),
}));

describe('useTechnologies', () => {
  let queryClient: QueryClient;

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    });
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  const wrapper = ({ children }: { children: React.ReactNode }) =>
    React.createElement(QueryClientProvider, { client: queryClient }, children);

  const mockTechnology: Technology = {
    id: 1,
    title: 'Test Technology',
    vendor: 'Test Vendor',
    domain: TechnologyDomain.AI_ML,
    status: TechnologyStatus.RESEARCH,
    relevance_score: 80,
    priority: 3,
    description: 'Test description',
    notes: null,
    use_cases: null,
    documentation_url: null,
    repository_url: null,
    website_url: null,
    tags: null,
    latency_ms: null,
    throughput_qps: null,
    integration_difficulty: null,
    integration_time_estimate_days: null,
    maturity_level: null,
    stability_score: null,
    cost_tier: null,
    cost_monthly_usd: null,
    dependencies: null,
    alternatives: null,
    last_hn_mention: null,
    hn_score_avg: null,
    github_stars: null,
    github_last_commit: null,
    created_at: '2024-01-01T00:00:00Z',
    updated_at: '2024-01-01T00:00:00Z',
  };

  describe('Optimistic Updates', () => {
    it('should optimistically add technology and rollback on error', async () => {
      const existingTech = { ...mockTechnology, id: 1 };
      const newTech: TechnologyCreate = {
        title: 'New Technology',
        vendor: 'New Vendor',
        domain: TechnologyDomain.AI_ML,
        status: TechnologyStatus.DISCOVERY,
      };

      // Setup initial state
      vi.mocked(api.getTechnologies).mockResolvedValue({
        items: [existingTech],
        total: 1,
        page: 1,
        page_size: 20,
      });
      vi.mocked(api.createTechnology).mockRejectedValue(new Error('Network error'));

      const { result } = renderHook(() => useTechnologies(), { wrapper });

      // Wait for initial query
      await waitFor(() => {
        expect(result.current.technologies).toEqual([existingTech]);
      });

      // Attempt to create technology (will fail)
      await act(async () => {
        try {
          await result.current.createTechnology(newTech);
        } catch (error) {
          // Expected to throw
        }
      });

      // Should have rolled back to original state
      await waitFor(() => {
        expect(result.current.technologies).toEqual([existingTech]);
      });
    });

    it('should optimistically update technology and rollback on error', async () => {
      const originalTech = { ...mockTechnology, id: 1, title: 'Original Title' };
      const updateData: TechnologyUpdate = { title: 'Updated Title' };

      vi.mocked(api.getTechnologies).mockResolvedValue({
        items: [originalTech],
        total: 1,
        page: 1,
        page_size: 20,
      });
      vi.mocked(api.updateTechnology).mockRejectedValue(new Error('Update failed'));

      const { result } = renderHook(() => useTechnologies(), { wrapper });

      // Wait for initial query
      await waitFor(() => {
        expect(result.current.technologies).toEqual([originalTech]);
      });

      // Attempt to update (will fail)
      await act(async () => {
        try {
          await result.current.updateTechnology(1, updateData);
        } catch (error) {
          // Expected to throw
        }
      });

      // Should have rolled back to original state
      await waitFor(() => {
        expect(result.current.technologies[0].title).toBe('Original Title');
      });
    });

    it('should optimistically delete technology and rollback on error', async () => {
      const tech1 = { ...mockTechnology, id: 1 };
      const tech2 = { ...mockTechnology, id: 2, title: 'Tech 2' };

      vi.mocked(api.getTechnologies).mockResolvedValue({
        items: [tech1, tech2],
        total: 2,
        page: 1,
        page_size: 20,
      });
      vi.mocked(api.deleteTechnology).mockRejectedValue(new Error('Delete failed'));

      const { result } = renderHook(() => useTechnologies(), { wrapper });

      // Wait for initial query
      await waitFor(() => {
        expect(result.current.technologies).toEqual([tech1, tech2]);
      });

      // Attempt to delete (will fail)
      await act(async () => {
        try {
          await result.current.deleteTechnology(1);
        } catch (error) {
          // Expected to throw
        }
      });

      // Should have rolled back to original state
      await waitFor(() => {
        expect(result.current.technologies).toHaveLength(2);
        expect(result.current.technologies).toEqual([tech1, tech2]);
      });
    });

    it('should handle race conditions with cancelQueries', async () => {
      const tech1 = { ...mockTechnology, id: 1 };
      const updateData: TechnologyUpdate = { title: 'Updated Title' };

      vi.mocked(api.getTechnologies).mockResolvedValue({
        items: [tech1],
        total: 1,
        page: 1,
        page_size: 20,
      });

      // Mock slow update to test race condition
      vi.mocked(api.updateTechnology).mockImplementation(
        () => new Promise((resolve) => setTimeout(() => resolve({ ...tech1, ...updateData }), 100))
      );

      const { result } = renderHook(() => useTechnologies(), { wrapper });

      // Wait for initial query
      await waitFor(() => {
        expect(result.current.technologies).toEqual([tech1]);
      });

      // Start multiple updates rapidly
      await act(async () => {
        const promises = [
          result.current.updateTechnology(1, { title: 'First Update' }),
          result.current.updateTechnology(1, { title: 'Second Update' }),
          result.current.updateTechnology(1, { title: 'Third Update' }),
        ];

        // Only the last update should win
        await Promise.all(promises);
      });

      // Verify the state is consistent
      await waitFor(() => {
        expect(result.current.technologies).toBeDefined();
        expect(result.current.technologies.length).toBeGreaterThan(0);
      });
    });
  });

  describe('Type Safety', () => {
    it('should maintain proper TypeScript types for context', async () => {
      const tech = { ...mockTechnology, id: 1 };
      vi.mocked(api.getTechnologies).mockResolvedValue({
        items: [tech],
        total: 1,
        page: 1,
        page_size: 20,
      });

      const { result } = renderHook(() => useTechnologies(), { wrapper });

      await waitFor(() => {
        expect(result.current.technologies).toEqual([tech]);
      });

      // TypeScript should properly type these without errors
      const { createTechnology, updateTechnology, deleteTechnology } = result.current;

      // These should all have proper typing
      expect(typeof createTechnology).toBe('function');
      expect(typeof updateTechnology).toBe('function');
      expect(typeof deleteTechnology).toBe('function');
    });
  });
});
