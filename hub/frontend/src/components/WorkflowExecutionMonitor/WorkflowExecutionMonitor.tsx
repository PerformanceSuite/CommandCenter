import React, { useState } from 'react';
import { useWorkflowRuns } from '../../hooks/useWorkflowRuns';
import { RunCard } from './RunCard';
import { RunDetail } from './RunDetail';

interface WorkflowExecutionMonitorProps {
  workflowId: string;
  workflowName?: string;
}

export const WorkflowExecutionMonitor: React.FC<WorkflowExecutionMonitorProps> = ({
  workflowId,
  workflowName,
}) => {
  const { data: runs, isLoading } = useWorkflowRuns(workflowId);
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center p-8">
        <div className="text-slate-400">Loading workflow runs...</div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-white mb-2">
          Execution History
          {workflowName && <span className="text-slate-400"> • {workflowName}</span>}
        </h2>
        <p className="text-slate-400">
          {runs?.length || 0} workflow run{runs?.length !== 1 ? 's' : ''}
        </p>
      </div>

      {/* Runs List */}
      {runs && runs.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-12 text-center">
          <p className="text-slate-500 text-lg">No workflow runs yet</p>
          <p className="text-slate-600 text-sm mt-2">
            Trigger the workflow to see execution history here
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {runs?.map((run) => (
            <RunCard
              key={run.id}
              run={run}
              onClick={() => setSelectedRunId(run.id)}
              isSelected={selectedRunId === run.id}
            />
          ))}
        </div>
      )}

      {/* Run Detail Modal */}
      {selectedRunId && (
        <RunDetail
          workflowId={workflowId}
          runId={selectedRunId}
          onClose={() => setSelectedRunId(null)}
        />
      )}
    </div>
  );
};
