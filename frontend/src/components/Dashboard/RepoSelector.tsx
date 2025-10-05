import React, { useState } from 'react';
import type { Repository } from '../../types/repository';
import { Check, GitBranch } from 'lucide-react';

interface RepoSelectorProps {
  repositories: Repository[];
}

export const RepoSelector: React.FC<RepoSelectorProps> = ({ repositories }) => {
  const [selectedRepo, setSelectedRepo] = useState<string | null>(null);

  const activeRepos = repositories.filter((r) => r.is_active);

  return (
    <div className="space-y-2">
      {activeRepos.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No active repositories</p>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {activeRepos.map((repo) => (
            <button
              key={repo.id}
              onClick={() => setSelectedRepo(repo.id)}
              className={`text-left p-4 rounded-lg border-2 transition-all ${
                selectedRepo === repo.id
                  ? 'border-primary-500 bg-primary-50'
                  : 'border-gray-200 hover:border-gray-300 bg-white'
              }`}
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center gap-2">
                  <GitBranch size={16} className="text-gray-400 mt-1" />
                  <div>
                    <p className="font-medium">{repo.name}</p>
                    <p className="text-sm text-gray-500">{repo.owner}</p>
                  </div>
                </div>
                {selectedRepo === repo.id && (
                  <Check size={20} className="text-primary-500" />
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
