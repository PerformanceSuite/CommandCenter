import React from 'react';
import { WorkflowNode } from './types';

interface NodeConfigPanelProps {
  node: WorkflowNode | null;
  onUpdate: (nodeId: string, updates: Partial<WorkflowNode['data']>) => void;
  onClose: () => void;
}

export const NodeConfigPanel: React.FC<NodeConfigPanelProps> = ({
  node,
  onUpdate,
  onClose,
}) => {
  if (!node) return null;

  const [inputs, setInputs] = React.useState(node.data.inputs);
  const [action, setAction] = React.useState(node.data.action);
  const [approvalRequired, setApprovalRequired] = React.useState(
    node.data.approvalRequired
  );

  const handleSave = () => {
    onUpdate(node.id, {
      action,
      inputs,
      approvalRequired,
    });
    onClose();
  };

  const handleAddInput = () => {
    const key = prompt('Input key:');
    if (key) {
      setInputs({ ...inputs, [key]: '' });
    }
  };

  const handleInputChange = (key: string, value: string) => {
    setInputs({ ...inputs, [key]: value });
  };

  const handleRemoveInput = (key: string) => {
    const newInputs = { ...inputs };
    delete newInputs[key];
    setInputs(newInputs);
  };

  return (
    <div
      style={{
        width: '320px',
        background: 'white',
        borderLeft: '1px solid #ddd',
        overflowY: 'auto',
        display: 'flex',
        flexDirection: 'column',
      }}
    >
      <div
        style={{
          padding: '1rem',
          borderBottom: '1px solid #ddd',
          background: '#f9f9f9',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
        }}
      >
        <h3 style={{ margin: 0, fontSize: '1.1rem' }}>Configure Node</h3>
        <button
          onClick={onClose}
          style={{
            background: 'none',
            border: 'none',
            fontSize: '20px',
            cursor: 'pointer',
            padding: '0 8px',
          }}
        >
          ×
        </button>
      </div>

      <div style={{ padding: '1rem', flex: 1 }}>
        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'block', fontWeight: 600, marginBottom: '4px' }}>
            Agent
          </label>
          <div style={{ color: '#666' }}>{node.data.agentName}</div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label
            style={{ display: 'block', fontWeight: 600, marginBottom: '4px' }}
            htmlFor="action"
          >
            Action
          </label>
          <input
            id="action"
            type="text"
            value={action}
            onChange={(e) => setAction(e.target.value)}
            style={{
              width: '100%',
              padding: '8px',
              border: '1px solid #ccc',
              borderRadius: '4px',
              fontSize: '14px',
            }}
          />
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '8px',
            }}
          >
            <label style={{ fontWeight: 600 }}>Inputs</label>
            <button
              onClick={handleAddInput}
              style={{
                padding: '4px 8px',
                background: '#4CAF50',
                color: 'white',
                border: 'none',
                borderRadius: '4px',
                cursor: 'pointer',
                fontSize: '12px',
              }}
            >
              + Add Input
            </button>
          </div>
          <div>
            {Object.entries(inputs).map(([key, value]) => (
              <div
                key={key}
                style={{
                  marginBottom: '8px',
                  padding: '8px',
                  background: '#f5f5f5',
                  borderRadius: '4px',
                }}
              >
                <div
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    marginBottom: '4px',
                  }}
                >
                  <span style={{ fontWeight: 600, fontSize: '13px' }}>{key}</span>
                  <button
                    onClick={() => handleRemoveInput(key)}
                    style={{
                      background: 'none',
                      border: 'none',
                      color: '#f44336',
                      cursor: 'pointer',
                      fontSize: '12px',
                    }}
                  >
                    Remove
                  </button>
                </div>
                <input
                  type="text"
                  value={value}
                  onChange={(e) => handleInputChange(key, e.target.value)}
                  placeholder="Value or template (e.g., {{ context.foo }})"
                  style={{
                    width: '100%',
                    padding: '6px',
                    border: '1px solid #ccc',
                    borderRadius: '4px',
                    fontSize: '13px',
                  }}
                />
              </div>
            ))}
            {Object.keys(inputs).length === 0 && (
              <div style={{ color: '#999', fontSize: '13px', fontStyle: 'italic' }}>
                No inputs configured
              </div>
            )}
          </div>
        </div>

        <div style={{ marginBottom: '1rem' }}>
          <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
            <input
              type="checkbox"
              checked={approvalRequired}
              onChange={(e) => setApprovalRequired(e.target.checked)}
              style={{ marginRight: '8px' }}
            />
            <span style={{ fontWeight: 600 }}>Require approval before execution</span>
          </label>
        </div>
      </div>

      <div
        style={{
          padding: '1rem',
          borderTop: '1px solid #ddd',
          display: 'flex',
          gap: '8px',
        }}
      >
        <button
          onClick={handleSave}
          style={{
            flex: 1,
            padding: '10px',
            background: '#4CAF50',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
            fontWeight: 600,
          }}
        >
          Save
        </button>
        <button
          onClick={onClose}
          style={{
            padding: '10px 20px',
            background: '#f5f5f5',
            border: '1px solid #ccc',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          Cancel
        </button>
      </div>
    </div>
  );
};
