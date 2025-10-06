import React from 'react';

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  label?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({
  size = 'md',
  className = '',
  label = 'Loading...'
}) => {
  const sizeClasses = {
    sm: 'h-4 w-4 border-2',
    md: 'h-8 w-8 border-3',
    lg: 'h-12 w-12 border-4',
  };

  return (
    <div
      className={`flex items-center justify-center ${className}`}
      role="status"
      aria-live="polite"
      aria-busy="true"
    >
      <div
        className={`${sizeClasses[size]} animate-spin rounded-full border-primary-600 border-t-transparent`}
        aria-hidden="true"
      />
      <span className="sr-only">{label}</span>
    </div>
  );
};
