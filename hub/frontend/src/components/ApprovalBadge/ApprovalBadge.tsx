import React from 'react';
import { useApprovals } from '../../hooks/useApprovals';

interface ApprovalBadgeProps {
  onClick?: () => void;
}

export const ApprovalBadge: React.FC<ApprovalBadgeProps> = ({ onClick }) => {
  const { data: approvals } = useApprovals('PENDING');
  const count = approvals?.length || 0;

  if (count === 0) return null;

  return (
    <div
      onClick={onClick}
      style={{
        position: 'fixed',
        bottom: '24px',
        right: '24px',
        background: '#FF9800',
        color: 'white',
        padding: '12px 20px',
        borderRadius: '24px',
        boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
        cursor: 'pointer',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        fontWeight: 600,
        fontSize: '14px',
        transition: 'all 0.2s',
        zIndex: 999,
      }}
      onMouseEnter={(e) => {
        e.currentTarget.style.transform = 'scale(1.05)';
        e.currentTarget.style.boxShadow = '0 6px 16px rgba(0,0,0,0.4)';
      }}
      onMouseLeave={(e) => {
        e.currentTarget.style.transform = 'scale(1)';
        e.currentTarget.style.boxShadow = '0 4px 12px rgba(0,0,0,0.3)';
      }}
    >
      <span style={{ fontSize: '18px' }}>⚠️</span>
      <span>{count} Pending Approval{count !== 1 ? 's' : ''}</span>
    </div>
  );
};
