import React, { useState } from 'react';
import TechnologyDeepDiveForm from './TechnologyDeepDiveForm';
import CustomAgentLauncher from './CustomAgentLauncher';
import ResearchTaskList from './ResearchTaskList';
import ResearchSummary from './ResearchSummary';
import ErrorBoundary from './ErrorBoundary';

type ActiveTab = 'deep-dive' | 'custom-agents' | 'task-list' | 'summary';

const ResearchHubView: React.FC = () => {
  const [activeTab, setActiveTab] = useState<ActiveTab>('deep-dive');

  return (
    <div className="research-hub-container">
      <div className="research-hub-header">
        <h1>Research Hub</h1>
        <p className="subtitle">
          Multi-agent AI research orchestration with technology monitoring
        </p>
      </div>

      {/* Tab Navigation */}
      <div className="tab-navigation">
        <button
          className={`tab-button ${activeTab === 'deep-dive' ? 'active' : ''}`}
          onClick={() => setActiveTab('deep-dive')}
        >
          Technology Deep Dive
        </button>
        <button
          className={`tab-button ${activeTab === 'custom-agents' ? 'active' : ''}`}
          onClick={() => setActiveTab('custom-agents')}
        >
          Custom Agents
        </button>
        <button
          className={`tab-button ${activeTab === 'task-list' ? 'active' : ''}`}
          onClick={() => setActiveTab('task-list')}
        >
          Research Tasks
        </button>
        <button
          className={`tab-button ${activeTab === 'summary' ? 'active' : ''}`}
          onClick={() => setActiveTab('summary')}
        >
          Summary
        </button>
      </div>

      {/* Tab Content */}
      <div className="tab-content">
        {activeTab === 'deep-dive' && (
          <ErrorBoundary>
            <TechnologyDeepDiveForm />
          </ErrorBoundary>
        )}
        {activeTab === 'custom-agents' && (
          <ErrorBoundary>
            <CustomAgentLauncher />
          </ErrorBoundary>
        )}
        {activeTab === 'task-list' && (
          <ErrorBoundary>
            <ResearchTaskList />
          </ErrorBoundary>
        )}
        {activeTab === 'summary' && (
          <ErrorBoundary>
            <ResearchSummary />
          </ErrorBoundary>
        )}
      </div>

      <style>{`
        .research-hub-container {
          padding: 2rem 2rem 2rem 2rem;
          max-width: 1400px;
          margin: 0;
        }

        .research-hub-header {
          margin-bottom: 2rem;
        }

        .research-hub-header h1 {
          font-size: 2rem;
          font-weight: 600;
          margin-bottom: 0.5rem;
          color: #f1f5f9;
        }

        .subtitle {
          font-size: 1rem;
          color: #94a3b8;
          margin: 0;
        }

        .tab-navigation {
          display: flex;
          gap: 0.5rem;
          border-bottom: 2px solid #334155;
          margin-bottom: 2rem;
        }

        .tab-button {
          padding: 0.75rem 1.5rem;
          background: none;
          border: none;
          border-bottom: 3px solid transparent;
          font-size: 1rem;
          font-weight: 500;
          color: #94a3b8;
          cursor: pointer;
          transition: all 0.2s;
          margin-bottom: -2px;
        }

        .tab-button:hover {
          color: #f1f5f9;
          background: #334155;
        }

        .tab-button.active {
          color: #2563eb;
          border-bottom-color: #2563eb;
        }

        .tab-content {
          background: #1e293b;
          border: 1px solid #334155;
          border-radius: 8px;
          box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3);
          padding: 2rem;
        }

        @media (max-width: 768px) {
          .research-hub-container {
            padding: 1rem;
          }

          .tab-navigation {
            overflow-x: auto;
          }

          .tab-button {
            font-size: 0.875rem;
            padding: 0.5rem 1rem;
            white-space: nowrap;
          }

          .tab-content {
            padding: 1rem;
          }
        }
      `}</style>
    </div>
  );
};

export default ResearchHubView;
