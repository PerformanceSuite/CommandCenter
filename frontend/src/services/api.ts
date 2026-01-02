import axios, { AxiosError, AxiosInstance, AxiosRequestConfig, AxiosResponse } from 'axios';
import type { Repository } from '../types/repository';
import type { Technology, TechnologyCreate, TechnologyUpdate } from '../types/technology';
import type { ResearchEntry } from '../types/research';
import type { KnowledgeQueryResponse } from '../types/knowledge';
import type { DashboardStats, DashboardActivity } from '../types/dashboard';
import type {
  ApprovalResponse,
  ApproveConceptsRequest,
  ApproveRequirementsRequest,
  RejectionResponse,
  ReviewQueueConceptsResponse,
  ReviewQueueRequirementsResponse,
} from '../types/review';

// Use relative URL so it works with any port configuration
// Nginx will proxy /api requests to the backend container
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

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

        // Add project ID header if a project is selected
        const projectId = localStorage.getItem('selected_project_id');
        if (projectId) {
          config.headers['X-Project-ID'] = projectId;
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
  async getTechnologies(params?: {
    page?: number;
    limit?: number;
    domain?: string;
    status?: string;
    search?: string;
  }): Promise<{ total: number; items: Technology[]; page: number; page_size: number }> {
    const queryParams: Record<string, string | number> = {};

    if (params?.page) {
      // Backend uses 'skip' for pagination, convert page to skip
      queryParams.skip = (params.page - 1) * (params.limit || 20);
    }
    if (params?.limit) {
      queryParams.limit = params.limit;
    }
    if (params?.domain) {
      queryParams.domain = params.domain;
    }
    if (params?.status) {
      queryParams.status = params.status;
    }
    if (params?.search) {
      queryParams.search = params.search;
    }

    const response = await this.client.get<{ total: number; items: Technology[]; page: number; page_size: number }>('/api/v1/technologies/', {
      params: queryParams,
    });

    // Validate response structure to prevent runtime errors
    if (!response.data || typeof response.data !== 'object') {
      throw new Error('Invalid API response: response data is missing or not an object');
    }

    const { total, items, page, page_size } = response.data;

    // Validate required fields exist and have correct types
    if (typeof total !== 'number') {
      throw new Error('Invalid API response: total field is missing or not a number');
    }
    if (!Array.isArray(items)) {
      throw new Error('Invalid API response: items field is missing or not an array');
    }
    if (typeof page !== 'number') {
      throw new Error('Invalid API response: page field is missing or not a number');
    }
    if (typeof page_size !== 'number') {
      throw new Error('Invalid API response: page_size field is missing or not a number');
    }

    return response.data;
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

  async getDashboardActivity(limit: number = 10): Promise<DashboardActivity> {
    const response = await this.client.get<DashboardActivity>('/api/v1/dashboard/recent-activity', {
      params: { limit },
    });
    return response.data;
  }

  // Review Queue
  async getConceptsForReview(params?: { limit?: number; statuses?: string }): Promise<ReviewQueueConceptsResponse> {
    const response = await this.client.get<ReviewQueueConceptsResponse>('/api/v1/graph/review-queue/concepts', {
      params,
    });
    return response.data;
  }

  async getRequirementsForReview(params?: { limit?: number; statuses?: string }): Promise<ReviewQueueRequirementsResponse> {
    const response = await this.client.get<ReviewQueueRequirementsResponse>('/api/v1/graph/review-queue/requirements', {
      params,
    });
    return response.data;
  }

  async approveConcepts(request: ApproveConceptsRequest): Promise<ApprovalResponse> {
    const response = await this.client.post<ApprovalResponse>('/api/v1/graph/concepts/approve', request);
    return response.data;
  }

  async approveRequirements(request: ApproveRequirementsRequest): Promise<ApprovalResponse> {
    const response = await this.client.post<ApprovalResponse>('/api/v1/graph/requirements/approve', request);
    return response.data;
  }

  async rejectConcepts(ids: number[]): Promise<RejectionResponse> {
    const response = await this.client.delete<RejectionResponse>('/api/v1/graph/concepts/reject', {
      data: { ids },
    });
    return response.data;
  }

  async rejectRequirements(ids: number[]): Promise<RejectionResponse> {
    const response = await this.client.delete<RejectionResponse>('/api/v1/graph/requirements/reject', {
      data: { ids },
    });
    return response.data;
  }

  // Generic HTTP methods for other APIs
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.get(url, config);
  }

  async post<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.post(url, data, config);
  }

  async put<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.put(url, data, config);
  }

  async patch<T>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<AxiosResponse<T>> {
    return this.client.patch(url, data, config);
  }

  async delete(url: string, config?: AxiosRequestConfig): Promise<AxiosResponse> {
    return this.client.delete(url, config);
  }
}

export const api = new ApiClient();
export default api;
