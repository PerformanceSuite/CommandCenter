import React, { useMemo } from 'react';
import { Chart as ChartJS, ArcElement, Tooltip, Legend, CategoryScale, TooltipItem } from 'chart.js';
import { Pie } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(ArcElement, Tooltip, Legend, CategoryScale);

export interface StatusChartProps {
  statusData: Record<string, number>;
  title?: string;
  onStatusClick?: (status: string) => void;
  isLoading?: boolean;
}

const STATUS_COLORS: Record<string, string> = {
  discovery: '#3b82f6', // blue
  research: '#8b5cf6', // purple
  evaluation: '#f59e0b', // amber
  implementation: '#10b981', // green
  integrated: '#06b6d4', // cyan
  'production-ready': '#22c55e', // green
  prototype: '#eab308', // yellow
  beta: '#f97316', // orange
  pending: '#94a3b8', // slate
  'in-progress': '#3b82f6', // blue
  completed: '#22c55e', // green
  blocked: '#ef4444', // red
};

export const StatusChart: React.FC<StatusChartProps> = ({
  statusData,
  title = 'Status Distribution',
  onStatusClick,
  isLoading = false,
}) => {
  const chartData = useMemo(() => {
    const labels = Object.keys(statusData);
    const values = Object.values(statusData);
    const colors = labels.map((label) => STATUS_COLORS[label] || '#6b7280');

    return {
      labels: labels.map((label) => label.charAt(0).toUpperCase() + label.slice(1)),
      datasets: [
        {
          data: values,
          backgroundColor: colors,
          borderColor: '#ffffff',
          borderWidth: 2,
          hoverOffset: 4,
        },
      ],
    };
  }, [statusData]);

  const options = useMemo(
    () => ({
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: {
          position: 'right' as const,
          labels: {
            padding: 15,
            font: {
              size: 12,
            },
            usePointStyle: true,
          },
        },
        tooltip: {
          callbacks: {
            label: (context: TooltipItem<'pie'>) => {
              const label = context.label || '';
              const value = context.parsed || 0;
              const total = context.dataset.data.reduce((a: number, b: number) => a + b, 0);
              const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0';
              return `${label}: ${value} (${percentage}%)`;
            },
          },
        },
      },
      onClick: (_event: unknown, elements: { index: number }[]) => {
        if (elements.length > 0 && onStatusClick) {
          const index = elements[0].index;
          const status = Object.keys(statusData)[index];
          onStatusClick(status);
        }
      },
    }),
    [statusData, onStatusClick]
  );

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <div className="h-64 flex items-center justify-center">
          <div className="animate-pulse flex flex-col items-center space-y-4">
            <div className="w-48 h-48 bg-gray-200 rounded-full" />
            <div className="space-y-2">
              <div className="h-3 bg-gray-200 rounded w-32" />
              <div className="h-3 bg-gray-200 rounded w-24" />
              <div className="h-3 bg-gray-200 rounded w-28" />
            </div>
          </div>
        </div>
      </div>
    );
  }

  const hasData = Object.values(statusData).some((value) => value > 0);

  if (!hasData) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <h3 className="text-lg font-semibold mb-4">{title}</h3>
        <div className="h-64 flex items-center justify-center text-gray-500">
          <div className="text-center">
            <p className="mb-2">No data available</p>
            <p className="text-sm">Start adding items to see the distribution</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow p-6">
      <h3 className="text-lg font-semibold mb-4">{title}</h3>
      <div className="h-64">
        <Pie data={chartData} options={options} />
      </div>
      {onStatusClick && (
        <p className="text-xs text-gray-500 mt-4 text-center">
          Click on a segment to filter by status
        </p>
      )}
    </div>
  );
};
