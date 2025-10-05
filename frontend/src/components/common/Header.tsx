import React from 'react';
import { useLocation } from 'react-router-dom';
import { Bell, Settings } from 'lucide-react';

export const Header: React.FC = () => {
  const location = useLocation();

  const getPageTitle = () => {
    const path = location.pathname;
    if (path === '/') return 'Dashboard';
    if (path === '/radar') return 'Technology Radar';
    if (path === '/research') return 'Research Hub';
    if (path === '/knowledge') return 'Knowledge Base';
    if (path === '/settings') return 'Settings';
    return 'Command Center';
  };

  return (
    <header className="bg-white border-b border-gray-200 px-6 py-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-2xl font-bold text-gray-900">{getPageTitle()}</h1>
          <p className="text-sm text-gray-500 mt-1">
            {new Date().toLocaleDateString('en-US', {
              weekday: 'long',
              year: 'numeric',
              month: 'long',
              day: 'numeric',
            })}
          </p>
        </div>

        <div className="flex items-center gap-4">
          <button
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Notifications"
          >
            <Bell size={20} />
          </button>
          <button
            className="p-2 text-gray-500 hover:text-gray-700 hover:bg-gray-100 rounded-lg transition-colors"
            title="Settings"
          >
            <Settings size={20} />
          </button>
        </div>
      </div>
    </header>
  );
};
