export interface Project {
  id: number;
  name: string;
  owner: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface ProjectCreate {
  name: string;
  owner: string;
  description?: string;
}

export interface ProjectUpdate {
  name?: string;
  description?: string;
}

export interface ProjectStats {
  total_repositories: number;
  total_technologies: number;
  total_research_tasks: number;
  total_knowledge_entries: number;
}
