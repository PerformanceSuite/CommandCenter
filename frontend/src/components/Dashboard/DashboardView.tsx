import React from 'react';
import { useNavigate } from 'react-router-dom';
import { useDashboard } from '../../hooks/useDashboard';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { MetricCard } from './MetricCard';
import { ActivityFeed } from './ActivityFeed';
import { StatusChart } from './StatusChart';
import { GitBranch, Database, ClipboardList, FileText, Plus } from 'lucide-react';

export const DashboardView: React.FC = () => {
  const navigate = useNavigate();
  const { stats, activity, loading, error } = useDashboard(10);

  if (loading) {
    return <LoadingSpinner size="lg" className="mt-20" />;
  }

  if (error) {
    return (
      <div className="text-center py-20">
        <p className="text-red-600 text-lg">Failed to load dashboard data</p>
        <p className="text-slate-400 mt-2">{error.message}</p>
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  // Calculate metrics
  const totalTechnologies = stats.technologies.total || 0;
  const totalTasks = stats.research_tasks.total || 0;
  const totalRepos = stats.repositories.total || 0;
  const totalDocuments = stats.knowledge_base.total_documents || 0;

  // Get status breakdowns
  const techByStatus = stats.technologies.by_status || {};
  const tasksByStatus = stats.research_tasks.by_status || {};

  return (
    <div className="space-y-6">
      {/* Stats Grid */}
      <section aria-label="Dashboard statistics">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <MetricCard
            label="Total Repositories"
            value={totalRepos}
            icon={GitBranch}
            color="bg-blue-500"
            onClick={() => navigate('/repositories')}
          />
          <MetricCard
            label="Technologies"
            value={totalTechnologies}
            icon={Database}
            color="bg-purple-500"
            subtitle={`${Object.keys(techByStatus).length} statuses`}
            onClick={() => navigate('/technologies')}
          />
          <MetricCard
            label="Research Tasks"
            value={totalTasks}
            icon={ClipboardList}
            color="bg-orange-500"
            subtitle={`${stats.research_tasks.overdue_count || 0} overdue`}
            onClick={() => navigate('/research')}
          />
          <MetricCard
            label="Knowledge Base"
            value={totalDocuments}
            icon={FileText}
            color="bg-green-500"
            subtitle="documents"
            onClick={() => navigate('/knowledge')}
          />
        </div>
      </section>

      {/* Quick Actions */}
      <section aria-label="Quick actions">
        <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg shadow p-6">
          <h2 className="text-xl font-bold text-white mb-4">Quick Actions</h2>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => navigate('/technologies/new')}
              className="flex items-center space-x-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors"
            >
              <Plus size={20} />
              <span>Add Technology</span>
            </button>
            <button
              onClick={() => navigate('/research/new')}
              className="flex items-center space-x-2 px-4 py-2 bg-orange-600 text-white rounded-lg hover:bg-orange-700 transition-colors"
            >
              <Plus size={20} />
              <span>Create Task</span>
            </button>
            <button
              onClick={() => navigate('/knowledge/upload')}
              className="flex items-center space-x-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors"
            >
              <Plus size={20} />
              <span>Upload Document</span>
            </button>
          </div>
        </div>
      </section>

      {/* Charts and Activity Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Technology Status Chart */}
        <StatusChart
          statusData={techByStatus}
          title="Technology Status Distribution"
          onStatusClick={(status) => navigate(`/technologies?status=${status}`)}
        />

        {/* Recent Activity */}
        <section className="bg-slate-800/50 border border-slate-700/50 rounded-lg shadow p-6" aria-labelledby="recent-activity-heading">
          <h2 id="recent-activity-heading" className="text-xl font-bold text-white mb-4">
            Recent Activity
          </h2>
          <ActivityFeed activities={activity || []} isLoading={loading} />
        </section>
      </div>

      {/* Task Status Overview */}
      {Object.keys(tasksByStatus).length > 0 && (
        <StatusChart
          statusData={tasksByStatus}
          title="Research Task Status Distribution"
          onStatusClick={(status) => navigate(`/research?status=${status}`)}
        />
      )}
    </div>
  );
};
