import axios, { AxiosInstance } from 'axios';
import type {
  ResearchTask,
  ResearchTaskCreate,
  ResearchTaskUpdate,
  ResearchTaskFilter,
  TaskStatus,
} from '../types/researchTask';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

class ResearchTaskApiClient {
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
      (error) => {
        if (error.response?.status === 401) {
          // Handle unauthorized
          localStorage.removeItem('auth_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }
    );
  }

  /**
   * Get all research tasks with optional filters
   */
  async getTasks(filters?: ResearchTaskFilter): Promise<ResearchTask[]> {
    const params = new URLSearchParams();

    if (filters?.technology_id) {
      params.append('technology_id', filters.technology_id.toString());
    }
    if (filters?.repository_id) {
      params.append('repository_id', filters.repository_id.toString());
    }
    if (filters?.status) {
      params.append('status', filters.status);
    }
    if (filters?.assigned_to) {
      params.append('assigned_to', filters.assigned_to);
    }

    const response = await this.client.get<ResearchTask[]>(
      `/api/v1/research-tasks?${params.toString()}`
    );
    return response.data;
  }

  /**
   * Get a single research task by ID
   */
  async getTaskById(taskId: number): Promise<ResearchTask> {
    const response = await this.client.get<ResearchTask>(
      `/api/v1/research-tasks/${taskId}`
    );
    return response.data;
  }

  /**
   * Create a new research task
   */
  async createTask(data: ResearchTaskCreate): Promise<ResearchTask> {
    const response = await this.client.post<ResearchTask>(
      '/api/v1/research-tasks',
      data
    );
    return response.data;
  }

  /**
   * Update an existing research task
   */
  async updateTask(
    taskId: number,
    data: ResearchTaskUpdate
  ): Promise<ResearchTask> {
    const response = await this.client.patch<ResearchTask>(
      `/api/v1/research-tasks/${taskId}`,
      data
    );
    return response.data;
  }

  /**
   * Delete a research task
   */
  async deleteTask(taskId: number): Promise<void> {
    await this.client.delete(`/api/v1/research-tasks/${taskId}`);
  }

  /**
   * Update task status
   */
  async updateTaskStatus(
    taskId: number,
    status: TaskStatus
  ): Promise<ResearchTask> {
    const response = await this.client.patch<ResearchTask>(
      `/api/v1/research-tasks/${taskId}/status`,
      null,
      {
        params: { new_status: status },
      }
    );
    return response.data;
  }

  /**
   * Update task progress
   */
  async updateTaskProgress(
    taskId: number,
    progressPercentage: number
  ): Promise<ResearchTask> {
    const response = await this.client.patch<ResearchTask>(
      `/api/v1/research-tasks/${taskId}/progress`,
      null,
      {
        params: { progress_percentage: progressPercentage },
      }
    );
    return response.data;
  }

  /**
   * Upload a document to a research task
   */
  async uploadDocument(taskId: number, file: File): Promise<ResearchTask> {
    const formData = new FormData();
    formData.append('file', file);

    const response = await this.client.post<ResearchTask>(
      `/api/v1/research-tasks/${taskId}/documents`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      }
    );
    return response.data;
  }

  /**
   * Get documents for a research task
   */
  async getTaskDocuments(taskId: number): Promise<any> {
    const response = await this.client.get(
      `/api/v1/research-tasks/${taskId}/documents`
    );
    return response.data;
  }

  /**
   * Get task statistics
   */
  async getStatistics(
    technologyId?: number,
    repositoryId?: number
  ): Promise<any> {
    const params = new URLSearchParams();

    if (technologyId) {
      params.append('technology_id', technologyId.toString());
    }
    if (repositoryId) {
      params.append('repository_id', repositoryId.toString());
    }

    const response = await this.client.get(
      `/api/v1/research-tasks/statistics/overview?${params.toString()}`
    );
    return response.data;
  }

  /**
   * Get upcoming tasks
   */
  async getUpcomingTasks(days: number = 7): Promise<ResearchTask[]> {
    const response = await this.client.get<ResearchTask[]>(
      `/api/v1/research-tasks/upcoming/list`,
      {
        params: { days },
      }
    );
    return response.data;
  }

  /**
   * Get overdue tasks
   */
  async getOverdueTasks(): Promise<ResearchTask[]> {
    const response = await this.client.get<ResearchTask[]>(
      `/api/v1/research-tasks/overdue/list`
    );
    return response.data;
  }
}

export const researchApi = new ResearchTaskApiClient();
export default researchApi;
