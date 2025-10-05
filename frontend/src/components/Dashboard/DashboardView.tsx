import React from 'react';
import { useRepositories } from '../../hooks/useRepositories';
import { useTechnologies } from '../../hooks/useTechnologies';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { RepoSelector } from './RepoSelector';
import { GitBranch, TrendingUp, Database, Activity } from 'lucide-react';

export const DashboardView: React.FC = () => {
  const { repositories, loading: reposLoading } = useRepositories();
  const { technologies, loading: techLoading } = useTechnologies();

  if (reposLoading || techLoading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  const activeRepos = repositories.filter((r) => r.is_active).length;
  const techByStatus = technologies.reduce((acc, tech) => {
    acc[tech.status] = (acc[tech.status] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const stats = [
    {
      label: 'Total Repositories',
      value: repositories.length,
      icon: <GitBranch size={24} />,
      color: 'bg-blue-500',
    },
    {
      label: 'Active Repos',
      value: activeRepos,
      icon: <Activity size={24} />,
      color: 'bg-green-500',
    },
    {
      label: 'Technologies',
      value: technologies.length,
      icon: <Database size={24} />,
      color: 'bg-purple-500',
    },
    {
      label: 'Production Ready',
      value: techByStatus['production-ready'] || 0,
      icon: <TrendingUp size={24} />,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {stats.map((stat) => (
          <div key={stat.label} className="bg-white rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-gray-500">{stat.label}</p>
                <p className="text-3xl font-bold mt-2">{stat.value}</p>
              </div>
              <div className={`${stat.color} p-3 rounded-lg text-white`}>{stat.icon}</div>
            </div>
          </div>
        ))}
      </div>

      {/* Repository Selector */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Active Repositories</h2>
        <RepoSelector repositories={repositories} />
      </div>

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Recent Activity</h2>
        <div className="space-y-4">
          {repositories.slice(0, 5).map((repo) => (
            <div key={repo.id} className="flex items-center justify-between border-b pb-4 last:border-b-0">
              <div>
                <p className="font-medium">{repo.full_name}</p>
                <p className="text-sm text-gray-500">{repo.last_commit_message || 'No recent commits'}</p>
              </div>
              <div className="text-sm text-gray-400">
                {repo.last_synced_at
                  ? new Date(repo.last_synced_at).toLocaleDateString()
                  : 'Never synced'}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};
