import React from 'react';
import { NavLink } from 'react-router-dom';
import {
  LayoutDashboard,
  Radar,
  BookOpen,
  Database,
  Settings,
  Terminal,
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
  { to: '/settings', icon: <Settings size={20} />, label: 'Settings' },
];

export const Sidebar: React.FC = () => {
  return (
    <aside className="w-64 bg-gray-900 text-white h-screen fixed left-0 top-0 flex flex-col">
      <div className="p-6 border-b border-gray-800">
        <div className="flex items-center gap-3">
          <Terminal size={32} className="text-primary-400" />
          <div>
            <h1 className="text-xl font-bold">Command Center</h1>
            <p className="text-xs text-gray-400">Development Hub</p>
          </div>
        </div>
      </div>

      <nav className="flex-1 px-4 py-6">
        <ul className="space-y-2">
          {navItems.map((item) => (
            <li key={item.to}>
              <NavLink
                to={item.to}
                end={item.to === '/'}
                className={({ isActive }) =>
                  `flex items-center gap-3 px-4 py-3 rounded-lg transition-colors ${
                    isActive
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`
                }
              >
                {item.icon}
                <span className="font-medium">{item.label}</span>
              </NavLink>
            </li>
          ))}
        </ul>
      </nav>

      <div className="p-4 border-t border-gray-800">
        <div className="text-xs text-gray-400">
          <p>Version 0.1.0</p>
          <p className="mt-1">Performia &copy; 2025</p>
        </div>
      </div>
    </aside>
  );
};
