import React, { useState } from 'react';
import { useWorkflows } from '../hooks/useWorkflows';
import { useTriggerWorkflow } from '../hooks/useWorkflowRuns';
import { WorkflowBuilder } from '../components/WorkflowBuilder/WorkflowBuilder';
import { WorkflowExecutionMonitor } from '../components/WorkflowExecutionMonitor';
import toast from 'react-hot-toast';

type View = 'list' | 'builder' | 'monitor';

export const WorkflowsPage: React.FC = () => {
  // For now, hardcode projectId to 1. In future, get from context/auth
  const projectId = 1;

  const [view, setView] = useState<View>('list');
  const [selectedWorkflowId, setSelectedWorkflowId] = useState<string | null>(null);

  const { data: workflows, isLoading } = useWorkflows(projectId);
  const triggerMutation = useTriggerWorkflow();

  const handleCreateNew = () => {
    setSelectedWorkflowId(null);
    setView('builder');
  };

  const handleEditWorkflow = (workflowId: string) => {
    setSelectedWorkflowId(workflowId);
    setView('builder');
  };

  const handleViewRuns = (workflowId: string) => {
    setSelectedWorkflowId(workflowId);
    setView('monitor');
  };

  const handleTriggerWorkflow = async (workflowId: string, workflowName: string) => {
    try {
      const result = await triggerMutation.mutateAsync({
        workflowId,
        contextJson: {},
      });
      toast.success(`Workflow "${workflowName}" triggered successfully!`);
      // Automatically switch to monitor view
      setSelectedWorkflowId(workflowId);
      setView('monitor');
    } catch (error: any) {
      toast.error(`Failed to trigger workflow: ${error.message}`);
    }
  };

  const handleBackToList = () => {
    setView('list');
    setSelectedWorkflowId(null);
  };

  const handleSaveWorkflow = (workflowId: string) => {
    toast.success('Workflow saved successfully!');
    setView('list');
  };

  // Builder View
  if (view === 'builder') {
    return (
      <div className="h-screen flex flex-col">
        <div className="bg-slate-900 border-b border-slate-800 px-6 py-4">
          <button
            onClick={handleBackToList}
            className="text-slate-400 hover:text-white transition-colors"
          >
            ← Back to Workflows
          </button>
        </div>
        <div className="flex-1">
          <WorkflowBuilder
            projectId={projectId}
            workflowId={selectedWorkflowId || undefined}
            onSave={handleSaveWorkflow}
          />
        </div>
      </div>
    );
  }

  // Monitor View
  if (view === 'monitor' && selectedWorkflowId) {
    const workflow = workflows?.find(w => w.id === selectedWorkflowId);
    return (
      <div>
        <div className="mb-6">
          <button
            onClick={handleBackToList}
            className="text-slate-400 hover:text-white transition-colors"
          >
            ← Back to Workflows
          </button>
        </div>
        <WorkflowExecutionMonitor
          workflowId={selectedWorkflowId}
          workflowName={workflow?.name}
        />
      </div>
    );
  }

  // List View (default)
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Workflows</h1>
          <p className="text-slate-400 mt-2">
            Create and manage agent orchestration workflows
          </p>
        </div>
        <button
          onClick={handleCreateNew}
          className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium"
        >
          + Create Workflow
        </button>
      </div>

      {/* Workflows List */}
      {isLoading ? (
        <div className="flex items-center justify-center p-12">
          <div className="text-slate-400">Loading workflows...</div>
        </div>
      ) : workflows && workflows.length === 0 ? (
        <div className="bg-slate-900 border border-slate-800 rounded-lg p-12 text-center">
          <div className="text-slate-400 text-lg mb-4">No workflows yet</div>
          <p className="text-slate-500 mb-6">
            Create your first workflow to orchestrate agents
          </p>
          <button
            onClick={handleCreateNew}
            className="px-6 py-3 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium"
          >
            Create Your First Workflow
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 gap-4">
          {workflows?.map((workflow) => (
            <div
              key={workflow.id}
              className="bg-slate-900 border border-slate-800 rounded-lg p-6 hover:border-slate-700 transition-colors"
            >
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-2">
                    <h3 className="text-xl font-semibold text-white">
                      {workflow.name}
                    </h3>
                    <span
                      className={`px-2 py-1 rounded text-xs font-medium ${
                        workflow.status === 'ACTIVE'
                          ? 'bg-green-400/10 text-green-400'
                          : 'bg-slate-400/10 text-slate-400'
                      }`}
                    >
                      {workflow.status}
                    </span>
                  </div>
                  {workflow.description && (
                    <p className="text-slate-400 mb-3">{workflow.description}</p>
                  )}
                  <div className="flex items-center gap-4 text-sm text-slate-500">
                    <span>{workflow.nodes?.length || 0} agents</span>
                    <span>•</span>
                    <span className="font-mono text-xs">{workflow.id}</span>
                  </div>
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleViewRuns(workflow.id)}
                    className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors text-sm"
                  >
                    View Runs
                  </button>
                  <button
                    onClick={() => handleEditWorkflow(workflow.id)}
                    className="px-3 py-2 bg-slate-800 hover:bg-slate-700 text-slate-300 rounded-lg transition-colors text-sm"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleTriggerWorkflow(workflow.id, workflow.name)}
                    disabled={triggerMutation.isPending || workflow.status !== 'ACTIVE'}
                    className="px-3 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {triggerMutation.isPending ? 'Triggering...' : 'Trigger'}
                  </button>
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default WorkflowsPage;
