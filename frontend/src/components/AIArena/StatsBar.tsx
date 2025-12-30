import type { HypothesisStats } from '../../types/hypothesis';

interface StatsBarProps {
  stats: HypothesisStats | null;
  loading?: boolean;
}

export function StatsBar({ stats, loading }: StatsBarProps) {
  if (loading) {
    return (
      <div className="grid grid-cols-5 gap-4 mb-6">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="bg-slate-800/30 rounded-lg p-4 animate-pulse">
            <div className="h-8 bg-slate-700 rounded w-12 mb-2" />
            <div className="h-4 bg-slate-700 rounded w-20" />
          </div>
        ))}
      </div>
    );
  }

  if (!stats) return null;

  const statItems = [
    { label: 'Total', value: stats.total, color: 'text-white' },
    { label: 'Untested', value: stats.untested_count, color: 'text-slate-400' },
    { label: 'Validated', value: stats.validated_count, color: 'text-green-400' },
    { label: 'Invalidated', value: stats.invalidated_count, color: 'text-red-400' },
    { label: 'Needs Data', value: stats.needs_data_count, color: 'text-amber-400' },
  ];

  return (
    <div className="grid grid-cols-5 gap-4 mb-6">
      {statItems.map((item) => (
        <div
          key={item.label}
          className="bg-slate-800/30 border border-slate-700/50 rounded-lg p-4"
        >
          <div className={`text-2xl font-bold ${item.color}`}>{item.value}</div>
          <div className="text-sm text-slate-500">{item.label}</div>
        </div>
      ))}
    </div>
  );
}

export default StatsBar;
