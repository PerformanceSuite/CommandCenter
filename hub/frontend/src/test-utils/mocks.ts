/**
 * Mock data and helpers for Hub frontend tests
 */

import type { Project, ProjectStats } from '../types';

export const mockProjects: Project[] = [
  {
    id: 1,
    name: 'TestProject1',
    slug: 'test-project-1',
    path: '/tmp/test-project-1',
    backend_port: 8010,
    frontend_port: 3010,
    postgres_port: 5442,
    redis_port: 6389,
    status: 'stopped',
    health: 'unknown',
    is_configured: true,
    repo_count: 5,
    tech_count: 3,
    task_count: 10,
    last_started: null,
    last_stopped: null,
    created_at: '2025-10-28T00:00:00Z',
    updated_at: null,
  },
  {
    id: 2,
    name: 'TestProject2',
    slug: 'test-project-2',
    path: '/tmp/test-project-2',
    backend_port: 8020,
    frontend_port: 3020,
    postgres_port: 5452,
    redis_port: 6399,
    status: 'running',
    health: 'healthy',
    is_configured: true,
    repo_count: 8,
    tech_count: 5,
    task_count: 15,
    last_started: '2025-10-28T10:00:00Z',
    last_stopped: null,
    created_at: '2025-10-27T00:00:00Z',
    updated_at: '2025-10-28T10:00:00Z',
  },
  {
    id: 3,
    name: 'ErrorProject',
    slug: 'error-project',
    path: '/tmp/error-project',
    backend_port: 8030,
    frontend_port: 3030,
    postgres_port: 5462,
    redis_port: 6409,
    status: 'error',
    health: 'unhealthy',
    is_configured: true,
    repo_count: 0,
    tech_count: 0,
    task_count: 0,
    last_started: null,
    last_stopped: null,
    created_at: '2025-10-26T00:00:00Z',
    updated_at: null,
  },
];

export const mockStats: ProjectStats = {
  total_projects: 3,
  running: 1,
  stopped: 1,
  errors: 1,
};

export const mockOperationResponse = {
  success: true,
  message: 'Operation completed successfully',
  project_id: 1,
  status: 'running',
};

/**
 * Create a mock fetch response
 */
export function createMockResponse<T>(data: T, ok: boolean = true): Response {
  return {
    ok,
    status: ok ? 200 : 500,
    statusText: ok ? 'OK' : 'Internal Server Error',
    json: async () => data,
  } as Response;
}

/**
 * Create a mock project with custom fields
 */
export function createMockProject(overrides: Partial<Project> = {}): Project {
  return {
    ...mockProjects[0],
    ...overrides,
  };
}
