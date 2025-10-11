import api from './api';
import { Project, ProjectCreate, ProjectUpdate, ProjectStats } from '../types/project';

export const projectApi = {
  // Get all projects
  async getProjects(): Promise<Project[]> {
    const response = await api.get<Project[]>('/api/v1/projects/');
    return response.data;
  },

  // Get single project
  async getProject(id: number): Promise<Project> {
    const response = await api.get<Project>(`/api/v1/projects/${id}`);
    return response.data;
  },

  // Create project
  async createProject(data: ProjectCreate): Promise<Project> {
    const response = await api.post<Project>('/api/v1/projects/', data);
    return response.data;
  },

  // Update project
  async updateProject(id: number, data: ProjectUpdate): Promise<Project> {
    const response = await api.patch<Project>(`/api/v1/projects/${id}`, data);
    return response.data;
  },

  // Delete project
  async deleteProject(id: number): Promise<void> {
    await api.delete(`/api/v1/projects/${id}`);
  },

  // Get project statistics
  async getProjectStats(id: number): Promise<ProjectStats> {
    const response = await api.get<ProjectStats>(`/api/v1/projects/${id}/stats`);
    return response.data;
  },
};
