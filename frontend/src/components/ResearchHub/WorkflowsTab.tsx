import { useState, useEffect } from 'react';
import { Workflow, Play, Clock, CheckCircle, XCircle, AlertCircle, Plus, RefreshCw } from 'lucide-react';

interface WorkflowRun {
  task_id: string;
  technology_name?: string;
  task_type: string;
  status: 'pending' | 'running' | 'completed' | 'failed';
  created_at: string;
  completed_at?: string;
  agent_count?: number;
  result_summary?: string;
}

interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  agent_roles: string[];
  enabled: boolean;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

// Default workflow templates for the AI Arena
const DEFAULT_TEMPLATES: WorkflowTemplate[] = [
  {
    id: 'deep-dive',
    name: 'Technology Deep Dive',
    description: 'Comprehensive analysis using Analyst, Researcher, Strategist, and Critic agents',
    agent_roles: ['analyst', 'researcher', 'strategist', 'critic'],
    enabled: true,
  },
  {
    id: 'hypothesis-validation',
    name: 'Hypothesis Validation',
    description: 'Multi-agent debate to validate or invalidate research hypotheses',
    agent_roles: ['analyst', 'critic', 'researcher'],
    enabled: true,
  },
  {
    id: 'competitive-analysis',
    name: 'Competitive Analysis',
    description: 'Analyze competitors and market positioning',
    agent_roles: ['analyst', 'strategist'],
    enabled: true,
  },
  {
    id: 'tech-monitoring',
    name: 'Technology Monitoring',
    description: 'Monitor HackerNews, GitHub, and arXiv for technology updates',
    agent_roles: ['researcher'],
    enabled: true,
  },
];

export function WorkflowsTab() {
  const [recentRuns, setRecentRuns] = useState<WorkflowRun[]>([]);
  const [templates] = useState<WorkflowTemplate[]>(DEFAULT_TEMPLATES);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchRecentRuns();
  }, []);

  const fetchRecentRuns = async () => {
    try {
      setLoading(true);
      setError(null);

      const res = await fetch(`${API_BASE}/api/v1/research/tasks`);
      if (res.ok) {
        const data = await res.json();
        setRecentRuns(data.tasks || []);
      } else if (res.status === 404) {
        // Endpoint might not exist yet
        setRecentRuns([]);
      } else {
        throw new Error('Failed to fetch workflow runs');
      }
    } catch (err) {
      // Don't show error for missing endpoint - just show empty state
      setRecentRuns([]);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="text-green-500" size={18} />;
      case 'failed':
        return <XCircle className="text-red-500" size={18} />;
      case 'running':
        return <RefreshCw className="text-blue-500 animate-spin" size={18} />;
      default:
        return <Clock className="text-amber-500" size={18} />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'bg-green-900/30 text-green-400 border-green-700/50';
      case 'failed':
        return 'bg-red-900/30 text-red-400 border-red-700/50';
      case 'running':
        return 'bg-blue-900/30 text-blue-400 border-blue-700/50';
      default:
        return 'bg-amber-900/30 text-amber-400 border-amber-700/50';
    }
  };

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString();
  };

  if (loading) {
    return (
      <div className="py-8 text-center">
        <div className="text-slate-400 animate-pulse">Loading workflows...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Workflow Templates */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Workflow className="text-purple-500" size={24} />
            <h3 className="text-xl font-semibold text-white">Workflow Templates</h3>
          </div>
          <button className="flex items-center gap-2 px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors">
            <Plus size={18} />
            Create Template
          </button>
        </div>
        <p className="text-sm text-slate-400 mb-4">
          Pre-configured multi-agent research workflows. Launch from Deep Dive or Custom Agents tabs.
        </p>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {templates.map((template) => (
            <div
              key={template.id}
              className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg hover:border-slate-600 transition-colors"
            >
              <div className="flex items-start justify-between mb-2">
                <h4 className="font-medium text-white">{template.name}</h4>
                <span
                  className={`px-2 py-0.5 text-xs rounded ${
                    template.enabled
                      ? 'bg-green-900/30 text-green-400'
                      : 'bg-slate-700 text-slate-400'
                  }`}
                >
                  {template.enabled ? 'Enabled' : 'Disabled'}
                </span>
              </div>
              <p className="text-sm text-slate-400 mb-3">{template.description}</p>
              <div className="flex flex-wrap gap-2">
                {template.agent_roles.map((role) => (
                  <span
                    key={role}
                    className="px-2 py-1 bg-slate-700/50 text-slate-300 text-xs rounded capitalize"
                  >
                    {role}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Recent Workflow Runs */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Play className="text-blue-500" size={24} />
            <h3 className="text-xl font-semibold text-white">Recent Runs</h3>
          </div>
          <button
            onClick={fetchRecentRuns}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 text-slate-300 rounded text-sm hover:bg-slate-600"
          >
            <RefreshCw size={14} />
            Refresh
          </button>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-4 bg-red-900/20 border border-red-700/50 rounded-lg mb-4">
            <AlertCircle className="text-red-400" size={18} />
            <span className="text-red-400">{error}</span>
          </div>
        )}

        {recentRuns.length === 0 ? (
          <div className="text-center py-12 bg-slate-800/30 rounded-lg border border-slate-700/50">
            <Workflow className="mx-auto text-slate-600 mb-3" size={48} />
            <p className="text-slate-400 mb-2">No workflow runs yet</p>
            <p className="text-sm text-slate-500">
              Launch a Technology Deep Dive or Custom Agent task to see runs here.
            </p>
          </div>
        ) : (
          <div className="space-y-3">
            {recentRuns.map((run) => (
              <div
                key={run.task_id}
                className={`p-4 rounded-lg border ${getStatusColor(run.status)}`}
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-3">
                    {getStatusIcon(run.status)}
                    <div>
                      <span className="font-medium text-white">
                        {run.technology_name || run.task_type}
                      </span>
                      <span className="text-sm text-slate-400 ml-2">
                        ({run.task_type})
                      </span>
                    </div>
                  </div>
                  <span className="text-xs text-slate-500">
                    {formatDate(run.created_at)}
                  </span>
                </div>

                {run.result_summary && (
                  <p className="text-sm text-slate-300 mt-2">{run.result_summary}</p>
                )}

                <div className="flex items-center gap-4 mt-3 text-xs text-slate-500">
                  {run.agent_count && (
                    <span>{run.agent_count} agents</span>
                  )}
                  {run.completed_at && (
                    <span>Completed: {formatDate(run.completed_at)}</span>
                  )}
                  <span className="font-mono">{run.task_id.slice(0, 8)}...</span>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

export default WorkflowsTab;
