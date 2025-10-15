import { useState } from 'react';
import type { Project } from '../types';
import { orchestrationApi } from '../services/api';

interface ProjectCardProps {
  project: Project;
  onUpdate: () => void;
}

function ProjectCard({ project, onUpdate }: ProjectCardProps) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const isRunning = project.status === 'running';
  const isStarting = project.status === 'starting';

  const handleStart = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await orchestrationApi.start(project.id);
      onUpdate();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start');
    } finally {
      setIsLoading(false);
    }
  };

  const handleStop = async () => {
    setIsLoading(true);
    setError(null);
    try {
      await orchestrationApi.stop(project.id);
      onUpdate();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to stop');
    } finally {
      setIsLoading(false);
    }
  };

  const handleOpen = () => {
    window.open(`http://localhost:${project.frontend_port}`, '_blank');
  };

  const getStatusDotClass = () => {
    switch (project.status) {
      case 'running':
        return 'status-dot running';
      case 'starting':
        return 'status-dot starting';
      case 'error':
        return 'status-dot error';
      default:
        return 'status-dot stopped';
    }
  };

  const getCardClass = () => {
    let baseClass = 'project-card';
    if (isRunning) baseClass += ' running glow-green';
    return baseClass;
  };

  return (
    <div className={getCardClass()}>
      {/* Header with status */}
      <div className="flex items-start justify-between mb-4">
        <div>
          <h3 className="text-xl font-bold text-white">{project.name}</h3>
          <p className="text-slate-400 text-sm mt-1 truncate" title={project.path}>
            {project.path}
          </p>
        </div>
        <div className="flex items-center gap-2">
          <div className={getStatusDotClass()} />
          <span className="text-sm text-slate-300 capitalize">
            {project.status}
          </span>
        </div>
      </div>

      {/* Stats */}
      <div className="grid grid-cols-2 gap-4 mb-4 text-sm">
        <div>
          <span className="text-slate-400">Frontend:</span>
          <span className="ml-2 text-white font-mono">{project.frontend_port}</span>
        </div>
        <div>
          <span className="text-slate-400">Backend:</span>
          <span className="ml-2 text-white font-mono">{project.backend_port}</span>
        </div>
        <div className="col-span-2">
          <span className="text-slate-400">Project:</span>
          <span className="ml-2 text-white font-mono text-xs">{project.compose_project_name}</span>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="mb-4 p-3 bg-red-900/20 border border-red-500/30 rounded text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        {isRunning ? (
          <>
            <button
              onClick={handleStop}
              disabled={isLoading}
              className="btn-danger flex-1"
            >
              {isLoading ? 'Stopping...' : 'Stop'}
            </button>
            <button
              onClick={handleOpen}
              className="btn-primary flex-1"
            >
              Open
            </button>
          </>
        ) : (
          <button
            onClick={handleStart}
            disabled={isLoading || isStarting}
            className="btn-success w-full"
          >
            {isLoading || isStarting ? 'Starting...' : 'Start'}
          </button>
        )}
      </div>

      {/* Last Started */}
      {project.last_started && (
        <div className="mt-3 text-xs text-slate-500">
          Last started: {new Date(project.last_started).toLocaleString()}
        </div>
      )}
    </div>
  );
}

export default ProjectCard;
