import React, { useState } from 'react';
import { AgentRun } from '../../hooks/useWorkflowRuns';

interface AgentRunCardProps {
  agentRun: AgentRun;
  index: number;
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'SUCCESS':
      return 'text-green-400 bg-green-400/10';
    case 'FAILED':
      return 'text-red-400 bg-red-400/10';
    case 'RUNNING':
      return 'text-blue-400 bg-blue-400/10';
    case 'PENDING':
      return 'text-yellow-400 bg-yellow-400/10';
    case 'WAITING_APPROVAL':
      return 'text-purple-400 bg-purple-400/10';
    default:
      return 'text-slate-400 bg-slate-400/10';
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

export const AgentRunCard: React.FC<AgentRunCardProps> = ({ agentRun, index }) => {
  const [showDetails, setShowDetails] = useState(false);

  const statusColor = getStatusColor(agentRun.status);
  const statusIcon = getStatusIcon(agentRun.status);

  return (
    <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setShowDetails(!showDetails)}
        className="w-full p-4 text-left hover:bg-slate-800/70 transition-colors"
      >
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <span className="text-slate-500 font-mono text-sm">#{index}</span>
            <div className={`px-2 py-1 rounded text-xs font-medium ${statusColor}`}>
              <span className="mr-1">{statusIcon}</span>
              {agentRun.status}
            </div>
            <span className="text-white font-semibold">{agentRun.agent.name}</span>
            <span className="text-slate-400 text-sm">({agentRun.agent.type})</span>
          </div>

          <div className="flex items-center gap-4 text-sm">
            {agentRun.durationMs !== undefined && agentRun.durationMs !== null && (
              <span className="text-slate-400">
                {agentRun.durationMs < 1000
                  ? `${agentRun.durationMs}ms`
                  : `${(agentRun.durationMs / 1000).toFixed(2)}s`}
              </span>
            )}
            <span className="text-slate-500">
              {showDetails ? '▼' : '▶'}
            </span>
          </div>
        </div>
      </button>

      {/* Details */}
      {showDetails && (
        <div className="p-4 border-t border-slate-700 space-y-4">
          {/* Input */}
          {agentRun.inputJson && (
            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-2">Input</h4>
              <div className="bg-slate-900 rounded p-3">
                <pre className="text-xs text-slate-300 overflow-x-auto">
                  {JSON.stringify(agentRun.inputJson, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Output */}
          {agentRun.outputJson && (
            <div>
              <h4 className="text-sm font-semibold text-slate-300 mb-2">Output</h4>
              <div className="bg-slate-900 rounded p-3">
                <pre className="text-xs text-slate-300 overflow-x-auto">
                  {JSON.stringify(agentRun.outputJson, null, 2)}
                </pre>
              </div>
            </div>
          )}

          {/* Error */}
          {agentRun.error && (
            <div>
              <h4 className="text-sm font-semibold text-red-400 mb-2">Error</h4>
              <div className="bg-red-900/20 border border-red-800 rounded p-3">
                <pre className="text-xs text-red-300 whitespace-pre-wrap">
                  {agentRun.error}
                </pre>
              </div>
            </div>
          )}

          {/* Timestamps */}
          <div className="flex items-center gap-4 text-xs text-slate-500">
            <div>
              <span className="text-slate-600">Started:</span>{' '}
              {new Date(agentRun.startedAt).toLocaleString()}
            </div>
            {agentRun.finishedAt && (
              <div>
                <span className="text-slate-600">Finished:</span>{' '}
                {new Date(agentRun.finishedAt).toLocaleString()}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};
