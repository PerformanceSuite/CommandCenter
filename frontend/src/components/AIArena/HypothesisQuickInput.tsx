import { useState } from 'react';
import toast from 'react-hot-toast';
import hypothesesApi from '../../services/hypothesesApi';
import { CATEGORY_LABELS } from '../../types/hypothesis';

interface HypothesisQuickInputProps {
  onHypothesisCreated?: () => void;
}

export function HypothesisQuickInput({ onHypothesisCreated }: HypothesisQuickInputProps) {
  const [statement, setStatement] = useState('');
  const [category, setCategory] = useState<string>('general');
  const [context, setContext] = useState('');
  const [showContext, setShowContext] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (statement.trim().length < 10) {
      toast.error('Hypothesis must be at least 10 characters');
      return;
    }

    setIsSubmitting(true);

    try {
      await hypothesesApi.create({
        statement: statement.trim(),
        context: context.trim() || undefined,
        category,
      });

      toast.success('Hypothesis created successfully!');

      // Clear form
      setStatement('');
      setContext('');
      setShowContext(false);

      // Notify parent to refresh
      if (onHypothesisCreated) {
        onHypothesisCreated();
      }
    } catch (error) {
      console.error('Failed to create hypothesis:', error);
      toast.error(error instanceof Error ? error.message : 'Failed to create hypothesis');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="bg-slate-800/50 rounded-lg p-4 mb-6 border border-slate-700">
      <form onSubmit={handleSubmit}>
        {/* Main input */}
        <div className="flex items-start gap-3">
          <div className="flex-1">
            <input
              type="text"
              value={statement}
              onChange={(e) => setStatement(e.target.value)}
              placeholder="Enter a hypothesis to validate..."
              className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors"
              disabled={isSubmitting}
              maxLength={500}
            />
            {statement.length > 0 && (
              <div className="text-xs text-slate-500 mt-1">
                {statement.length}/500 characters
              </div>
            )}
          </div>

          {/* Category dropdown */}
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            className="bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white focus:outline-none focus:border-blue-500 transition-colors"
            disabled={isSubmitting}
          >
            <option value="general">General</option>
            {Object.entries(CATEGORY_LABELS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>

          {/* Submit button */}
          <button
            type="submit"
            disabled={isSubmitting || statement.trim().length < 10}
            className="bg-blue-600 hover:bg-blue-700 disabled:bg-slate-700 disabled:text-slate-500 text-white px-6 py-2.5 rounded-lg font-medium transition-colors whitespace-nowrap"
          >
            {isSubmitting ? 'Creating...' : 'Create'}
          </button>
        </div>

        {/* Context section (collapsible) */}
        <div className="mt-3">
          {!showContext ? (
            <button
              type="button"
              onClick={() => setShowContext(true)}
              className="text-sm text-slate-400 hover:text-white transition-colors"
            >
              + Add context (optional)
            </button>
          ) : (
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <label className="text-sm text-slate-400">Context</label>
                <button
                  type="button"
                  onClick={() => {
                    setShowContext(false);
                    setContext('');
                  }}
                  className="text-xs text-slate-500 hover:text-slate-400"
                >
                  Hide
                </button>
              </div>
              <textarea
                value={context}
                onChange={(e) => setContext(e.target.value)}
                placeholder="Add any additional context or background information..."
                rows={3}
                className="w-full bg-slate-900 border border-slate-700 rounded-lg px-4 py-2.5 text-white placeholder-slate-500 focus:outline-none focus:border-blue-500 transition-colors resize-none"
                disabled={isSubmitting}
              />
            </div>
          )}
        </div>
      </form>
    </div>
  );
}

export default HypothesisQuickInput;
