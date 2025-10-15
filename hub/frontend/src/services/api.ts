// CommandCenter Hub - API Client

import type {
  Project,
  ProjectCreate,
  ProjectStats,
  FilesystemBrowseResponse,
  OperationResponse,
} from '../types';

const API_BASE = '/api';

// Helper function for fetch requests
async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

// Projects API
export const projectsApi = {
  list: (): Promise<Project[]> =>
    fetchJSON(`${API_BASE}/projects/`),

  get: (id: number): Promise<Project> =>
    fetchJSON(`${API_BASE}/projects/${id}`),

  create: (data: ProjectCreate): Promise<Project> =>
    fetchJSON(`${API_BASE}/projects/`, {
      method: 'POST',
      body: JSON.stringify(data),
    }),

  delete: (id: number): Promise<void> =>
    fetchJSON(`${API_BASE}/projects/${id}`, {
      method: 'DELETE',
    }),

  stats: (): Promise<ProjectStats> =>
    fetchJSON(`${API_BASE}/projects/stats`),
};

// Orchestration API
export const orchestrationApi = {
  start: (id: number): Promise<OperationResponse> =>
    fetchJSON(`${API_BASE}/orchestration/${id}/start`, {
      method: 'POST',
    }),

  stop: (id: number): Promise<OperationResponse> =>
    fetchJSON(`${API_BASE}/orchestration/${id}/stop`, {
      method: 'POST',
    }),

  restart: (id: number): Promise<OperationResponse> =>
    fetchJSON(`${API_BASE}/orchestration/${id}/restart`, {
      method: 'POST',
    }),

  health: (id: number): Promise<OperationResponse> =>
    fetchJSON(`${API_BASE}/orchestration/${id}/health`),
};

// Filesystem API
export const filesystemApi = {
  browse: (path: string): Promise<FilesystemBrowseResponse> => {
    const params = new URLSearchParams({ path });
    return fetchJSON(`${API_BASE}/filesystem/browse?${params}`);
  },
};

// Export combined API
export const api = {
  projects: projectsApi,
  orchestration: orchestrationApi,
  filesystem: filesystemApi,
};

export default api;
