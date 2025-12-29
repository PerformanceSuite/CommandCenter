import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import type {
  EvidenceItem,
  EvidenceStats,
  EvidenceFilters,
} from '../../types/hypothesis';
import {
  SOURCE_TYPE_LABELS,
  SOURCE_TYPE_COLORS,
} from '../../types/hypothesis';
import hypothesesApi from '../../services/hypothesesApi';

/**
 * EvidenceExplorer - Browse and filter evidence across all hypotheses
 */
export function EvidenceExplorer() {
  // Data state
  const [evidence, setEvidence] = useState<EvidenceItem[]>([]);
  const [stats, setStats] = useState<EvidenceStats | null>(null);
  const [total, setTotal] = useState(0);

  // UI state
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<EvidenceFilters>({});
  const [expandedId, setExpandedId] = useState<string | null>(null);

  // Fetch evidence
  const fetchEvidence = useCallback(async () => {
    try {
      const response = await hypothesesApi.listEvidence(filters);
      setEvidence(response.items);
      setTotal(response.total);
    } catch (err) {
      console.error('Failed to fetch evidence:', err);
      toast.error('Failed to load evidence');
    }
  }, [filters]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await hypothesesApi.getEvidenceStats();
      setStats(response);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchEvidence(), fetchStats()]);
      setLoading(false);
    };
    loadData();
  }, [fetchEvidence, fetchStats]);

  // Filter handlers
  const handleSupportsFilter = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      supports: value === '' ? undefined : value === 'true',
    }));
  };

  const handleSourceFilter = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      source: value || undefined,
    }));
  };

  const handleConfidenceFilter = (value: string) => {
    setFilters((prev) => ({
      ...prev,
      min_confidence: value ? parseInt(value, 10) : undefined,
    }));
  };

  const toggleExpand = (id: string) => {
    setExpandedId(expandedId === id ? null : id);
  };

  return (
    <div className="space-y-6">
      {/* Stats Overview */}
      <EvidenceStatsBar stats={stats} loading={loading} />

      {/* Filters */}
      <div className="flex flex-wrap items-center gap-4">
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Type:</label>
          <select
            value={filters.supports === undefined ? '' : String(filters.supports)}
            onChange={(e) => handleSupportsFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white"
          >
            <option value="">All</option>
            <option value="true">Supporting</option>
            <option value="false">Contradicting</option>
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Source:</label>
          <input
            type="text"
            value={filters.source || ''}
            onChange={(e) => handleSourceFilter(e.target.value)}
            placeholder="Filter by source..."
            className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white w-48"
          />
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Min Confidence:</label>
          <select
            value={filters.min_confidence ?? ''}
            onChange={(e) => handleConfidenceFilter(e.target.value)}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white"
          >
            <option value="">Any</option>
            <option value="50">50%+</option>
            <option value="70">70%+</option>
            <option value="80">80%+</option>
            <option value="90">90%+</option>
          </select>
        </div>

        <div className="flex-1" />

        <div className="text-sm text-slate-500">
          {total} evidence item{total !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Evidence List */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-slate-800/30 rounded-lg p-4 animate-pulse">
              <div className="h-5 bg-slate-700 rounded w-2/3 mb-2" />
              <div className="h-4 bg-slate-700 rounded w-1/3" />
            </div>
          ))}
        </div>
      ) : evidence.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-slate-500 text-lg">No evidence found</div>
          <p className="text-slate-600 mt-2">
            {Object.keys(filters).some((k) => filters[k as keyof EvidenceFilters] !== undefined)
              ? 'Try adjusting your filters'
              : 'Evidence will appear here as hypotheses are validated'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {evidence.map((item) => (
            <EvidenceCard
              key={item.id}
              evidence={item}
              isExpanded={expandedId === item.id}
              onToggle={() => toggleExpand(item.id)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Stats bar showing evidence overview
 */
function EvidenceStatsBar({
  stats,
  loading,
}: {
  stats: EvidenceStats | null;
  loading: boolean;
}) {
  if (loading || !stats) {
    return (
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-slate-800/50 rounded-lg p-4 animate-pulse">
            <div className="h-4 bg-slate-700 rounded w-1/2 mb-2" />
            <div className="h-8 bg-slate-700 rounded w-2/3" />
          </div>
        ))}
      </div>
    );
  }

  const supportingPct = stats.total > 0 ? Math.round((stats.supporting / stats.total) * 100) : 0;

  return (
    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
      {/* Total Evidence */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Total Evidence</div>
        <div className="text-2xl font-bold text-white">{stats.total}</div>
      </div>

      {/* Supporting vs Contradicting */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Support Ratio</div>
        <div className="flex items-baseline gap-2">
          <span className="text-2xl font-bold text-green-400">{stats.supporting}</span>
          <span className="text-slate-500">/</span>
          <span className="text-2xl font-bold text-red-400">{stats.contradicting}</span>
        </div>
        <div className="mt-2 h-1.5 bg-slate-700 rounded-full overflow-hidden">
          <div
            className="h-full bg-green-500"
            style={{ width: `${supportingPct}%` }}
          />
        </div>
      </div>

      {/* Average Confidence */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Avg Confidence</div>
        <div className="text-2xl font-bold text-white">{stats.average_confidence}%</div>
      </div>

      {/* Source Breakdown */}
      <div className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">By Source Type</div>
        <div className="flex flex-wrap gap-1 mt-1">
          {Object.entries(stats.by_source_type).map(([type, count]) => (
            <span
              key={type}
              className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium"
              style={{
                backgroundColor: `${SOURCE_TYPE_COLORS[type] || '#64748B'}20`,
                color: SOURCE_TYPE_COLORS[type] || '#64748B',
              }}
            >
              {SOURCE_TYPE_LABELS[type] || type}: {count}
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}

/**
 * Individual evidence card
 */
interface EvidenceCardProps {
  evidence: EvidenceItem;
  isExpanded: boolean;
  onToggle: () => void;
}

function EvidenceCard({ evidence, isExpanded, onToggle }: EvidenceCardProps) {
  const supportColor = evidence.supports ? 'green' : 'red';
  const supportLabel = evidence.supports ? 'Supports' : 'Contradicts';

  return (
    <div className="bg-slate-800/30 border border-slate-700 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-start gap-4 px-4 py-3 hover:bg-slate-800/50 transition-colors text-left"
      >
        {/* Support Indicator */}
        <div
          className={`mt-1 w-2 h-2 rounded-full flex-shrink-0 bg-${supportColor}-500`}
          title={supportLabel}
        />

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="text-white line-clamp-2">{evidence.content}</div>
          <div className="flex items-center gap-3 mt-2 text-xs text-slate-500">
            <span className={`text-${supportColor}-400 font-medium`}>{supportLabel}</span>
            <span>-</span>
            <span>{evidence.source}</span>
            <span>-</span>
            <span>{formatDate(evidence.collected_at)}</span>
          </div>
        </div>

        {/* Confidence & Expand */}
        <div className="flex items-center gap-3 flex-shrink-0">
          <ConfidenceBadge value={evidence.confidence} />
          <span className="text-slate-400">
            {isExpanded ? (
              <ChevronUpIcon className="w-5 h-5" />
            ) : (
              <ChevronDownIcon className="w-5 h-5" />
            )}
          </span>
        </div>
      </button>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="border-t border-slate-700 px-4 py-4 space-y-4">
          {/* Linked Hypothesis */}
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">
              Linked Hypothesis
            </div>
            <div className="text-sm text-slate-300 bg-slate-800/50 rounded p-2">
              {evidence.hypothesis_statement}
              {evidence.hypothesis_statement.length >= 100 && '...'}
            </div>
          </div>

          {/* Full Content */}
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">
              Full Content
            </div>
            <div className="text-sm text-slate-200 whitespace-pre-wrap">
              {evidence.content}
            </div>
          </div>

          {/* Metadata */}
          <div className="flex flex-wrap gap-4 text-sm">
            <div>
              <span className="text-slate-500">Source:</span>
              <span className="ml-2 text-white">{evidence.source}</span>
            </div>
            <div>
              <span className="text-slate-500">Collected by:</span>
              <span className="ml-2 text-white">{evidence.collected_by}</span>
            </div>
            <div>
              <span className="text-slate-500">Date:</span>
              <span className="ml-2 text-white">{formatDateTime(evidence.collected_at)}</span>
            </div>
            <div>
              <span className="text-slate-500">Confidence:</span>
              <span className="ml-2 text-white">{evidence.confidence}%</span>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

/**
 * Confidence badge
 */
function ConfidenceBadge({ value }: { value: number }) {
  const getColor = (v: number) => {
    if (v >= 80) return 'green';
    if (v >= 60) return 'blue';
    if (v >= 40) return 'amber';
    return 'red';
  };

  const color = getColor(value);

  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-medium bg-${color}-500/20 text-${color}-400`}
    >
      {value}%
    </span>
  );
}

/**
 * Helper to format date
 */
function formatDate(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
}

function formatDateTime(dateStr: string): string {
  const date = new Date(dateStr);
  return date.toLocaleString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: 'numeric',
    minute: '2-digit',
  });
}

// Icons
function ChevronDownIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
    </svg>
  );
}

function ChevronUpIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 15l7-7 7 7" />
    </svg>
  );
}

export default EvidenceExplorer;
