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

// Debate types

export type ConsensusLevel = 'strong' | 'moderate' | 'weak' | 'deadlock';
export type DebateStatus = 'pending' | 'in_progress' | 'completed' | 'failed' | 'timeout';

export interface AgentResponse {
  answer: string;
  reasoning: string;
  confidence: number; // 0-100
  evidence: string[];
  agent_name: string;
  model: string;
}

export interface DebateRound {
  round_number: number;
  responses: AgentResponse[];
  consensus_level: ConsensusLevel | null;
  started_at: string;
  completed_at: string | null;
  metadata: {
    agreement_score?: number;
    weighted_confidence?: number;
  };
}

export interface DebateResult {
  debate_id: string;
  question: string;
  rounds: DebateRound[];
  final_answer: string;
  final_confidence: number;
  consensus_level: ConsensusLevel;
  dissenting_views: AgentResponse[];
  status: DebateStatus;
  started_at: string;
  completed_at: string | null;
  total_cost: number;
  error_message: string | null;
}

export interface ValidationResultResponse {
  hypothesis_id: string;
  status: HypothesisStatus;
  validation_score: number;
  consensus_reached: boolean;
  rounds_taken: number;
  final_answer: string;
  reasoning_summary: string;
  recommendation: string;
  follow_up_questions: string[];
  duration_seconds: number;
  total_cost: number;
  validated_at: string;
  debate_result?: DebateResult;
}

// Agent colors for visualization
export const AGENT_COLORS: Record<string, string> = {
  analyst: '#3B82F6',    // blue
  researcher: '#10B981', // green
  strategist: '#F59E0B', // amber
  critic: '#EF4444',     // red
};

export const CONSENSUS_COLORS: Record<ConsensusLevel, string> = {
  strong: 'green',
  moderate: 'blue',
  weak: 'amber',
  deadlock: 'red',
};

export const CONSENSUS_LABELS: Record<ConsensusLevel, string> = {
  strong: 'Strong Consensus',
  moderate: 'Moderate Consensus',
  weak: 'Weak Consensus',
  deadlock: 'Deadlock',
};

// Evidence Explorer types

export interface EvidenceItem {
  id: string;
  hypothesis_id: string;
  hypothesis_statement: string;
  source: string;
  content: string;
  supports: boolean;
  confidence: number;
  collected_at: string;
  collected_by: string;
  metadata: Record<string, unknown>;
}

export interface EvidenceListResponse {
  items: EvidenceItem[];
  total: number;
  limit: number;
  offset: number;
}

export interface EvidenceStats {
  total: number;
  supporting: number;
  contradicting: number;
  average_confidence: number;
  by_source_type: Record<string, number>;
  by_collector: Record<string, number>;
}

export interface EvidenceFilters {
  supports?: boolean;
  source?: string;
  min_confidence?: number;
}

export const SOURCE_TYPE_LABELS: Record<string, string> = {
  interview: 'Interviews',
  survey: 'Surveys',
  web: 'Web Sources',
  research: 'Research Reports',
  ai_debate: 'AI Debates',
  other: 'Other',
};

export const SOURCE_TYPE_COLORS: Record<string, string> = {
  interview: '#8B5CF6',  // purple
  survey: '#06B6D4',     // cyan
  web: '#3B82F6',        // blue
  research: '#10B981',   // green
  ai_debate: '#F59E0B',  // amber
  other: '#64748B',      // slate
};
