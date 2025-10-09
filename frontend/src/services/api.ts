import axios, { AxiosError, AxiosInstance, AxiosResponse } from 'axios';
import type { Repository } from '../types/repository';
import type { Technology, TechnologyCreate, TechnologyUpdate } from '../types/technology';
import type { ResearchEntry } from '../types/research';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface KnowledgeQueryResponse {
  answer: string;
  sources: Array<{
    content: string;
    title?: string;
    score?: number;
  }>;
}

interface DashboardStats {
  total_repositories: number;
  total_technologies: number;
  total_research_entries: number;
  [key: string]: number | string;
}

interface ActivityItem {
  id: number;
  type: string;
  title: string;
  timestamp: string;
  [key: string]: unknown;
}

class ApiClient {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000,
    });

    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // Add auth token if available
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      (error: AxiosError) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  // Repositories
  async getRepositories(): Promise<Repository[]> {
    const response: AxiosResponse<Repository[]> = await this.client.get('/api/v1/repositories');
    return response.data;
  }

  async getRepository(id: string): Promise<Repository> {
    const response: AxiosResponse<Repository> = await this.client.get(`/api/v1/repositories/${id}`);
    return response.data;
  }

  async createRepository(data: Partial<Repository>): Promise<Repository> {
    const response: AxiosResponse<Repository> = await this.client.post('/api/v1/repositories', data);
    return response.data;
  }

  async updateRepository(id: string, data: Partial<Repository>): Promise<Repository> {
    const response: AxiosResponse<Repository> = await this.client.put(`/api/v1/repositories/${id}`, data);
    return response.data;
  }

  async deleteRepository(id: string): Promise<void> {
    await this.client.delete(`/api/v1/repositories/${id}`);
  }

  async syncRepository(id: string): Promise<void> {
    await this.client.post(`/api/v1/repositories/${id}/sync`);
  }

  // Technologies
  async getTechnologies(): Promise<Technology[]> {
    const response = await this.client.get<{ total: number; items: Technology[]; page: number; page_size: number }>('/api/v1/technologies/');
    return response.data.items; // Extract items array from paginated response
  }

  async getTechnology(id: number): Promise<Technology> {
    const response: AxiosResponse<Technology> = await this.client.get(`/api/v1/technologies/${id}`);
    return response.data;
  }

  async createTechnology(data: TechnologyCreate): Promise<Technology> {
    const response: AxiosResponse<Technology> = await this.client.post('/api/v1/technologies/', data);
    return response.data;
  }

  async updateTechnology(id: number, data: TechnologyUpdate): Promise<Technology> {
    const response: AxiosResponse<Technology> = await this.client.put(`/api/v1/technologies/${id}`, data);
    return response.data;
  }

  async deleteTechnology(id: number): Promise<void> {
    await this.client.delete(`/api/v1/technologies/${id}`);
  }

  // Research
  async getResearchEntries(): Promise<ResearchEntry[]> {
    const response: AxiosResponse<ResearchEntry[]> = await this.client.get('/api/v1/research');
    return response.data;
  }

  async getResearchEntry(id: string): Promise<ResearchEntry> {
    const response: AxiosResponse<ResearchEntry> = await this.client.get(`/api/v1/research/${id}`);
    return response.data;
  }

  async createResearchEntry(data: Partial<ResearchEntry>): Promise<ResearchEntry> {
    const response: AxiosResponse<ResearchEntry> = await this.client.post('/api/v1/research', data);
    return response.data;
  }

  async updateResearchEntry(id: string, data: Partial<ResearchEntry>): Promise<ResearchEntry> {
    const response: AxiosResponse<ResearchEntry> = await this.client.put(`/api/v1/research/${id}`, data);
    return response.data;
  }

  async deleteResearchEntry(id: string): Promise<void> {
    await this.client.delete(`/api/v1/research/${id}`);
  }

  // Knowledge Base
  async queryKnowledge(query: string): Promise<KnowledgeQueryResponse> {
    const response = await this.client.post<KnowledgeQueryResponse>('/api/v1/knowledge/query', { query });
    return response.data;
  }

  // Dashboard
  async getDashboardStats(): Promise<DashboardStats> {
    const response = await this.client.get<DashboardStats>('/api/v1/dashboard/stats');
    return response.data;
  }

  async getDashboardActivity(limit: number = 10): Promise<ActivityItem[]> {
    const response = await this.client.get<ActivityItem[]>('/api/v1/dashboard/recent-activity', {
      params: { limit },
    });
    return response.data;
  }
}

export const api = new ApiClient();
export default api;
