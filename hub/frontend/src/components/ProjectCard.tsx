import { useState } from 'react';
import type { Project } from '../types';
import { deleteProject, api } from '../services/api';

interface ProjectCardProps {
  project: Project;
  onDelete: () => void;
}

function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const [showConfirm, setShowConfirm] = useState(false);
  const [deleting, setDeleting] = useState(false);
  const [starting, setStarting] = useState(false);

  const handleOpen = async () => {
    // If project is stopped, start it first
    if (project.status === 'stopped') {
      setStarting(true);
      try {
        await api.orchestration.start(project.id);
        // Wait for services to start
        await new Promise(resolve => setTimeout(resolve, 3000));
      } catch (error) {
        console.error('Failed to start project:', error);
        alert('Failed to start project. Check logs for details.');
        setStarting(false);
        return;
      }
      setStarting(false);
    }

    // Open the project
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

  return (
    <div className="flex items-center gap-4 p-4 bg-slate-800/30 border border-slate-700/50 rounded-lg hover:bg-slate-800/50 hover:border-slate-600 transition-all">
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
          <button
            onClick={handleOpen}
            disabled={starting}
            className="btn-primary px-6"
            title={`${project.status === 'stopped' ? 'Start and open' : 'Open'} CommandCenter at localhost:${project.frontend_port}`}
          >
            {starting ? 'Starting...' : (project.status === 'stopped' ? 'Start & Open' : 'Open')}
          </button>
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
