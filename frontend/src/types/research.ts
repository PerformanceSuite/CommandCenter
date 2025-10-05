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
