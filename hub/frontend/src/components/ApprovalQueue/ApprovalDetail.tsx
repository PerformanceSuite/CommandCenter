import React, { useState } from 'react';
import { useApproveWorkflow, useRejectWorkflow } from '../../hooks/useApprovals';

interface ApprovalDetailProps {
  approvalId: string;
  workflowRunId: string;
  nodeId: string;
  onClose: () => void;
}

export const ApprovalDetail: React.FC<ApprovalDetailProps> = ({
  approvalId,
  workflowRunId,
  nodeId,
  onClose,
}) => {
  const [notes, setNotes] = useState('');
  const approveWorkflow = useApproveWorkflow();
  const rejectWorkflow = useRejectWorkflow();

  const handleApprove = async () => {
    if (confirm('Are you sure you want to approve this workflow step?')) {
      try {
        await approveWorkflow.mutateAsync({ approvalId, notes });
        alert('Workflow approved successfully!');
        onClose();
      } catch (error: any) {
        alert(`Failed to approve: ${error.message}`);
      }
    }
  };

  const handleReject = async () => {
    if (!notes.trim()) {
      alert('Please provide a reason for rejection');
      return;
    }

    if (confirm('Are you sure you want to reject this workflow step?')) {
      try {
        await rejectWorkflow.mutateAsync({ approvalId, notes });
        alert('Workflow rejected');
        onClose();
      } catch (error: any) {
        alert(`Failed to reject: ${error.message}`);
      }
    }
  };

  return (
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
      onClick={onClose}
    >
      <div
        style={{
          background: 'white',
          padding: 0,
          borderRadius: '8px',
          maxWidth: '600px',
          width: '90%',
          maxHeight: '80vh',
          display: 'flex',
          flexDirection: 'column',
        }}
        onClick={(e) => e.stopPropagation()}
      >
        <div
          style={{
            padding: '1.5rem',
            borderBottom: '1px solid #ddd',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
          }}
        >
          <h3 style={{ margin: 0 }}>⚠️ Approval Required</h3>
          <button
            onClick={onClose}
            style={{
              background: 'none',
              border: 'none',
              fontSize: '24px',
              cursor: 'pointer',
              padding: '0 8px',
            }}
          >
            ×
          </button>
        </div>

        <div style={{ padding: '1.5rem', flex: 1, overflowY: 'auto' }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ fontWeight: 600, marginBottom: '4px' }}>Workflow Run</div>
            <div
              style={{
                padding: '8px',
                background: '#f5f5f5',
                borderRadius: '4px',
                fontSize: '14px',
                fontFamily: 'monospace',
              }}
            >
              {workflowRunId}
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ fontWeight: 600, marginBottom: '4px' }}>Node ID</div>
            <div
              style={{
                padding: '8px',
                background: '#f5f5f5',
                borderRadius: '4px',
                fontSize: '14px',
                fontFamily: 'monospace',
              }}
            >
              {nodeId}
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <label
              style={{ fontWeight: 600, display: 'block', marginBottom: '8px' }}
              htmlFor="notes"
            >
              Notes (optional for approval, required for rejection)
            </label>
            <textarea
              id="notes"
              value={notes}
              onChange={(e) => setNotes(e.target.value)}
              placeholder="Add notes about your decision..."
              rows={4}
              style={{
                width: '100%',
                padding: '8px',
                border: '1px solid #ccc',
                borderRadius: '4px',
                fontSize: '14px',
                fontFamily: 'inherit',
                resize: 'vertical',
              }}
            />
          </div>

          <div
            style={{
              padding: '12px',
              background: '#fff3e0',
              border: '1px solid #FF9800',
              borderRadius: '4px',
              fontSize: '13px',
            }}
          >
            <strong>⚠️ Important:</strong> Approving this step will allow the workflow to
            continue execution. Rejecting will stop the workflow.
          </div>
        </div>

        <div
          style={{
            padding: '1.5rem',
            borderTop: '1px solid #ddd',
            display: 'flex',
            gap: '12px',
            justifyContent: 'flex-end',
          }}
        >
          <button
            onClick={handleReject}
            disabled={rejectWorkflow.isPending}
            style={{
              padding: '10px 20px',
              background: '#f44336',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: rejectWorkflow.isPending ? 'not-allowed' : 'pointer',
              fontWeight: 600,
              opacity: rejectWorkflow.isPending ? 0.6 : 1,
            }}
          >
            {rejectWorkflow.isPending ? 'Rejecting...' : 'Reject'}
          </button>
          <button
            onClick={handleApprove}
            disabled={approveWorkflow.isPending}
            style={{
              padding: '10px 20px',
              background: '#4CAF50',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: approveWorkflow.isPending ? 'not-allowed' : 'pointer',
              fontWeight: 600,
              opacity: approveWorkflow.isPending ? 0.6 : 1,
            }}
          >
            {approveWorkflow.isPending ? 'Approving...' : 'Approve'}
          </button>
        </div>
      </div>
    </div>
  );
};
