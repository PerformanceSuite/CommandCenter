// Hypothesis Dashboard TypeScript Types

export type HypothesisStatus =
  | 'untested'
  | 'validating'
  | 'validated'
  | 'invalidated'
  | 'needs_more_data'
  | 'pivoted';

export type HypothesisCategory =
  | 'customer'
  | 'problem'
  | 'solution'
  | 'channel'
  | 'revenue'
  | 'market'
  | 'technical'
  | 'regulatory'
  | 'competitive'
  | 'gtm';

export type ImpactLevel = 'high' | 'medium' | 'low';
export type RiskLevel = 'high' | 'medium' | 'low';
export type TestabilityLevel = 'easy' | 'medium' | 'hard';

export interface HypothesisEvidence {
  id: string;
  source: string;
  content: string;
  supports: boolean;
  confidence: number;
  collected_at: string;
  collected_by: string;
}

export interface HypothesisSummary {
  id: string;
  statement: string;
  category: HypothesisCategory;
  status: HypothesisStatus;
  priority_score: number;
  evidence_count: number;
  validation_score: number | null;
  created_at: string;
  updated_at: string;
}

export interface HypothesisDetail extends HypothesisSummary {
  impact: ImpactLevel;
  risk: RiskLevel;
  testability: TestabilityLevel;
  success_criteria: string;
  context: string | null;
  tags: string[];
  evidence: HypothesisEvidence[];
  validated_at: string | null;
  metadata: Record<string, unknown>;
}

export interface HypothesisListResponse {
  items: HypothesisSummary[];
  total: number;
  limit: number;
  offset: number;
}

export interface HypothesisStats {
  total: number;
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  average_validation_score: number;
  validated_count: number;
  invalidated_count: number;
  needs_data_count: number;
  untested_count: number;
}

// Validation types

export interface ValidationRequest {
  max_rounds?: number;
  agents?: string[];
}

export interface ValidationTaskResponse {
  task_id: string;
  hypothesis_id: string;
  status: string;
  message: string;
}

export interface ValidationStatus {
  task_id: string;
  hypothesis_id: string;
  status: 'running' | 'completed' | 'failed';
  current_round: number;
  max_rounds: number;
  responses_count: number;
  consensus_level: string | null;
  started_at: string;
  completed_at: string | null;
  error: string | null;
}

// UI-specific types

export interface HypothesisFilters {
  status?: HypothesisStatus;
  category?: HypothesisCategory;
}

export const STATUS_COLORS: Record<HypothesisStatus, string> = {
  untested: 'slate',
  validating: 'blue',
  validated: 'green',
  invalidated: 'red',
  needs_more_data: 'amber',
  pivoted: 'purple',
};

export const STATUS_LABELS: Record<HypothesisStatus, string> = {
  untested: 'Untested',
  validating: 'Validating',
  validated: 'Validated',
  invalidated: 'Invalidated',
  needs_more_data: 'Needs Data',
  pivoted: 'Pivoted',
};

export const CATEGORY_LABELS: Record<HypothesisCategory, string> = {
  customer: 'Customer',
  problem: 'Problem',
  solution: 'Solution',
  channel: 'Channel',
  revenue: 'Revenue',
  market: 'Market',
  technical: 'Technical',
  regulatory: 'Regulatory',
  competitive: 'Competitive',
  gtm: 'Go-to-Market',
};
