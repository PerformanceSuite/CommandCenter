import { useState, useMemo } from 'react';
import { ClipboardCheck, CheckCircle2, XCircle, Loader2 } from 'lucide-react';
import { useReviewQueue } from '../../hooks/useReviewQueue';
import { ConceptCard } from './ConceptCard';
import { RequirementCard } from './RequirementCard';
import type { ReviewTab, ReviewSelection } from '../../types/review';

export function ReviewView() {
  const [activeTab, setActiveTab] = useState<ReviewTab>('concepts');
  const [selection, setSelection] = useState<ReviewSelection>({
    concepts: new Set(),
    requirements: new Set(),
  });

  const {
    concepts,
    requirements,
    totalPendingConcepts,
    totalPendingRequirements,
    totalPending,
    loading,
    approveConcepts,
    approveRequirements,
    rejectConcepts,
    rejectRequirements,
    isApprovingConcepts,
    isApprovingRequirements,
    isRejectingConcepts,
    isRejectingRequirements,
  } = useReviewQueue();

  const isProcessing = isApprovingConcepts || isApprovingRequirements || isRejectingConcepts || isRejectingRequirements;

  // Selection helpers
  const selectedConceptIds = useMemo(() => Array.from(selection.concepts), [selection.concepts]);
  const selectedRequirementIds = useMemo(() => Array.from(selection.requirements), [selection.requirements]);

  const currentItems = activeTab === 'concepts' ? concepts : requirements;
  const currentSelection = activeTab === 'concepts' ? selection.concepts : selection.requirements;
  const allSelected = currentItems.length > 0 && currentSelection.size === currentItems.length;

  const toggleSelectAll = () => {
    if (activeTab === 'concepts') {
      if (allSelected) {
        setSelection((prev) => ({ ...prev, concepts: new Set() }));
      } else {
        setSelection((prev) => ({ ...prev, concepts: new Set(concepts.map((c) => c.id)) }));
      }
    } else {
      if (allSelected) {
        setSelection((prev) => ({ ...prev, requirements: new Set() }));
      } else {
        setSelection((prev) => ({ ...prev, requirements: new Set(requirements.map((r) => r.id)) }));
      }
    }
  };

  const toggleConceptSelection = (id: number) => {
    setSelection((prev) => {
      const next = new Set(prev.concepts);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return { ...prev, concepts: next };
    });
  };

  const toggleRequirementSelection = (id: number) => {
    setSelection((prev) => {
      const next = new Set(prev.requirements);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return { ...prev, requirements: next };
    });
  };

  // Action handlers
  const handleApproveSelected = async () => {
    if (activeTab === 'concepts' && selectedConceptIds.length > 0) {
      await approveConcepts(selectedConceptIds);
      setSelection((prev) => ({ ...prev, concepts: new Set() }));
    } else if (activeTab === 'requirements' && selectedRequirementIds.length > 0) {
      await approveRequirements(selectedRequirementIds);
      setSelection((prev) => ({ ...prev, requirements: new Set() }));
    }
  };

  const handleRejectSelected = async () => {
    if (activeTab === 'concepts' && selectedConceptIds.length > 0) {
      await rejectConcepts(selectedConceptIds);
      setSelection((prev) => ({ ...prev, concepts: new Set() }));
    } else if (activeTab === 'requirements' && selectedRequirementIds.length > 0) {
      await rejectRequirements(selectedRequirementIds);
      setSelection((prev) => ({ ...prev, requirements: new Set() }));
    }
  };

  const handleApproveSingle = async (id: number) => {
    if (activeTab === 'concepts') {
      await approveConcepts([id]);
    } else {
      await approveRequirements([id]);
    }
  };

  const handleRejectSingle = async (id: number) => {
    if (activeTab === 'concepts') {
      await rejectConcepts([id]);
    } else {
      await rejectRequirements([id]);
    }
  };

  const hasSelection = activeTab === 'concepts' ? selectedConceptIds.length > 0 : selectedRequirementIds.length > 0;

  return (
    <div className="p-6 max-w-6xl mx-auto">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-3">
          <ClipboardCheck className="w-8 h-8 text-blue-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">Review Queue</h1>
            <p className="text-gray-400 text-sm">
              Approve AI-extracted concepts and requirements before indexing to KnowledgeBeast
            </p>
          </div>
        </div>
        <div className="bg-blue-500/20 text-blue-400 px-4 py-2 rounded-lg font-medium">
          {totalPending} items pending
        </div>
      </div>

      {/* Tabs */}
      <div className="flex gap-2 mb-6">
        <button
          onClick={() => setActiveTab('concepts')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'concepts'
              ? 'bg-blue-500 text-white'
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          Concepts ({totalPendingConcepts})
        </button>
        <button
          onClick={() => setActiveTab('requirements')}
          className={`px-4 py-2 rounded-lg font-medium transition-colors ${
            activeTab === 'requirements'
              ? 'bg-blue-500 text-white'
              : 'bg-slate-700 text-gray-300 hover:bg-slate-600'
          }`}
        >
          Requirements ({totalPendingRequirements})
        </button>
      </div>

      {/* Bulk Actions */}
      <div className="flex items-center gap-4 mb-4 p-3 bg-slate-800 rounded-lg">
        <label className="flex items-center gap-2 text-gray-300 cursor-pointer">
          <input
            type="checkbox"
            checked={allSelected}
            onChange={toggleSelectAll}
            className="w-4 h-4 rounded border-gray-600 bg-slate-700 text-blue-500 focus:ring-blue-500"
          />
          Select All
        </label>
        <div className="flex-1" />
        <button
          onClick={handleApproveSelected}
          disabled={!hasSelection || isProcessing}
          className="flex items-center gap-2 px-4 py-2 bg-green-600 hover:bg-green-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
        >
          {isApprovingConcepts || isApprovingRequirements ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <CheckCircle2 className="w-4 h-4" />
          )}
          Approve Selected
        </button>
        <button
          onClick={handleRejectSelected}
          disabled={!hasSelection || isProcessing}
          className="flex items-center gap-2 px-4 py-2 bg-red-600 hover:bg-red-500 disabled:bg-gray-600 disabled:cursor-not-allowed text-white rounded-lg font-medium transition-colors"
        >
          {isRejectingConcepts || isRejectingRequirements ? (
            <Loader2 className="w-4 h-4 animate-spin" />
          ) : (
            <XCircle className="w-4 h-4" />
          )}
          Reject Selected
        </button>
      </div>

      {/* Loading State */}
      {loading && (
        <div className="flex items-center justify-center py-12">
          <Loader2 className="w-8 h-8 text-blue-400 animate-spin" />
          <span className="ml-3 text-gray-400">Loading review queue...</span>
        </div>
      )}

      {/* Empty State */}
      {!loading && currentItems.length === 0 && (
        <div className="text-center py-12 bg-slate-800 rounded-lg">
          <ClipboardCheck className="w-12 h-12 text-gray-600 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-gray-300 mb-2">No items pending review</h3>
          <p className="text-gray-500">
            {activeTab === 'concepts'
              ? 'All concepts have been reviewed.'
              : 'All requirements have been reviewed.'}
          </p>
        </div>
      )}

      {/* Items List */}
      {!loading && currentItems.length > 0 && (
        <div className="space-y-4">
          {activeTab === 'concepts' &&
            concepts.map((concept) => (
              <ConceptCard
                key={concept.id}
                concept={concept}
                selected={selection.concepts.has(concept.id)}
                onToggleSelect={() => toggleConceptSelection(concept.id)}
                onApprove={() => handleApproveSingle(concept.id)}
                onReject={() => handleRejectSingle(concept.id)}
                disabled={isProcessing}
              />
            ))}
          {activeTab === 'requirements' &&
            requirements.map((requirement) => (
              <RequirementCard
                key={requirement.id}
                requirement={requirement}
                selected={selection.requirements.has(requirement.id)}
                onToggleSelect={() => toggleRequirementSelection(requirement.id)}
                onApprove={() => handleApproveSingle(requirement.id)}
                onReject={() => handleRejectSingle(requirement.id)}
                disabled={isProcessing}
              />
            ))}
        </div>
      )}
    </div>
  );
}

export default ReviewView;
