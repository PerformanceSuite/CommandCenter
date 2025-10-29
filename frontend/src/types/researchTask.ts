export enum TaskStatus {
  PENDING = 'pending',
  IN_PROGRESS = 'in_progress',
  BLOCKED = 'blocked',
  COMPLETED = 'completed',
  CANCELLED = 'cancelled',
}

export interface DocumentUpload {
  filename: string;
  stored_filename: string;
  file_path: string;
  content_type: string;
  size: number;
  uploaded_at: string;
}

export interface ResearchTask {
  id: number;
  title: string;
  description?: string;
  status: TaskStatus;
  technology_id?: number;
  repository_id?: number;
  user_notes?: string;
  findings?: string;
  assigned_to?: string;
  due_date?: string;
  completed_at?: string;
  progress_percentage: number;
  estimated_hours?: number;
  actual_hours?: number;
  uploaded_documents?: DocumentUpload[];
  metadata_?: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface ResearchTaskCreate {
  title: string;
  description?: string;
  status?: TaskStatus;
  technology_id?: number;
  repository_id?: number;
  user_notes?: string;
  findings?: string;
  assigned_to?: string;
  due_date?: string;
  estimated_hours?: number;
}

export interface ResearchTaskUpdate {
  title?: string;
  description?: string;
  status?: TaskStatus;
  user_notes?: string;
  findings?: string;
  assigned_to?: string;
  due_date?: string;
  progress_percentage?: number;
  actual_hours?: number;
}

export interface ResearchTaskListResponse {
  tasks: ResearchTask[];
  total: number;
}

export interface ResearchTaskFilter {
  technology_id?: number;
  repository_id?: number;
  status?: TaskStatus;
  assigned_to?: string;
}
