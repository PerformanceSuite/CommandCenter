import React, { useState, useEffect } from 'react';
import { researchApi } from '../../services/researchApi';
import type { ResearchTask as OrchestrationTask } from '../../types/research';

const ResearchTaskList: React.FC = () => {
  const [tasks, setTasks] = useState<Map<string, OrchestrationTask>>(new Map());
  const [expandedTaskId, setExpandedTaskId] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    // Poll for task updates every 3 seconds
    // Empty dependency array - interval created once on mount, not on every task update
    const interval = setInterval(() => {
      refreshTasks();
    }, 3000);

    return () => clearInterval(interval);
  }, []); // Fixed: removed 'tasks' from deps to prevent memory leak

  const refreshTasks = async () => {
    if (tasks.size === 0) return;

    try {
      const promises = Array.from(tasks.keys()).map(taskId =>
        researchApi.getResearchTaskStatus(taskId)
      );
      const updated = await Promise.all(promises);

      const newTasks = new Map(tasks);
      updated.forEach(task => {
        newTasks.set(task.task_id, task);
      });
      setTasks(newTasks);
    } catch (err: any) {
      console.error('Failed to refresh tasks:', err);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    try {
      await refreshTasks();
    } catch (err: any) {
      setError('Failed to refresh tasks');
    } finally {
      setRefreshing(false);
    }
  };

  const handleAddTask = async (taskId: string) => {
    setError(null);
    try {
      const task = await researchApi.getResearchTaskStatus(taskId);
      const newTasks = new Map(tasks);
      newTasks.set(task.task_id, task);
      setTasks(newTasks);
      setExpandedTaskId(task.task_id);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Task not found');
    }
  };

  const toggleExpand = (taskId: string) => {
    setExpandedTaskId(expandedTaskId === taskId ? null : taskId);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'running': return '🔄';
      case 'completed': return '✅';
      case 'failed': return '❌';
      default: return '❓';
    }
  };

  const getStatusClass = (status: string) => {
    switch (status) {
      case 'pending': return 'status-pending';
      case 'running': return 'status-running';
      case 'completed': return 'status-completed';
      case 'failed': return 'status-failed';
      default: return '';
    }
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleString();
  };

  const [newTaskId, setNewTaskId] = useState('');

  return (
    <div className="research-task-list">
      <div className="header-section">
        <h2>Research Tasks</h2>
        <button
          className="btn-refresh"
          onClick={handleRefresh}
          disabled={refreshing || tasks.size === 0}
        >
          {refreshing ? 'Refreshing...' : 'Refresh All'}
        </button>
      </div>

      <p className="description">
        Track research tasks launched from Deep Dive or Custom Agents. Tasks update
        automatically every 3 seconds.
      </p>

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      <div className="add-task-section">
        <input
          type="text"
          value={newTaskId}
          onChange={(e) => setNewTaskId(e.target.value)}
          placeholder="Enter task ID to track..."
        />
        <button
          className="btn-add"
          onClick={() => {
            handleAddTask(newTaskId);
            setNewTaskId('');
          }}
          disabled={!newTaskId.trim()}
        >
          Add Task
        </button>
      </div>

      {tasks.size === 0 ? (
        <div className="empty-state">
          <p>No tasks tracked yet.</p>
          <p>Launch a research task from Deep Dive or Custom Agents tabs, then add the task ID here to track progress.</p>
        </div>
      ) : (
        <div className="tasks-container">
          {Array.from(tasks.values()).map((task) => (
            <div key={task.task_id} className="task-card">
              <div
                className="task-header"
                onClick={() => toggleExpand(task.task_id)}
              >
                <div className="task-header-left">
                  <span className={`status-badge ${getStatusClass(task.status)}`}>
                    {getStatusIcon(task.status)} {task.status}
                  </span>
                  {task.technology && (
                    <span className="technology-badge">{task.technology}</span>
                  )}
                </div>
                <div className="task-header-right">
                  <span className="task-id">{task.task_id.slice(0, 8)}...</span>
                  <span className="expand-icon">
                    {expandedTaskId === task.task_id ? '▼' : '▶'}
                  </span>
                </div>
              </div>

              {expandedTaskId === task.task_id && (
                <div className="task-details">
                  <div className="detail-row">
                    <strong>Task ID:</strong>
                    <code>{task.task_id}</code>
                  </div>
                  <div className="detail-row">
                    <strong>Created:</strong>
                    <span>{formatDate(task.created_at)}</span>
                  </div>
                  {task.completed_at && (
                    <div className="detail-row">
                      <strong>Completed:</strong>
                      <span>{formatDate(task.completed_at)}</span>
                    </div>
                  )}

                  {task.summary && (
                    <div className="summary-section">
                      <strong>Summary:</strong>
                      <p>{task.summary}</p>
                    </div>
                  )}

                  {task.error && (
                    <div className="error-section">
                      <strong>Error:</strong>
                      <p>{task.error}</p>
                    </div>
                  )}

                  {task.results && task.results.length > 0 && (
                    <div className="results-section">
                      <strong>Results ({task.results.length} agents):</strong>
                      {task.results.map((result, index) => (
                        <div key={index} className="result-card">
                          <div className="result-header">
                            <span className="agent-role">
                              {result.metadata?.agent_role || `Agent ${index + 1}`}
                            </span>
                            {result.metadata && (
                              <span className="model-info">
                                {result.metadata.model_used} ({result.metadata.provider})
                              </span>
                            )}
                          </div>

                          {result.error ? (
                            <div className="result-error">
                              Error: {result.error}
                            </div>
                          ) : (
                            <div className="result-data">
                              <pre>{JSON.stringify(result.data, null, 2)}</pre>
                            </div>
                          )}

                          {result.metadata && (
                            <div className="result-metadata">
                              <span>⏱️ {result.metadata.execution_time_seconds.toFixed(2)}s</span>
                              {result.metadata.tokens_used && (
                                <span>
                                  🎫 {result.metadata.tokens_used.total.toLocaleString()} tokens
                                </span>
                              )}
                              {result.metadata.cost_usd && (
                                <span>💰 ${result.metadata.cost_usd.toFixed(4)}</span>
                              )}
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <style>{`
        .research-task-list {
          min-height: 400px;
        }

        .header-section {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.5rem;
        }

        .research-task-list h2 {
          font-size: 1.5rem;
          font-weight: 600;
          color: #1a202c;
          margin: 0;
        }

        .btn-refresh {
          padding: 0.5rem 1rem;
          background: #edf2f7;
          border: 1px solid #cbd5e0;
          color: #2d3748;
          border-radius: 6px;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-refresh:hover:not(:disabled) {
          background: #e2e8f0;
        }

        .btn-refresh:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .description {
          font-size: 0.95rem;
          color: #718096;
          margin-bottom: 1.5rem;
          line-height: 1.5;
        }

        .error-message {
          background: #fed7d7;
          border: 1px solid #fc8181;
          color: #742a2a;
          padding: 1rem;
          border-radius: 6px;
          margin-bottom: 1rem;
        }

        .add-task-section {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 1.5rem;
        }

        .add-task-section input {
          flex: 1;
          padding: 0.625rem;
          border: 1px solid #cbd5e0;
          border-radius: 6px;
          font-size: 1rem;
        }

        .add-task-section input:focus {
          outline: none;
          border-color: #3182ce;
          box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
        }

        .btn-add {
          padding: 0.625rem 1.5rem;
          background: #3182ce;
          border: none;
          color: white;
          border-radius: 6px;
          font-size: 1rem;
          cursor: pointer;
          transition: background 0.2s;
        }

        .btn-add:hover:not(:disabled) {
          background: #2c5282;
        }

        .btn-add:disabled {
          background: #cbd5e0;
          cursor: not-allowed;
        }

        .empty-state {
          text-align: center;
          padding: 3rem 1rem;
          color: #718096;
        }

        .empty-state p:first-child {
          font-size: 1.1rem;
          font-weight: 500;
          margin-bottom: 0.5rem;
        }

        .tasks-container {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .task-card {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          overflow: hidden;
        }

        .task-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem;
          cursor: pointer;
          transition: background 0.2s;
        }

        .task-header:hover {
          background: #f7fafc;
        }

        .task-header-left {
          display: flex;
          align-items: center;
          gap: 0.75rem;
        }

        .task-header-right {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .status-badge {
          padding: 0.25rem 0.75rem;
          border-radius: 4px;
          font-size: 0.875rem;
          font-weight: 500;
        }

        .status-pending {
          background: #fef5e7;
          color: #8b7923;
        }

        .status-running {
          background: #e3f2fd;
          color: #1565c0;
          animation: pulse 2s infinite;
        }

        .status-completed {
          background: #c6f6d5;
          color: #22543d;
        }

        .status-failed {
          background: #fed7d7;
          color: #742a2a;
        }

        @keyframes pulse {
          0%, 100% { opacity: 1; }
          50% { opacity: 0.7; }
        }

        .technology-badge {
          padding: 0.25rem 0.75rem;
          background: #edf2f7;
          border-radius: 4px;
          font-size: 0.875rem;
          color: #2d3748;
        }

        .task-id {
          font-family: monospace;
          font-size: 0.875rem;
          color: #718096;
        }

        .expand-icon {
          color: #a0aec0;
          font-size: 0.75rem;
        }

        .task-details {
          padding: 1rem;
          background: #f7fafc;
          border-top: 1px solid #e2e8f0;
        }

        .detail-row {
          display: flex;
          gap: 0.75rem;
          margin-bottom: 0.75rem;
          font-size: 0.95rem;
        }

        .detail-row strong {
          color: #2d3748;
          min-width: 100px;
        }

        .detail-row code {
          background: #edf2f7;
          padding: 0.125rem 0.375rem;
          border-radius: 3px;
          font-size: 0.875rem;
          color: #2d3748;
        }

        .summary-section,
        .error-section {
          margin-top: 1rem;
          padding: 1rem;
          border-radius: 6px;
        }

        .summary-section {
          background: white;
          border: 1px solid #e2e8f0;
        }

        .error-section {
          background: #fed7d7;
          border: 1px solid #fc8181;
          color: #742a2a;
        }

        .summary-section strong,
        .error-section strong {
          display: block;
          margin-bottom: 0.5rem;
        }

        .results-section {
          margin-top: 1rem;
        }

        .results-section > strong {
          display: block;
          margin-bottom: 0.75rem;
          color: #2d3748;
        }

        .result-card {
          background: white;
          border: 1px solid #e2e8f0;
          border-radius: 6px;
          padding: 1rem;
          margin-bottom: 0.75rem;
        }

        .result-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 0.75rem;
          padding-bottom: 0.75rem;
          border-bottom: 1px solid #e2e8f0;
        }

        .agent-role {
          font-weight: 600;
          color: #2d3748;
        }

        .model-info {
          font-size: 0.875rem;
          color: #718096;
        }

        .result-error {
          padding: 0.75rem;
          background: #fed7d7;
          border-radius: 4px;
          color: #742a2a;
        }

        .result-data pre {
          background: #f7fafc;
          padding: 0.75rem;
          border-radius: 4px;
          overflow-x: auto;
          font-size: 0.875rem;
          line-height: 1.5;
          margin: 0;
        }

        .result-metadata {
          display: flex;
          gap: 1.5rem;
          margin-top: 0.75rem;
          padding-top: 0.75rem;
          border-top: 1px solid #e2e8f0;
          font-size: 0.875rem;
          color: #718096;
        }
      `}</style>
    </div>
  );
};

export default ResearchTaskList;
