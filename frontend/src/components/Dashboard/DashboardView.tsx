import React, { useMemo } from 'react';
import { useRepositories } from '../../hooks/useRepositories';
import { useTechnologies } from '../../hooks/useTechnologies';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { RepoSelector } from './RepoSelector';
import { GitBranch, TrendingUp, Database, Activity } from 'lucide-react';

export const DashboardView: React.FC = () => {
  const { repositories, loading: reposLoading } = useRepositories();
  const { technologies, loading: techLoading } = useTechnologies();

  // Memoize computed values to avoid recalculations
  const activeRepos = useMemo(
    () => repositories.filter((r) => r.is_active).length,
    [repositories]
  );

  const techByStatus = useMemo(
    () => technologies.reduce((acc, tech) => {
      acc[tech.status] = (acc[tech.status] || 0) + 1;
      return acc;
    }, {} as Record<string, number>),
    [technologies]
  );

  const stats = useMemo(
    () => [
      {
        label: 'Total Repositories',
        value: repositories.length,
        icon: <GitBranch size={24} aria-hidden="true" />,
        color: 'bg-blue-500',
      },
      {
        label: 'Active Repos',
        value: activeRepos,
        icon: <Activity size={24} aria-hidden="true" />,
        color: 'bg-green-500',
      },
      {
        label: 'Technologies',
        value: technologies.length,
        icon: <Database size={24} aria-hidden="true" />,
        color: 'bg-purple-500',
      },
      {
        label: 'Production Ready',
        value: techByStatus['production-ready'] || 0,
        icon: <TrendingUp size={24} aria-hidden="true" />,
        color: 'bg-orange-500',
      },
    ],
    [repositories.length, activeRepos, technologies.length, techByStatus]
  );

  const recentRepos = useMemo(
    () => repositories.slice(0, 5),
    [repositories]
  );

  if (reposLoading || techLoading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <section aria-label="Dashboard statistics">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {stats.map((stat) => (
            <div
              key={stat.label}
              className="bg-white rounded-lg shadow p-6"
              role="region"
              aria-label={`${stat.label}: ${stat.value}`}
            >
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-500">{stat.label}</p>
                  <p className="text-3xl font-bold mt-2" aria-live="polite">{stat.value}</p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg text-white`}>{stat.icon}</div>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Repository Selector */}
      <section className="bg-white rounded-lg shadow p-6" aria-labelledby="active-repos-heading">
        <h2 id="active-repos-heading" className="text-xl font-bold mb-4">Active Repositories</h2>
        <RepoSelector repositories={repositories} />
      </section>

      {/* Recent Activity */}
      <section className="bg-white rounded-lg shadow p-6" aria-labelledby="recent-activity-heading">
        <h2 id="recent-activity-heading" className="text-xl font-bold mb-4">Recent Activity</h2>
        <div className="space-y-4" role="list">
          {recentRepos.map((repo) => (
            <div
              key={repo.id}
              className="flex items-center justify-between border-b pb-4 last:border-b-0"
              role="listitem"
            >
              <div>
                <p className="font-medium">{repo.full_name}</p>
                <p className="text-sm text-gray-500">{repo.last_commit_message || 'No recent commits'}</p>
              </div>
              <div className="text-sm text-gray-400">
                <time dateTime={repo.last_synced_at || undefined}>
                  {repo.last_synced_at
                    ? new Date(repo.last_synced_at).toLocaleDateString()
                    : 'Never synced'}
                </time>
              </div>
            </div>
          ))}
        </div>
      </section>
    </div>
  );
};
