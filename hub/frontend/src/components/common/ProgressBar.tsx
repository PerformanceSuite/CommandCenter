import React from 'react';

interface ProgressBarProps {
  value: number; // 0-100
  label?: string;
  status?: 'success' | 'error' | 'running';
}

export const ProgressBar: React.FC<ProgressBarProps> = ({
  value,
  label,
  status = 'running'
}) => {
  const clampedValue = Math.max(0, Math.min(100, value));

  const getColorClass = () => {
    switch (status) {
      case 'success':
        return 'bg-green-500';
      case 'error':
        return 'bg-red-500';
      case 'running':
      default:
        return 'bg-blue-500';
    }
  };

  return (
    <div className="w-full my-4">
      <div className="w-full h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full ${getColorClass()} transition-all duration-300 ease-out`}
          style={{ width: `${clampedValue}%` }}
        />
      </div>
      {label && (
        <div className="mt-2 text-sm text-gray-300">{label}</div>
      )}
      <div className="mt-1 text-xs text-gray-400 text-right">{clampedValue}%</div>
    </div>
  );
};
