import React from 'react';
import { LucideIcon } from 'lucide-react';

export interface MetricCardProps {
  label: string;
  value: number | string;
  icon: LucideIcon;
  color: string;
  trend?: {
    value: number;
    isPositive: boolean;
  };
  subtitle?: string;
  onClick?: () => void;
  isLoading?: boolean;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  icon: Icon,
  color,
  trend,
  subtitle,
  onClick,
  isLoading = false,
}) => {
  const baseClasses = 'bg-slate-800/50 border border-slate-700/50 rounded-lg shadow p-6 transition-all duration-200';
  const clickableClasses = onClick ? 'cursor-pointer hover:shadow-lg hover:scale-105 hover:bg-slate-800/70' : '';

  if (isLoading) {
    return (
      <div className={`${baseClasses} animate-pulse`}>
        <div className="flex items-center justify-between">
          <div className="flex-1">
            <div className="h-4 bg-slate-700 rounded w-24 mb-3" />
            <div className="h-8 bg-slate-700 rounded w-16" />
          </div>
          <div className={`${color} p-3 rounded-lg opacity-50`}>
            <div className="w-6 h-6 bg-white/30 rounded" />
          </div>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`${baseClasses} ${clickableClasses}`}
      onClick={onClick}
      role={onClick ? 'button' : 'region'}
      tabIndex={onClick ? 0 : undefined}
      onKeyDown={
        onClick
          ? (e) => {
              if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                onClick();
              }
            }
          : undefined
      }
      aria-label={`${label}: ${value}`}
    >
      <div className="flex items-center justify-between">
        <div className="flex-1">
          <p className="text-sm font-medium text-slate-400">{label}</p>
          <p className="text-3xl font-bold mt-2 text-white" aria-live="polite">
            {value}
          </p>
          {subtitle && <p className="text-xs text-slate-500 mt-1">{subtitle}</p>}
          {trend && (
            <div className="flex items-center mt-2">
              <span
                className={`text-sm font-medium ${
                  trend.isPositive ? 'text-green-400' : 'text-red-400'
                }`}
              >
                {trend.isPositive ? '+' : ''}
                {trend.value}%
              </span>
              <span className="text-xs text-slate-500 ml-2">vs last period</span>
            </div>
          )}
        </div>
        <div className={`${color} p-3 rounded-lg text-white`}>
          <Icon size={24} aria-hidden="true" />
        </div>
      </div>
    </div>
  );
};
