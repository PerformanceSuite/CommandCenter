export interface ResearchEntry {
  id: string;
  title: string;
  source: string;
  url?: string;
  summary: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface ResearchFilter {
  tags?: string[];
  source?: string;
  dateFrom?: string;
  dateTo?: string;
}

// ===== Research Orchestration Types (Phase 2 API) =====

export interface AgentTaskRequest {
  role: string;
  prompt: string;
  model?: string;
  provider?: string;
  temperature?: number;
  max_tokens?: number;
}

export interface TechnologyDeepDiveRequest {
  technology_name: string;
  research_questions?: string[];
  project_id: number;
}

export interface MultiAgentLaunchRequest {
  tasks: AgentTaskRequest[];
  max_concurrent?: number;
  project_id: number;
}

export interface TechnologyMonitorRequest {
  sources: string[];
  days_back?: number;
}

export interface AgentResultMetadata {
  agent_role: string;
  model_used: string;
  provider: string;
  execution_time_seconds: number;
  tokens_used?: {
    prompt: number;
    completion: number;
    total: number;
  };
  cost_usd?: number;
}

export interface AgentResult {
  data: Record<string, any>;
  metadata?: AgentResultMetadata | null;
  error?: string | null;
}

export interface ResearchTask {
  task_id: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  technology?: string | null;
  created_at: string;
  completed_at?: string | null;
  results?: AgentResult[] | null;
  summary?: string | null;
  error?: string | null;
}

export interface ModelInfo {
  model_id: string;
  tier: 'premium' | 'standard' | 'economy' | 'local';
  cost_per_1m_tokens?: number | null;
  max_tokens?: number;
  description?: string | null;
}

export interface AvailableModelsResponse {
  providers: Record<string, ModelInfo[]>;
  default_provider: string;
  default_model: string;
}

export interface ResearchSummaryResponse {
  total_tasks: number;
  completed_tasks: number;
  failed_tasks: number;
  agents_deployed: number;
  total_cost_usd: number;
  avg_execution_time_seconds: number;
}

export interface MonitoringAlert {
  type: 'opportunity' | 'risk' | 'change';
  severity: 'low' | 'medium' | 'high';
  description: string;
  action_required?: string;
}

export interface TechnologyMonitorResponse {
  technology_id: number;
  technology_name: string;
  period: string;
  hackernews?: Record<string, any> | null;
  github?: Record<string, any> | null;
  arxiv?: Record<string, any> | null;
  alerts: MonitoringAlert[];
  last_updated: string;
}
