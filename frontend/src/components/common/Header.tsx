import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Bell, Settings } from 'lucide-react';

export const Header: React.FC = () => {
  const navigate = useNavigate();
  const projectName = import.meta.env.VITE_PROJECT_NAME || '';

  return (
    <header className="bg-slate-900 py-3" role="banner">
      <div className="flex items-center justify-between px-6">
        {/* Project Name - Extra left padding to align with content */}
        {projectName && (
          <h2 className="text-3xl font-bold text-white pl-8">{projectName}</h2>
        )}
        <div className={projectName ? '' : 'ml-auto'}></div>
        <div className="flex items-center gap-4" role="toolbar" aria-label="Header actions">
          <button
            className="p-2 text-white hover:bg-slate-800 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-slate-900"
            aria-label="Notifications"
            type="button"
          >
            <Bell size={20} aria-hidden="true" />
          </button>
          <button
            onClick={() => navigate('/settings')}
            className="p-2 text-white hover:bg-slate-800 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-slate-900"
            aria-label="Settings"
            type="button"
          >
            <Settings size={20} aria-hidden="true" />
          </button>
        </div>
      </div>
    </header>
  );
};
