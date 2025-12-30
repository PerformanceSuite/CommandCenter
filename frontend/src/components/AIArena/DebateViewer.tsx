import { useState } from 'react';
import type {
  DebateResult,
  DebateRound,
  AgentResponse,
  ConsensusLevel,
} from '../../types/hypothesis';
import {
  AGENT_COLORS,
  CONSENSUS_COLORS,
  CONSENSUS_LABELS,
} from '../../types/hypothesis';

interface DebateViewerProps {
  debate: DebateResult;
}

/**
 * DebateViewer - Visualizes AI Arena debate results
 *
 * Shows rounds, agent responses, confidence levels, and consensus.
 */
export function DebateViewer({ debate }: DebateViewerProps) {
  const [expandedRound, setExpandedRound] = useState<number | null>(
    debate.rounds.length > 0 ? debate.rounds.length - 1 : null
  );
  const [expandedResponse, setExpandedResponse] = useState<string | null>(null);

  const toggleRound = (roundNumber: number) => {
    setExpandedRound(expandedRound === roundNumber ? null : roundNumber);
  };

  const toggleResponse = (key: string) => {
    setExpandedResponse(expandedResponse === key ? null : key);
  };

  return (
    <div className="space-y-6">
      {/* Summary Header */}
      <DebateSummary debate={debate} />

      {/* Rounds Timeline */}
      <div className="space-y-3">
        <h3 className="text-sm font-medium text-slate-400 uppercase tracking-wide">
          Debate Rounds
        </h3>

        {debate.rounds.map((round) => (
          <RoundCard
            key={round.round_number}
            round={round}
            isExpanded={expandedRound === round.round_number}
            onToggle={() => toggleRound(round.round_number)}
            expandedResponse={expandedResponse}
            onToggleResponse={toggleResponse}
            isLast={round.round_number === debate.rounds.length - 1}
          />
        ))}
      </div>

      {/* Dissenting Views */}
      {debate.dissenting_views.length > 0 && (
        <DissentingViews views={debate.dissenting_views} />
      )}
    </div>
  );
}

/**
 * Summary card showing final result and key metrics
 */
