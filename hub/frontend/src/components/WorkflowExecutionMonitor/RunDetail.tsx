import React from 'react';
import { useWorkflowRun, useRetryWorkflowRun } from '../../hooks/useWorkflowRuns';
import { AgentRunCard } from './AgentRunCard';

interface RunDetailProps {
  workflowId: string;
  runId: string;
  onClose: () => void;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'SUCCESS':
      return 'text-green-400';
    case 'FAILED':
      return 'text-red-400';
    case 'RUNNING':
      return 'text-blue-400 animate-pulse';
    case 'PENDING':
      return 'text-yellow-400';
    case 'WAITING_APPROVAL':
      return 'text-purple-400';
    default:
      return 'text-slate-400';
  }
};

export const RunDetail: React.FC<RunDetailProps> = ({ workflowId, runId, onClose }) => {
  const { data: run, isLoading } = useWorkflowRun(workflowId, runId);
  const retryMutation = useRetryWorkflowRun();

  const handleRetry = () => {
    if (confirm('Retry this workflow run with the same context?')) {
      retryMutation.mutate(runId, {
        onSuccess: () => {
          onClose();
        },
      });
    }
  };

  if (isLoading || !run) {
    return (
      <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
        <div className="bg-slate-900 rounded-lg p-8">
          <div className="text-white">Loading run details...</div>
        </div>
      </div>
    );
  }

  const agentRuns = run.agentRuns || [];
  const duration = run.finishedAt
    ? new Date(run.finishedAt).getTime() - new Date(run.startedAt).getTime()
    : Date.now() - new Date(run.startedAt).getTime();

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-6">
      <div className="bg-slate-900 rounded-lg w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col border border-slate-800">
        {/* Header */}
        <div className="p-6 border-b border-slate-800">
          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white mb-2">
                Workflow Run Details
              </h2>
              <div className="flex items-center gap-4 text-sm">
                <div className={`font-semibold ${getStatusColor(run.status)}`}>
                  Status: {run.status}
                </div>
                <div className="text-slate-400">
                  Duration: {(duration / 1000).toFixed(1)}s
                </div>
                <div className="text-slate-500 font-mono">
                  {run.id}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2">
              {run.status === 'FAILED' && (
                <button
                  onClick={handleRetry}
                  disabled={retryMutation.isPending}
                  className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors disabled:opacity-50"
                >
                  {retryMutation.isPending ? 'Retrying...' : 'Retry'}
                </button>
              )}
              <button
                onClick={onClose}
                className="px-4 py-2 bg-slate-800 hover:bg-slate-700 text-white rounded-lg transition-colors"
              >
                Close
              </button>
            </div>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6 space-y-6">
          {/* Workflow Info */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-3">Workflow</h3>
            <div className="bg-slate-800/50 rounded-lg p-4 space-y-2">
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Name:</span>
                <span className="text-white font-medium">{run.workflow?.name}</span>
              </div>
              {run.workflow?.description && (
                <div className="flex items-start gap-2">
                  <span className="text-slate-400">Description:</span>
                  <span className="text-slate-300">{run.workflow.description}</span>
                </div>
              )}
              <div className="flex items-center gap-2">
                <span className="text-slate-400">Triggered by:</span>
                <span className="text-slate-300 font-mono">{run.trigger}</span>
              </div>
            </div>
          </div>

          {/* Context */}
          {run.contextJson && Object.keys(run.contextJson).length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">Context</h3>
              <div className="bg-slate-800/50 rounded-lg p-4">
                <pre className="text-sm text-slate-300 overflow-x-auto">
                  {JSON.stringify(run.contextJson, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Agent Runs */}
          <div>
            <h3 className="text-lg font-semibold text-white mb-3">
              Agent Executions ({agentRuns.length})
            </h3>
            {agentRuns.length === 0 ? (
              <div className="bg-slate-800/50 rounded-lg p-8 text-center text-slate-400">
                No agent runs yet
              </div>
            ) : (
              <div className="space-y-3">
                {agentRuns.map((agentRun, index) => (
                  <AgentRunCard key={agentRun.id} agentRun={agentRun} index={index + 1} />
                ))}
              </div>
            )}
          </div>

          {/* Approvals */}
          {run.approvals && run.approvals.length > 0 && (
            <div>
              <h3 className="text-lg font-semibold text-white mb-3">
                Approvals ({run.approvals.length})
              </h3>
              <div className="space-y-2">
                {run.approvals.map((approval: any) => (
                  <div key={approval.id} className="bg-slate-800/50 rounded-lg p-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className={`font-semibold ${
                        approval.status === 'APPROVED' ? 'text-green-400' :
                        approval.status === 'REJECTED' ? 'text-red-400' :
                        'text-yellow-400'
                      }`}>
                        {approval.status}
                      </span>
                      <span className="text-xs text-slate-500">
                        {new Date(approval.requestedAt).toLocaleString()}
                      </span>
                    </div>
                    {approval.notes && (
                      <p className="text-sm text-slate-300">{approval.notes}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
