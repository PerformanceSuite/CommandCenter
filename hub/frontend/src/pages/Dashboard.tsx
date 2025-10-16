import { useState, useEffect } from 'react';
import toast from 'react-hot-toast';
import ProjectCard from '../components/ProjectCard';
import FolderBrowser from '../components/FolderBrowser';
import { projectsApi, api } from '../services/api';
import type { Project, ProjectStats } from '../types';

// Constants for container startup
const CONTAINER_STARTUP_TIMEOUT_SECONDS = 90;
const HEALTH_CHECK_INTERVAL_MS = 1000;
const BACKEND_HEALTH_CHECK_TIMEOUT_MS = 5000;

// Toast messages
const TOAST_MESSAGES = {
  CREATING: (name: string) => `Creating ${name}...`,
  STARTING: (name: string) => `Starting containers for ${name}...`,
  WAITING: (name: string) => `Waiting for ${name} to be ready...`,
  VERIFYING: (name: string) => `Verifying ${name} backend is ready...`,
  OPENING: (name: string) => `Opening ${name} in new tab...`,
  SUCCESS: (name: string) => `${name} opened successfully!`,
  TIMEOUT: (name: string, port: number) =>
    `Timeout waiting for ${name}. It may still be starting. Try opening manually at localhost:${port}`,
  POPUP_BLOCKED: (port: number) =>
    `Pop-up blocked! Please allow pop-ups or click the "Open Manually" button to access localhost:${port}`,
  BACKEND_NOT_READY: (name: string) =>
    `Containers started but ${name} backend is not responding yet. Continuing to wait...`,
};

