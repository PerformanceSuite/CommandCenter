export interface DashboardStats {
  total_repositories: number;
  total_technologies: number;
  total_research_tasks: number;
  total_knowledge_entries: number;
  technologies_by_domain?: Record<string, number>;
  technologies_by_status?: Record<string, number>;
  research_by_priority?: Record<string, number>;
  recent_activity_count?: number;
}

export interface ActivityItem {
  id: string;
  type: 'repository' | 'technology' | 'research' | 'knowledge';
  action: 'created' | 'updated' | 'deleted' | 'synced';
  title: string;
  description?: string;
  timestamp: string;
  user?: string;
  metadata?: Record<string, unknown>;
}

export interface DashboardActivity {
  items: ActivityItem[];
  total: number;
}
