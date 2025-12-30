import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Radar,
  BookOpen,
  Database,
  Settings,
  Terminal,
  Sparkles,
} from 'lucide-react';

interface NavItem {
  to: string;
  icon: React.ReactNode;
  label: string;
}

const navItems: NavItem[] = [
  { to: '/', icon: <LayoutDashboard size={20} />, label: 'Dashboard' },
  { to: '/radar', icon: <Radar size={20} />, label: 'Tech Radar' },
  { to: '/research', icon: <BookOpen size={20} />, label: 'Research Hub' },
  { to: '/knowledge', icon: <Database size={20} />, label: 'Knowledge Base' },
  { to: '/arena', icon: <Sparkles size={20} />, label: 'AI Arena' },
  { to: '/settings', icon: <Settings size={20} />, label: 'Settings' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside
      className="w-64 bg-gray-900 text-white h-screen fixed left-0 top-0 flex flex-col"
      aria-label="Main navigation"
      role="complementary"
    >
      {/* Logo/Hub Link - Aligns with header */}
      <div className="px-6 py-6 flex items-center">
        <a
          href="http://localhost:9000"
          className="flex items-center gap-2 hover:opacity-80 transition-opacity"
          aria-label="Back to Command Center Hub"
        >
          <Terminal size={24} className="text-primary-400" aria-hidden="true" />
          <h1 className="text-xl font-bold bg-gradient-to-r from-blue-400 via-blue-500 to-blue-600 bg-clip-text text-transparent whitespace-nowrap leading-none">
            Command Center
          </h1>
        </a>
      </div>

      <nav className="flex-1 px-4 pt-2 pb-6" aria-label="Primary navigation">
        <ul className="space-y-2" role="list">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors focus:outline-none focus:ring-2 focus:ring-primary-500 focus:ring-offset-2 focus:ring-offset-gray-900 ${
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`
                }
                aria-label={item.label}
              >
                {({ isActive }) => (
                  <>
                    <span aria-hidden="true">{item.icon}</span>
                    <span className="font-medium">{item.label}</span>
                    {isActive && <span className="sr-only">(current page)</span>}
                  </>
                )}
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t border-gray-800" role="contentinfo">
        <div className="text-xs text-gray-400">
          <p>Version 0.1.0</p>
          <p className="mt-1">&copy; 2025</p>
        </div>
      </div>
    </aside>
  );
};
