import React, { useState } from 'react';
import { useApprovals } from '../../hooks/useApprovals';
import { ApprovalCard } from './ApprovalCard';
import { ApprovalDetail } from './ApprovalDetail';

export const ApprovalQueue: React.FC = () => {
  const { data: approvals, isLoading } = useApprovals('PENDING');
  const [selectedApprovalId, setSelectedApprovalId] = useState<string | null>(null);

  if (isLoading) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        Loading approvals...
      </div>
    );
  }

  return (
    <div style={{ padding: '2rem', maxWidth: '800px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ margin: 0, marginBottom: '8px' }}>Pending Approvals</h2>
        <p style={{ margin: 0, color: '#666' }}>
          {approvals?.length || 0} workflow(s) waiting for approval
        </p>
      </div>

      {approvals && approvals.length === 0 ? (
        <div
          style={{
            padding: '3rem',
            textAlign: 'center',
            background: '#f5f5f5',
            borderRadius: '8px',
            color: '#999',
          }}
        >
          No pending approvals
        </div>
      ) : (
        <div>
          {approvals?.map((approval) => (
            <ApprovalCard
              key={approval.id}
              approval={approval}
              onClick={() => setSelectedApprovalId(approval.id)}
            />
          ))}
        </div>
      )}

      {selectedApprovalId && (() => {
        const approval = approvals?.find((a) => a.id === selectedApprovalId);
        return approval ? (
          <ApprovalDetail
            approvalId={approval.id}
            workflowRunId={approval.workflowRunId}
            nodeId={approval.nodeId}
            onClose={() => setSelectedApprovalId(null)}
          />
        ) : null;
      })()}
    </div>
  );
};
