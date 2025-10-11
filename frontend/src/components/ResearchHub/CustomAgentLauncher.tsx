import React, { useState, useEffect } from 'react';
import { researchApi } from '../../services/researchApi';
import type {
  AgentTaskRequest,
  MultiAgentLaunchRequest,
  AvailableModelsResponse,
} from '../../types/research';

const AGENT_ROLES = [
  { value: 'deep_researcher', label: 'Deep Researcher', description: 'Technical analysis and architecture research' },
  { value: 'integrator', label: 'Integrator', description: 'Integration feasibility assessment' },
  { value: 'monitor', label: 'Monitor', description: 'Current trends and community activity' },
  { value: 'comparator', label: 'Comparator', description: 'Technology comparison and benchmarking' },
  { value: 'strategist', label: 'Strategist', description: 'Strategic recommendations and roadmapping' },
];

const CustomAgentLauncher: React.FC = () => {
  const [agents, setAgents] = useState<AgentTaskRequest[]>([
    { role: 'deep_researcher', prompt: '' },
  ]);
  const [projectId, setProjectId] = useState(1);
  const [maxConcurrent, setMaxConcurrent] = useState(3);
  const [availableModels, setAvailableModels] = useState<AvailableModelsResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);

  useEffect(() => {
    loadAvailableModels();
  }, []);

  const loadAvailableModels = async () => {
    try {
      const models = await researchApi.getAvailableModels();
      setAvailableModels(models);
    } catch (err: any) {
      console.error('Failed to load models:', err);
    }
  };

  const handleAddAgent = () => {
    setAgents([...agents, { role: 'deep_researcher', prompt: '' }]);
  };

  const handleRemoveAgent = (index: number) => {
    setAgents(agents.filter((_, i) => i !== index));
  };

  const handleAgentChange = (index: number, field: keyof AgentTaskRequest, value: any) => {
    const updated = [...agents];
    updated[index] = { ...updated[index], [field]: value };
    setAgents(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const request: MultiAgentLaunchRequest = {
        tasks: agents.filter(a => a.prompt.trim() !== ''),
        max_concurrent: maxConcurrent,
        project_id: projectId,
      };

      const task = await researchApi.launchCustomAgents(request);
      setTaskId(task.task_id);

      // Reset form
      setAgents([{ role: 'deep_researcher', prompt: '' }]);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to launch agents');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="custom-agent-launcher">
      <h2>Custom Agent Launcher</h2>
      <p className="description">
        Launch multiple AI agents in parallel with full control over roles, prompts,
        and models. Perfect for complex research requiring specialized perspectives.
      </p>

      {taskId && (
        <div className="success-message">
          ✅ Agents launched successfully! Task ID: <strong>{taskId}</strong>
          <br />
          Check the <strong>Research Tasks</strong> tab to view progress.
        </div>
      )}

      {error && (
        <div className="error-message">
          ❌ {error}
        </div>
      )}

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label htmlFor="project-id">
            Project ID <span className="required">*</span>
          </label>
          <input
            id="project-id"
            type="number"
            value={projectId}
            onChange={(e) => setProjectId(parseInt(e.target.value))}
            min={1}
            required
            disabled={loading}
          />
        </div>

        <div className="form-group">
          <label htmlFor="max-concurrent">
            Max Concurrent Agents
          </label>
          <input
            id="max-concurrent"
            type="number"
            value={maxConcurrent}
            onChange={(e) => setMaxConcurrent(parseInt(e.target.value))}
            min={1}
            max={10}
            disabled={loading}
          />
          <small>Number of agents to run simultaneously (1-10)</small>
        </div>

        <div className="agents-section">
          <h3>Agent Tasks</h3>
          {agents.map((agent, index) => (
            <div key={index} className="agent-card">
              <div className="agent-header">
                <h4>Agent {index + 1}</h4>
                {agents.length > 1 && (
                  <button
                    type="button"
                    className="btn-remove-agent"
                    onClick={() => handleRemoveAgent(index)}
                    disabled={loading}
                  >
                    Remove
                  </button>
                )}
              </div>

              <div className="form-group">
                <label>Role</label>
                <select
                  value={agent.role}
                  onChange={(e) => handleAgentChange(index, 'role', e.target.value)}
                  disabled={loading}
                >
                  {AGENT_ROLES.map((role) => (
                    <option key={role.value} value={role.value}>
                      {role.label}
                    </option>
                  ))}
                </select>
                <small>
                  {AGENT_ROLES.find(r => r.value === agent.role)?.description}
                </small>
              </div>

              <div className="form-group">
                <label>
                  Prompt <span className="required">*</span>
                </label>
                <textarea
                  value={agent.prompt}
                  onChange={(e) => handleAgentChange(index, 'prompt', e.target.value)}
                  placeholder="What should this agent research? Be specific..."
                  rows={4}
                  required
                  disabled={loading}
                />
              </div>

              <div className="model-selection">
                <div className="form-group">
                  <label>Model (optional)</label>
                  <select
                    value={agent.model || ''}
                    onChange={(e) => handleAgentChange(index, 'model', e.target.value || undefined)}
                    disabled={loading || !availableModels}
                  >
                    <option value="">Default Model</option>
                    {availableModels && Object.entries(availableModels.providers).map(([provider, models]) => (
                      <optgroup key={provider} label={provider}>
                        {models.map((model) => (
                          <option key={model.model_id} value={model.model_id}>
                            {model.model_id} ({model.tier})
                          </option>
                        ))}
                      </optgroup>
                    ))}
                  </select>
                </div>

                <div className="form-group">
                  <label>Temperature</label>
                  <input
                    type="number"
                    value={agent.temperature ?? 0.7}
                    onChange={(e) => handleAgentChange(index, 'temperature', parseFloat(e.target.value))}
                    min={0}
                    max={2}
                    step={0.1}
                    disabled={loading}
                  />
                  <small>0 = deterministic, 2 = very creative</small>
                </div>

                <div className="form-group">
                  <label>Max Tokens</label>
                  <input
                    type="number"
                    value={agent.max_tokens ?? 4096}
                    onChange={(e) => handleAgentChange(index, 'max_tokens', parseInt(e.target.value))}
                    min={100}
                    max={32000}
                    step={100}
                    disabled={loading}
                  />
                </div>
              </div>
            </div>
          ))}

          <button
            type="button"
            className="btn-add-agent"
            onClick={handleAddAgent}
            disabled={loading}
          >
            + Add Agent
          </button>
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn-primary"
            disabled={loading || agents.every(a => !a.prompt.trim())}
          >
            {loading ? 'Launching Agents...' : `Launch ${agents.length} Agent${agents.length > 1 ? 's' : ''}`}
          </button>
        </div>
      </form>

      <style>{`
        .custom-agent-launcher h2 {
          font-size: 1.5rem;
          font-weight: 600;
          margin-bottom: 0.5rem;
          color: #1a202c;
        }

        .description {
          font-size: 0.95rem;
          color: #718096;
          margin-bottom: 1.5rem;
          line-height: 1.5;
        }

        .success-message {
          background: #c6f6d5;
          border: 1px solid #9ae6b4;
          color: #22543d;
          padding: 1rem;
          border-radius: 6px;
          margin-bottom: 1.5rem;
          line-height: 1.6;
        }

        .error-message {
          background: #fed7d7;
          border: 1px solid #fc8181;
          color: #742a2a;
          padding: 1rem;
          border-radius: 6px;
          margin-bottom: 1.5rem;
        }

        .form-group {
          margin-bottom: 1.5rem;
        }

        .form-group label {
          display: block;
          font-weight: 500;
          margin-bottom: 0.5rem;
          color: #2d3748;
        }

        .required {
          color: #e53e3e;
        }

        .form-group input[type="text"],
        .form-group input[type="number"],
        .form-group select,
        .form-group textarea {
          width: 100%;
          padding: 0.625rem;
          border: 1px solid #cbd5e0;
          border-radius: 6px;
          font-size: 1rem;
          transition: border-color 0.2s;
          font-family: inherit;
        }

        .form-group textarea {
          resize: vertical;
        }

        .form-group input:focus,
        .form-group select:focus,
        .form-group textarea:focus {
          outline: none;
          border-color: #3182ce;
          box-shadow: 0 0 0 3px rgba(49, 130, 206, 0.1);
        }

        .form-group input:disabled,
        .form-group select:disabled,
        .form-group textarea:disabled {
          background: #f7fafc;
          cursor: not-allowed;
        }

        .form-group small {
          display: block;
          margin-top: 0.25rem;
          font-size: 0.875rem;
          color: #718096;
        }

        .agents-section {
          margin-top: 2rem;
        }

        .agents-section h3 {
          font-size: 1.25rem;
          font-weight: 600;
          margin-bottom: 1rem;
          color: #2d3748;
        }

        .agent-card {
          background: #f7fafc;
          border: 1px solid #e2e8f0;
          border-radius: 8px;
          padding: 1.5rem;
          margin-bottom: 1rem;
        }

        .agent-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
          padding-bottom: 1rem;
          border-bottom: 1px solid #e2e8f0;
        }

        .agent-header h4 {
          font-size: 1.1rem;
          font-weight: 600;
          color: #2d3748;
          margin: 0;
        }

        .btn-remove-agent {
          padding: 0.5rem 1rem;
          background: #fed7d7;
          border: 1px solid #fc8181;
          color: #742a2a;
          border-radius: 6px;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s;
        }

        .btn-remove-agent:hover:not(:disabled) {
          background: #fc8181;
          color: white;
        }

        .btn-remove-agent:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .model-selection {
          display: grid;
          grid-template-columns: 2fr 1fr 1fr;
          gap: 1rem;
          margin-top: 1rem;
        }

        .btn-add-agent {
          width: 100%;
          padding: 0.75rem;
          background: #edf2f7;
          border: 2px dashed #cbd5e0;
          color: #2d3748;
          border-radius: 6px;
          font-size: 1rem;
          cursor: pointer;
          transition: all 0.2s;
          margin-top: 1rem;
        }

        .btn-add-agent:hover:not(:disabled) {
          background: #e2e8f0;
          border-color: #a0aec0;
        }

        .btn-add-agent:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .form-actions {
          margin-top: 2rem;
          padding-top: 1.5rem;
          border-top: 1px solid #e2e8f0;
        }

        .btn-primary {
          padding: 0.75rem 2rem;
          background: #3182ce;
          border: none;
          color: white;
          border-radius: 6px;
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }

        .btn-primary:hover:not(:disabled) {
          background: #2c5282;
        }

        .btn-primary:disabled {
          background: #cbd5e0;
          cursor: not-allowed;
        }

        @media (max-width: 768px) {
          .model-selection {
            grid-template-columns: 1fr;
          }
        }
      `}</style>
    </div>
  );
};

export default CustomAgentLauncher;
