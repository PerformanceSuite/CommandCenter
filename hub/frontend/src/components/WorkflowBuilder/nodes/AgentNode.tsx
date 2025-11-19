import React from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { AgentNodeData } from '../types';

export const AgentNode: React.FC<NodeProps<AgentNodeData>> = ({
  data,
  selected,
}) => {
  return (
    <div
      style={{
        minWidth: '180px',
        background: 'white',
        border: `2px solid ${selected ? '#2196F3' : '#4CAF50'}`,
        borderRadius: '8px',
        boxShadow: selected
          ? '0 0 0 2px rgba(33, 150, 243, 0.3)'
          : '0 2px 4px rgba(0,0,0,0.1)',
      }}
    >
      <Handle type="target" position={Position.Top} />

      <div
        style={{
          padding: '8px 12px',
          background: '#4CAF50',
          color: 'white',
          borderRadius: '6px 6px 0 0',
          fontWeight: 600,
          fontSize: '14px',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <span>{data.agentName}</span>
        {data.approvalRequired && (
          <span
            style={{
              background: '#FF9800',
              padding: '2px 6px',
              borderRadius: '4px',
              fontSize: '11px',
            }}
          >
            ⚠️ Approval
          </span>
        )}
      </div>

      <div style={{ padding: '12px' }}>
        <div style={{ fontSize: '13px', color: '#666', marginBottom: '4px' }}>
          {data.action}
        </div>
        {Object.keys(data.inputs).length > 0 && (
          <div style={{ fontSize: '11px', color: '#999' }}>
            {Object.keys(data.inputs).length} input(s)
          </div>
        )}
      </div>

      <Handle type="source" position={Position.Bottom} />
    </div>
  );
};
