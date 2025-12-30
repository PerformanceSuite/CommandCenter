import { useState } from 'react';
import { HypothesisCreate } from '../../../services/intelligenceApi';
import type { HypothesisCategory, ImpactLevel, RiskLevel } from '../../../types/hypothesis';

interface HypothesisCreateFormProps {
  onSubmit: (data: HypothesisCreate) => Promise<void>;
  onClose: () => void;
}

const CATEGORIES: { value: HypothesisCategory; label: string }[] = [
  { value: 'customer', label: 'Customer' },
  { value: 'problem', label: 'Problem' },
  { value: 'solution', label: 'Solution' },
  { value: 'technical', label: 'Technical' },
  { value: 'market', label: 'Market' },
  { value: 'competitive', label: 'Competitive' },
  { value: 'gtm', label: 'Go-to-Market' },
  { value: 'regulatory', label: 'Regulatory' },
];

const IMPACT_LEVELS: { value: ImpactLevel; label: string }[] = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

const RISK_LEVELS: { value: RiskLevel; label: string }[] = [
  { value: 'high', label: 'High' },
  { value: 'medium', label: 'Medium' },
  { value: 'low', label: 'Low' },
];

/**
 * HypothesisCreateForm - Modal form for creating a new hypothesis
 */
export function HypothesisCreateForm({ onSubmit, onClose }: HypothesisCreateFormProps) {
  const [statement, setStatement] = useState('');
  const [category, setCategory] = useState<HypothesisCategory>('technical');
  const [impact, setImpact] = useState<ImpactLevel>('medium');
  const [risk, setRisk] = useState<RiskLevel>('medium');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (statement.length < 10) {
      setError('Statement must be at least 10 characters');
      return;
    }

    try {
      setSubmitting(true);
      setError(null);
      await onSubmit({ statement, category, impact, risk });
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create hypothesis');
      setSubmitting(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className="bg-slate-900 border border-slate-700 rounded-lg w-full max-w-lg mx-4">
        {/* Header */}
        <div className="border-b border-slate-700 px-6 py-4">
          <h2 className="text-lg font-semibold text-white">Create Hypothesis</h2>
          <p className="text-sm text-slate-400 mt-1">
            Add a new hypothesis to test for this research task
          </p>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="px-6 py-4 space-y-4">
          {/* Statement */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Hypothesis Statement *
            </label>
            <textarea
              value={statement}
              onChange={(e) => setStatement(e.target.value)}
              placeholder="We believe that..."
              rows={3}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              required
              minLength={10}
            />
            <p className="text-xs text-slate-500 mt-1">
              {statement.length} / 10 minimum characters
            </p>
          </div>

          {/* Category */}
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Category
            </label>
            <select
              value={category}
              onChange={(e) => setCategory(e.target.value as HypothesisCategory)}
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              {CATEGORIES.map((cat) => (
                <option key={cat.value} value={cat.value}>
                  {cat.label}
                </option>
              ))}
            </select>
          </div>

          {/* Impact & Risk Row */}
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Impact Level
              </label>
              <select
                value={impact}
                onChange={(e) => setImpact(e.target.value as ImpactLevel)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {IMPACT_LEVELS.map((level) => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Risk Level
              </label>
              <select
                value={risk}
                onChange={(e) => setRisk(e.target.value as RiskLevel)}
                className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {RISK_LEVELS.map((level) => (
                  <option key={level.value} value={level.value}>
                    {level.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Error Message */}
          {error && (
            <div className="text-sm text-red-400 bg-red-900/20 border border-red-900/50 rounded px-3 py-2">
              {error}
            </div>
          )}
        </form>

        {/* Footer */}
        <div className="border-t border-slate-700 px-6 py-4 flex justify-end gap-3">
          <button
            type="button"
            onClick={onClose}
            disabled={submitting}
            className="px-4 py-2 text-slate-400 hover:text-white transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={submitting || statement.length < 10}
            className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {submitting ? 'Creating...' : 'Create Hypothesis'}
          </button>
        </div>
      </div>
    </div>
  );
}

export default HypothesisCreateForm;
