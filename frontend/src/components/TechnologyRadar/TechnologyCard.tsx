import React, { memo, useMemo } from 'react';
import type { Technology } from '../../types/technology';
import { TrendingUp, Beaker, TestTube, Rocket } from 'lucide-react';

interface TechnologyCardProps {
  technology: Technology;
}

const statusConfig = {
  research: { label: 'Research', icon: Beaker, color: 'bg-blue-100 text-blue-700' },
  prototype: { label: 'Prototype', icon: TestTube, color: 'bg-yellow-100 text-yellow-700' },
  beta: { label: 'Beta', icon: TrendingUp, color: 'bg-orange-100 text-orange-700' },
  'production-ready': { label: 'Production', icon: Rocket, color: 'bg-green-100 text-green-700' },
};

export const TechnologyCard: React.FC<TechnologyCardProps> = memo(({ technology }) => {
  const status = statusConfig[technology.status];
  const StatusIcon = status.icon;

  // Memoize the relevance width calculation
  const relevanceWidth = useMemo(
    () => `${technology.relevance * 10}%`,
    [technology.relevance]
  );

  // Memoize ARIA label for accessibility
  const cardAriaLabel = useMemo(
    () => `${technology.title} by ${technology.vendor}, ${status.label} status, relevance ${technology.relevance} out of 10`,
    [technology.title, technology.vendor, status.label, technology.relevance]
  );

  return (
    <article
      className="border border-gray-200 rounded-lg p-4 hover:shadow-md transition-shadow"
      aria-label={cardAriaLabel}
      role="article"
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <h3 className="font-semibold text-lg">{technology.title}</h3>
          <p className="text-sm text-gray-500">{technology.vendor}</p>
        </div>
        <div
          className={`${status.color} px-2 py-1 rounded-full flex items-center gap-1 text-xs font-medium`}
          role="status"
          aria-label={`Status: ${status.label}`}
        >
          <StatusIcon size={12} aria-hidden="true" />
          {status.label}
        </div>
      </div>

      <div className="mb-3">
        <div className="flex items-center justify-between text-sm mb-1">
          <span className="text-gray-600">Relevance</span>
          <span className="font-medium" aria-label={`Relevance score: ${technology.relevance} out of 10`}>
            {technology.relevance}/10
          </span>
        </div>
        <div
          className="w-full bg-gray-200 rounded-full h-2"
          role="progressbar"
          aria-valuenow={technology.relevance}
          aria-valuemin={0}
          aria-valuemax={10}
          aria-label="Technology relevance score"
        >
          <div
            className="bg-primary-500 h-2 rounded-full transition-all"
            style={{ width: relevanceWidth }}
          />
        </div>
      </div>

      {technology.notes && (
        <p className="text-sm text-gray-600 line-clamp-3">{technology.notes}</p>
      )}
    </article>
  );
});

TechnologyCard.displayName = 'TechnologyCard';
