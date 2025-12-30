import { useState, useEffect, useCallback } from 'react';
import {
  intelligenceApi,
  IntelligenceSummary,
  NeedsAttentionItem,
  RecentValidation,
} from '../../services/intelligenceApi';

interface IntelligenceTabProps {
  projectId?: number;
}

/**
 * IntelligenceTab - Dashboard showing research intelligence overview
 *
 * Replaces the Summary tab with a more comprehensive intelligence view.
 * Shows hypothesis stats, recent validations, and items needing attention.
 */
export function IntelligenceTab({ projectId = 1 }: IntelligenceTabProps) {
  const [summary, setSummary] = useState<IntelligenceSummary | null>(null);
  const [needsAttention, setNeedsAttention] = useState<NeedsAttentionItem[]>([]);
  const [recentValidations, setRecentValidations] = useState<RecentValidation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [summaryData, attentionData, validationsData] = await Promise.all([
        intelligenceApi.getSummary(projectId),
        intelligenceApi.getNeedsAttention(projectId, 10),
        intelligenceApi.getRecentValidations(projectId, 10),
      ]);

      setSummary(summaryData);
      setNeedsAttention(attentionData.items);
      setRecentValidations(validationsData.validations);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load intelligence data');
    } finally {
      setLoading(false);
    }
  }, [projectId]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  if (loading) {
    return (
      <div className="py-12 text-center">
        <div className="text-slate-400 animate-pulse">Loading intelligence data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-12 text-center">
        <div className="text-red-400 mb-4">{error}</div>
        <button
          onClick={fetchData}
          className="text-blue-400 hover:text-blue-300"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-semibold text-white">Intelligence Dashboard</h2>
          <p className="text-sm text-slate-400 mt-1">
            Overview of research hypotheses, validations, and knowledge base
          </p>
        </div>
        <button
          onClick={fetchData}
          className="px-3 py-1.5 text-sm bg-slate-700 text-slate-300 rounded hover:bg-slate-600 transition-colors"
        >
          Refresh
        </button>
      </div>

      {/* Summary Stats */}
      {summary && (
        <div className="grid grid-cols-4 gap-4">
          {/* Research Tasks */}
          <StatCard
            title="Research Tasks"
            value={summary.research_tasks.total}
            color="blue"
            subtitle={Object.entries(summary.research_tasks.by_status)
              .map(([status, count]) => `${count} ${status}`)
              .join(', ') || 'No tasks'}
          />

          {/* Hypotheses */}
          <StatCard
            title="Hypotheses"
            value={summary.hypotheses.total}
            color="purple"
            subtitle={`${summary.hypotheses.validated} validated, ${summary.hypotheses.untested} untested`}
          />

          {/* Knowledge Base */}
          <StatCard
            title="KB Entries"
            value={summary.knowledge_base.documents}
            color="green"
            subtitle={`${summary.knowledge_base.findings_indexed} findings indexed`}
          />

          {/* Gaps */}
          <StatCard
            title="Open Gaps"
            value={summary.gaps.open_count}
            color={summary.gaps.open_count > 5 ? 'amber' : 'slate'}
            subtitle={summary.gaps.oldest_gap ? `Oldest: ${summary.gaps.oldest_gap}` : 'No gaps'}
          />
        </div>
      )}

      {/* Main Content Grid */}
      <div className="grid grid-cols-2 gap-6">
        {/* Needs Attention */}
        <div className="bg-slate-800/30 rounded-lg border border-slate-700/50 p-4">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <AlertIcon className="w-5 h-5 text-amber-400" />
            Needs Attention
          </h3>

          {needsAttention.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              All hypotheses are up to date
            </div>
          ) : (
            <div className="space-y-3">
              {needsAttention.map((item) => (
                <div
                  key={`${item.type}-${item.id}`}
                  className="bg-slate-800/50 rounded p-3 border border-slate-700/50"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="text-white font-medium truncate" title={item.title}>
                        {item.title}
                      </div>
                      <div className="text-sm text-slate-400 mt-1">{item.reason}</div>
                    </div>
                    <span className={`px-2 py-0.5 rounded text-xs ml-3 ${
                      item.priority === 'high' ? 'bg-red-900/30 text-red-400' :
                      'bg-amber-900/30 text-amber-400'
                    }`}>
                      {item.priority}
                    </span>
                  </div>
                  <div className="text-xs text-slate-500 mt-2">
                    Created {new Date(item.created_at).toLocaleDateString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Recent Validations */}
        <div className="bg-slate-800/30 rounded-lg border border-slate-700/50 p-4">
          <h3 className="text-lg font-semibold text-white mb-4 flex items-center gap-2">
            <CheckCircleIcon className="w-5 h-5 text-green-400" />
            Recent Validations
          </h3>

          {recentValidations.length === 0 ? (
            <div className="text-center py-8 text-slate-500">
              No validations completed yet
            </div>
          ) : (
            <div className="space-y-3">
              {recentValidations.map((validation) => (
                <div
                  key={validation.hypothesis_id}
                  className="bg-slate-800/50 rounded p-3 border border-slate-700/50"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1 min-w-0">
                      <div className="text-white font-medium truncate" title={validation.statement}>
                        {validation.statement}
                      </div>
                      <div className="flex items-center gap-3 mt-2 text-sm">
                        {validation.verdict && (
                          <span className={`px-2 py-0.5 rounded text-xs ${
                            validation.verdict === 'validated' ? 'bg-green-900/30 text-green-400' :
                            validation.verdict === 'invalidated' ? 'bg-red-900/30 text-red-400' :
                            'bg-amber-900/30 text-amber-400'
                          }`}>
                            {validation.verdict.replace('_', ' ')}
                          </span>
                        )}
                        {validation.validation_score !== null && (
                          <span className="text-slate-400">
                            {validation.validation_score.toFixed(0)}% confidence
                          </span>
                        )}
                      </div>
                    </div>
                  </div>
                  <div className="text-xs text-slate-500 mt-2">
                    Completed {new Date(validation.completed_at).toLocaleString()}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Hypothesis Stats Breakdown */}
      {summary && summary.hypotheses.total > 0 && (
        <div className="bg-slate-800/30 rounded-lg border border-slate-700/50 p-4">
          <h3 className="text-lg font-semibold text-white mb-4">Hypothesis Status Distribution</h3>
          <div className="flex items-center gap-4">
            <StatusBar
              label="Validated"
              count={summary.hypotheses.validated}
              total={summary.hypotheses.total}
              color="green"
            />
            <StatusBar
              label="Invalidated"
              count={summary.hypotheses.invalidated}
              total={summary.hypotheses.total}
              color="red"
            />
            <StatusBar
              label="Needs Data"
              count={summary.hypotheses.needs_data}
              total={summary.hypotheses.total}
              color="amber"
            />
            <StatusBar
              label="Untested"
              count={summary.hypotheses.untested}
              total={summary.hypotheses.total}
              color="slate"
            />
          </div>
        </div>
      )}
    </div>
  );
}

// Stat Card Component
function StatCard({
  title,
  value,
  subtitle,
  color,
}: {
  title: string;
  value: number;
  subtitle: string;
  color: 'blue' | 'purple' | 'green' | 'amber' | 'slate';
}) {
  const colorClasses = {
    blue: 'bg-blue-900/30 border-blue-900/50',
    purple: 'bg-purple-900/30 border-purple-900/50',
    green: 'bg-green-900/30 border-green-900/50',
    amber: 'bg-amber-900/30 border-amber-900/50',
    slate: 'bg-slate-800/50 border-slate-700/50',
  };

  const textColors = {
    blue: 'text-blue-400',
    purple: 'text-purple-400',
    green: 'text-green-400',
    amber: 'text-amber-400',
    slate: 'text-slate-300',
  };

  return (
    <div className={`rounded-lg p-4 border ${colorClasses[color]}`}>
      <div className="text-sm text-slate-400">{title}</div>
      <div className={`text-3xl font-bold mt-1 ${textColors[color]}`}>{value}</div>
      <div className="text-xs text-slate-500 mt-1 truncate" title={subtitle}>
        {subtitle}
      </div>
    </div>
  );
}

// Status Bar Component
function StatusBar({
  label,
  count,
  total,
  color,
}: {
  label: string;
  count: number;
  total: number;
  color: 'green' | 'red' | 'amber' | 'slate';
}) {
  const percentage = total > 0 ? (count / total) * 100 : 0;

  const bgColors = {
    green: 'bg-green-500',
    red: 'bg-red-500',
    amber: 'bg-amber-500',
    slate: 'bg-slate-500',
  };

  return (
    <div className="flex-1">
      <div className="flex justify-between text-sm mb-1">
        <span className="text-slate-400">{label}</span>
        <span className="text-white">{count}</span>
      </div>
      <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${bgColors[color]} transition-all`}
          style={{ width: `${percentage}%` }}
        />
      </div>
    </div>
  );
}

// Icons
function AlertIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  );
}

function CheckCircleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
      />
    </svg>
  );
}

export default IntelligenceTab;
