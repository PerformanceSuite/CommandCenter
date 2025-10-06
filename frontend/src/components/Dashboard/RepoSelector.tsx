import React, { useState, useMemo, useCallback } from 'react';
import type { Repository } from '../../types/repository';
import { Check, GitBranch } from 'lucide-react';

interface RepoSelectorProps {
  repositories: Repository[];
}

export const RepoSelector: React.FC<RepoSelectorProps> = ({ repositories }) => {
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null);

  const activeRepos = useMemo(
    () => repositories.filter((r) => r.is_active),
    [repositories]
  );

  const handleRepoSelect = useCallback((repoId: string) => {
    setSelectedRepo(repoId);
  }, []);

  return (
    <div className="space-y-2" role="group" aria-label="Repository selector">
      {activeRepos.length === 0 ? (
        <p className="text-gray-500 text-center py-8" role="status">
          No active repositories
        </p>
      ) : (
        <div
          className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4"
          role="list"
        >
          {activeRepos.map((repo) => (
            <button
              key={repo.id}
              onClick={() => handleRepoSelect(repo.id)}
              className={`text-left p-4 rounded-lg border-2 transition-all focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 ${
                selectedRepo === repo.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
              role="listitem"
              aria-pressed={selectedRepo === repo.id}
              aria-label={`Select repository ${repo.full_name}${repo.description ? `: ${repo.description}` : ''}`}
              type="button"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <GitBranch size={16} className="text-gray-400 mt-1" aria-hidden="true" />
                  <div>
                    <p className="font-medium">{repo.name}</p>
                    <p className="text-sm text-gray-500">{repo.owner}</p>
                  </div>
                </div>
                {selectedRepo === repo.id && (
                  <Check size={20} className="text-primary-500" aria-hidden="true" />
                )}
              </div>
              {repo.description && (
                <p className="text-sm text-gray-600 mt-2 line-clamp-2">{repo.description}</p>
              )}
            </button>
          ))}
        </div>
      )}
    </div>
  );
};
