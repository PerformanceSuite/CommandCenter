import { useState } from 'react';
import toast from 'react-hot-toast';
import type { Project } from '../types';
import { deleteProject, api } from '../services/api';

interface ProjectCardProps {
  project: Project;
  onDelete: () => void;
}

function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);

  const handleOpen = () => {
    // Just open the URL directly - let the project handle "not started" state
    window.open(`http://localhost:${project.frontend_port}`, '_blank');
  };

  const handleDelete = async (deleteFiles: boolean) => {
    setDeleting(true);
    try {
      await deleteProject(project.id, deleteFiles);
      onDelete();
    } catch (error) {
      console.error('Failed to delete project:', error);
      alert('Failed to delete project');
    } finally {
      setDeleting(false);
      setShowConfirm(false);
    }
  };

  const getStatusColor = () => {
    switch (project.status) {
      case 'running':
        return project.health === 'healthy' ? 'bg-green-500' : 'bg-yellow-500';
      case 'stopped':
        return 'bg-gray-500';
      case 'error':
        return 'bg-red-500';
      default:
        return 'bg-gray-500';
    }
  };

  const getStatusText = () => {
    switch (project.status) {
      case 'running':
        return project.health === 'healthy' ? 'Running' : 'Starting...';
      case 'stopped':
        return 'Stopped';
      case 'error':
        return 'Error';
      default:
        return 'Unknown';
    }
  };

  return (
    <div className="flex items-center gap-4 p-4 bg-slate-800/30 border border-slate-700/50 rounded-lg hover:bg-slate-800/50 hover:border-slate-600 transition-all">
      {/* Status Indicator */}
      <div className="flex items-center gap-2">
        <div className={`w-3 h-3 rounded-full ${getStatusColor()} ${project.status === 'running' && project.health === 'healthy' ? 'animate-pulse' : ''}`} />
        <span className="text-xs text-slate-400 min-w-[60px]">{getStatusText()}</span>
      </div>

      {/* Project Info */}
      <div className="flex-1 min-w-0">
        <h3 className="text-lg font-semibold text-white">{project.name}</h3>
        <p className="text-sm text-slate-400 truncate" title={project.path}>
          {project.path}
        </p>
      </div>

      {/* Ports */}
      <div className="flex gap-6 text-sm">
        <div>
          <span className="text-slate-500">Frontend:</span>
          <span className="ml-2 text-slate-300 font-mono">{project.frontend_port}</span>
        </div>
        <div>
          <span className="text-slate-500">Backend:</span>
          <span className="ml-2 text-slate-300 font-mono">{project.backend_port}</span>
        </div>
      </div>

      {/* Actions */}
      {!showConfirm ? (
        <>
          {project.status === 'stopped' ? (
            <button
              onClick={async () => {
                try {
                  toast.loading(`Starting ${project.name}...`, { id: `start-${project.id}` });
                  await api.orchestration.start(project.id);
                  toast.success(`${project.name} started!`, { id: `start-${project.id}` });
                  setTimeout(() => window.location.reload(), 1000);
                } catch (error) {
                  toast.error(`Failed to start ${project.name}`, { id: `start-${project.id}` });
                }
              }}
              className="px-6 py-2 bg-green-600 text-white border border-green-500 rounded-lg hover:bg-green-700 hover:border-green-600 transition-all font-semibold"
              title="Start containers"
            >
              Start
            </button>
          ) : project.status === 'running' ? (
            <>
              <button
                onClick={handleOpen}
                className="btn-primary px-6"
                title={`Open CommandCenter at localhost:${project.frontend_port}`}
              >
                Open
              </button>
              <button
                onClick={async () => {
                  try {
                    toast.loading(`Stopping ${project.name}...`, { id: `stop-${project.id}` });
                    await api.orchestration.stop(project.id);
                    toast.success(`${project.name} stopped`, { id: `stop-${project.id}` });
                    setTimeout(() => window.location.reload(), 1000);
                  } catch (error) {
                    toast.error(`Failed to stop ${project.name}`, { id: `stop-${project.id}` });
                  }
                }}
                className="px-4 py-2 bg-yellow-600/20 text-yellow-400 border border-yellow-600/30 rounded-lg hover:bg-yellow-600/30 hover:border-yellow-600/50 transition-all"
                title="Stop containers"
              >
                Stop
              </button>
            </>
          ) : (
            <button
              onClick={handleOpen}
              className="btn-primary px-6"
              title={`Open CommandCenter at localhost:${project.frontend_port}`}
            >
              Open
            </button>
          )}
          <button
            onClick={() => setShowConfirm(true)}
            className="px-4 py-2 bg-red-600/20 text-red-400 border border-red-600/30 rounded-lg hover:bg-red-600/30 hover:border-red-600/50 transition-all"
            title="Delete project"
          >
            Delete
          </button>
        </>
      ) : (
        <div className="flex gap-2 items-center">
          <span className="text-sm text-slate-400">Delete files too?</span>
          <button
            onClick={() => handleDelete(false)}
            disabled={deleting}
            className="px-3 py-1 bg-slate-700 text-slate-300 rounded hover:bg-slate-600 disabled:opacity-50"
            title="Remove from registry only"
          >
            No
          </button>
          <button
            onClick={() => handleDelete(true)}
            disabled={deleting}
            className="px-3 py-1 bg-red-600 text-white rounded hover:bg-red-700 disabled:opacity-50"
            title="Remove from registry AND delete all files"
          >
            Yes
          </button>
          <button
            onClick={() => setShowConfirm(false)}
            disabled={deleting}
            className="px-3 py-1 bg-slate-700 text-slate-300 rounded hover:bg-slate-600 disabled:opacity-50"
          >
            Cancel
          </button>
        </div>
      )}
    </div>
  );
}

export default ProjectCard;
