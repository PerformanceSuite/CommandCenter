/* eslint-disable @typescript-eslint/no-explicit-any */
import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';

// Custom render function with providers
export function renderWithRouter(
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) {
  function Wrapper({ children }: { children: React.ReactNode }) {
    return <BrowserRouter>{children}</BrowserRouter>;
  }

  return render(ui, { wrapper: Wrapper, ...options });
}

// Mock data generators
export const mockRepository = (overrides = {}) => ({
  id: 1,
  owner: 'testowner',
  name: 'testrepo',
  full_name: 'testowner/testrepo',
  description: 'Test repository',
  url: 'https://github.com/testowner/testrepo',
  clone_url: 'https://github.com/testowner/testrepo.git',
  default_branch: 'main',
  is_private: false,
  github_id: 12345,
  stars: 100,
  forks: 10,
  language: 'Python',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides,
});

export const mockTechnology = (overrides = {}) => ({
  id: 1,
  title: 'Python',
  vendor: 'PSF',
  domain: 'ai-ml',
  status: 'discovery',
  relevance_score: 80,
  priority: 4,
  description: 'A high-level programming language',
  documentation_url: 'https://python.org',
  repository_url: 'https://github.com/python/cpython',
  tags: 'language,backend',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides,
});

export const mockResearchTask = (overrides = {}) => ({
  id: 1,
  title: 'Research FastAPI',
  description: 'Investigate FastAPI best practices',
  status: 'pending',
  priority: 'high',
  repository_id: 1,
  technology_id: 1,
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  ...overrides,
});

// API mock helper
export const createMockApiResponse = <T,>(data: T, status = 200) => ({
  data,
  status,
  statusText: 'OK',
  headers: {},
  config: {} as any,
});

export * from '@testing-library/react';
