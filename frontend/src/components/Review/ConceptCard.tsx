import { CheckCircle2, XCircle, FileText } from 'lucide-react';
import type { Concept } from '../../types/review';

interface ConceptCardProps {
  concept: Concept;
  selected: boolean;
  onToggleSelect: () => void;
  onApprove: () => void;
  onReject: () => void;
  disabled?: boolean;
}

const CONFIDENCE_COLORS = {
  high: 'bg-green-500',
  medium: 'bg-yellow-500',
  low: 'bg-red-500',
};

const TYPE_COLORS: Record<string, string> = {
  product: 'bg-blue-500',
  feature: 'bg-purple-500',
  module: 'bg-cyan-500',
  process: 'bg-orange-500',
  technology: 'bg-green-500',
  framework: 'bg-pink-500',
  methodology: 'bg-indigo-500',
  other: 'bg-gray-500',
};

export function ConceptCard({
  concept,
  selected,
  onToggleSelect,
  onApprove,
  onReject,
  disabled,
}: ConceptCardProps) {
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
          <div className="flex items-center gap-2 mb-2">
            <h3 className="text-lg font-semibold text-white truncate">{concept.name}</h3>
            <span
              className={`px-2 py-0.5 text-xs font-medium rounded-full text-white ${
                TYPE_COLORS[concept.concept_type] || TYPE_COLORS.other
              }`}
            >
              {concept.concept_type}
            </span>
            <div className="flex items-center gap-1 ml-2">
              <div className={`w-2 h-2 rounded-full ${CONFIDENCE_COLORS[concept.confidence]}`} />
              <span className="text-xs text-gray-400">{concept.confidence}</span>
            </div>
          </div>

          {/* Definition */}
          {concept.definition && (
            <p className="text-gray-300 text-sm mb-2 line-clamp-2">{concept.definition}</p>
          )}

          {/* Metadata */}
          <div className="flex items-center gap-4 text-xs text-gray-500">
            {concept.domain && (
              <span className="bg-slate-700 px-2 py-1 rounded">Domain: {concept.domain}</span>
            )}
            {concept.source_document_path && (
              <span className="flex items-center gap-1">
                <FileText className="w-3 h-3" />
                {concept.source_document_path}
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
