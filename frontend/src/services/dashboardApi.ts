import axios, { AxiosInstance } from 'axios';

// Use relative URL so it works with any port configuration
// Nginx will proxy /api requests to the backend container
const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

export interface DashboardStats {
  repositories: {
    total: number;
    recently_synced: Array<{
      id: number;
      full_name: string;
      last_synced_at: string | null;
    }>;
  };
  technologies: {
    total: number;
    by_status: Record<string, number>;
    by_domain: Record<string, number>;
    high_priority: Array<{
      id: number;
      title: string;
      priority: number;
      status: string;
    }>;
  };
  research_tasks: {
    total: number;
    by_status: Record<string, number>;
    overdue_count: number;
    upcoming_count: number;
    overdue_tasks: Array<{
      id: number;
      title: string;
      due_date: string;
      status: string;
    }>;
    upcoming_tasks: Array<{
      id: number;
      title: string;
      due_date: string;
      status: string;
    }>;
  };
  knowledge_base: {
    total_documents?: number;
    total_chunks?: number;
    error?: string;
  };
}

export interface ActivityEvent {
  id: string | number;
  type: 'repository' | 'technology' | 'task' | 'document';
  action: 'created' | 'updated' | 'completed';
  title: string;
  timestamp: string;
  status?: string;
}

export interface RecentActivity {
  recent_repositories: Array<{
    id: number;
    full_name: string;
    updated_at: string;
  }>;
  recent_technologies: Array<{
    id: number;
    title: string;
    status: string;
    updated_at: string;
  }>;
  recent_tasks: Array<{
    id: number;
    title: string;
    status: string;
    updated_at: string;
  }>;
}

class DashboardApiService {
  private client: AxiosInstance;

  constructor() {
    this.client = axios.create({
      baseURL: BASE_URL,
      headers: {
        'Content-Type': 'application/json',
      },
      timeout: 10000,
    });

    // Request interceptor to add auth token
    this.client.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('auth_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => Promise.reject(error)
    );
  }

  /**
   * Get aggregate dashboard statistics
   */
  async getStats(): Promise<DashboardStats> {
    const response = await this.client.get<DashboardStats>('/api/v1/dashboard/stats');
    return response.data;
  }

  /**
   * Get recent activity across all entities
   */
  async getRecentActivity(limit: number = 10): Promise<ActivityEvent[]> {
    const response = await this.client.get<RecentActivity>('/api/v1/dashboard/recent-activity', {
      params: { limit },
    });

    // Transform the data into a unified activity feed
    const activities: ActivityEvent[] = [];

    // Add repositories
    response.data.recent_repositories.forEach((repo) => {
      activities.push({
        id: repo.id,
        type: 'repository',
        action: 'updated',
        title: repo.full_name,
        timestamp: repo.updated_at,
      });
    });

    // Add technologies
    response.data.recent_technologies.forEach((tech) => {
      activities.push({
        id: tech.id,
        type: 'technology',
        action: 'updated',
        title: tech.title,
        status: tech.status,
        timestamp: tech.updated_at,
      });
    });

    // Add tasks
    response.data.recent_tasks.forEach((task) => {
      activities.push({
        id: task.id,
        type: 'task',
        action: task.status === 'completed' ? 'completed' : 'updated',
        title: task.title,
        status: task.status,
        timestamp: task.updated_at,
      });
    });

    // Sort by timestamp (most recent first)
    activities.sort((a, b) =>
      new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime()
    );

    // Return only the requested limit
    return activities.slice(0, limit);
  }
}

export const dashboardApi = new DashboardApiService();
export default dashboardApi;
