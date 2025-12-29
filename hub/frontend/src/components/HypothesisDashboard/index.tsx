import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import type {
  HypothesisSummary,
  HypothesisStats,
  HypothesisFilters,
  HypothesisStatus,
  HypothesisCategory,
} from '../../types/hypothesis';
import { STATUS_LABELS, CATEGORY_LABELS } from '../../types/hypothesis';
import hypothesesApi from '../../services/hypothesesApi';
import { HypothesisCard } from './HypothesisCard';
import { StatsBar } from './StatsBar';
import { ValidationModal } from './ValidationModal';

export function HypothesisDashboard() {
  // Data state
  const [hypotheses, setHypotheses] = useState<HypothesisSummary[]>([]);
  const [stats, setStats] = useState<HypothesisStats | null>(null);
  const [total, setTotal] = useState(0);

  // UI state
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState<HypothesisFilters>({});
  const [validatingId, setValidatingId] = useState<string | null>(null);
  const [selectedHypothesis, setSelectedHypothesis] = useState<HypothesisSummary | null>(null);
  const [showModal, setShowModal] = useState(false);

  // Fetch hypotheses
  const fetchHypotheses = useCallback(async () => {
    try {
      const response = await hypothesesApi.list(filters);
      setHypotheses(response.items);
      setTotal(response.total);
    } catch (err) {
      console.error('Failed to fetch hypotheses:', err);
      toast.error('Failed to load hypotheses');
    }
  }, [filters]);

  // Fetch stats
  const fetchStats = useCallback(async () => {
    try {
      const response = await hypothesesApi.stats();
      setStats(response);
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  }, []);

  // Initial load
  useEffect(() => {
    const loadData = async () => {
      setLoading(true);
      await Promise.all([fetchHypotheses(), fetchStats()]);
      setLoading(false);
    };
    loadData();
  }, [fetchHypotheses, fetchStats]);

  // Handle validate click
  const handleValidate = (id: string) => {
    const hypothesis = hypotheses.find((h) => h.id === id);
    if (hypothesis) {
      setSelectedHypothesis(hypothesis);
      setShowModal(true);
    }
  };

  // Handle view click
  const handleView = (id: string) => {
    // For now, just expand the card or show details
    // Could navigate to a detail page in the future
    toast.success(`Viewing hypothesis ${id}`);
  };

  // Handle modal close
  const handleModalClose = () => {
    setShowModal(false);
    setSelectedHypothesis(null);
  };

  // Handle validation complete
  const handleValidationComplete = () => {
    fetchHypotheses();
    fetchStats();
  };

  // Filter handlers
  const handleStatusFilter = (status: HypothesisStatus | '') => {
    setFilters((prev) => ({
      ...prev,
      status: status || undefined,
    }));
  };

  const handleCategoryFilter = (category: HypothesisCategory | '') => {
    setFilters((prev) => ({
      ...prev,
      category: category || undefined,
    }));
  };

  return (
    <div>
      {/* Stats Bar */}
      <StatsBar stats={stats} loading={loading} />

      {/* Filters */}
      <div className="flex items-center gap-4 mb-6">
        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Status:</label>
          <select
            value={filters.status || ''}
            onChange={(e) => handleStatusFilter(e.target.value as HypothesisStatus | '')}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white"
          >
            <option value="">All</option>
            {Object.entries(STATUS_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex items-center gap-2">
          <label className="text-sm text-slate-400">Category:</label>
          <select
            value={filters.category || ''}
            onChange={(e) => handleCategoryFilter(e.target.value as HypothesisCategory | '')}
            className="bg-slate-800 border border-slate-700 rounded px-3 py-1.5 text-sm text-white"
          >
            <option value="">All</option>
            {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        <div className="flex-1" />

        <div className="text-sm text-slate-500">
          {total} hypothesis{total !== 1 ? 'es' : ''}
        </div>
      </div>

      {/* Hypothesis List */}
      {loading ? (
        <div className="space-y-3">
          {[...Array(5)].map((_, i) => (
            <div key={i} className="bg-slate-800/30 rounded-lg p-4 animate-pulse">
              <div className="h-5 bg-slate-700 rounded w-2/3 mb-2" />
              <div className="h-4 bg-slate-700 rounded w-1/3" />
            </div>
          ))}
        </div>
      ) : hypotheses.length === 0 ? (
        <div className="text-center py-12">
          <div className="text-slate-500 text-lg">No hypotheses found</div>
          <p className="text-slate-600 mt-2">
            {filters.status || filters.category
              ? 'Try adjusting your filters'
              : 'Create hypotheses via the API to get started'}
          </p>
        </div>
      ) : (
        <div className="space-y-3">
          {hypotheses.map((hypothesis) => (
            <HypothesisCard
              key={hypothesis.id}
              hypothesis={hypothesis}
              onValidate={handleValidate}
              onView={handleView}
              isValidating={validatingId === hypothesis.id}
            />
          ))}
        </div>
      )}

      {/* Validation Modal */}
      {selectedHypothesis && (
        <ValidationModal
          hypothesis={selectedHypothesis}
          isOpen={showModal}
          onClose={handleModalClose}
          onComplete={handleValidationComplete}
        />
      )}
    </div>
  );
}

export default HypothesisDashboard;
