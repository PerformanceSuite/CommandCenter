// Enums matching backend
export enum TechnologyDomain {
  AUDIO_DSP = 'audio-dsp',
  AI_ML = 'ai-ml',
  MUSIC_THEORY = 'music-theory',
  PERFORMANCE = 'performance',
  UI_UX = 'ui-ux',
  INFRASTRUCTURE = 'infrastructure',
  OTHER = 'other',
}

export enum TechnologyStatus {
  DISCOVERY = 'discovery',
  RESEARCH = 'research',
  EVALUATION = 'evaluation',
  IMPLEMENTATION = 'implementation',
  INTEGRATED = 'integrated',
  ARCHIVED = 'archived',
}

export enum IntegrationDifficulty {
  TRIVIAL = 'trivial',
  EASY = 'easy',
  MODERATE = 'moderate',
  COMPLEX = 'complex',
  VERY_COMPLEX = 'very_complex',
}

export enum MaturityLevel {
  ALPHA = 'alpha',
  BETA = 'beta',
  STABLE = 'stable',
  MATURE = 'mature',
  LEGACY = 'legacy',
}

export enum CostTier {
  FREE = 'free',
  FREEMIUM = 'freemium',
  AFFORDABLE = 'affordable',
  MODERATE = 'moderate',
  EXPENSIVE = 'expensive',
  ENTERPRISE = 'enterprise',
}

// Main Technology interface
export interface Technology {
  id: number;
  title: string;
  vendor: string | null;
  domain: TechnologyDomain;
  status: TechnologyStatus;
  relevance_score: number; // 0-100
  priority: number; // 1-5
  description: string | null;
  notes: string | null;
  use_cases: string | null;
  documentation_url: string | null;
  repository_url: string | null;
  website_url: string | null;
  tags: string | null; // Comma-separated

  // Technology Radar v2 - Enhanced Evaluation Fields (14 new fields)
  // Performance characteristics
  latency_ms: number | null; // P99 latency in milliseconds
  throughput_qps: number | null; // Queries per second

  // Integration assessment
  integration_difficulty: IntegrationDifficulty | null;
  integration_time_estimate_days: number | null;

  // Maturity and stability
  maturity_level: MaturityLevel | null;
  stability_score: number | null; // 0-100

  // Cost analysis
  cost_tier: CostTier | null;
  cost_monthly_usd: number | null;

  // Dependencies and relationships
  dependencies: Record<string, string> | null; // {tech_id: relationship}
  alternatives: string | null; // Comma-separated tech IDs

  // Monitoring and alerts
  last_hn_mention: string | null;
  hn_score_avg: number | null;
  github_stars: number | null;
  github_last_commit: string | null;

  created_at: string;
  updated_at: string;
}

// Create and Update types
export interface TechnologyCreate {
  title: string;
  vendor?: string | null;
  domain?: TechnologyDomain;
  status?: TechnologyStatus;
  relevance_score?: number;
  priority?: number;
  description?: string | null;
  notes?: string | null;
  use_cases?: string | null;
  documentation_url?: string | null;
  repository_url?: string | null;
  website_url?: string | null;
  tags?: string | null;

  // Technology Radar v2 fields
  latency_ms?: number | null;
  throughput_qps?: number | null;
  integration_difficulty?: IntegrationDifficulty | null;
  integration_time_estimate_days?: number | null;
  maturity_level?: MaturityLevel | null;
  stability_score?: number | null;
  cost_tier?: CostTier | null;
  cost_monthly_usd?: number | null;
  dependencies?: Record<string, string> | null;
  alternatives?: string | null;
}

export interface TechnologyUpdate {
  title?: string;
  vendor?: string | null;
  domain?: TechnologyDomain;
  status?: TechnologyStatus;
  relevance_score?: number;
  priority?: number;
  description?: string | null;
  notes?: string | null;
  use_cases?: string | null;
  documentation_url?: string | null;
  repository_url?: string | null;
  website_url?: string | null;
  tags?: string | null;

  // Technology Radar v2 fields
  latency_ms?: number | null;
  throughput_qps?: number | null;
  integration_difficulty?: IntegrationDifficulty | null;
  integration_time_estimate_days?: number | null;
  maturity_level?: MaturityLevel | null;
  stability_score?: number | null;
  cost_tier?: CostTier | null;
  cost_monthly_usd?: number | null;
  dependencies?: Record<string, string> | null;
  alternatives?: string | null;
}

// API Response type
export interface TechnologyListResponse {
  total: number;
  items: Technology[];
  page: number;
  page_size: number;
}

// Domain grouping helper type
export interface TechnologyDomainGroup {
  name: string;
  count: number;
  technologies: Technology[];
}
