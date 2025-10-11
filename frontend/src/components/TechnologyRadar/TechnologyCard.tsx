import React, { memo, useMemo, useState } from 'react';
import type { Technology } from '../../types/technology';
import { TrendingUp, Beaker, TestTube, Rocket, Edit2, Trash2, ExternalLink, Star, MessageCircle, GitBranch, Zap, Timer, Code, DollarSign, Activity } from 'lucide-react';

interface TechnologyCardProps {
  technology: Technology;
  onEdit?: (technology: Technology) => void;
  onDelete?: (technology: Technology) => void;
}

const statusConfig: Record<string, { label: string; icon: any; color: string }> = {
  discovery: { label: 'Discovery', icon: Beaker, color: 'bg-purple-100 text-purple-700' },
  research: { label: 'Research', icon: TestTube, color: 'bg-blue-100 text-blue-700' },
  evaluation: { label: 'Evaluation', icon: TrendingUp, color: 'bg-yellow-100 text-yellow-700' },
  implementation: { label: 'Implementation', icon: Rocket, color: 'bg-orange-100 text-orange-700' },
  integrated: { label: 'Integrated', icon: Rocket, color: 'bg-green-100 text-green-700' },
  archived: { label: 'Archived', icon: Beaker, color: 'bg-gray-100 text-gray-700' },
};

const costTierColors: Record<string, string> = {
  free: 'bg-green-100 text-green-700',
  freemium: 'bg-emerald-100 text-emerald-700',
  affordable: 'bg-blue-100 text-blue-700',
  moderate: 'bg-yellow-100 text-yellow-700',
  expensive: 'bg-orange-100 text-orange-700',
  enterprise: 'bg-red-100 text-red-700',
};

const maturityLevelColors: Record<string, string> = {
  alpha: 'bg-red-100 text-red-700',
  beta: 'bg-orange-100 text-orange-700',
  stable: 'bg-green-100 text-green-700',
  mature: 'bg-blue-100 text-blue-700',
  legacy: 'bg-gray-100 text-gray-700',
};

