import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import ProjectCard from '../components/ProjectCard';
import FolderBrowser from '../components/FolderBrowser';
import { projectsApi, api } from '../services/api';
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
  const [createdProject, setCreatedProject] = useState<Project | null>(null);

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
      setError('Please select a folder and enter a project name');
      return;
    }

    setCreatingProject(true);
    setError(null);

    try {
      const newProject = await projectsApi.create({
        name: projectName.trim(),
        path: selectedPath,
      });

      // Reload projects to show the new project in the list
      await loadProjects();

      // Store the created project after reload (prevents race condition)
      setCreatedProject(newProject);

      // Clear error/success messages
      setError(null);
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to create project';
      setError(`Failed to create project: ${errorMsg}`);
      console.error('Project creation error:', err);
    } finally {
      setCreatingProject(false);
    }
  };

  const handleOpenProject = async () => {
    if (!createdProject) return;

    // Open immediately
    window.open(`http://localhost:${createdProject.frontend_port}`, '_blank');

    // Start in the background if stopped
    if (createdProject.status === 'stopped') {
      try {
        await api.orchestration.start(createdProject.id);
        // Show success notification after a short delay
        setTimeout(() => {
          toast.success(`Project "${createdProject.name}" is starting...`);
        }, 1000);
      } catch (error) {
        console.error('Failed to start project:', error);
        // Show error notification after a delay
        setTimeout(() => {
          toast.error(`Failed to start "${createdProject.name}". Check the logs for details.`);
        }, 2000);
      }
    }

    // Reset form after opening
    setProjectName('');
    setSelectedPath(null);
    setCreatedProject(null);
  };

  const handleCancelCreate = () => {
    setProjectName('');
    setSelectedPath(null);
    setCreatedProject(null);
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

      {/* Error/Success Display */}
      {error && (
        <div className={`mb-6 p-4 rounded-lg ${
          error.startsWith('✓')
            ? 'bg-green-900/20 border border-green-500/30'
            : 'bg-red-900/20 border border-red-500/30'
        }`}>
          <p className={error.startsWith('✓') ? 'text-green-400' : 'text-red-400'}>{error}</p>
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

            <div className="space-y-2">
              <div className="p-3 bg-blue-900/20 border border-blue-500/30 rounded">
                <p className="text-sm text-blue-300">
                  CommandCenter will be cloned into: <span className="font-mono">{selectedPath}/commandcenter</span>
                </p>
              </div>

              {createdProject && (
                <div className="p-3 bg-green-900/20 border border-green-500/30 rounded">
                  <p className="text-sm text-green-300">
                    Project will be available at: <span className="font-mono font-bold">localhost:{createdProject.frontend_port}</span>
                  </p>
                </div>
              )}
            </div>

            <div className="flex gap-3">
              {!createdProject ? (
                <>
                  <button
                    onClick={handleCreateProject}
                    disabled={creatingProject || !projectName.trim()}
                    className="btn-success relative"
                  >
                    {creatingProject ? (
                      <span className="flex items-center gap-2">
                        Creating
                        <span className="inline-flex gap-0.5">
                          <span className="animate-bounce" style={{ animationDelay: '0ms' }}>.</span>
                          <span className="animate-bounce" style={{ animationDelay: '150ms' }}>.</span>
                          <span className="animate-bounce" style={{ animationDelay: '300ms' }}>.</span>
                        </span>
                      </span>
                    ) : (
                      'Create Project'
                    )}
                  </button>
                  <button
                    onClick={handleCancelCreate}
                    disabled={creatingProject}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                </>
              ) : (
                <>
                  <button
                    onClick={handleOpenProject}
                    className="btn-primary px-8"
                  >
                    Open
                  </button>
                  <button
                    onClick={handleCancelCreate}
                    className="btn-secondary"
                  >
                    Cancel
                  </button>
                </>
              )}
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
