import { useState } from 'react';
import { DebateResponse, intelligenceApi, GapSuggestion } from '../../../services/intelligenceApi';

interface DebateViewerProps {
  debate: DebateResponse;
  onTaskCreated?: (taskId: number, title: string) => void;
}

/**
 * DebateViewer - Displays debate results and gap analysis
 */
export function DebateViewer({ debate, onTaskCreated }: DebateViewerProps) {
  const [suggestedTasks, setSuggestedTasks] = useState<GapSuggestion[] | null>(null);
  const [loadingSuggestions, setLoadingSuggestions] = useState(false);
  const [creatingTask, setCreatingTask] = useState<number | null>(null);

  const loadSuggestedTasks = async () => {
    if (suggestedTasks) return; // Already loaded

    setLoadingSuggestions(true);
    try {
      const result = await intelligenceApi.getSuggestedTasks(debate.id);
      setSuggestedTasks(result.suggestions);
    } catch (err) {
      console.error('Failed to load suggestions:', err);
    } finally {
      setLoadingSuggestions(false);
    }
  };

  const createTaskFromSuggestion = async (index: number) => {
    setCreatingTask(index);
    try {
      const result = await intelligenceApi.createTaskFromGap(debate.id, index);
      onTaskCreated?.(result.research_task_id, result.title);
    } catch (err) {
      console.error('Failed to create task:', err);
    } finally {
      setCreatingTask(null);
    }
  };

  const getVerdictColor = () => {
    switch (debate.final_verdict) {
      case 'validated':
        return 'text-green-400 bg-green-900/30';
      case 'invalidated':
        return 'text-red-400 bg-red-900/30';
      default:
        return 'text-amber-400 bg-amber-900/30';
    }
  };

  const getConsensusColor = () => {
    switch (debate.consensus_level) {
      case 'strong':
        return 'bg-green-500/20 text-green-400';
      case 'moderate':
        return 'bg-blue-500/20 text-blue-400';
      case 'weak':
        return 'bg-amber-500/20 text-amber-400';
      default:
        return 'bg-slate-500/20 text-slate-400';
    }
  };

  return (
    <div className="space-y-6">
      {/* Summary Card */}
      <div className="bg-slate-800/50 rounded-lg p-4 border border-slate-700">
        {/* Verdict & Consensus */}
        <div className="flex items-center justify-between mb-4">
          <span className={`px-3 py-1 rounded-full text-sm font-medium ${getVerdictColor()}`}>
            {debate.final_verdict ? debate.final_verdict.replace('_', ' ').toUpperCase() : 'In Progress'}
          </span>
          {debate.consensus_level && (
            <span className={`px-3 py-1 rounded-full text-sm ${getConsensusColor()}`}>
              {debate.consensus_level} consensus
            </span>
          )}
        </div>

        {/* Reasoning */}
        {debate.verdict_reasoning && (
          <div className="mb-4">
            <div className="text-xs text-slate-500 uppercase tracking-wide mb-1">Reasoning</div>
            <div className="text-slate-300">{debate.verdict_reasoning}</div>
          </div>
        )}

        {/* Metrics */}
        <div className="flex items-center gap-6 text-sm">
          <div>
            <span className="text-slate-500">Rounds:</span>
            <span className="ml-2 text-white font-medium">
              {debate.rounds_completed} / {debate.rounds_requested}
            </span>
          </div>
          {debate.agents_used && (
            <div>
              <span className="text-slate-500">Agents:</span>
              <span className="ml-2 text-white font-medium">
                {debate.agents_used.length}
              </span>
            </div>
          )}
          {debate.completed_at && (
            <div>
              <span className="text-slate-500">Completed:</span>
              <span className="ml-2 text-white font-medium">
                {new Date(debate.completed_at).toLocaleString()}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Agents Used */}
      {debate.agents_used && debate.agents_used.length > 0 && (
        <div>
          <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wide mb-2">
            Participating Agents
          </h4>
          <div className="flex flex-wrap gap-2">
            {debate.agents_used.map((agent) => (
              <span
                key={agent}
                className="px-3 py-1 rounded-full text-sm bg-slate-700 text-slate-300 capitalize"
              >
                {agent}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Gap Analysis */}
      {debate.gap_analysis && (
        <div>
          <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wide mb-2">
            Gap Analysis
          </h4>
          <div className="bg-slate-800/30 rounded-lg p-4 border border-slate-700/50">
            {(() => {
              const questions = (debate.gap_analysis as { follow_up_questions?: string[] })?.follow_up_questions;
              return questions && Array.isArray(questions) && questions.length > 0 ? (
                <div>
                  <div className="text-xs text-slate-500 mb-2">Follow-up Questions</div>
                  <ul className="space-y-2">
                    {questions.map((q, idx) => (
                      <li key={idx} className="text-sm text-slate-300 flex items-start gap-2">
                        <span className="text-slate-500 mt-1">•</span>
                        <span>{q}</span>
                      </li>
                    ))}
                  </ul>
                </div>
              ) : null;
            })()}
          </div>
        </div>
      )}

      {/* Suggested Research Tasks */}
      <div>
        <div className="flex items-center justify-between mb-2">
          <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wide">
            Suggested Research Tasks
          </h4>
          {!suggestedTasks && (
            <button
              onClick={loadSuggestedTasks}
              disabled={loadingSuggestions}
              className="text-sm text-blue-400 hover:text-blue-300 disabled:opacity-50"
            >
              {loadingSuggestions ? 'Loading...' : 'Load Suggestions'}
            </button>
          )}
        </div>

        {suggestedTasks && suggestedTasks.length > 0 ? (
          <div className="space-y-2">
            {suggestedTasks.map((task, idx) => (
              <div
                key={idx}
                className="bg-slate-800/30 rounded-lg p-3 border border-slate-700/50 flex items-start justify-between gap-4"
              >
                <div className="flex-1">
                  <div className="text-white font-medium">{task.title}</div>
                  <div className="text-sm text-slate-400 mt-1">{task.description}</div>
                  <div className="flex gap-3 mt-2 text-xs">
                    <span className={`px-2 py-0.5 rounded ${
                      task.priority === 'high' ? 'bg-red-900/30 text-red-400' :
                      task.priority === 'medium' ? 'bg-amber-900/30 text-amber-400' :
                      'bg-slate-700 text-slate-400'
                    }`}>
                      {task.priority} priority
                    </span>
                    <span className="px-2 py-0.5 rounded bg-slate-700 text-slate-400">
                      {task.estimated_effort} effort
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => createTaskFromSuggestion(idx)}
                  disabled={creatingTask === idx}
                  className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors disabled:opacity-50 whitespace-nowrap"
                >
                  {creatingTask === idx ? 'Creating...' : 'Create Task'}
                </button>
              </div>
            ))}
          </div>
        ) : suggestedTasks?.length === 0 ? (
          <div className="text-sm text-slate-500">No suggestions available</div>
        ) : null}
      </div>
    </div>
  );
}

export default DebateViewer;
