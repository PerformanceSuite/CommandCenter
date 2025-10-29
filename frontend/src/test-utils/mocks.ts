import { vi } from 'vitest';
import type { Repository } from '../types/repository';
import type { Technology } from '../types/technology';
import type { ResearchEntry } from '../types/research';

// Mock data generators
export const mockRepository = (overrides: Partial<Repository> = {}): Repository => ({
  id: '1',
  owner: 'testowner',
  name: 'testrepo',
  full_name: 'testowner/testrepo',
  description: 'Test repository',
  url: 'https://github.com/testowner/testrepo',
  clone_url: 'https://github.com/testowner/testrepo.git',
  default_branch: 'main',
  is_private: false,
  is_active: true,
  github_id: 12345,
  stars: 100,
  forks: 10,
  language: 'Python',
  created_at: '2024-01-01T00:00:00Z',
  updated_at: '2024-01-01T00:00:00Z',
  last_synced_at: '2024-01-01T00:00:00Z',
  last_commit_sha: 'abc123',
  ...overrides,
});

export const mockTechnology = (overrides: Partial<Technology> = {}): Technology => ({
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

export const mockResearchTask = (overrides: Partial<ResearchEntry> = {}): ResearchEntry => ({
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

// Mock API responses
export const createMockApiResponse = <T,>(data: T, status = 200) => ({
  data,
  status,
  statusText: 'OK',
  headers: {},
  config: {} as Record<string, unknown>,
});

// Mock axios instance
export const createMockAxios = () => ({
  get: vi.fn(),
  post: vi.fn(),
  put: vi.fn(),
  patch: vi.fn(),
  delete: vi.fn(),
  request: vi.fn(),
  interceptors: {
    request: {
      use: vi.fn(),
      eject: vi.fn(),
    },
    response: {
      use: vi.fn(),
      eject: vi.fn(),
    },
  },
});

// Mock localStorage
export const mockLocalStorage = () => {
  const store: Record<string, string> = {};

  return {
    getItem: vi.fn((key: string) => store[key] || null),
    setItem: vi.fn((key: string, value: string) => {
      store[key] = value;
    }),
    removeItem: vi.fn((key: string) => {
      delete store[key];
    }),
    clear: vi.fn(() => {
      Object.keys(store).forEach(key => delete store[key]);
    }),
    get length() {
      return Object.keys(store).length;
    },
    key: vi.fn((index: number) => Object.keys(store)[index] || null),
  };
};

// Mock window.confirm
export const mockConfirm = (returnValue: boolean) => {
  window.confirm = vi.fn(() => returnValue);
};

// Mock window.alert
export const mockAlert = () => {
  window.alert = vi.fn();
};

// Auth token helpers
export const setMockAuthToken = (token = 'mock-jwt-token') => {
  localStorage.setItem('auth_token', token);
};

export const clearMockAuthToken = () => {
  localStorage.removeItem('auth_token');
};

// Project ID helpers
export const setMockProjectId = (projectId = '1') => {
  localStorage.setItem('selected_project_id', projectId);
};

export const clearMockProjectId = () => {
  localStorage.removeItem('selected_project_id');
};

// Dashboard stats mock
export const mockDashboardStats = () => ({
  technologies: {
    total: 10,
    by_status: {
      discovery: 3,
      evaluation: 4,
      adoption: 2,
      deprecated: 1,
    },
  },
  research_tasks: {
    total: 15,
    by_status: {
      pending: 5,
      in_progress: 6,
      completed: 4,
    },
    overdue_count: 2,
  },
  repositories: {
    total: 5,
  },
  knowledge_base: {
    total_documents: 25,
  },
});

// Activity feed mock
export const mockActivity = () => [
  {
    id: 1,
    type: 'technology_created',
    title: 'New technology added',
    description: 'Python added to AI/ML domain',
    timestamp: '2024-01-01T10:00:00Z',
  },
  {
    id: 2,
    type: 'research_task_completed',
    title: 'Research task completed',
    description: 'FastAPI investigation finished',
    timestamp: '2024-01-01T09:00:00Z',
  },
];
