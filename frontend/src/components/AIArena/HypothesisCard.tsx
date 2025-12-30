import { useState } from 'react';
import type { HypothesisSummary } from '../../types/hypothesis';
import { STATUS_COLORS, STATUS_LABELS, CATEGORY_LABELS } from '../../types/hypothesis';

interface HypothesisCardProps {
  hypothesis: HypothesisSummary;
  onValidate: (id: string) => void;
  onView: (id: string) => void;
  isValidating?: boolean;
}

export function HypothesisCard({
  hypothesis,
  onValidate,
  onView,
  isValidating = false,
}: HypothesisCardProps) {
  const [expanded, setExpanded] = useState(false);

  const getStatusColor = () => {
    const colors: Record<string, string> = {
      slate: 'bg-slate-500',
      blue: 'bg-blue-500 animate-pulse',
      green: 'bg-green-500',
      red: 'bg-red-500',
      amber: 'bg-amber-500',
      purple: 'bg-purple-500',
    };
    return colors[STATUS_COLORS[hypothesis.status]] || 'bg-slate-500';
  };

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-400';
    if (score >= 60) return 'text-amber-400';
    return 'text-slate-400';
  };

  const canValidate =
    hypothesis.status === 'untested' || hypothesis.status === 'needs_more_data';

  return (
    <div className="bg-slate-800/30 border border-slate-700/50 rounded-lg hover:bg-slate-800/50 hover:border-slate-600 transition-all">
      <div className="flex items-center gap-4 p-4">
        {/* Status Indicator */}
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${getStatusColor()}`} />
        </div>

        {/* Hypothesis Info */}
        <div className="flex-1 min-w-0">
          <h3 className="text-base font-medium text-white truncate" title={hypothesis.statement}>
            {hypothesis.statement}
          </h3>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-300">
              {CATEGORY_LABELS[hypothesis.category]}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded ${
              hypothesis.status === 'validated' ? 'bg-green-900/50 text-green-400' :
              hypothesis.status === 'invalidated' ? 'bg-red-900/50 text-red-400' :
              hypothesis.status === 'validating' ? 'bg-blue-900/50 text-blue-400' :
              'bg-slate-700 text-slate-400'
            }`}>
              {STATUS_LABELS[hypothesis.status]}
            </span>
            <span className="text-xs text-slate-500">
              {hypothesis.evidence_count} evidence
            </span>
          </div>
        </div>

        {/* Priority Score */}
        <div className="text-right">
          <div className={`text-lg font-bold ${getScoreColor(hypothesis.priority_score)}`}>
            {hypothesis.priority_score.toFixed(0)}
          </div>
          <div className="text-xs text-slate-500">Priority</div>
        </div>

        {/* Validation Score (if validated) */}
        {hypothesis.validation_score !== null && (
          <div className="text-right">
            <div className={`text-lg font-bold ${getScoreColor(hypothesis.validation_score)}`}>
              {hypothesis.validation_score.toFixed(0)}%
            </div>
            <div className="text-xs text-slate-500">Confidence</div>
          </div>
        )}

        {/* Actions */}
        <div className="flex gap-2">
          <button
            onClick={() => onView(hypothesis.id)}
            className="px-3 py-1.5 text-sm bg-slate-700 text-slate-300 rounded hover:bg-slate-600 transition-colors"
          >
            View
          </button>
          {canValidate && (
            <button
              onClick={() => onValidate(hypothesis.id)}
              disabled={isValidating}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isValidating ? 'Validating...' : 'Validate'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default HypothesisCard;
