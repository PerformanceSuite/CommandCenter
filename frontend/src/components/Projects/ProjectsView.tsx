import { useState } from 'react';
import { Plus, Trash2, Edit2, FolderOpen, Database, FileText, Beaker } from 'lucide-react';
import { useProjects } from '../../hooks/useProjects';
import { Project, ProjectCreate } from '../../types/project';
import { ProjectForm } from './ProjectForm';
import { projectApi } from '../../services/projectApi';

export const ProjectsView = () => {
  const { projects, loading, error, createProject, updateProject, deleteProject } = useProjects();
  const [showForm, setShowForm] = useState(false);
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [projectStats, setProjectStats] = useState<Record<number, any>>({});

  const handleCreate = async (data: ProjectCreate) => {
    try {
      await createProject(data);
      setShowForm(false);
    } catch (err) {
      console.error('Failed to create project:', err);
    }
  };

  const handleUpdate = async (data: ProjectCreate) => {
    if (!editingProject) return;
    try {
      await updateProject(editingProject.id, data);
      setEditingProject(null);
      setShowForm(false);
    } catch (err) {
      console.error('Failed to update project:', err);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this project? This will delete ALL associated data.')) {
      return;
    }
    try {
      await deleteProject(id);
      // Clear from localStorage if it was selected
      if (localStorage.getItem('selected_project_id') === id.toString()) {
        localStorage.removeItem('selected_project_id');
      }
    } catch (err) {
      console.error('Failed to delete project:', err);
    }
  };

  const handleEdit = (project: Project) => {
    setEditingProject(project);
    setShowForm(true);
  };

  const handleCancelForm = () => {
    setShowForm(false);
    setEditingProject(null);
  };

  const loadProjectStats = async (projectId: number) => {
    try {
      const stats = await projectApi.getProjectStats(projectId);
      setProjectStats(prev => ({ ...prev, [projectId]: stats }));
    } catch (err) {
      console.error('Failed to load project stats:', err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <p className="text-red-800">Error: {error}</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white">Projects</h2>
          <p className="text-slate-500 mt-1">Manage your research and development projects</p>
        </div>
        <button
          onClick={() => setShowForm(true)}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
        >
          <Plus className="w-5 h-5" />
          <span>New Project</span>
        </button>
      </div>

      {/* Project Form Modal */}
      {showForm && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-slate-800 border border-slate-700 rounded-lg p-6 max-w-md w-full mx-4">
            <h3 className="text-xl font-bold mb-4">
              {editingProject ? 'Edit Project' : 'Create New Project'}
            </h3>
            <ProjectForm
              initialData={editingProject || undefined}
              onSubmit={editingProject ? handleUpdate : handleCreate}
              onCancel={handleCancelForm}
            />
          </div>
        </div>
      )}

      {/* Project List */}
      {projects.length === 0 ? (
        <div className="text-center py-12 bg-slate-900 rounded-lg border-2 border-dashed border-gray-300">
          <FolderOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-lg font-medium text-white mb-2">No projects yet</h3>
          <p className="text-slate-500 mb-4">Create your first project to get started</p>
          <button
            onClick={() => setShowForm(true)}
            className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
          >
            <Plus className="w-5 h-5" />
            <span>Create Project</span>
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {projects.map((project) => (
            <div
              key={project.id}
              className="bg-slate-800 border-gray-200 rounded-lg p-6 hover:shadow-lg transition-shadow"
              onMouseEnter={() => !projectStats[project.id] && loadProjectStats(project.id)}
            >
              {/* Project Header */}
              <div className="flex items-start justify-between mb-4">
                <div className="flex items-start gap-3 flex-1">
                  <div className="p-2 bg-blue-100 rounded-lg">
                    <FolderOpen className="w-6 h-6 text-blue-600" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <h3 className="font-semibold text-white truncate">{project.name}</h3>
                    <p className="text-sm text-slate-500 mt-1">Owner: {project.owner}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    onClick={() => handleEdit(project)}
                    className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 rounded transition-colors"
                    title="Edit project"
                  >
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button
                    onClick={() => handleDelete(project.id)}
                    className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 rounded transition-colors"
                    title="Delete project"
                  >
                    <Trash2 className="w-4 h-4" />
                  </button>
                </div>
              </div>

              {/* Description */}
              {project.description && (
                <p className="text-sm text-slate-400 mb-4 line-clamp-2">{project.description}</p>
              )}

              {/* Stats */}
              {projectStats[project.id] && (
                <div className="grid grid-cols-2 gap-3 pt-4 border-t border-gray-100">
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-gray-400" />
                    <div>
                      <div className="text-xs text-slate-500">Repositories</div>
                      <div className="text-sm font-semibold text-white">
                        {projectStats[project.id].total_repositories || 0}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Beaker className="w-4 h-4 text-gray-400" />
                    <div>
                      <div className="text-xs text-slate-500">Technologies</div>
                      <div className="text-sm font-semibold text-white">
                        {projectStats[project.id].total_technologies || 0}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <FileText className="w-4 h-4 text-gray-400" />
                    <div>
                      <div className="text-xs text-slate-500">Research</div>
                      <div className="text-sm font-semibold text-white">
                        {projectStats[project.id].total_research_tasks || 0}
                      </div>
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    <Database className="w-4 h-4 text-gray-400" />
                    <div>
                      <div className="text-xs text-slate-500">Knowledge</div>
                      <div className="text-sm font-semibold text-white">
                        {projectStats[project.id].total_knowledge_entries || 0}
                      </div>
                    </div>
                  </div>
                </div>
              )}

              {/* Dates */}
              <div className="mt-4 pt-4 border-t border-gray-100 text-xs text-gray-400">
                Created {new Date(project.created_at).toLocaleDateString()}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
