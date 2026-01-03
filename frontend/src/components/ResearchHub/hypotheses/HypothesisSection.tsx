import { useState, useEffect, useCallback } from 'react';
import { intelligenceApi, HypothesisResponse, HypothesisCreate } from '../../../services/intelligenceApi';
import { HypothesisCard } from './HypothesisCard';
import { HypothesisCreateForm } from './HypothesisCreateForm';
import { ValidationModal } from './ValidationModal';

interface HypothesisSectionProps {
  taskId: number;
  onHypothesisValidated?: () => void;
}

/**
 * HypothesisSection - Displays and manages hypotheses for a research task
 *
 * Features:
 * - List hypotheses with status indicators
 * - Create new hypotheses
 * - Launch validation debates
 * - View validation results
 */
export function HypothesisSection({ taskId, onHypothesisValidated }: HypothesisSectionProps) {
  const [hypotheses, setHypotheses] = useState<HypothesisResponse[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [validatingHypothesis, setValidatingHypothesis] = useState<HypothesisResponse | null>(null);
  const [expandedHypothesis, setExpandedHypothesis] = useState<number | null>(null);

  // Fetch hypotheses for the task
  const fetchHypotheses = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await intelligenceApi.listByTask(taskId);
      setHypotheses(response.items);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load hypotheses');
    } finally {
      setLoading(false);
    }
  }, [taskId]);

  useEffect(() => {
    fetchHypotheses();
  }, [fetchHypotheses]);

  // Create new hypothesis
  const handleCreate = async (data: HypothesisCreate) => {
    await intelligenceApi.createUnderTask(taskId, data);
    setShowCreateForm(false);
    fetchHypotheses();
  };

  // Start validation
  const handleValidate = (hypothesis: HypothesisResponse) => {
    setValidatingHypothesis(hypothesis);
  };

  // Validation complete
  const handleValidationComplete = () => {
    setValidatingHypothesis(null);
    fetchHypotheses();
    onHypothesisValidated?.();
  };

  // Delete hypothesis
  const handleDelete = async (hypothesisId: number) => {
    if (!confirm('Are you sure you want to delete this hypothesis?')) return;

    try {
      await intelligenceApi.delete(hypothesisId);
      fetchHypotheses();
    } catch (err) {
      console.error('Failed to delete hypothesis:', err);
    }
  };

  // Toggle expanded view
  const handleToggleExpand = (hypothesisId: number) => {
    setExpandedHypothesis(expandedHypothesis === hypothesisId ? null : hypothesisId);
  };

  if (loading) {
    return (
      <div className="py-8 text-center">
        <div className="text-slate-400 animate-pulse">Loading hypotheses...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8 text-center">
        <div className="text-red-400">{error}</div>
        <button
          onClick={fetchHypotheses}
          className="mt-2 text-sm text-blue-400 hover:text-blue-300"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h3 className="text-lg font-semibold text-white">Hypotheses</h3>
          <p className="text-sm text-slate-400">
            {hypotheses.length} hypothesis{hypotheses.length !== 1 ? 'es' : ''} for this task
          </p>
        </div>
        <button
          onClick={() => setShowCreateForm(true)}
          className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors flex items-center gap-2"
        >
          <PlusIcon className="w-4 h-4" />
          Add Hypothesis
        </button>
      </div>

      {/* Stats Summary */}
      {hypotheses.length > 0 && (
        <div className="grid grid-cols-4 gap-4">
          <StatCard
            label="Total"
            value={hypotheses.length}
            color="slate"
          />
          <StatCard
            label="Validated"
            value={hypotheses.filter(h => h.status === 'validated').length}
            color="green"
          />
          <StatCard
            label="Invalidated"
            value={hypotheses.filter(h => h.status === 'invalidated').length}
            color="red"
          />
          <StatCard
            label="Pending"
            value={hypotheses.filter(h => h.status === 'untested' || h.status === 'needs_more_data').length}
            color="amber"
          />
        </div>
      )}

      {/* Hypothesis List */}
      {hypotheses.length === 0 ? (
        <div className="py-12 text-center bg-slate-800/30 rounded-lg border border-slate-700/50">
          <div className="text-slate-400 mb-4">No hypotheses yet</div>
          <button
            onClick={() => setShowCreateForm(true)}
            className="text-blue-400 hover:text-blue-300"
          >
            Create your first hypothesis
          </button>
        </div>
      ) : (
        <div className="space-y-3">
          {hypotheses.map((hypothesis) => (
            <HypothesisCard
              key={hypothesis.id}
              hypothesis={hypothesis}
              isExpanded={expandedHypothesis === hypothesis.id}
              onToggleExpand={() => handleToggleExpand(hypothesis.id)}
              onValidate={() => handleValidate(hypothesis)}
              onDelete={() => handleDelete(hypothesis.id)}
            />
          ))}
        </div>
      )}

      {/* Create Form Modal */}
      {showCreateForm && (
        <HypothesisCreateForm
          onSubmit={handleCreate}
          onClose={() => setShowCreateForm(false)}
        />
      )}

      {/* Validation Modal */}
      {validatingHypothesis && (
        <ValidationModal
          hypothesis={validatingHypothesis}
          isOpen={true}
          onClose={() => setValidatingHypothesis(null)}
          onComplete={handleValidationComplete}
        />
      )}
    </div>
  );
}

// Stat card component
function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: number;
  color: 'slate' | 'green' | 'red' | 'amber' | 'blue';
}) {
  const bgColors = {
    slate: 'bg-slate-800/50',
    green: 'bg-green-900/30',
    red: 'bg-red-900/30',
    amber: 'bg-amber-900/30',
    blue: 'bg-blue-900/30',
  };

  const textColors = {
    slate: 'text-slate-300',
    green: 'text-green-400',
    red: 'text-red-400',
    amber: 'text-amber-400',
    blue: 'text-blue-400',
  };

  return (
    <div className={`${bgColors[color]} rounded-lg p-3 border border-slate-700/50`}>
      <div className={`text-2xl font-bold ${textColors[color]}`}>{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  );
}

// Plus icon
function PlusIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
    </svg>
  );
}

export default HypothesisSection;
