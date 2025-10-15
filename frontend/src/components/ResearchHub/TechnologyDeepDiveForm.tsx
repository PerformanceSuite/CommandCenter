import React, { useState } from 'react';
import { researchApi } from '../../services/researchApi';
import type { TechnologyDeepDiveRequest } from '../../types/research';

const TechnologyDeepDiveForm: React.FC = () => {
  const [technologyName, setTechnologyName] = useState('');
  const [projectId, setProjectId] = useState(1);
  const [researchQuestions, setResearchQuestions] = useState<string[]>(['']);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [taskId, setTaskId] = useState<string | null>(null);

  const handleAddQuestion = () => {
    setResearchQuestions([...researchQuestions, '']);
  };

  const handleRemoveQuestion = (index: number) => {
    setResearchQuestions(researchQuestions.filter((_, i) => i !== index));
  };

  const handleQuestionChange = (index: number, value: string) => {
    const updated = [...researchQuestions];
    updated[index] = value;
    setResearchQuestions(updated);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const request: TechnologyDeepDiveRequest = {
        technology_name: technologyName,
        project_id: projectId,
        research_questions: researchQuestions.filter(q => q.trim() !== ''),
      };

      const task = await researchApi.launchTechnologyDeepDive(request);
      setTaskId(task.task_id);

      // Reset form
      setTechnologyName('');
      setResearchQuestions(['']);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to launch research');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="tech-deep-dive-form">
      <h2>Technology Deep Dive</h2>
      <p className="description">
        Launch comprehensive research with 3 parallel AI agents: Deep Researcher,
        Integrator, and Monitor. Results include technical analysis, integration
        feasibility, and current trends.
      </p>

      {taskId && (
        <div className="success-message">
          ✅ Research launched successfully! Task ID: <strong>{taskId}</strong>
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
          <label htmlFor="technology-name">
            Technology Name <span className="required">*</span>
          </label>
          <input
            id="technology-name"
            type="text"
            value={technologyName}
            onChange={(e) => setTechnologyName(e.target.value)}
            placeholder="e.g., Rust, React, PostgreSQL"
            required
            disabled={loading}
          />
          <small>The technology you want to research in depth</small>
        </div>

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
          <small>The project this research belongs to</small>
        </div>

        <div className="form-group">
          <label>Research Questions (optional)</label>
          {researchQuestions.map((question, index) => (
            <div key={index} className="question-input-group">
              <input
                type="text"
                value={question}
                onChange={(e) => handleQuestionChange(index, e.target.value)}
                placeholder={`Question ${index + 1} (e.g., "What are the performance characteristics?")`}
                disabled={loading}
              />
              {researchQuestions.length > 1 && (
                <button
                  type="button"
                  className="btn-remove"
                  onClick={() => handleRemoveQuestion(index)}
                  disabled={loading}
                >
                  Remove
                </button>
              )}
            </div>
          ))}
          <button
            type="button"
            className="btn-secondary"
            onClick={handleAddQuestion}
            disabled={loading}
          >
            + Add Question
          </button>
          <small>Specific questions for the agents to investigate</small>
        </div>

        <div className="form-actions">
          <button
            type="submit"
            className="btn-primary"
            disabled={loading || !technologyName}
          >
            {loading ? 'Launching Research...' : 'Launch Deep Dive'}
          </button>
        </div>
      </form>

      <style>{`
        .tech-deep-dive-form h2 {
          font-size: 1.5rem;
          font-weight: 600;
          margin-bottom: 0.5rem;
          color: #f1f5f9;
        }

        .description {
          font-size: 0.95rem;
          color: #94a3b8;
          margin-bottom: 1.5rem;
          line-height: 1.5;
        }

        .success-message {
          background: #064e3b;
          border: 1px solid #059669;
          color: #d1fae5;
          padding: 1rem;
          border-radius: 6px;
          margin-bottom: 1.5rem;
          line-height: 1.6;
        }

        .error-message {
          background: #7f1d1d;
          border: 1px solid #dc2626;
          color: #fecaca;
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
          color: #f1f5f9;
        }

        .required {
          color: #ef4444;
        }

        .form-group input[type="text"],
        .form-group input[type="number"] {
          width: 100%;
          padding: 0.625rem;
          background: white;
          border: 1px solid #d1d5db;
          color: #1f2937;
          border-radius: 6px;
          font-size: 1rem;
          transition: border-color 0.2s;
        }

        .form-group input:focus {
          outline: none;
          border-color: #3b82f6;
          box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.2);
        }

        .form-group input:disabled {
          background: #f3f4f6;
          cursor: not-allowed;
          opacity: 0.6;
        }

        .form-group small {
          display: block;
          margin-top: 0.25rem;
          font-size: 0.875rem;
          color: #94a3b8;
        }

        .question-input-group {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 0.75rem;
        }

        .question-input-group input {
          flex: 1;
        }

        .btn-remove {
          padding: 0.625rem 1rem;
          background: #7f1d1d;
          border: 1px solid #dc2626;
          color: #fecaca;
          border-radius: 6px;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s;
          white-space: nowrap;
        }

        .btn-remove:hover:not(:disabled) {
          background: #991b1b;
          color: white;
        }

        .btn-remove:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .btn-secondary {
          padding: 0.625rem 1rem;
          background: #1e293b;
          border: 1px solid #334155;
          color: #f1f5f9;
          border-radius: 6px;
          font-size: 0.875rem;
          cursor: pointer;
          transition: all 0.2s;
          margin-bottom: 0.5rem;
        }

        .btn-secondary:hover:not(:disabled) {
          background: #334155;
        }

        .btn-secondary:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .form-actions {
          margin-top: 2rem;
          padding-top: 1.5rem;
          border-top: 1px solid #334155;
        }

        .btn-primary {
          padding: 0.75rem 2rem;
          background: #3b82f6;
          border: none;
          color: white;
          border-radius: 6px;
          font-size: 1rem;
          font-weight: 500;
          cursor: pointer;
          transition: background 0.2s;
        }

        .btn-primary:hover:not(:disabled) {
          background: #2563eb;
        }

        .btn-primary:disabled {
          background: #334155;
          cursor: not-allowed;
          opacity: 0.5;
        }
      `}</style>
    </div>
  );
};

export default TechnologyDeepDiveForm;
