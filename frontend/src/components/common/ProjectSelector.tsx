import { useState, useEffect } from 'react';
import { ChevronDown, Plus, FolderOpen } from 'lucide-react';
import { useProjects } from '../../hooks/useProjects';
import { Project } from '../../types/project';

export const ProjectSelector = () => {
  const { projects, loading } = useProjects();
  const [selectedProject, setSelectedProject] = useState<Project | null>(null);
  const [isOpen, setIsOpen] = useState(false);

  // Load selected project from localStorage on mount
  useEffect(() => {
    const savedProjectId = localStorage.getItem('selected_project_id');
    if (savedProjectId && projects.length > 0) {
      const project = projects.find(p => p.id === parseInt(savedProjectId));
      if (project) {
        setSelectedProject(project);
      } else {
        // If saved project not found, select first project
        setSelectedProject(projects[0]);
        localStorage.setItem('selected_project_id', projects[0].id.toString());
      }
    } else if (projects.length > 0 && !selectedProject) {
      // No saved project, select first one
      setSelectedProject(projects[0]);
      localStorage.setItem('selected_project_id', projects[0].id.toString());
    }
  }, [projects, selectedProject]);

  const handleProjectSelect = (project: Project) => {
    setSelectedProject(project);
    localStorage.setItem('selected_project_id', project.id.toString());
    setIsOpen(false);
    // Reload the page to fetch data for the new project
    window.location.reload();
  };

  const handleCreateProject = () => {
    setIsOpen(false);
    // Navigate to project management page
    window.location.href = '/projects';
  };

  if (loading) {
    return (
      <div className="relative">
        <div className="flex items-center gap-2 px-4 py-2 bg-slate-800 dark:bg-gray-700 rounded-lg animate-pulse">
          <FolderOpen className="w-5 h-5 text-gray-400" />
          <span className="text-sm text-gray-400">Loading...</span>
        </div>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="relative">
        <button
          onClick={handleCreateProject}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <Plus className="w-5 h-5" />
          <span className="text-sm font-medium">Create First Project</span>
        </button>
      </div>
    );
  }

  return (
    <div className="relative">
      {/* Selector Button */}
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-3 px-4 py-2 bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-slate-900 dark:hover:bg-gray-700 transition-colors min-w-[200px]"
      >
        <FolderOpen className="w-5 h-5 text-blue-600 dark:text-blue-400" />
        <div className="flex-1 text-left">
          <div className="text-sm font-medium text-white dark:text-white">
            {selectedProject?.name || 'Select Project'}
          </div>
          {selectedProject?.description && (
            <div className="text-xs text-slate-500 dark:text-gray-400 truncate">
              {selectedProject.description}
            </div>
          )}
        </div>
        <ChevronDown
          className={`w-4 h-4 text-slate-500 transition-transform ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <>
          {/* Backdrop */}
          <div
            className="fixed inset-0 z-10"
            onClick={() => setIsOpen(false)}
          />

          {/* Menu */}
          <div className="absolute top-full left-0 mt-2 w-full min-w-[280px] bg-white dark:bg-gray-800 border border-gray-300 dark:border-gray-600 rounded-lg shadow-lg z-20 max-h-[400px] overflow-y-auto">
            {/* Project List */}
            <div className="py-2">
              {projects.map((project) => (
                <button
                  key={project.id}
                  onClick={() => handleProjectSelect(project)}
                  className={`w-full px-4 py-3 text-left hover:bg-slate-800 dark:hover:bg-gray-700 transition-colors ${
                    selectedProject?.id === project.id
                      ? 'bg-blue-50 dark:bg-blue-900/20'
                      : ''
                  }`}
                >
                  <div className="flex items-start gap-3">
                    <FolderOpen
                      className={`w-5 h-5 mt-0.5 ${
                        selectedProject?.id === project.id
                          ? 'text-blue-600 dark:text-blue-400'
                          : 'text-gray-400'
                      }`}
                    />
                    <div className="flex-1 min-w-0">
                      <div className="font-medium text-white dark:text-white">
                        {project.name}
                      </div>
                      {project.description && (
                        <div className="text-sm text-slate-500 dark:text-gray-400 truncate mt-1">
                          {project.description}
                        </div>
                      )}
                      <div className="text-xs text-gray-400 dark:text-slate-500 mt-1">
                        Owner: {project.owner}
                      </div>
                    </div>
                    {selectedProject?.id === project.id && (
                      <div className="flex items-center justify-center w-5 h-5 bg-blue-600 dark:bg-blue-500 rounded-full">
                        <svg
                          className="w-3 h-3 text-white"
                          fill="none"
                          strokeLinecap="round"
                          strokeLinejoin="round"
                          strokeWidth="2"
                          viewBox="0 0 24 24"
                          stroke="currentColor"
                        >
                          <path d="M5 13l4 4L19 7" />
                        </svg>
                      </div>
                    )}
                  </div>
                </button>
              ))}
            </div>

            {/* Divider */}
            <div className="border-t border-gray-200 dark:border-gray-700" />

            {/* Create New Project Button */}
            <button
              onClick={handleCreateProject}
              className="w-full px-4 py-3 text-left hover:bg-slate-800 dark:hover:bg-gray-700 transition-colors flex items-center gap-3 text-blue-600 dark:text-blue-400 font-medium"
            >
              <Plus className="w-5 h-5" />
              <span>Create New Project</span>
            </button>
          </div>
        </>
      )}
    </div>
  );
};
