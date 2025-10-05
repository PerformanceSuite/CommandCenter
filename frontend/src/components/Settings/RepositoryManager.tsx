import React from 'react';
import { useRepositories } from '../../hooks/useRepositories';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { GitBranch, RefreshCw, Trash2 } from 'lucide-react';

export const RepositoryManager: React.FC = () => {
  const { repositories, loading, syncRepository, deleteRepository } = useRepositories();

  if (loading) {
    return <LoadingSpinner size="md" />;
  }

  const handleSync = async (id: string) => {
    try {
      await syncRepository(id);
    } catch (error) {
      console.error('Failed to sync repository:', error);
    }
  };

  const handleDelete = async (id: string) => {
    if (window.confirm('Are you sure you want to remove this repository?')) {
      try {
        await deleteRepository(id);
      } catch (error) {
        console.error('Failed to delete repository:', error);
      }
    }
  };

  return (
    <div className="space-y-4">
      {repositories.length === 0 ? (
        <p className="text-gray-500 text-center py-8">No repositories configured</p>
      ) : (
        <div className="space-y-3">
          {repositories.map((repo) => (
            <div
              key={repo.id}
              className="flex items-center justify-between p-4 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              <div className="flex items-center gap-3">
                <GitBranch size={20} className="text-gray-400" />
                <div>
                  <p className="font-medium">{repo.full_name}</p>
                  <p className="text-sm text-gray-500">
                    {repo.description || 'No description'}
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <span
                  className={`px-2 py-1 text-xs rounded-full ${
                    repo.is_active
                      ? 'bg-green-100 text-green-700'
                      : 'bg-gray-100 text-gray-700'
                  }`}
                >
                  {repo.is_active ? 'Active' : 'Inactive'}
                </span>

                <button
                  onClick={() => handleSync(repo.id)}
                  className="p-2 text-gray-600 hover:text-primary-600 hover:bg-primary-50 rounded-lg transition-colors"
                  title="Sync repository"
                >
                  <RefreshCw size={16} />
                </button>

                <button
                  onClick={() => handleDelete(repo.id)}
                  className="p-2 text-gray-600 hover:text-red-600 hover:bg-red-50 rounded-lg transition-colors"
                  title="Remove repository"
                >
                  <Trash2 size={16} />
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
