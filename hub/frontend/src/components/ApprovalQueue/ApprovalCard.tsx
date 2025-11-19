import React from 'react';

interface Approval {
  id: string;
  workflowRunId: string;
  nodeId: string;
  requestedAt: string;
}

interface ApprovalCardProps {
  approval: Approval;
  onClick: () => void;
}

export const ApprovalCard: React.FC<ApprovalCardProps> = ({
  approval,
  onClick,
}) => {
  const requestedDate = new Date(approval.requestedAt);
  const timeAgo = Math.floor((Date.now() - requestedDate.getTime()) / 60000);

  return (
    <div
      onClick={onClick}
      style={{
        padding: '16px',
        background: '#fff3e0',
        border: '2px solid #FF9800',
        borderRadius: '8px',
        marginBottom: '12px',
        cursor: 'pointer',
        transition: 'all 0.2s',
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.boxShadow = '0 4px 8px rgba(0,0,0,0.1)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.boxShadow = 'none';
      }}
    >
      <div
        style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'start',
          marginBottom: '8px',
        }}
      >
        <div style={{ fontWeight: 600, fontSize: '15px' }}>
          ⚠️ Approval Required
        </div>
        <div style={{ fontSize: '12px', color: '#666' }}>
          {timeAgo === 0 ? 'Just now' : `${timeAgo}m ago`}
        </div>
      </div>
      <div style={{ fontSize: '13px', color: '#666', marginBottom: '4px' }}>
        Workflow Run: {approval.workflowRunId.substring(0, 8)}...
      </div>
      <div style={{ fontSize: '13px', color: '#666' }}>
        Node: {approval.nodeId}
      </div>
    </div>
  );
};
