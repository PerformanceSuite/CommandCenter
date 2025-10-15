import React, { useMemo } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import { Bell, Settings } from 'lucide-react';

export const Header: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();

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
    <header className="bg-primary-600 px-6 py-3" role="banner">
      <div className="flex items-center justify-end">
        <div className="flex items-center gap-4" role="toolbar" aria-label="Header actions">
          <button
            className="p-2 text-white hover:bg-primary-700 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-primary-600"
            aria-label="Notifications"
            type="button"
          >
            <Bell size={20} aria-hidden="true" />
          </button>
          <button
            onClick={() => navigate('/settings')}
            className="p-2 text-white hover:bg-primary-700 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-white focus:ring-offset-2 focus:ring-offset-primary-600"
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
