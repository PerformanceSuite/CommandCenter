// Hypothesis Dashboard API Client

import api from './api';
import type {
  DebateResult,
  EvidenceFilters,
  EvidenceListResponse,
  EvidenceStats,
  HypothesisDetail,
  HypothesisFilters,
  HypothesisListResponse,
  HypothesisStats,
  ValidationRequest,
  ValidationStatus,
  ValidationTaskResponse,
} from '../types/hypothesis';

// Quick create request type
export interface CreateHypothesisRequest {
  statement: string;
  context?: string;
  category?: string;
}

// Hypotheses API
export const hypothesesApi = {
  /**
   * List hypotheses with optional filtering
   */
  list: async (
    filters?: HypothesisFilters,
    limit = 20,
    offset = 0
  ): Promise<HypothesisListResponse> => {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.category) params.set('category', filters.category);
    params.set('limit', limit.toString());
    params.set('offset', offset.toString());

    const response = await api.get<HypothesisListResponse>(`/api/v1/hypotheses/?${params}`);
    return response.data;
  },

  /**
   * Get a single hypothesis with full details
   */
  get: async (id: string): Promise<HypothesisDetail> => {
    const response = await api.get<HypothesisDetail>(`/api/v1/hypotheses/${id}`);
    return response.data;
  },

  /**
   * Create a new hypothesis with quick input
   */
  create: async (request: CreateHypothesisRequest): Promise<HypothesisDetail> => {
    const response = await api.post<HypothesisDetail>('/api/v1/hypotheses/', request);
    return response.data;
  },

  /**
   * Get dashboard statistics
   */
  stats: async (): Promise<HypothesisStats> => {
    const response = await api.get<HypothesisStats>('/api/v1/hypotheses/stats');
    return response.data;
  },

  /**
   * Start validation for a hypothesis
   */
  validate: async (
    id: string,
    request?: ValidationRequest
  ): Promise<ValidationTaskResponse> => {
    const response = await api.post<ValidationTaskResponse>(
      `/api/v1/hypotheses/${id}/validate`,
      request || {}
    );
    return response.data;
  },

  /**
   * Get validation status for a hypothesis
   */
  getValidationStatus: async (hypothesisId: string): Promise<ValidationStatus> => {
    const response = await api.get<ValidationStatus>(
      `/api/v1/hypotheses/${hypothesisId}/validation-status`
    );
    return response.data;
  },

  /**
   * Get validation status by task ID
   */
  getValidationTask: async (taskId: string): Promise<ValidationStatus> => {
    const response = await api.get<ValidationStatus>(`/api/v1/hypotheses/validation/${taskId}`);
    return response.data;
  },

  /**
   * Get full debate result for a completed validation task
   */
  getDebateResult: async (taskId: string): Promise<DebateResult> => {
    const response = await api.get<DebateResult>(`/api/v1/hypotheses/validation/${taskId}/debate`);
    return response.data;
  },

  // Evidence Explorer endpoints

  /**
   * List all evidence across hypotheses with optional filtering
   */
  listEvidence: async (
    filters?: EvidenceFilters,
    limit = 50,
    offset = 0
  ): Promise<EvidenceListResponse> => {
    const params = new URLSearchParams();
    if (filters?.supports !== undefined) params.set('supports', String(filters.supports));
    if (filters?.source) params.set('source', filters.source);
    if (filters?.min_confidence !== undefined) params.set('min_confidence', String(filters.min_confidence));
    params.set('limit', limit.toString());
    params.set('offset', offset.toString());

    const response = await api.get<EvidenceListResponse>(`/api/v1/hypotheses/evidence/list?${params}`);
    return response.data;
  },

  /**
   * Get evidence statistics
   */
  getEvidenceStats: async (): Promise<EvidenceStats> => {
    const response = await api.get<EvidenceStats>('/api/v1/hypotheses/evidence/stats');
    return response.data;
  },
};

export default hypothesesApi;
