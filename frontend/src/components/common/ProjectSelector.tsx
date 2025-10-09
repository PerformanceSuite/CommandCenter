import React, { useState, useEffect } from 'react';
import api from '../../services/api';

interface Project {
  id: number;
  name: string;
  owner: string;
}

export const ProjectSelector: React.FC = () => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [selectedProject, setSelectedProject] = useState<string | null>(
    localStorage.getItem('project_id')
  );
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Fetch available projects
    const fetchProjects = async () => {
      try {
        const response = await api.getProjects();
        setProjects(response);

        // If no project selected, select first one
        if (!selectedProject && response.length > 0) {
          handleProjectChange(response[0].id.toString());
        }
      } catch (error) {
        console.error('Failed to fetch projects:', error);
        // If projects endpoint doesn't exist yet, create a default project
        setProjects([{ id: 1, name: 'Default Project', owner: 'system' }]);
        if (!selectedProject) {
          handleProjectChange('1');
        }
      } finally {
        setLoading(false);
      }
    };

    fetchProjects();
  }, []);

  const handleProjectChange = (projectId: string) => {
    setSelectedProject(projectId);

    // Save to localStorage
    localStorage.setItem('project_id', projectId);

    // Trigger a custom event that api.ts can listen to
    window.dispatchEvent(new CustomEvent('projectChanged', { detail: { projectId } }));

    // Reload page to refresh data for new project
    window.location.reload();
  };

  if (loading) {
    return <div className="text-sm text-gray-500">Loading projects...</div>;
  }

  if (projects.length === 0) {
    return <div className="text-sm text-red-500">No projects available</div>;
  }

  return (
    <div className="flex items-center gap-2">
      <label htmlFor="project-select" className="text-sm font-medium text-gray-700">
        Project:
      </label>
      <select
        id="project-select"
        value={selectedProject || ''}
        onChange={(e) => handleProjectChange(e.target.value)}
        className="px-3 py-1.5 border border-gray-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
      >
        {projects.map((project) => (
          <option key={project.id} value={project.id}>
            {project.name}
          </option>
        ))}
      </select>
    </div>
  );
};
