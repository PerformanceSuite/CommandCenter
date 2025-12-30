// Hypothesis Dashboard API Client

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

// API base - points to CommandCenter backend
// In production, this would be configured per-project
const API_BASE = '/api/v1';

// Helper function for fetch requests
async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

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
  list: (
    filters?: HypothesisFilters,
    limit = 20,
    offset = 0
  ): Promise<HypothesisListResponse> => {
    const params = new URLSearchParams();
    if (filters?.status) params.set('status', filters.status);
    if (filters?.category) params.set('category', filters.category);
    params.set('limit', limit.toString());
    params.set('offset', offset.toString());

    return fetchJSON(`${API_BASE}/hypotheses/?${params}`);
  },

  /**
   * Get a single hypothesis with full details
   */
  get: (id: string): Promise<HypothesisDetail> =>
    fetchJSON(`${API_BASE}/hypotheses/${id}`),

  /**
   * Create a new hypothesis with quick input
   */
  create: (request: CreateHypothesisRequest): Promise<HypothesisDetail> =>
    fetchJSON(`${API_BASE}/hypotheses/`, {
      method: 'POST',
      body: JSON.stringify(request),
    }),

  /**
   * Get dashboard statistics
   */
  stats: (): Promise<HypothesisStats> =>
    fetchJSON(`${API_BASE}/hypotheses/stats`),

  /**
   * Start validation for a hypothesis
   */
  validate: (
    id: string,
    request?: ValidationRequest
  ): Promise<ValidationTaskResponse> =>
    fetchJSON(`${API_BASE}/hypotheses/${id}/validate`, {
      method: 'POST',
      body: JSON.stringify(request || {}),
    }),

  /**
   * Get validation status for a hypothesis
   */
  getValidationStatus: (hypothesisId: string): Promise<ValidationStatus> =>
    fetchJSON(`${API_BASE}/hypotheses/${hypothesisId}/validation-status`),

  /**
   * Get validation status by task ID
   */
  getValidationTask: (taskId: string): Promise<ValidationStatus> =>
    fetchJSON(`${API_BASE}/hypotheses/validation/${taskId}`),

  /**
   * Get full debate result for a completed validation task
   */
  getDebateResult: (taskId: string): Promise<DebateResult> =>
    fetchJSON(`${API_BASE}/hypotheses/validation/${taskId}/debate`),

  // Evidence Explorer endpoints

  /**
   * List all evidence across hypotheses with optional filtering
   */
  listEvidence: (
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

    return fetchJSON(`${API_BASE}/hypotheses/evidence/list?${params}`);
  },

  /**
   * Get evidence statistics
   */
  getEvidenceStats: (): Promise<EvidenceStats> =>
    fetchJSON(`${API_BASE}/hypotheses/evidence/stats`),
};

export default hypothesesApi;
