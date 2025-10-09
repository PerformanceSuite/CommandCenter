export interface KnowledgeSearchRequest {
  query: string;
  category?: string;
  technology_id?: number;
  limit?: number;
}

export interface KnowledgeSearchResult {
  content: string;
  title: string;
  category: string;
  technology_id?: number;
  source_file?: string;
  score: number;
  metadata: Record<string, unknown>;
}

export interface KnowledgeEntry {
  id: number;
  title: string;
  content: string;
  category: string;
  technology_id?: number;
  source_file?: string;
  source_url?: string;
  source_type?: string;
  vector_db_id?: string;
  embedding_model?: string;
  page_number?: number;
  chunk_index?: number;
  confidence_score?: number;
  relevance_score?: number;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeStatistics {
  collection: string;
  vector_db: {
    total_chunks: number;
    categories: Record<string, number>;
    embedding_model: string;
    db_path: string;
    collection_name: string;
  };
  database: {
    total_entries: number;
    categories: Record<string, number>;
  };
  embedding_model: string;
}

export interface DocumentUploadRequest {
  file: File;
  category: string;
  technology_id?: number;
  collection?: string;
}

export interface DocumentUploadResponse {
  id: number;
  filename: string;
  category: string;
  collection: string;
  chunks_added: number;
  file_size: number;
  status: string;
}
