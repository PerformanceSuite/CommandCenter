import React, { useState } from 'react';
import { FileText, Tag, Link as LinkIcon, ChevronDown, ChevronUp } from 'lucide-react';
import type { KnowledgeSearchResult as SearchResult } from '../../types/knowledge';

interface KnowledgeSearchResultProps {
  result: SearchResult;
  searchQuery: string;
  onTechnologyClick?: (technologyId: number) => void;
}

export const KnowledgeSearchResult: React.FC<KnowledgeSearchResultProps> = ({
  result,
  searchQuery,
  onTechnologyClick,
}) => {
  const [showContext, setShowContext] = useState(false);

  const relevancePercentage = Math.round(result.score * 100);
  const relevanceColor =
    relevancePercentage >= 80
      ? 'bg-green-100 text-green-800'
      : relevancePercentage >= 60
      ? 'bg-blue-100 text-blue-800'
      : 'bg-yellow-100 text-yellow-800';

  const highlightQuery = (text: string): React.ReactNode => {
    if (!searchQuery.trim()) return text;

    const regex = new RegExp(`(${searchQuery.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')})`, 'gi');
    const parts = text.split(regex);

    return parts.map((part, index) =>
      regex.test(part) ? (
        <mark key={index} className="bg-yellow-200 font-semibold">
          {part}
        </mark>
      ) : (
        <span key={index}>{part}</span>
      )
    );
  };

  return (
    <div className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow">
      <div className="flex items-start justify-between mb-3">
        <div className="flex items-start gap-2 flex-1">
          <FileText className="text-gray-400 mt-1 flex-shrink-0" size={18} />
          <div className="flex-1 min-w-0">
            <h3 className="font-semibold text-gray-900 truncate">{result.title}</h3>
            {result.source_file && (
              <p className="text-sm text-gray-500 truncate">{result.source_file}</p>
            )}
          </div>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0 ml-4">
          <span className={`px-2 py-1 rounded text-xs font-medium ${relevanceColor}`}>
            {relevancePercentage}% match
          </span>
        </div>
      </div>

      <div className="mb-3">
        <p className="text-gray-800 leading-relaxed">{highlightQuery(result.content)}</p>
      </div>

      <div className="flex items-center gap-3 flex-wrap">
        <div className="flex items-center gap-1 text-sm">
          <Tag className="text-gray-400" size={14} />
          <span className="px-2 py-0.5 bg-gray-100 text-gray-700 rounded text-xs font-medium">
            {result.category}
          </span>
        </div>

        {result.technology_id && (
          <button
            onClick={() => onTechnologyClick?.(result.technology_id!)}
            className="flex items-center gap-1 text-sm text-primary-600 hover:text-primary-700 hover:underline"
          >
            <LinkIcon size={14} />
            <span>View Technology</span>
          </button>
        )}

        {result.metadata && Object.keys(result.metadata).length > 0 && (
          <button
            onClick={() => setShowContext(!showContext)}
            className="flex items-center gap-1 text-sm text-gray-600 hover:text-gray-800 ml-auto"
          >
            {showContext ? (
              <>
                <ChevronUp size={14} />
                <span>Hide Context</span>
              </>
            ) : (
              <>
                <ChevronDown size={14} />
                <span>View Context</span>
              </>
            )}
          </button>
        )}
      </div>

      {showContext && result.metadata && (
        <div className="mt-3 pt-3 border-t border-gray-200">
          <h4 className="text-xs font-semibold text-gray-700 mb-2">Metadata</h4>
          <div className="grid grid-cols-2 gap-2 text-xs">
            {Object.entries(result.metadata).map(([key, value]) => (
              <div key={key} className="flex flex-col">
                <span className="text-gray-500 capitalize">
                  {key.replace(/_/g, ' ')}:
                </span>
                <span className="text-gray-800 font-medium">
                  {typeof value === 'object' ? JSON.stringify(value) : String(value)}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};
