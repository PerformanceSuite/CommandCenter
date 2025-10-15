// CommandCenter Hub - TypeScript Types

export interface Project {
  id: number;
  name: string;
  slug: string;
  path: string;
  cc_path: string;

  // Ports
  backend_port: number;
  frontend_port: number;
  postgres_port: number;
  redis_port: number;

  // Status
  status: ProjectStatus;
  health: HealthStatus;

  // Metadata
  compose_project_name: string;
  last_started?: string;
  created_at: string;
  updated_at: string;
}

export type ProjectStatus = 'running' | 'stopped' | 'starting' | 'error';
export type HealthStatus = 'healthy' | 'unhealthy' | 'unknown';

export interface ProjectCreate {
  name: string;
  path: string;
}

export interface ProjectStats {
  total_projects: number;
  running: number;
  stopped: number;
  errors: number;
}

export interface Directory {
  name: string;
  path: string;
}

export interface FilesystemBrowseResponse {
  currentPath: string;
  parent: string | null;
  directories: Directory[];
}

export interface ApiError {
  detail: string;
}

export interface OperationResponse {
  message: string;
  project?: Project;
}
