import React from 'react';
import { useAgents } from '../../hooks/useAgents';

interface Agent {
  id: string;
  name: string;
  type: string;
  description?: string;
  capabilities: Array<{ name: string }>;
}

interface AgentPaletteProps {
  projectId: number;
  onDragStart: (event: React.DragEvent, agent: Agent) => void;
}

export const AgentPalette: React.FC<AgentPaletteProps> = ({
  projectId,
  onDragStart,
}) => {
  const { data: agents, isLoading } = useAgents(projectId);

  if (isLoading) {
    return (
      <div style={{ width: '280px', padding: '2rem', textAlign: 'center' }}>
        Loading agents...
      </div>
    );
  }

  return (
    <div
      style={{
        width: '280px',
        background: 'white',
        borderRight: '1px solid #ddd',
        overflowY: 'auto',
      }}
    >
      <h3
        style={{
          padding: '1rem',
          margin: 0,
          fontSize: '1.1rem',
          borderBottom: '1px solid #ddd',
          background: '#f9f9f9',
        }}
      >
        Available Agents
      </h3>
      <div style={{ padding: '0.5rem' }}>
        {agents?.map((agent) => (
          <div
            key={agent.id}
            draggable
            onDragStart={(e) => onDragStart(e, agent)}
            style={{
              display: 'flex',
              gap: '12px',
              padding: '12px',
              marginBottom: '8px',
              background: '#f5f5f5',
              border: '1px solid #ddd',
              borderRadius: '6px',
              cursor: 'grab',
              transition: 'all 0.2s',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = '#e8f5e9';
              e.currentTarget.style.borderColor = '#4CAF50';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = '#f5f5f5';
              e.currentTarget.style.borderColor = '#ddd';
            }}
          >
            <div style={{ fontSize: '24px' }}>🤖</div>
            <div style={{ flex: 1, minWidth: 0 }}>
              <div
                style={{
                  fontWeight: 600,
                  fontSize: '14px',
                  marginBottom: '2px',
                }}
              >
                {agent.name}
              </div>
              <div
                style={{
                  fontSize: '11px',
                  color: '#666',
                  textTransform: 'uppercase',
                }}
              >
                {agent.type}
              </div>
              {agent.description && (
                <div
                  style={{
                    fontSize: '12px',
                    color: '#888',
                    marginTop: '4px',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                  }}
                >
                  {agent.description}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};