function DebateSummary({ debate }: { debate: DebateResult }) {
  const consensusColor = CONSENSUS_COLORS[debate.consensus_level as ConsensusLevel] || 'slate';
  const consensusLabel = CONSENSUS_LABELS[debate.consensus_level as ConsensusLevel] || debate.consensus_level;

  return (
    <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
      {/* Consensus Badge */}
      <div className="flex items-center justify-between mb-4">
        <span
          className={`px-3 py-1 rounded-full text-sm font-medium bg-${consensusColor}-500/20 text-${consensusColor}-400 border border-${consensusColor}-500/30`}
        >
          {consensusLabel}
        </span>
        <div className="text-sm text-slate-500">
          {debate.rounds.length} round{debate.rounds.length !== 1 ? 's' : ''}
        </div>
      </div>

      {/* Final Answer */}
      <div className="mb-4">
        <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Final Answer</div>
        <div className="text-white">{debate.final_answer || 'No consensus reached'}</div>
      </div>

      {/* Metrics Row */}
      <div className="flex items-center gap-6 text-sm">
        <div>
          <span className="text-slate-500">Confidence:</span>
          <span className="ml-2 text-white font-medium">
            {Math.round(debate.final_confidence)}%
          </span>
        </div>
        {debate.total_cost > 0 && (
          <div>
            <span className="text-slate-500">Cost:</span>
            <span className="ml-2 text-white font-medium">
              ${debate.total_cost.toFixed(4)}
            </span>
          </div>
        )}
        {debate.completed_at && debate.started_at && (
          <div>
            <span className="text-slate-500">Duration:</span>
            <span className="ml-2 text-white font-medium">
              {formatDuration(debate.started_at, debate.completed_at)}
            </span>
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Individual round card with expandable responses
 */
interface RoundCardProps {
  round: DebateRound;
  isExpanded: boolean;
  onToggle: () => void;
  expandedResponse: string | null;
  onToggleResponse: (key: string) => void;
  isLast: boolean;
}

function RoundCard({
  round,
  isExpanded,
  onToggle,
  expandedResponse,
  onToggleResponse,
  isLast,
}: RoundCardProps) {
  const consensusColor = round.consensus_level
    ? CONSENSUS_COLORS[round.consensus_level as ConsensusLevel] || 'slate'
    : 'slate';

  return (
    <div
      className={`border rounded-lg overflow-hidden transition-colors ${
        isLast ? 'border-blue-500/50 bg-blue-500/5' : 'border-slate-700 bg-slate-800/30'
      }`}
    >
      {/* Round Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between px-4 py-3 hover:bg-slate-800/50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="text-white font-medium">Round {round.round_number + 1}</span>
          <span className="text-slate-500 text-sm">
            {round.responses.length} response{round.responses.length !== 1 ? 's' : ''}
          </span>
          {round.consensus_level && (
            <span
              className={`px-2 py-0.5 rounded text-xs bg-${consensusColor}-500/20 text-${consensusColor}-400`}
            >
              {round.consensus_level}
            </span>
          )}
        </div>
        <div className="flex items-center gap-3">
          {/* Confidence meter */}
          <div className="flex items-center gap-2">
            <span className="text-xs text-slate-500">Avg:</span>
            <ConfidenceMeter
              value={Math.round(
                round.responses.reduce((sum, r) => sum + r.confidence, 0) / round.responses.length
              )}
              size="sm"
            />
          </div>
          <span className="text-slate-400">
            {isExpanded ? (
              <ChevronUpIcon className="w-5 h-5" />
            ) : (
              <ChevronDownIcon className="w-5 h-5" />
            )}
          </span>
        </div>
      </button>

      {/* Expanded Content */}
      {isExpanded && (
        <div className="border-t border-slate-700 divide-y divide-slate-700/50">
          {round.responses.map((response, idx) => (
            <AgentResponseCard
              key={`${round.round_number}-${idx}`}
              response={response}
              isExpanded={expandedResponse === `${round.round_number}-${idx}`}
              onToggle={() => onToggleResponse(`${round.round_number}-${idx}`)}
            />
          ))}
        </div>
      )}
    </div>
  );
}

/**
 * Individual agent response card
 */
interface AgentResponseCardProps {
  response: AgentResponse;
  isExpanded: boolean;
  onToggle: () => void;
}

function AgentResponseCard({ response, isExpanded, onToggle }: AgentResponseCardProps) {
  const agentColor = AGENT_COLORS[response.agent_name] || '#64748B';

  return (
    <div className="px-4 py-3">
      {/* Agent Header */}
      <button
        onClick={onToggle}
        className="w-full flex items-center justify-between"
      >
        <div className="flex items-center gap-3">
          <div
            className="w-2 h-2 rounded-full"
            style={{ backgroundColor: agentColor }}
          />
          <span className="text-white font-medium capitalize">{response.agent_name}</span>
          <span className="text-xs text-slate-500">{response.model}</span>
        </div>
        <div className="flex items-center gap-3">
          <ConfidenceMeter value={response.confidence} />
          <span className="text-slate-400">
            {isExpanded ? (
              <ChevronUpIcon className="w-4 h-4" />
            ) : (
              <ChevronDownIcon className="w-4 h-4" />
            )}
          </span>
        </div>
      </button>

      {/* Answer Preview */}
      <div className="mt-2 text-sm text-slate-300 line-clamp-2">{response.answer}</div>

      {/* Expanded Details */}
      {isExpanded && (
        <div className="mt-4 space-y-4 pl-5 border-l-2 border-slate-700">
          {/* Full Answer */}
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Answer</div>
            <div className="text-sm text-slate-200">{response.answer}</div>
          </div>

          {/* Reasoning */}
          <div>
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Reasoning</div>
            <div className="text-sm text-slate-300 whitespace-pre-wrap">{response.reasoning}</div>
          </div>

          {/* Evidence */}
          {response.evidence.length > 0 && (
            <div>
              <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Evidence</div>
              <ul className="space-y-1">
                {response.evidence.map((item, idx) => (
                  <li key={idx} className="text-sm text-slate-400 flex items-start gap-2">
                    <span className="text-slate-500 mt-1">-</span>
                    <span>{item}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

/**
 * Dissenting views section
 */
function DissentingViews({ views }: { views: AgentResponse[] }) {
  return (
    <div className="bg-red-500/5 border border-red-500/20 rounded-lg p-4">
      <h3 className="text-sm font-medium text-red-400 mb-3 flex items-center gap-2">
        <AlertTriangleIcon className="w-4 h-4" />
        Dissenting Views
      </h3>
      <div className="space-y-3">
        {views.map((view, idx) => (
          <div key={idx} className="text-sm">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-white font-medium capitalize">{view.agent_name}</span>
              <ConfidenceMeter value={view.confidence} size="sm" />
            </div>
            <div className="text-slate-400">{view.answer}</div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Confidence meter visualization
 */
function ConfidenceMeter({ value, size = 'md' }: { value: number; size?: 'sm' | 'md' }) {
  const getColor = (v: number) => {
    if (v >= 80) return 'bg-green-500';
    if (v >= 60) return 'bg-blue-500';
    if (v >= 40) return 'bg-amber-500';
    return 'bg-red-500';
  };

  const width = size === 'sm' ? 'w-12' : 'w-16';
  const height = size === 'sm' ? 'h-1.5' : 'h-2';

  return (
    <div className="flex items-center gap-2">
      <div className={`${width} ${height} bg-slate-700 rounded-full overflow-hidden`}>
        <div
          className={`h-full ${getColor(value)} transition-all`}
          style={{ width: `${value}%` }}
        />
      </div>
      <span className={`text-white ${size === 'sm' ? 'text-xs' : 'text-sm'}`}>{value}%</span>
    </div>
  );
}

/**
 * Helper function to format duration
 */
function formatDuration(start: string, end: string): string {
  const startDate = new Date(start);
  const endDate = new Date(end);
  const seconds = Math.round((endDate.getTime() - startDate.getTime()) / 1000);

  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = seconds % 60;
  return `${minutes}m ${remainingSeconds}s`;
}

// Simple icon components
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

function AlertTriangleIcon({ className }: { className?: string }) {
  return (
    <svg className={className} fill="none" viewBox="0 0 24 24" stroke="currentColor">
      <path
        strokeLinecap="round"
        strokeLinejoin="round"
        strokeWidth={2}
        d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
      />
    </svg>
  );
}

export default DebateViewer;
