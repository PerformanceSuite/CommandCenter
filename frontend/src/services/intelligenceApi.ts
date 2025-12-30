// Intelligence Integration API Client
// Connects to Research Hub intelligence endpoints

import api from './api';
import type {
  HypothesisCategory,
  HypothesisStatus,
  ImpactLevel,
  RiskLevel,
} from '../types/hypothesis';

// Types for new intelligence endpoints

export interface HypothesisCreate {
  statement: string;
  category: HypothesisCategory;
  impact?: ImpactLevel;
  risk?: RiskLevel;
}

export interface QuickHypothesisCreate extends HypothesisCreate {
  context?: string;
}

export interface HypothesisResponse {
  id: number;
  project_id: number;
  research_task_id: number;
  statement: string;
  category: HypothesisCategory;
  status: HypothesisStatus;
  impact: ImpactLevel;
  risk: RiskLevel;
  priority_score: number;
  validation_score: number | null;
  knowledge_entry_id: string | null;
  created_at: string;
  updated_at: string;
  evidence_count: number;
  debate_count: number;
}

export interface HypothesisListResponse {
  total: number;
  items: HypothesisResponse[];
}

export interface QuickHypothesisResponse {
  hypothesis_id: number;
  research_task_id: number;
  hypothesis: HypothesisResponse;
}

export interface DebateStartResponse {
  debate_id: number;
  status: string;
}

export interface DebateResponse {
  id: number;
  hypothesis_id: number;
  status: string;
  rounds_requested: number;
  rounds_completed: number;
  agents_used: string[];
  consensus_level: string | null;
  final_verdict: string | null;
  verdict_reasoning: string | null;
  gap_analysis: Record<string, unknown> | null;
  suggested_research: Record<string, unknown> | null;
  started_at: string;
  completed_at: string | null;
}

export interface GapSuggestion {
  title: string;
  description: string;
  priority: string;
  estimated_effort: string;
}

export interface EvidenceCreate {
  content: string;
  stance: 'supporting' | 'contradicting' | 'neutral';
  confidence?: number;
  source_type?: string;
  source_id?: string;
}

export interface EvidenceResponse {
  id: number;
  hypothesis_id: number;
  content: string;
  source_type: string;
  source_id: string | null;
  stance: string;
  confidence: number;
  created_at: string;
}

export interface EvidenceSuggestion {
  content: string;
  source_type: string;
  source_id: string | null;
  suggested_stance: string;
  confidence: number;
  relevance_score: number;
  source_collection: string;
}

export interface IntelligenceSummary {
  research_tasks: {
    total: number;
    by_status: Record<string, number>;
  };
  hypotheses: {
    total: number;
    validated: number;
    invalidated: number;
    needs_data: number;
    untested: number;
  };
  knowledge_base: {
    documents: number;
    findings_indexed: number;
    hypotheses_indexed: number;
  };
  gaps: {
    open_count: number;
    oldest_gap: string | null;
  };
}

export interface NeedsAttentionItem {
  id: number;
  type: string;
  title: string;
  reason: string;
  priority: string;
  created_at: string;
}

export interface RecentValidation {
  hypothesis_id: number;
  statement: string;
  verdict: string | null;
  validation_score: number | null;
  completed_at: string;
}

