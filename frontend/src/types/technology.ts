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
