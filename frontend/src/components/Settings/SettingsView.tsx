import React from 'react';
import { RepositoryManager } from './RepositoryManager';

export const SettingsView: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">Repository Management</h2>
        <RepositoryManager />
      </div>

      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-xl font-bold mb-4">General Settings</h2>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              API Endpoint
            </label>
            <input
              type="text"
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              placeholder="http://localhost:8000"
              readOnly
              value={import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}
            />
          </div>
        </div>
      </div>
    </div>
  );
};
