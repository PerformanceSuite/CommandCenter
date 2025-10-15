import type { Project } from '../types';

interface ProjectCardProps {
  project: Project;
}

function ProjectCard({ project }: ProjectCardProps) {
  const handleOpen = () => {
    window.open(`http://localhost:${project.frontend_port}`, '_blank');
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

      {/* Open Button */}
      <button
        onClick={handleOpen}
        className="btn-primary px-6"
        title={`Open CommandCenter at localhost:${project.frontend_port}`}
      >
        Open
      </button>
    </div>
  );
}

export default ProjectCard;
