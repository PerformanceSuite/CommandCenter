import React, { useState, useEffect } from 'react';
import { Key, Server, User, CheckCircle, XCircle } from 'lucide-react';
import { RepositoryManager } from './RepositoryManager';

interface ApiKeyStatus {
  name: string;
  key: string;
  configured: boolean;
  maskedValue?: string;
}

export const SettingsView: React.FC = () => {
  const [apiKeys, setApiKeys] = useState<ApiKeyStatus[]>([]);

  useEffect(() => {
    // Check environment variables for API key configuration
    const keys: ApiKeyStatus[] = [
      {
        name: 'Anthropic API Key',
        key: 'VITE_ANTHROPIC_API_KEY',
        configured: !!import.meta.env.VITE_ANTHROPIC_API_KEY,
        maskedValue: import.meta.env.VITE_ANTHROPIC_API_KEY
          ? maskApiKey(import.meta.env.VITE_ANTHROPIC_API_KEY)
          : undefined
      },
      {
        name: 'OpenAI API Key',
        key: 'VITE_OPENAI_API_KEY',
        configured: !!import.meta.env.VITE_OPENAI_API_KEY,
        maskedValue: import.meta.env.VITE_OPENAI_API_KEY
          ? maskApiKey(import.meta.env.VITE_OPENAI_API_KEY)
          : undefined
      },
      {
        name: 'GitHub Token',
        key: 'VITE_GITHUB_TOKEN',
        configured: !!import.meta.env.VITE_GITHUB_TOKEN,
        maskedValue: import.meta.env.VITE_GITHUB_TOKEN
          ? maskApiKey(import.meta.env.VITE_GITHUB_TOKEN)
          : undefined
      }
    ];
    setApiKeys(keys);
  }, []);

  const maskApiKey = (key: string): string => {
    if (key.length <= 8) return '***';
    const prefix = key.substring(0, 7);
    const suffix = key.substring(key.length - 4);
    return `${prefix}***...***${suffix}`;
  };

  return (
    <div className="space-y-6">
      {/* API Key Management */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Key className="text-primary-600" size={24} />
          <h2 className="text-xl font-bold">API Key Management</h2>
        </div>
        <p className="text-sm text-slate-400 mb-4">
          API keys are configured via environment variables for security. Keys are managed in the backend .env file.
        </p>
        <div className="space-y-3">
          {apiKeys.map((apiKey) => (
            <div
              key={apiKey.key}
              className="flex items-center justify-between p-4 border border-slate-700 rounded-lg"
            >
              <div className="flex items-center gap-3">
                {apiKey.configured ? (
                  <CheckCircle className="text-green-500" size={20} />
                ) : (
                  <XCircle className="text-red-500" size={20} />
                )}
                <div>
                  <div className="font-medium text-white">{apiKey.name}</div>
                  <div className="text-xs text-slate-500">{apiKey.key}</div>
                </div>
              </div>
              <div className="text-right">
                {apiKey.configured ? (
                  <div>
                    <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
                      Configured
                    </span>
                    <div className="text-xs text-slate-500 mt-1 font-mono">
                      {apiKey.maskedValue}
                    </div>
                  </div>
                ) : (
                  <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
                    Not Configured
                  </span>
                )}
              </div>
            </div>
          ))}
        </div>
        <div className="mt-4 p-3 bg-primary-900/30 border border-primary-700 rounded-lg">
          <p className="text-sm text-primary-200">
            <strong>Note:</strong> To configure API keys, update the backend <code className="bg-primary-800 px-1 rounded">.env</code> file and restart the services.
          </p>
        </div>
      </div>

      {/* Repository Management */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Server className="text-primary-600" size={24} />
          <h2 className="text-xl font-bold">Repository Management</h2>
        </div>
        <RepositoryManager />
      </div>

      {/* System Configuration */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <Server className="text-primary-600" size={24} />
          <h2 className="text-xl font-bold">System Configuration</h2>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Backend API Endpoint
            </label>
            <input
              type="text"
              className="w-full px-4 py-2 border border-slate-700 rounded-lg bg-slate-900 text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              readOnly
              value={import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'}
            />
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Environment
            </label>
            <input
              type="text"
              className="w-full px-4 py-2 border border-slate-700 rounded-lg bg-slate-900 text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              readOnly
              value={import.meta.env.MODE || 'development'}
            />
          </div>
        </div>
      </div>

      {/* User Preferences */}
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow p-6">
        <div className="flex items-center gap-2 mb-4">
          <User className="text-primary-600" size={24} />
          <h2 className="text-xl font-bold">User Preferences</h2>
        </div>
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Theme
            </label>
            <select
              className="w-full px-4 py-2 border border-slate-700 rounded-lg bg-slate-900 text-white focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              defaultValue="dark"
            >
              <option value="dark">Dark</option>
              <option value="light">Light (Coming Soon)</option>
              <option value="auto">Auto (Coming Soon)</option>
            </select>
          </div>
          <div>
            <label className="block text-sm font-medium text-slate-300 mb-2">
              Notifications
            </label>
            <div className="space-y-2">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  defaultChecked
                />
                <span className="ml-2 text-sm text-slate-300">
                  Repository sync notifications
                </span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                  defaultChecked
                />
                <span className="ml-2 text-sm text-slate-300">
                  Research task updates
                </span>
              </label>
              <label className="flex items-center">
                <input
                  type="checkbox"
                  className="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
                />
                <span className="ml-2 text-sm text-slate-300">
                  Technology radar changes
                </span>
              </label>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
