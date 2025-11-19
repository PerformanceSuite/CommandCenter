import React, { useState } from 'react';
import { useApprovals } from '../../hooks/useApprovals';
import { ApprovalCard } from './ApprovalCard';

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

      {selectedApprovalId && (
        <div
          style={{
            position: 'fixed',
            top: 0,
            left: 0,
            right: 0,
            bottom: 0,
            background: 'rgba(0,0,0,0.5)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            zIndex: 1000,
          }}
          onClick={() => setSelectedApprovalId(null)}
        >
          <div
            style={{
              background: 'white',
              padding: '2rem',
              borderRadius: '8px',
              maxWidth: '500px',
              width: '90%',
            }}
            onClick={(e) => e.stopPropagation()}
          >
            <h3>Approval Details</h3>
            <p>Approval ID: {selectedApprovalId}</p>
            <p>Full detail view will be implemented in Task 27</p>
            <button
              onClick={() => setSelectedApprovalId(null)}
              style={{
                padding: '8px 16px',
                background: '#f5f5f5',
                border: '1px solid #ccc',
                borderRadius: '4px',
                cursor: 'pointer',
              }}
            >
              Close
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
