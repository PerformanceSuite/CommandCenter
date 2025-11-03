// CommandCenter Hub - API Client

import type {
  Project,
  ProjectCreate,
  ProjectStats,
  FilesystemBrowseResponse,
  OperationResponse,
  TaskResponse,
  TaskStatus,
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

  delete: (id: number, deleteFiles: boolean = false): Promise<void> =>
    fetch(`${API_BASE}/projects/${id}?delete_files=${deleteFiles}`, {
      method: 'DELETE',
    }).then(response => {
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`);
      }
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

  status: (id: number): Promise<any> =>
    fetchJSON(`${API_BASE}/orchestration/${id}/status`),

  health: (id: number): Promise<OperationResponse> =>
    fetchJSON(`${API_BASE}/orchestration/${id}/health`),
};

// Filesystem API
export const filesystemApi = {
  getHome: (): Promise<{ path: string }> =>
    fetchJSON(`${API_BASE}/filesystem/home`),

  browse: (path: string): Promise<FilesystemBrowseResponse> => {
    const params = new URLSearchParams({ path });
    return fetchJSON(`${API_BASE}/filesystem/browse?${params}`);
  },
};

// Task API (Background Operations)
export const tasksApi = {
  // Start project in background
  start: (id: number): Promise<TaskResponse> =>
    fetchJSON(`${API_BASE}/orchestration/${id}/start`, {
      method: 'POST',
    }),

  // Stop project in background
  stop: (id: number): Promise<TaskResponse> =>
    fetchJSON(`${API_BASE}/orchestration/${id}/stop`, {
      method: 'POST',
    }),

  // Restart service in background
  restart: (id: number, serviceName: string): Promise<TaskResponse> =>
    fetchJSON(`${API_BASE}/orchestration/${id}/restart/${serviceName}`, {
      method: 'POST',
    }),

  // Get task status
  getStatus: (taskId: string): Promise<TaskStatus> =>
    fetchJSON(`${API_BASE}/task-status/${taskId}`),
};

// Convenience exports
export const deleteProject = (id: number, deleteFiles: boolean = false) =>
  projectsApi.delete(id, deleteFiles);

// Export combined API
export const api = {
  projects: projectsApi,
  orchestration: orchestrationApi,
  filesystem: filesystemApi,
  tasks: tasksApi,
};

export default api;