function Dashboard() {
  const [projects, setProjects] = useState<Project[]>([]);
  const [stats, setStats] = useState<ProjectStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showBrowser, setShowBrowser] = useState(false);
  const [creatingProject, setCreatingProject] = useState(false);
  const [projectName, setProjectName] = useState('');
  const [selectedPath, setSelectedPath] = useState<string | null>(null);
  const [failedProject, setFailedProject] = useState<Project | null>(null);

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

  /**
   * Verify backend is actually responding by polling the /health endpoint
   */
  const verifyBackendHealth = async (port: number): Promise<boolean> => {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), BACKEND_HEALTH_CHECK_TIMEOUT_MS);

      await fetch(`http://localhost:${port}/health`, {
        signal: controller.signal,
        mode: 'no-cors', // Allow cross-origin for localhost
      });

      clearTimeout(timeoutId);

      // In no-cors mode, we can't read response, but if fetch succeeds, backend is responding
      return true;
    } catch (err) {
      // Network error or timeout means backend not ready
      return false;
    }
  };

  const handleCreateProject = async () => {
    if (!selectedPath || !projectName.trim()) {
      setError('Please select a folder and enter a project name');
      return;
    }

    setCreatingProject(true);
    setError(null);
    setFailedProject(null);

    // Open blank tab immediately (before async operations) to avoid pop-up blocker
    const newTab = window.open('about:blank', '_blank', 'noopener,noreferrer');

    try {
      // Step 1: Create the project
      toast.loading(TOAST_MESSAGES.CREATING(projectName), {
        id: 'create-flow',
        duration: Infinity,
        position: 'bottom-center',
      });

      const newProject = await projectsApi.create({
        name: projectName.trim(),
        path: selectedPath,
      });

      // Step 2: Automatically start the containers
      toast.loading(TOAST_MESSAGES.STARTING(projectName), {
        id: 'create-flow',
        duration: Infinity,
        position: 'bottom-center',
      });

      await api.orchestration.start(newProject.id);

      // Step 3: Wait for containers to be healthy
      toast.loading(TOAST_MESSAGES.WAITING(projectName), {
        id: 'create-flow',
        duration: Infinity,
        position: 'bottom-center',
      });

      let attempts = 0;
      const maxAttempts = CONTAINER_STARTUP_TIMEOUT_SECONDS;
      let isReady = false;

      while (attempts < maxAttempts) {
        await new Promise(resolve => setTimeout(resolve, HEALTH_CHECK_INTERVAL_MS));

        try {
          const status = await api.orchestration.status(newProject.id);

          if (status.status === 'running' && status.health === 'healthy') {
            // Step 3.5: Verify backend is actually responding
            toast.loading(TOAST_MESSAGES.VERIFYING(projectName), {
              id: 'create-flow',
              duration: Infinity,
              position: 'bottom-center',
            });

            const backendHealthy = await verifyBackendHealth(newProject.backend_port);

            if (backendHealthy) {
              isReady = true;

              // Step 4: Update the tab we opened earlier
              toast.loading(TOAST_MESSAGES.OPENING(projectName), {
                id: 'create-flow',
                duration: Infinity,
                position: 'bottom-center',
              });

              const cacheBreaker = Date.now();
              const url = `http://localhost:${newProject.frontend_port}/?v=${cacheBreaker}`;

              if (newTab && !newTab.closed) {
                newTab.location.href = url;
                newTab.focus();
                toast.success(TOAST_MESSAGES.SUCCESS(projectName), {
                  id: 'create-flow',
                  duration: 3000,
                  position: 'bottom-center',
                });
              } else {
                // Tab was closed or blocked
                toast.error(TOAST_MESSAGES.POPUP_BLOCKED(newProject.frontend_port), {
                  id: 'create-flow',
                  duration: 10000,
                  position: 'bottom-center',
                });
                setFailedProject(newProject);
              }

              // Reset form after short delay
              setTimeout(() => {
                setProjectName('');
                setSelectedPath(null);
              }, 1500);

              break;
            } else {
              // Containers healthy but backend not responding yet
              if (attempts % 10 === 0) {
                console.log(TOAST_MESSAGES.BACKEND_NOT_READY(projectName));
              }
            }
          }
        } catch (statusErr) {
          console.log('Status check attempt', attempts, statusErr);
        }

        attempts++;
      }

      if (!isReady) {
        // Close the blank tab if still open
        if (newTab && !newTab.closed) {
          newTab.close();
        }

        toast.error(TOAST_MESSAGES.TIMEOUT(projectName, newProject.frontend_port), {
          id: 'create-flow',
          duration: Infinity,
          position: 'bottom-center',
        });
        setFailedProject(newProject);
      }

      // Reload projects to show updated status
      await loadProjects();

      setError(null);
    } catch (err) {
      // Close the blank tab if still open
      if (newTab && !newTab.closed) {
        newTab.close();
      }

      const errorMsg = err instanceof Error ? err.message : 'Failed to create project';
      setError(`Failed to create project: ${errorMsg}`);
      toast.error(errorMsg, {
        id: 'create-flow',
        duration: 5000,
        position: 'bottom-center',
      });
      console.error('Project creation error:', err);
    } finally {
      setCreatingProject(false);
    }
  };

  const handleOpenManually = () => {
    if (!failedProject) return;

    const cacheBreaker = Date.now();
    const url = `http://localhost:${failedProject.frontend_port}/?v=${cacheBreaker}`;
    const newTab = window.open(url, '_blank', 'noopener,noreferrer');

    if (newTab) {
      newTab.focus();
      toast.success(TOAST_MESSAGES.SUCCESS(failedProject.name), {
        duration: 3000,
        position: 'bottom-center',
      });
      setFailedProject(null);
      setProjectName('');
      setSelectedPath(null);
    } else {
      toast.error(TOAST_MESSAGES.POPUP_BLOCKED(failedProject.frontend_port), {
        duration: 5000,
        position: 'bottom-center',
      });
    }
  };

  const handleRetryStartup = async () => {
    if (!failedProject) return;

    setCreatingProject(true);
    toast.dismiss();

    try {
      // Restart containers
      toast.loading(TOAST_MESSAGES.STARTING(failedProject.name), {
        id: 'retry-flow',
        duration: Infinity,
        position: 'bottom-center',
      });

      await api.orchestration.start(failedProject.id);

      toast.success(`${failedProject.name} restarted. Try opening it now.`, {
        id: 'retry-flow',
        duration: 5000,
        position: 'bottom-center',
      });

      await loadProjects();
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Failed to restart';
      toast.error(errorMsg, {
        id: 'retry-flow',
        duration: 5000,
        position: 'bottom-center',
      });
    } finally {
      setCreatingProject(false);
    }
  };

  const handleCancelCreate = () => {
    setProjectName('');
    setSelectedPath(null);
    setFailedProject(null);
    toast.dismiss();
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

            <div className="p-3 bg-blue-900/20 border border-blue-500/30 rounded">
              <p className="text-sm text-blue-300">
                CommandCenter will be cloned into: <span className="font-mono">{selectedPath}/commandcenter</span>
              </p>
              <p className="text-sm text-blue-300 mt-2">
                Project will automatically open when ready
              </p>
            </div>

            <div className="relative">
              <div id="toast-container" className="mb-4"></div>

              {/* Recovery options if project creation timed out */}
              {failedProject && (
                <div className="mb-4 p-4 bg-yellow-900/20 border border-yellow-500/30 rounded">
                  <p className="text-sm text-yellow-300 mb-3">
                    <strong>{failedProject.name}</strong> may still be starting up. You can:
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={handleOpenManually}
                      className="btn-primary text-sm px-4 py-2"
                    >
                      Open Manually
                    </button>
                    <button
                      onClick={handleRetryStartup}
                      disabled={creatingProject}
                      className="btn-secondary text-sm px-4 py-2"
                    >
                      Retry Startup
                    </button>
                    <button
                      onClick={() => setFailedProject(null)}
                      className="btn-secondary text-sm px-4 py-2"
                    >
                      Dismiss
                    </button>
                  </div>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={handleCreateProject}
                  disabled={creatingProject || !projectName.trim()}
                  className="btn-success relative"
                >
                  {creatingProject ? 'Creating Project...' : 'Create Project'}
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