// Intelligence API
export const intelligenceApi = {
  // =========================================================================
  // Hypothesis CRUD (under research tasks)
  // =========================================================================

  /**
   * List hypotheses for a research task
   */
  listByTask: async (
    taskId: number,
    options?: { skip?: number; limit?: number; status?: HypothesisStatus }
  ): Promise<HypothesisListResponse> => {
    const params = new URLSearchParams();
    if (options?.skip) params.set('skip', options.skip.toString());
    if (options?.limit) params.set('limit', options.limit.toString());
    if (options?.status) params.set('status', options.status);

    const response = await api.get<HypothesisListResponse>(
      `/api/v1/research-tasks/${taskId}/hypotheses?${params}`
    );
    return response.data;
  },

  /**
   * Create hypothesis under a research task
   */
  createUnderTask: async (
    taskId: number,
    data: HypothesisCreate
  ): Promise<HypothesisResponse> => {
    const response = await api.post<HypothesisResponse>(
      `/api/v1/research-tasks/${taskId}/hypotheses`,
      data
    );
    return response.data;
  },

  /**
   * Quick hypothesis creation (auto-creates parent task)
   */
  createQuick: async (
    projectId: number,
    data: QuickHypothesisCreate
  ): Promise<QuickHypothesisResponse> => {
    const response = await api.post<QuickHypothesisResponse>(
      `/api/v1/projects/${projectId}/quick-hypothesis`,
      data
    );
    return response.data;
  },

  /**
   * Get hypothesis by ID
   */
  get: async (hypothesisId: number): Promise<HypothesisResponse> => {
    const response = await api.get<HypothesisResponse>(
      `/api/v1/hypotheses/${hypothesisId}`
    );
    return response.data;
  },

  /**
   * Update hypothesis
   */
  update: async (
    hypothesisId: number,
    data: Partial<HypothesisCreate & { status?: HypothesisStatus }>
  ): Promise<HypothesisResponse> => {
    const response = await api.patch<HypothesisResponse>(
      `/api/v1/hypotheses/${hypothesisId}`,
      data
    );
    return response.data;
  },

  /**
   * Delete hypothesis
   */
  delete: async (hypothesisId: number): Promise<void> => {
    await api.delete(`/api/v1/hypotheses/${hypothesisId}`);
  },

  // =========================================================================
  // Validation (Debate)
  // =========================================================================

  /**
   * Start validation debate
   */
  startValidation: async (
    hypothesisId: number,
    data?: { agents?: string[]; rounds?: number }
  ): Promise<DebateStartResponse> => {
    const response = await api.post<DebateStartResponse>(
      `/api/v1/hypotheses/${hypothesisId}/validate`,
      data || {}
    );
    return response.data;
  },

  /**
   * Get debate status/results
   */
  getDebate: async (debateId: number): Promise<DebateResponse> => {
    const response = await api.get<DebateResponse>(`/api/v1/debates/${debateId}`);
    return response.data;
  },

  /**
   * Get suggested tasks from gap analysis
   */
  getSuggestedTasks: async (
    debateId: number
  ): Promise<{ debate_id: number; suggestions: GapSuggestion[] }> => {
    const response = await api.get<{ debate_id: number; suggestions: GapSuggestion[] }>(
      `/api/v1/debates/${debateId}/suggested-tasks`
    );
    return response.data;
  },

  /**
   * Create task from gap suggestion
   */
  createTaskFromGap: async (
    debateId: number,
    suggestionIndex: number
  ): Promise<{ research_task_id: number; title: string }> => {
    const response = await api.post<{ research_task_id: number; title: string }>(
      `/api/v1/debates/${debateId}/create-task-from-gap`,
      { suggestion_index: suggestionIndex }
    );
    return response.data;
  },

  // =========================================================================
  // Evidence
  // =========================================================================

  /**
   * List evidence for hypothesis
   */
  listEvidence: async (
    hypothesisId: number,
    options?: { skip?: number; limit?: number }
  ): Promise<{ total: number; items: EvidenceResponse[] }> => {
    const params = new URLSearchParams();
    if (options?.skip) params.set('skip', options.skip.toString());
    if (options?.limit) params.set('limit', options.limit.toString());

    const response = await api.get<{ total: number; items: EvidenceResponse[] }>(
      `/api/v1/hypotheses/${hypothesisId}/evidence?${params}`
    );
    return response.data;
  },

  /**
   * Add evidence manually
   */
  addEvidence: async (
    hypothesisId: number,
    data: EvidenceCreate
  ): Promise<EvidenceResponse> => {
    const response = await api.post<EvidenceResponse>(
      `/api/v1/hypotheses/${hypothesisId}/evidence`,
      data
    );
    return response.data;
  },

  /**
   * Get AI-suggested evidence
   */
  getSuggestedEvidence: async (
    hypothesisId: number,
    limit?: number
  ): Promise<{ suggestions: EvidenceSuggestion[]; query_used: string }> => {
    const params = limit ? `?limit=${limit}` : '';
    const response = await api.get<{ suggestions: EvidenceSuggestion[]; query_used: string }>(
      `/api/v1/hypotheses/${hypothesisId}/suggested-evidence${params}`
    );
    return response.data;
  },

  /**
   * Accept suggested evidence
   */
  acceptSuggestedEvidence: async (
    hypothesisId: number,
    suggestionIndices: number[]
  ): Promise<EvidenceResponse[]> => {
    const response = await api.post<EvidenceResponse[]>(
      `/api/v1/hypotheses/${hypothesisId}/evidence/accept`,
      { suggestion_indices: suggestionIndices }
    );
    return response.data;
  },

  // =========================================================================
  // Intelligence Dashboard
  // =========================================================================

  /**
   * Get intelligence summary for project
   */
  getSummary: async (projectId: number): Promise<IntelligenceSummary> => {
    const response = await api.get<IntelligenceSummary>(
      `/api/v1/projects/${projectId}/intelligence/summary`
    );
    return response.data;
  },

  /**
   * Get items needing attention
   */
  getNeedsAttention: async (
    projectId: number,
    limit?: number
  ): Promise<{ items: NeedsAttentionItem[]; total: number }> => {
    const params = limit ? `?limit=${limit}` : '';
    const response = await api.get<{ items: NeedsAttentionItem[]; total: number }>(
      `/api/v1/projects/${projectId}/intelligence/needs-attention${params}`
    );
    return response.data;
  },

  /**
   * Get recent validations
   */
  getRecentValidations: async (
    projectId: number,
    limit?: number
  ): Promise<{ validations: RecentValidation[] }> => {
    const params = limit ? `?limit=${limit}` : '';
    const response = await api.get<{ validations: RecentValidation[] }>(
      `/api/v1/projects/${projectId}/intelligence/recent-validations${params}`
    );
    return response.data;
  },

  // =========================================================================
  // Research Findings
  // =========================================================================

  /**
   * Index findings to KB
   */
  indexFindings: async (
    taskId: number
  ): Promise<{ indexed_count: number; task_id: number }> => {
    const response = await api.post<{ indexed_count: number; task_id: number }>(
      `/api/v1/research-tasks/${taskId}/index-findings`
    );
    return response.data;
  },
};

export default intelligenceApi;
