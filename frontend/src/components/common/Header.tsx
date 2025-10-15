import React, { useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Bell, Settings } from 'lucide-react';

export const Header: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

  // Get project name from environment variable (set by Hub during deployment)
  const projectName = import.meta.env.VITE_PROJECT_NAME || 'Command Center';

  const pageTitle = useMemo(() => {
    const path = location.pathname;
    if (path === '/') return 'Dashboard';
    if (path === '/projects') return 'Projects';
    if (path === '/radar') return 'Technology Radar';
    if (path === '/research') return 'Research Hub';
    if (path === '/knowledge') return 'Knowledge Base';
    if (path === '/settings') return 'Settings';
    return 'Command Center';
  }, [location.pathname]);

  const currentDate = useMemo(
    () => new Date().toLocaleDateString('en-US', {
      weekday: 'long',
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    }),
    []
  );

  return (
    <header className="bg-slate-800/50 border-b border-slate-700/50 px-6 py-4" role="banner">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-white">{pageTitle}</h1>
          <p className="text-sm text-slate-400 mt-1" aria-label={`Current date: ${currentDate}`}>
            <time dateTime={new Date().toISOString()}>
              {currentDate}
            </time>
          </p>
        </div>

        <div className="flex items-center gap-4" role="toolbar" aria-label="Header actions">
          {/* Project Name Badge */}
          <div className="px-4 py-2 bg-slate-700 text-white rounded-lg font-semibold text-sm">
            {projectName}
          </div>

          <button
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-slate-800"
            aria-label="Notifications"
            type="button"
          >
            <Bell size={20} aria-hidden="true" />
          </button>
          <button
            onClick={() => navigate('/settings')}
            className="p-2 text-slate-400 hover:text-white hover:bg-slate-700 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-slate-800"
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