const integrationDifficultyLabels: Record<string, string> = {
  trivial: 'Trivial',
  easy: 'Easy',
  moderate: 'Moderate',
  complex: 'Complex',
  very_complex: 'Very Complex',
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

  // Check if v2 fields exist
  const hasV2Fields = useMemo(() => {
    return !!(
      technology.latency_ms ||
      technology.throughput_qps ||
      technology.integration_difficulty ||
      technology.maturity_level ||
      technology.stability_score ||
      technology.cost_tier ||
      technology.github_stars ||
      technology.hn_score_avg
    );
  }, [technology]);

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

      {/* V2 Quick Metrics (badges) */}
      {hasV2Fields && (
        <div className="flex flex-wrap gap-2 mb-3 pb-3 border-b border-gray-100">
          {technology.github_stars !== null && (
            <div className="flex items-center gap-1 px-2 py-1 bg-gray-50 rounded text-xs">
              <Star size={12} className="text-yellow-500" />
              <span className="font-medium">{technology.github_stars.toLocaleString()}</span>
            </div>
          )}
          {technology.hn_score_avg !== null && (
            <div className="flex items-center gap-1 px-2 py-1 bg-gray-50 rounded text-xs">
              <MessageCircle size={12} className="text-orange-500" />
              <span className="font-medium">HN {technology.hn_score_avg.toFixed(1)}</span>
            </div>
          )}
          {technology.maturity_level && (
            <div className={`px-2 py-1 rounded text-xs font-medium ${maturityLevelColors[technology.maturity_level]}`}>
              {technology.maturity_level.charAt(0).toUpperCase() + technology.maturity_level.slice(1)}
            </div>
          )}
          {technology.cost_tier && (
            <div className={`px-2 py-1 rounded text-xs font-medium flex items-center gap-1 ${costTierColors[technology.cost_tier]}`}>
              <DollarSign size={12} />
              {technology.cost_tier.charAt(0).toUpperCase() + technology.cost_tier.slice(1)}
            </div>
          )}
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
      {(technology.notes || technology.use_cases || hasV2Fields) && (
        <div className="mb-3">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            {expanded ? '▼ Show less' : '▶ Show detailed evaluation'}
          </button>
          {expanded && (
            <div className="mt-3 space-y-3 text-sm">
              {/* Performance Metrics */}
              {(technology.latency_ms !== null || technology.throughput_qps !== null || technology.stability_score !== null) && (
                <div className="bg-blue-50 p-3 rounded-lg">
                  <p className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <Zap size={14} className="text-blue-600" />
                    Performance & Stability
                  </p>
                  <div className="space-y-1">
                    {technology.latency_ms !== null && (
                      <div className="flex items-center gap-2">
                        <Timer size={12} className="text-gray-500" />
                        <span className="text-gray-600">P99 Latency:</span>
                        <span className="font-medium">{technology.latency_ms}ms</span>
                      </div>
                    )}
                    {technology.throughput_qps !== null && (
                      <div className="flex items-center gap-2">
                        <Activity size={12} className="text-gray-500" />
                        <span className="text-gray-600">Throughput:</span>
                        <span className="font-medium">{technology.throughput_qps} QPS</span>
                      </div>
                    )}
                    {technology.stability_score !== null && (
                      <div>
                        <div className="flex items-center justify-between mb-1">
                          <span className="text-gray-600">Stability Score:</span>
                          <span className="font-medium">{technology.stability_score}/100</span>
                        </div>
                        <div className="w-full bg-gray-200 rounded-full h-2">
                          <div
                            className="bg-blue-500 h-2 rounded-full transition-all"
                            style={{ width: `${technology.stability_score}%` }}
                          />
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Integration Assessment */}
              {(technology.integration_difficulty || technology.integration_time_estimate_days !== null) && (
                <div className="bg-purple-50 p-3 rounded-lg">
                  <p className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <Code size={14} className="text-purple-600" />
                    Integration Assessment
                  </p>
                  <div className="space-y-1">
                    {technology.integration_difficulty && (
                      <div className="flex items-center gap-2">
                        <span className="text-gray-600">Difficulty:</span>
                        <span className="font-medium">{integrationDifficultyLabels[technology.integration_difficulty]}</span>
                      </div>
                    )}
                    {technology.integration_time_estimate_days !== null && (
                      <div className="flex items-center gap-2">
                        <span className="text-gray-600">Estimated Time:</span>
                        <span className="font-medium">{technology.integration_time_estimate_days} days</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Cost Analysis */}
              {(technology.cost_monthly_usd !== null) && (
                <div className="bg-green-50 p-3 rounded-lg">
                  <p className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <DollarSign size={14} className="text-green-600" />
                    Cost Analysis
                  </p>
                  <div className="flex items-center gap-2">
                    <span className="text-gray-600">Monthly Cost:</span>
                    <span className="font-medium">${technology.cost_monthly_usd.toLocaleString()}</span>
                  </div>
                </div>
              )}

              {/* Monitoring Data */}
              {(technology.last_hn_mention || technology.github_last_commit) && (
                <div className="bg-orange-50 p-3 rounded-lg">
                  <p className="font-semibold text-gray-800 mb-2 flex items-center gap-2">
                    <GitBranch size={14} className="text-orange-600" />
                    Activity Monitoring
                  </p>
                  <div className="space-y-1">
                    {technology.last_hn_mention && (
                      <div className="flex items-center gap-2">
                        <MessageCircle size={12} className="text-gray-500" />
                        <span className="text-gray-600">Last HN Mention:</span>
                        <span className="font-medium">{new Date(technology.last_hn_mention).toLocaleDateString()}</span>
                      </div>
                    )}
                    {technology.github_last_commit && (
                      <div className="flex items-center gap-2">
                        <GitBranch size={12} className="text-gray-500" />
                        <span className="text-gray-600">Last Commit:</span>
                        <span className="font-medium">{new Date(technology.github_last_commit).toLocaleDateString()}</span>
                      </div>
                    )}
                  </div>
                </div>
              )}

              {/* Alternatives */}
              {technology.alternatives && (
                <div className="bg-gray-50 p-3 rounded-lg">
                  <p className="font-semibold text-gray-800 mb-2">Alternatives</p>
                  <p className="text-gray-600">{technology.alternatives}</p>
                </div>
              )}

              {/* Use Cases & Notes (existing fields) */}
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
