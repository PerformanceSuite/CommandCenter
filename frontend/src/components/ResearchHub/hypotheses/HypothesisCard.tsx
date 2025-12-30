import { HypothesisResponse } from '../../../services/intelligenceApi';
import { CATEGORY_LABELS, STATUS_LABELS, STATUS_COLORS } from '../../../types/hypothesis';

interface HypothesisCardProps {
  hypothesis: HypothesisResponse;
  isExpanded: boolean;
  onToggleExpand: () => void;
  onValidate: () => void;
  onDelete: () => void;
}

/**
 * HypothesisCard - Displays a single hypothesis with actions
 */
export function HypothesisCard({
  hypothesis,
  isExpanded,
  onToggleExpand,
  onValidate,
  onDelete,
}: HypothesisCardProps) {
  const getStatusColor = () => {
    const colorMap: Record<string, string> = {
      slate: 'bg-slate-500',
      blue: 'bg-blue-500 animate-pulse',
      green: 'bg-green-500',
      red: 'bg-red-500',
      amber: 'bg-amber-500',
      purple: 'bg-purple-500',
    };
    const colorName = STATUS_COLORS[hypothesis.status as keyof typeof STATUS_COLORS] || 'slate';
    return colorMap[colorName] || 'bg-slate-500';
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
      {/* Main Row */}
      <div className="flex items-center gap-4 p-4">
        {/* Status Indicator */}
        <div className={`w-3 h-3 rounded-full ${getStatusColor()}`} />

        {/* Hypothesis Info */}
        <div className="flex-1 min-w-0">
          <button
            onClick={onToggleExpand}
            className="text-left w-full"
          >
            <h3 className="text-base font-medium text-white truncate" title={hypothesis.statement}>
              {hypothesis.statement}
            </h3>
          </button>
          <div className="flex items-center gap-3 mt-1">
            <span className="text-xs px-2 py-0.5 rounded bg-slate-700 text-slate-300">
              {CATEGORY_LABELS[hypothesis.category as keyof typeof CATEGORY_LABELS] || hypothesis.category}
            </span>
            <span className={`text-xs px-2 py-0.5 rounded ${
              hypothesis.status === 'validated' ? 'bg-green-900/50 text-green-400' :
              hypothesis.status === 'invalidated' ? 'bg-red-900/50 text-red-400' :
              hypothesis.status === 'validating' ? 'bg-blue-900/50 text-blue-400' :
              hypothesis.status === 'needs_more_data' ? 'bg-amber-900/50 text-amber-400' :
              'bg-slate-700 text-slate-400'
            }`}>
              {STATUS_LABELS[hypothesis.status as keyof typeof STATUS_LABELS] || hypothesis.status}
            </span>
            <span className="text-xs text-slate-500">
              {hypothesis.evidence_count} evidence
            </span>
            <span className="text-xs text-slate-500">
              {hypothesis.debate_count} debates
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
            onClick={onToggleExpand}
            className="px-3 py-1.5 text-sm bg-slate-700 text-slate-300 rounded hover:bg-slate-600 transition-colors"
          >
            {isExpanded ? 'Collapse' : 'Expand'}
          </button>
          {canValidate && (
            <button
              onClick={onValidate}
              className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Validate
            </button>
          )}
        </div>
      </div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-slate-700/50 p-4 space-y-4">
          {/* Metadata Grid */}
          <div className="grid grid-cols-4 gap-4 text-sm">
            <div>
              <span className="text-slate-500">Impact:</span>
              <span className="ml-2 text-white capitalize">{hypothesis.impact}</span>
            </div>
            <div>
              <span className="text-slate-500">Risk:</span>
              <span className="ml-2 text-white capitalize">{hypothesis.risk}</span>
            </div>
            <div>
              <span className="text-slate-500">Created:</span>
              <span className="ml-2 text-white">
                {new Date(hypothesis.created_at).toLocaleDateString()}
              </span>
            </div>
            <div>
              <span className="text-slate-500">Updated:</span>
              <span className="ml-2 text-white">
                {new Date(hypothesis.updated_at).toLocaleDateString()}
              </span>
            </div>
          </div>

          {/* Actions Row */}
          <div className="flex justify-end gap-2 pt-2 border-t border-slate-700/50">
            <button
              onClick={onDelete}
              className="px-3 py-1.5 text-sm text-red-400 hover:text-red-300 transition-colors"
            >
              Delete
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

export default HypothesisCard;
