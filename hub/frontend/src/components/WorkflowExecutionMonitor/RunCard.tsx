import React from 'react';
import { WorkflowRun } from '../../hooks/useWorkflowRuns';

interface RunCardProps {
  run: WorkflowRun;
  onClick: () => void;
  isSelected: boolean;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'SUCCESS':
      return 'text-green-400 bg-green-400/10 border-green-400/20';
    case 'FAILED':
      return 'text-red-400 bg-red-400/10 border-red-400/20';
    case 'RUNNING':
      return 'text-blue-400 bg-blue-400/10 border-blue-400/20';
    case 'PENDING':
      return 'text-yellow-400 bg-yellow-400/10 border-yellow-400/20';
    case 'WAITING_APPROVAL':
      return 'text-purple-400 bg-purple-400/10 border-purple-400/20';
    default:
      return 'text-slate-400 bg-slate-400/10 border-slate-400/20';
  }
};

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'SUCCESS':
      return '✓';
    case 'FAILED':
      return '✕';
    case 'RUNNING':
      return '⟳';
    case 'PENDING':
      return '○';
    case 'WAITING_APPROVAL':
      return '⏸';
    default:
      return '?';
  }
};

const formatDuration = (startedAt: string, finishedAt?: string) => {
  const start = new Date(startedAt);
  const end = finishedAt ? new Date(finishedAt) : new Date();
  const durationMs = end.getTime() - start.getTime();

  if (durationMs < 1000) return `${durationMs}ms`;
  if (durationMs < 60000) return `${(durationMs / 1000).toFixed(1)}s`;
  return `${(durationMs / 60000).toFixed(1)}m`;
};

const formatTimestamp = (timestamp: string) => {
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();

  if (diffMs < 60000) return 'Just now';
  if (diffMs < 3600000) return `${Math.floor(diffMs / 60000)}m ago`;
  if (diffMs < 86400000) return `${Math.floor(diffMs / 3600000)}h ago`;
  return date.toLocaleDateString();
};

export const RunCard: React.FC<RunCardProps> = ({ run, onClick, isSelected }) => {
  const statusColor = getStatusColor(run.status);
  const statusIcon = getStatusIcon(run.status);
  const duration = formatDuration(run.startedAt, run.finishedAt);
  const timestamp = formatTimestamp(run.startedAt);

  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left p-4 rounded-lg border transition-all
        ${isSelected
          ? 'bg-slate-800 border-slate-600'
          : 'bg-slate-900 border-slate-800 hover:border-slate-700 hover:bg-slate-850'
        }
      `}
    >
      <div className="flex items-center justify-between">
        {/* Status Badge */}
        <div className="flex items-center gap-3">
          <div className={`px-3 py-1 rounded-full border text-sm font-medium ${statusColor}`}>
            <span className="mr-1.5">{statusIcon}</span>
            {run.status}
          </div>

          {/* Trigger Info */}
          <div className="flex items-center gap-2 text-sm">
            <span className="text-slate-500">Triggered by:</span>
            <span className="text-slate-300 font-mono">{run.trigger}</span>
          </div>
        </div>

        {/* Timing Info */}
        <div className="flex items-center gap-4 text-sm text-slate-400">
          <div>
            <span className="text-slate-500">Duration:</span> {duration}
          </div>
          <div>
            {timestamp}
          </div>
        </div>
      </div>

      {/* Run ID */}
      <div className="mt-2 text-xs text-slate-500 font-mono">
        ID: {run.id}
      </div>
    </button>
  );
};
