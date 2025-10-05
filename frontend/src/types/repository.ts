export interface Repository {
  id: string;
  owner: string;
  name: string;
  full_name: string;
  description?: string;
  is_private: boolean;
  is_active: boolean;
  last_commit_message?: string;
  last_commit_author?: string;
  last_synced_at?: string;
}

export interface RepositoryStats {
  total_repos: number;
  active_repos: number;
  last_sync?: string;
}
