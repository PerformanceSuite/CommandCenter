export type TechnologyStatus = 'research' | 'prototype' | 'beta' | 'production-ready';

export interface Technology {
  id: string;
  domain: string;
  title: string;
  vendor: string;
  status: TechnologyStatus;
  relevance: number;
  notes?: string;
  created_at?: string;
  updated_at?: string;
}

export interface TechnologyDomain {
  name: string;
  count: number;
  technologies: Technology[];
}
