import { useState, useEffect } from 'react';
import { intelligenceApi, HypothesisResponse, DebateResponse } from '../../../services/intelligenceApi';
import { DebateViewer } from './DebateViewer';

interface ValidationModalProps {
  hypothesis: HypothesisResponse;
  isOpen: boolean;
  onClose: () => void;
  onComplete: () => void;
}

type ModalState = 'config' | 'progress' | 'complete' | 'error';

const AVAILABLE_AGENTS = [
  { id: 'analyst', name: 'Analyst', description: 'Claude-based market analyst' },
  { id: 'researcher', name: 'Researcher', description: 'Gemini-based data researcher' },
  { id: 'strategist', name: 'Strategist', description: 'GPT-based business strategist' },
  { id: 'critic', name: 'Critic', description: "Claude-based devil's advocate" },
];

/**
 * ValidationModal - Modal for configuring and running hypothesis validation
 */
export function ValidationModal({
  hypothesis,
  isOpen,
  onClose,
  onComplete,
}: ValidationModalProps) {
  const [state, setState] = useState<ModalState>('config');
  const [maxRounds, setMaxRounds] = useState(3);
  const [selectedAgents, setSelectedAgents] = useState(['analyst', 'researcher', 'critic']);
  const [debateId, setDebateId] = useState<number | null>(null);
  const [debate, setDebate] = useState<DebateResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Poll for debate status
  useEffect(() => {
    if (!debateId || state !== 'progress') return;

    const pollInterval = setInterval(async () => {
      try {
        const status = await intelligenceApi.getDebate(debateId);
        setDebate(status);

        if (status.status === 'completed') {
          setState('complete');
          clearInterval(pollInterval);
        } else if (status.status === 'failed') {
          setError('Validation failed');
          setState('error');
          clearInterval(pollInterval);
        }
      } catch (err) {
        console.error('Failed to poll status:', err);
      }
    }, 2000);

    return () => clearInterval(pollInterval);
  }, [debateId, state]);

  // Reset state when modal opens
  useEffect(() => {
    if (isOpen) {
      setState('config');
      setDebateId(null);
      setDebate(null);
      setError(null);
    }
  }, [isOpen]);

  const handleStartValidation = async () => {
    try {
      const response = await intelligenceApi.startValidation(hypothesis.id, {
        agents: selectedAgents,
        rounds: maxRounds,
      });
      setDebateId(response.debate_id);
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

          {state === 'progress' && debate && (
            <div className="space-y-4">
              {/* Progress Bar */}
              <div>
                <div className="flex justify-between text-sm text-slate-400 mb-1">
                  <span>Round {debate.rounds_completed} of {debate.rounds_requested}</span>
                  <span>Status: {debate.status}</span>
                </div>
                <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                  <div
                    className="h-full bg-blue-500 transition-all duration-500"
                    style={{ width: `${(debate.rounds_completed / debate.rounds_requested) * 100}%` }}
                  />
                </div>
              </div>

              {/* Status Info */}
              <div className="text-center py-4">
                <div className="text-blue-400 animate-pulse text-lg">Validating...</div>
                {debate.consensus_level && (
                  <div className="text-slate-400 mt-2">
                    Current consensus: <span className="text-white">{debate.consensus_level}</span>
                  </div>
                )}
              </div>
            </div>
          )}

          {state === 'complete' && debate && (
            <div className="space-y-4">
              {/* Success Header */}
              <div className="text-center py-4">
                <div className="text-3xl mb-2">
                  {debate.final_verdict === 'validated' ? '✅' :
                   debate.final_verdict === 'invalidated' ? '❌' : '🔄'}
                </div>
                <div className="text-lg font-semibold text-white">Validation Complete</div>
                {debate.final_verdict && (
                  <div className="text-slate-400 mt-1 capitalize">{debate.final_verdict.replace('_', ' ')}</div>
                )}
              </div>

              {/* Debate Result */}
              <DebateViewer debate={debate} />
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
