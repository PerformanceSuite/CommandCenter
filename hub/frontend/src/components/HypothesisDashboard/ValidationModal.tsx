import { useState, useEffect } from 'react';
import type { ValidationStatus, HypothesisSummary, DebateResult } from '../../types/hypothesis';
import hypothesesApi from '../../services/hypothesesApi';
import { DebateViewer } from '../DebateViewer';

interface ValidationModalProps {
  hypothesis: HypothesisSummary;
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

type ModalState = 'config' | 'progress' | 'complete' | 'error';

const AVAILABLE_AGENTS = [
  { id: 'analyst', name: 'Analyst', description: 'Claude-based market analyst' },
  { id: 'researcher', name: 'Researcher', description: 'Gemini-based data researcher' },
  { id: 'strategist', name: 'Strategist', description: 'GPT-based business strategist' },
  { id: 'critic', name: 'Critic', description: 'Claude-based devil\'s advocate' },
];

export function ValidationModal({
  hypothesis,
  isOpen,
  onClose,
  onComplete,
}: ValidationModalProps) {
  const [state, setState] = useState<ModalState>('config');
  const [maxRounds, setMaxRounds] = useState(3);
  const [selectedAgents, setSelectedAgents] = useState(['analyst', 'researcher', 'critic']);
  const [taskId, setTaskId] = useState<string | null>(null);
  const [status, setStatus] = useState<ValidationStatus | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [debateResult, setDebateResult] = useState<DebateResult | null>(null);
  const [loadingDebate, setLoadingDebate] = useState(false);

  // Poll for status updates
  useEffect(() => {
    if (!taskId || state !== 'progress') return;

    const pollInterval = setInterval(async () => {
      try {
        const newStatus = await hypothesesApi.getValidationTask(taskId);
        setStatus(newStatus);

        if (newStatus.status === 'completed') {
          setState('complete');
          clearInterval(pollInterval);
          // Fetch the debate result
          fetchDebateResult(taskId);
        } else if (newStatus.status === 'failed') {
          setError(newStatus.error || 'Validation failed');
          setState('error');
          clearInterval(pollInterval);
        }
      } catch (err) {
        console.error('Failed to poll status:', err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [taskId, state]);

  // Fetch debate result
  const fetchDebateResult = async (tid: string) => {
    setLoadingDebate(true);
    try {
      const result = await hypothesesApi.getDebateResult(tid);
      setDebateResult(result);
    } catch (err) {
      console.error('Failed to fetch debate result:', err);
      // Not critical - modal still shows success
    } finally {
      setLoadingDebate(false);
    }
  };

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setState('config');
      setTaskId(null);
      setStatus(null);
      setError(null);
      setDebateResult(null);
      setLoadingDebate(false);
    }
  }, [isOpen]);

  const handleStartValidation = async () => {
    try {
      const response = await hypothesesApi.validate(hypothesis.id, {
        max_rounds: maxRounds,
        agents: selectedAgents,
      });
      setTaskId(response.task_id);
      setState('progress');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start validation');
      setState('error');
    }
  };

  const toggleAgent = (agentId: string) => {
    setSelectedAgents((prev) =>
      prev.includes(agentId)
        ? prev.filter((id) => id !== agentId)
        : [...prev, agentId]
    );
  };

  if (!isOpen) return null;

  // Modal is larger when showing results
  const modalWidth = state === 'complete' ? 'max-w-3xl' : 'max-w-lg';

  return (
    <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
      <div className={`bg-slate-900 border border-slate-700 rounded-lg w-full ${modalWidth} mx-4 max-h-[90vh] flex flex-col`}>
        {/* Header */}
        <div className="border-b border-slate-700 px-6 py-4">
          <h2 className="text-lg font-semibold text-white">Validate Hypothesis</h2>
          <p className="text-sm text-slate-400 mt-1 truncate">{hypothesis.statement}</p>
        </div>

        {/* Content */}
        <div className="px-6 py-4 overflow-y-auto flex-1">
          {state === 'config' && (
            <div className="space-y-4">
              {/* Max Rounds */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Maximum Debate Rounds
                </label>
                <input
                  type="range"
                  min="1"
                  max="5"
                  value={maxRounds}
                  onChange={(e) => setMaxRounds(Number(e.target.value))}
                  className="w-full"
                />
                <div className="text-center text-slate-400 mt-1">{maxRounds} rounds</div>
              </div>

              {/* Agent Selection */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Participating Agents
                </label>
                <div className="space-y-2">
                  {AVAILABLE_AGENTS.map((agent) => (
                    <label
                      key={agent.id}
                      className="flex items-center gap-3 p-2 rounded bg-slate-800/50 cursor-pointer hover:bg-slate-800"
                    >
                      <input
                        type="checkbox"
                        checked={selectedAgents.includes(agent.id)}
                        onChange={() => toggleAgent(agent.id)}
                        className="rounded border-slate-600"
                      />
                      <div>
                        <div className="text-sm font-medium text-white">{agent.name}</div>
                        <div className="text-xs text-slate-500">{agent.description}</div>
                      </div>
                    </label>
                  ))}
                </div>
              </div>
            </div>
          )}

          {state === 'progress' && status && (
            <div className="space-y-4">
              {/* Progress Bar */}
              <div>
                <div className="flex justify-between text-sm text-slate-400 mb-1">
                  <span>Round {status.current_round} of {status.max_rounds}</span>
                  <span>{status.responses_count} responses</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all duration-500"
                    style={{ width: `${(status.current_round / status.max_rounds) * 100}%` }}
                  />
                </div>
              </div>

              {/* Status Info */}
              <div className="text-center py-4">
                <div className="text-blue-400 animate-pulse text-lg">Validating...</div>
                {status.consensus_level && (
                  <div className="text-slate-400 mt-2">
                    Current consensus: <span className="text-white">{status.consensus_level}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {state === 'complete' && (
            <div className="space-y-4">
              {/* Success Header */}
              <div className="text-center py-4">
                <div className="text-3xl mb-2">
                  {hypothesis.status === 'validated' ? '✅' : hypothesis.status === 'invalidated' ? '❌' : '🔄'}
                </div>
                <div className="text-lg font-semibold text-white">Validation Complete</div>
              </div>

              {/* Debate Result */}
              {loadingDebate && (
                <div className="text-center py-4">
                  <div className="text-slate-400 animate-pulse">Loading debate results...</div>
                </div>
              )}

              {debateResult && (
                <DebateViewer debate={debateResult} />
              )}

              {!loadingDebate && !debateResult && (
                <div className="text-center py-4 text-slate-500">
                  Debate details not available
                </div>
              )}
            </div>
          )}

          {state === 'error' && (
            <div className="text-center py-6">
              <div className="text-4xl mb-4">⚠️</div>
              <div className="text-xl font-semibold text-red-400 mb-2">Validation Failed</div>
              <div className="text-slate-400">{error}</div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="border-t border-slate-700 px-6 py-4 flex justify-end gap-3">
          {state === 'config' && (
            <>
              <button
                onClick={onClose}
                className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleStartValidation}
                disabled={selectedAgents.length < 2}
                className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                Start Validation
              </button>
            </>
          )}

          {state === 'progress' && (
            <button
              onClick={onClose}
              className="px-4 py-2 text-slate-400 hover:text-white transition-colors"
            >
              Run in Background
            </button>
          )}

          {(state === 'complete' || state === 'error') && (
            <button
              onClick={() => {
                onComplete();
                onClose();
              }}
              className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
            >
              Close
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

export default ValidationModal;
