import React, { useState, useEffect } from 'react';
import { researchApi } from '../../services/researchApi';
import type { ResearchSummaryResponse } from '../../types/research';

const ResearchSummary: React.FC = () => {
  const [summary, setSummary] = useState<ResearchSummaryResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let isMounted = true;

    const loadData = async () => {
      try {
        const data = await researchApi.getResearchSummary();
        if (isMounted) {
          setSummary(data);
          setError(null);
        }
      } catch (err: any) {
        if (isMounted) {
          setError(err.response?.data?.detail || err.message || 'Failed to load summary');
        }
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    loadData();

    // Refresh every 10 seconds
    const interval = setInterval(loadData, 10000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, []);

  const loadSummary = async () => {
    try {
      const data = await researchApi.getResearchSummary();
      setSummary(data);
      setError(null);
    } catch (err: any) {
      setError(err.response?.data?.detail || err.message || 'Failed to load summary');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="research-summary">
        <h2>Research Summary</h2>
        <div className="loading-state">Loading summary...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="research-summary">
        <h2>Research Summary</h2>
        <div className="error-message">❌ {error}</div>
        <button className="btn-retry" onClick={loadSummary}>
          Retry
        </button>
      </div>
    );
  }

  if (!summary) return null;

  const completionRate = summary.total_tasks > 0
    ? (summary.completed_tasks / summary.total_tasks) * 100
    : 0;

  const failureRate = summary.total_tasks > 0
    ? (summary.failed_tasks / summary.total_tasks) * 100
    : 0;

  return (
    <div className="research-summary">
      <h2>Research Summary</h2>
      <p className="description">
        Overview of all research activities and performance metrics
      </p>

      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon">📋</div>
          <div className="stat-content">
            <div className="stat-value">{summary.total_tasks}</div>
            <div className="stat-label">Total Tasks</div>
          </div>
        </div>

        <div className="stat-card success">
          <div className="stat-icon">✅</div>
          <div className="stat-content">
            <div className="stat-value">{summary.completed_tasks}</div>
            <div className="stat-label">Completed</div>
            <div className="stat-percentage">{completionRate.toFixed(1)}%</div>
          </div>
        </div>

        <div className="stat-card error">
          <div className="stat-icon">❌</div>
          <div className="stat-content">
            <div className="stat-value">{summary.failed_tasks}</div>
            <div className="stat-label">Failed</div>
            {failureRate > 0 && (
              <div className="stat-percentage">{failureRate.toFixed(1)}%</div>
            )}
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">🤖</div>
          <div className="stat-content">
            <div className="stat-value">{summary.agents_deployed}</div>
            <div className="stat-label">Agents Deployed</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">⏱️</div>
          <div className="stat-content">
            <div className="stat-value">
              {summary.avg_execution_time_seconds.toFixed(1)}s
            </div>
            <div className="stat-label">Avg Execution Time</div>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon">💰</div>
          <div className="stat-content">
            <div className="stat-value">
              ${summary.total_cost_usd.toFixed(2)}
            </div>
            <div className="stat-label">Total Cost</div>
          </div>
        </div>
      </div>

      {summary.total_tasks > 0 && (
        <div className="progress-section">
          <h3>Task Completion Progress</h3>
          <div className="progress-bar-container">
            <div className="progress-bar">
              <div
                className="progress-fill completed"
                style={{ width: `${completionRate}%` }}
              />
              <div
                className="progress-fill failed"
                style={{ width: `${failureRate}%` }}
              />
            </div>
            <div className="progress-legend">
              <span className="legend-item">
                <span className="legend-color completed" />
                Completed ({summary.completed_tasks})
              </span>
              <span className="legend-item">
                <span className="legend-color failed" />
                Failed ({summary.failed_tasks})
              </span>
              <span className="legend-item">
                <span className="legend-color pending" />
                Pending ({summary.total_tasks - summary.completed_tasks - summary.failed_tasks})
              </span>
            </div>
          </div>
        </div>
      )}

      {summary.total_tasks === 0 && (
        <div className="empty-state">
          <p>No research tasks have been launched yet.</p>
          <p>Start by launching a Technology Deep Dive or Custom Agents.</p>
        </div>
      )}

      <div className="refresh-info">
        Auto-refreshing every 10 seconds
      </div>

      <style>{`
        .research-summary h2 {
          font-size: 1.5rem;
          font-weight: 600;
          margin-bottom: 0.5rem;
          color: #f1f5f9;
        }

        .description {
          font-size: 0.95rem;
          color: #94a3b8;
          margin-bottom: 2rem;
          line-height: 1.5;
        }

        .loading-state {
          text-align: center;
          padding: 3rem;
          color: #94a3b8;
        }

        .error-message {
          background: #7f1d1d;
          border: 1px solid #dc2626;
          color: #fecaca;
          padding: 1rem;
          border-radius: 6px;
          margin-bottom: 1rem;
        }

        .btn-retry {
          padding: 0.75rem 1.5rem;
          background: #3b82f6;
          border: none;
          color: white;
          border-radius: 6px;
          font-size: 1rem;
          cursor: pointer;
          transition: background 0.2s;
        }

        .btn-retry:hover {
          background: #2563eb;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
          margin-bottom: 2rem;
        }

        .stat-card {
          background: #0f172a;
          border: 2px solid #334155;
          border-radius: 8px;
          padding: 1.5rem;
          display: flex;
          align-items: center;
          gap: 1rem;
          transition: transform 0.2s, box-shadow 0.2s;
        }

        .stat-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.5);
        }

        .stat-card.success {
          border-color: #059669;
          background: linear-gradient(135deg, #0f172a 0%, #064e3b 100%);
        }

        .stat-card.error {
          border-color: #dc2626;
          background: linear-gradient(135deg, #0f172a 0%, #7f1d1d 100%);
        }

        .stat-icon {
          font-size: 2rem;
          opacity: 0.8;
        }

        .stat-content {
          flex: 1;
        }

        .stat-value {
          font-size: 2rem;
          font-weight: 700;
          color: #f1f5f9;
          line-height: 1;
          margin-bottom: 0.25rem;
        }

        .stat-label {
          font-size: 0.875rem;
          color: #94a3b8;
          font-weight: 500;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .stat-percentage {
          font-size: 0.875rem;
          color: #cbd5e1;
          margin-top: 0.25rem;
          font-weight: 600;
        }

        .progress-section {
          margin-top: 2rem;
          padding-top: 2rem;
          border-top: 1px solid #334155;
        }

        .progress-section h3 {
          font-size: 1.25rem;
          font-weight: 600;
          color: #f1f5f9;
          margin-bottom: 1rem;
        }

        .progress-bar-container {
          background: #0f172a;
          border: 1px solid #334155;
          border-radius: 8px;
          padding: 1.5rem;
        }

        .progress-bar {
          height: 40px;
          background: #1e293b;
          border-radius: 8px;
          overflow: hidden;
          display: flex;
          margin-bottom: 1rem;
        }

        .progress-fill {
          height: 100%;
          transition: width 0.5s ease;
        }

        .progress-fill.completed {
          background: linear-gradient(90deg, #10b981 0%, #059669 100%);
        }

        .progress-fill.failed {
          background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
        }

        .progress-legend {
          display: flex;
          gap: 2rem;
          justify-content: center;
          flex-wrap: wrap;
        }

        .legend-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          font-size: 0.875rem;
          color: #94a3b8;
        }

        .legend-color {
          width: 20px;
          height: 20px;
          border-radius: 4px;
        }

        .legend-color.completed {
          background: linear-gradient(90deg, #10b981 0%, #059669 100%);
        }

        .legend-color.failed {
          background: linear-gradient(90deg, #ef4444 0%, #dc2626 100%);
        }

        .legend-color.pending {
          background: #1e293b;
          border: 2px solid #475569;
        }

        .empty-state {
          text-align: center;
          padding: 3rem 1rem;
          color: #94a3b8;
          background: #1e293b;
          border-radius: 8px;
          margin-top: 2rem;
        }

        .empty-state p:first-child {
          font-size: 1.1rem;
          font-weight: 500;
          margin-bottom: 0.5rem;
        }

        .refresh-info {
          text-align: center;
          margin-top: 2rem;
          font-size: 0.875rem;
          color: #64748b;
        }

        @media (max-width: 768px) {
          .stats-grid {
            grid-template-columns: 1fr;
          }

          .progress-legend {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.75rem;
          }
        }
      `}</style>
    </div>
  );
};

export default ResearchSummary;
