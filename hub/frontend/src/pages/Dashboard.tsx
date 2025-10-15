import { useState, useEffect } from 'react';
import ProjectCard from '../components/ProjectCard';
import FolderBrowser from '../components/FolderBrowser';
import { projectsApi } from '../services/api';
import type { Project, ProjectStats } from '../types';

function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBrowser, setShowBrowser] = useState(false);
  const [creatingProject, setCreatingProject] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [selectedPath, setSelectedPath] = useState<string | null>(null);

  const loadProjects = async () => {
    try {
      setError(null);
      const [projectsData, statsData] = await Promise.all([
        projectsApi.list(),
        projectsApi.stats(),
      ]);
      setProjects(projectsData);
      setStats(statsData);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load projects');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadProjects();
    // Poll for updates every 5 seconds
    const interval = setInterval(loadProjects, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleFolderSelect = (path: string) => {
    setSelectedPath(path);
    setShowBrowser(false);
    // Suggest project name from folder name
    const folderName = path.split('/').pop() || 'project';
    setProjectName(folderName.charAt(0).toUpperCase() + folderName.slice(1));
  };

  const handleCreateProject = async () => {
    if (!selectedPath || !projectName.trim()) {
      alert('Please select a folder and enter a project name');
      return;
    }

    setCreatingProject(true);
    setError(null);

    try {
      await projectsApi.create({
        name: projectName.trim(),
        path: selectedPath,
      });

      // Reset form
      setProjectName('');
      setSelectedPath(null);

      // Reload projects
      await loadProjects();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create project');
    } finally {
      setCreatingProject(false);
    }
  };

  const handleCancelCreate = () => {
    setProjectName('');
    setSelectedPath(null);
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-20">
        <div className="text-slate-400 text-lg">Loading projects...</div>
      </div>
    );
  }

  return (
    <div>
      {/* Stats Bar */}
      {stats && (
        <div className="grid grid-cols-4 gap-4 mb-8">
          <div className="card">
            <div className="text-slate-400 text-sm">Total Projects</div>
            <div className="text-2xl font-bold text-white mt-1">{stats.total_projects}</div>
          </div>
          <div className="card">
            <div className="text-slate-400 text-sm">Running</div>
            <div className="text-2xl font-bold text-green-400 mt-1">{stats.running}</div>
          </div>
          <div className="card">
            <div className="text-slate-400 text-sm">Stopped</div>
            <div className="text-2xl font-bold text-gray-400 mt-1">{stats.stopped}</div>
          </div>
          <div className="card">
            <div className="text-slate-400 text-sm">Errors</div>
            <div className="text-2xl font-bold text-red-400 mt-1">{stats.errors}</div>
          </div>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="mb-6 p-4 bg-red-900/20 border border-red-500/30 rounded-lg">
          <p className="text-red-400">{error}</p>
        </div>
      )}

      {/* Add Project Section */}
      <div className="card mb-8">
        <h2 className="text-xl font-bold text-white mb-4">Add New Project</h2>

        {selectedPath ? (
          <div className="space-y-4">
            <div>
              <label className="block text-sm text-slate-400 mb-2">Project Folder:</label>
              <div className="font-mono text-sm bg-slate-950 border border-slate-700 rounded px-4 py-2 text-white">
                {selectedPath}
              </div>
            </div>

            <div>
              <label className="block text-sm text-slate-400 mb-2">Project Name:</label>
              <input
                type="text"
                value={projectName}
                onChange={(e) => setProjectName(e.target.value)}
                className="input-field"
                placeholder="e.g., Performia"
              />
            </div>

            <div className="p-3 bg-blue-900/20 border border-blue-500/30 rounded">
              <p className="text-sm text-blue-300">
                CommandCenter will be cloned into: <span className="font-mono">{selectedPath}/commandcenter</span>
              </p>
            </div>

            <div className="flex gap-3">
              <button
                onClick={handleCreateProject}
                disabled={creatingProject || !projectName.trim()}
                className="btn-success"
              >
                {creatingProject ? 'Creating...' : 'Create Project'}
              </button>
              <button
                onClick={handleCancelCreate}
                disabled={creatingProject}
                className="btn-secondary"
              >
                Cancel
              </button>
            </div>
          </div>
        ) : (
          <button
            onClick={() => setShowBrowser(true)}
            className="btn-primary"
          >
            + Add New Project
          </button>
        )}
      </div>

      {/* Projects List */}
      {projects.length > 0 ? (
        <div>
          <h2 className="text-xl font-bold text-white mb-4">Your Projects</h2>
          <div className="space-y-3">
            {projects.map((project) => (
              <ProjectCard
                key={project.id}
                project={project}
                onDelete={loadProjects}
              />
            ))}
          </div>
        </div>
      ) : (
        <div className="text-center py-12">
          <p className="text-slate-400 text-lg">No projects yet. Add your first project above!</p>
        </div>
      )}

      {/* Folder Browser Modal */}
      {showBrowser && (
        <FolderBrowser
          onSelect={handleFolderSelect}
          onClose={() => setShowBrowser(false)}
        />
      )}
    </div>
  );
}

export default Dashboard;
