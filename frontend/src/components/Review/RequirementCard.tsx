import { CheckCircle2, XCircle, FileText, Tag } from 'lucide-react';
import type { Requirement } from '../../types/review';

interface RequirementCardProps {
  requirement: Requirement;
  selected: boolean;
  onToggleSelect: () => void;
  onApprove: () => void;
  onReject: () => void;
  disabled?: boolean;
}

const TYPE_COLORS: Record<string, string> = {
  functional: 'bg-blue-500',
  nonFunctional: 'bg-purple-500',
  constraint: 'bg-orange-500',
  dependency: 'bg-cyan-500',
  outcome: 'bg-green-500',
};

const PRIORITY_COLORS: Record<string, string> = {
  critical: 'bg-red-500',
  high: 'bg-orange-500',
  medium: 'bg-yellow-500',
  low: 'bg-green-500',
  unknown: 'bg-gray-500',
};

export function RequirementCard({
  requirement,
  selected,
  onToggleSelect,
  onApprove,
  onReject,
  disabled,
}: RequirementCardProps) {
  return (
    <div
      className={`bg-slate-800 rounded-lg p-4 border-2 transition-colors ${
        selected ? 'border-blue-500' : 'border-transparent'
      }`}
    >
      <div className="flex items-start gap-4">
        {/* Checkbox */}
        <input
          type="checkbox"
          checked={selected}
          onChange={onToggleSelect}
          disabled={disabled}
          className="mt-1 w-5 h-5 rounded border-gray-600 bg-slate-700 text-blue-500 focus:ring-blue-500"
        />

        {/* Content */}
        <div className="flex-1 min-w-0">
          {/* Header */}
          <div className="flex items-center gap-2 mb-2 flex-wrap">
            <span className="px-2 py-1 bg-slate-700 text-white text-sm font-mono rounded">
              {requirement.req_id}
            </span>
            <span
              className={`px-2 py-0.5 text-xs font-medium rounded-full text-white ${
                TYPE_COLORS[requirement.req_type] || 'bg-gray-500'
              }`}
            >
              {requirement.req_type}
            </span>
            <span
              className={`px-2 py-0.5 text-xs font-medium rounded-full text-white ${
                PRIORITY_COLORS[requirement.priority] || PRIORITY_COLORS.unknown
              }`}
            >
              {requirement.priority}
            </span>
          </div>

          {/* Text */}
          <p className="text-gray-300 text-sm mb-2">{requirement.text}</p>

          {/* Metadata */}
          <div className="flex items-center gap-4 text-xs text-gray-500 flex-wrap">
            {requirement.source_concept && (
              <span className="flex items-center gap-1">
                <Tag className="w-3 h-3" />
                {requirement.source_concept}
              </span>
            )}
            {requirement.source_document_path && (
              <span className="flex items-center gap-1">
                <FileText className="w-3 h-3" />
                {requirement.source_document_path}
              </span>
            )}
          </div>
        </div>

        {/* Actions */}
        <div className="flex items-center gap-2">
          <button
            onClick={onApprove}
            disabled={disabled}
            className="p-2 bg-green-600 hover:bg-green-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
            title="Approve"
          >
            <CheckCircle2 className="w-5 h-5" />
          </button>
          <button
            onClick={onReject}
            disabled={disabled}
            className="p-2 bg-red-600 hover:bg-red-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
            title="Reject"
          >
            <XCircle className="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  );
}
