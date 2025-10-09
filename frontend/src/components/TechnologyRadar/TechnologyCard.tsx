import React, { memo, useMemo, useState } from 'react';
import type { Technology } from '../../types/technology';
import { TrendingUp, Beaker, TestTube, Rocket, Edit2, Trash2, ExternalLink, LucideIcon } from 'lucide-react';

interface TechnologyCardProps {
  technology: Technology;
  onEdit?: (technology: Technology) => void;
  onDelete?: (technology: Technology) => void;
}

const statusConfig: Record<string, { label: string; icon: LucideIcon; color: string }> = {
  discovery: { label: 'Discovery', icon: Beaker, color: 'bg-purple-100 text-purple-700' },
  research: { label: 'Research', icon: TestTube, color: 'bg-blue-100 text-blue-700' },
  evaluation: { label: 'Evaluation', icon: TrendingUp, color: 'bg-yellow-100 text-yellow-700' },
  implementation: { label: 'Implementation', icon: Rocket, color: 'bg-orange-100 text-orange-700' },
  integrated: { label: 'Integrated', icon: Rocket, color: 'bg-green-100 text-green-700' },
  archived: { label: 'Archived', icon: Beaker, color: 'bg-gray-100 text-gray-700' },
};

export const TechnologyCard: React.FC<TechnologyCardProps> = memo(({ technology, onEdit, onDelete }) => {
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);
  const [expanded, setExpanded] = useState(false);

  const status = statusConfig[technology.status] || statusConfig.discovery;
  const StatusIcon = status.icon;

  // Memoize the relevance width calculation
  const relevanceWidth = useMemo(
    () => `${technology.relevance_score}%`,
    [technology.relevance_score]
  );

  // Memoize ARIA label for accessibility
  const cardAriaLabel = useMemo(
    () => `${technology.title} by ${technology.vendor || 'Unknown vendor'}, ${status.label} status, relevance ${technology.relevance_score} out of 100`,
    [technology.title, technology.vendor, status.label, technology.relevance_score]
  );

  // Parse tags
  const tags = useMemo(() => {
    if (!technology.tags) return [];
    return technology.tags.split(',').map(t => t.trim()).filter(Boolean);
  }, [technology.tags]);

  const handleDelete = () => {
    if (onDelete) {
      onDelete(technology);
      setShowDeleteConfirm(false);
    }
  };

  return (
    <article
      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow bg-white"
      aria-label={cardAriaLabel}
      role="article"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-lg">{technology.title}</h3>
          {technology.vendor && (
            <p className="text-sm text-gray-500">{technology.vendor}</p>
          )}
        </div>
        <div className="flex items-center gap-2">
          <div
            className={`${status.color} px-2 py-1 rounded-full flex items-center gap-1 text-xs font-medium`}
            role="status"
            aria-label={`Status: ${status.label}`}
          >
            <StatusIcon size={12} aria-hidden="true" />
            {status.label}
          </div>
        </div>
      </div>

      {/* Priority */}
      <div className="mb-3 flex items-center gap-2">
        <span className="text-sm text-gray-600">Priority:</span>
        <div className="flex gap-1">
          {[1, 2, 3, 4, 5].map((star) => (
            <span
              key={star}
              className={`text-lg ${
                star <= technology.priority ? 'text-yellow-500' : 'text-gray-300'
              }`}
            >
              ★
            </span>
          ))}
        </div>
      </div>

      {/* Relevance Score */}
      <div className="mb-3">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-gray-600">Relevance</span>
          <span className="font-medium" aria-label={`Relevance score: ${technology.relevance_score} out of 100`}>
            {technology.relevance_score}/100
          </span>
        </div>
        <div
          className="w-full bg-gray-200 rounded-full h-2"
          role="progressbar"
          aria-valuenow={technology.relevance_score}
          aria-valuemin={0}
          aria-valuemax={100}
          aria-label="Technology relevance score"
        >
          <div
            className="bg-primary-500 h-2 rounded-full transition-all"
            style={{ width: relevanceWidth }}
          />
        </div>
      </div>

      {/* Description */}
      {technology.description && (
        <p className="text-sm text-gray-600 mb-3 line-clamp-2">{technology.description}</p>
      )}

      {/* Tags */}
      {tags.length > 0 && (
        <div className="flex flex-wrap gap-1 mb-3">
          {tags.map((tag, index) => (
            <span
              key={index}
              className="px-2 py-1 bg-gray-100 text-gray-700 text-xs rounded"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      {/* External Links */}
      <div className="flex gap-2 mb-3">
        {technology.website_url && (
          <a
            href={technology.website_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:text-primary-700 text-xs flex items-center gap-1"
          >
            <ExternalLink size={12} />
            Website
          </a>
        )}
        {technology.documentation_url && (
          <a
            href={technology.documentation_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:text-primary-700 text-xs flex items-center gap-1"
          >
            <ExternalLink size={12} />
            Docs
          </a>
        )}
        {technology.repository_url && (
          <a
            href={technology.repository_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-primary-600 hover:text-primary-700 text-xs flex items-center gap-1"
          >
            <ExternalLink size={12} />
            Repo
          </a>
        )}
      </div>

      {/* Expandable Details */}
      {(technology.notes || technology.use_cases) && (
        <div className="mb-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-primary-600 hover:text-primary-700"
          >
            {expanded ? 'Show less' : 'Show more'}
          </button>
          {expanded && (
            <div className="mt-2 space-y-2 text-sm">
              {technology.use_cases && (
                <div>
                  <p className="font-medium text-gray-700">Use Cases:</p>
                  <p className="text-gray-600">{technology.use_cases}</p>
                </div>
              )}
              {technology.notes && (
                <div>
                  <p className="font-medium text-gray-700">Notes:</p>
                  <p className="text-gray-600">{technology.notes}</p>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Action Buttons */}
      {(onEdit || onDelete) && (
        <div className="flex items-center justify-end gap-2 pt-3 border-t border-gray-100">
          {onEdit && (
            <button
              onClick={() => onEdit(technology)}
              className="px-3 py-1.5 text-sm text-gray-700 bg-white border border-gray-300 rounded hover:bg-gray-50 transition-colors flex items-center gap-1"
              aria-label="Edit technology"
            >
              <Edit2 size={14} />
              Edit
            </button>
          )}
          {onDelete && !showDeleteConfirm && (
            <button
              onClick={() => setShowDeleteConfirm(true)}
              className="px-3 py-1.5 text-sm text-red-600 bg-white border border-red-300 rounded hover:bg-red-50 transition-colors flex items-center gap-1"
              aria-label="Delete technology"
            >
              <Trash2 size={14} />
              Delete
            </button>
          )}
          {showDeleteConfirm && (
            <div className="flex items-center gap-2">
              <span className="text-sm text-gray-600">Delete?</span>
              <button
                onClick={handleDelete}
                className="px-2 py-1 text-xs text-white bg-red-600 rounded hover:bg-red-700"
              >
                Yes
              </button>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="px-2 py-1 text-xs text-gray-700 bg-gray-200 rounded hover:bg-gray-300"
              >
                No
              </button>
            </div>
          )}
        </div>
      )}
    </article>
  );
});

TechnologyCard.displayName = 'TechnologyCard';
