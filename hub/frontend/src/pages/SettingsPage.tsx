import { useState, useEffect } from 'react';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

interface Repository {
  id: number;
  owner: string;
  name: string;
  full_name: string;
  url: string;
}

interface ApiKeyInfo {
  key: string;
  name: string;
  configured: boolean;
  masked_value: string | null;
}

interface Provider {
  alias: string;
  model_id: string;
  api_key_required: string;
  configured: boolean;
  cost_per_1m_input: number | null;
  cost_per_1m_output: number | null;
}

export default function SettingsPage() {
  // Repository state
  const [repositories, setRepositories] = useState<Repository[]>([
    { id: 1, owner: 'PerformanceSuite', name: 'CommandCenter', full_name: 'PerformanceSuite/CommandCenter', url: 'https://github.com/PerformanceSuite/CommandCenter' },
  ]);
  const [showForm, setShowForm] = useState(false);
  const [formData, setFormData] = useState({ owner: '', name: '', access_token: '' });

  // API Keys state
  const [apiKeys, setApiKeys] = useState<ApiKeyInfo[]>([]);
  const [providers, setProviders] = useState<Provider[]>([]);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [newKeyValue, setNewKeyValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error'; text: string } | null>(null);

  // Fetch API keys on mount
  useEffect(() => {
    fetchApiKeys();
    fetchProviders();
  }, []);

  const fetchApiKeys = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/api-keys`);
      if (res.ok) {
        const data = await res.json();
        setApiKeys(data.keys);
      }
    } catch (err) {
      console.error('Failed to fetch API keys:', err);
    }
  };

  const fetchProviders = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/providers`);
      if (res.ok) {
        const data = await res.json();
        setProviders(data.providers);
      }
    } catch (err) {
      console.error('Failed to fetch providers:', err);
    }
  };

  const handleSaveKey = async (keyName: string) => {
    setLoading(true);
    setMessage(null);

    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/api-keys`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          updates: [{ key: keyName, value: newKeyValue }],
        }),
      });

      if (res.ok) {
        setMessage({ type: 'success', text: `${keyName} updated successfully` });
        setEditingKey(null);
        setNewKeyValue('');
        await fetchApiKeys();
        await fetchProviders();
      } else {
        const data = await res.json();
        setMessage({ type: 'error', text: data.detail || 'Failed to update key' });
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to connect to server' });
    } finally {
      setLoading(false);
    }
  };

  const handleRemoveKey = async (keyName: string) => {
    if (!confirm(`Remove ${keyName}?`)) return;

    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/v1/settings/api-keys`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          updates: [{ key: keyName, value: '' }],
        }),
      });

      if (res.ok) {
        setMessage({ type: 'success', text: `${keyName} removed` });
        await fetchApiKeys();
        await fetchProviders();
      }
    } catch (err) {
      setMessage({ type: 'error', text: 'Failed to remove key' });
    } finally {
      setLoading(false);
    }
  };

  // Repository handlers
  const handleAddRepository = (e: React.FormEvent) => {
    e.preventDefault();
    if (!formData.owner || !formData.name) return;

    const newRepo: Repository = {
      id: Date.now(),
      owner: formData.owner,
      name: formData.name,
      full_name: `${formData.owner}/${formData.name}`,
      url: `https://github.com/${formData.owner}/${formData.name}`,
    };
    setRepositories([...repositories, newRepo]);
    setFormData({ owner: '', name: '', access_token: '' });
    setShowForm(false);
  };

  const handleDelete = (id: number) => {
    setRepositories(repositories.filter(r => r.id !== id));
  };

  return (
    <main role="main" className="space-y-8">
      <header className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-white">Settings</h1>
          <p className="text-slate-400 mt-1">Manage API keys, repositories, and system configuration</p>
        </div>
      </header>

      {/* Status Message */}
      {message && (
        <div className={`p-4 rounded-lg ${message.type === 'success' ? 'bg-green-900/50 border border-green-700 text-green-300' : 'bg-red-900/50 border border-red-700 text-red-300'}`}>
          {message.text}
        </div>
      )}

      {/* API Keys Section */}
      <section className="bg-slate-900 rounded-xl p-6 border border-slate-800">
        <h2 className="text-xl font-semibold text-white mb-4">API Keys</h2>
        <p className="text-slate-400 text-sm mb-6">Configure API keys for LLM providers. Keys are stored in your local .env file.</p>

        <div className="space-y-4">
          {apiKeys.map((key) => (
            <div key={key.key} className="flex items-center justify-between p-4 bg-slate-800 rounded-lg">
              <div className="flex-1">
                <div className="flex items-center gap-3">
                  <h3 className="font-medium text-white">{key.name}</h3>
                  <span className={`px-2 py-0.5 text-xs rounded ${key.configured ? 'bg-green-900 text-green-300' : 'bg-slate-700 text-slate-400'}`}>
                    {key.configured ? 'Configured' : 'Not Set'}
                  </span>
                </div>
                <p className="text-sm text-slate-500 mt-1">{key.key}</p>
                {key.configured && key.masked_value && (
                  <p className="text-sm text-slate-400 mt-1 font-mono">{key.masked_value}</p>
                )}
              </div>

              {editingKey === key.key ? (
                <div className="flex items-center gap-2">
                  <input
                    type="password"
                    value={newKeyValue}
                    onChange={(e) => setNewKeyValue(e.target.value)}
                    placeholder="Enter API key..."
                    className="px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white text-sm w-64"
                    autoFocus
                  />
                  <button
                    onClick={() => handleSaveKey(key.key)}
                    disabled={loading || !newKeyValue}
                    className="px-3 py-2 bg-green-600 text-white text-sm rounded hover:bg-green-700 transition-colors disabled:opacity-50"
                  >
                    Save
                  </button>
                  <button
                    onClick={() => { setEditingKey(null); setNewKeyValue(''); }}
                    className="px-3 py-2 bg-slate-600 text-white text-sm rounded hover:bg-slate-500 transition-colors"
                  >
                    Cancel
                  </button>
                </div>
              ) : (
                <div className="flex gap-2">
                  <button
                    onClick={() => setEditingKey(key.key)}
                    className="px-3 py-2 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                  >
                    {key.configured ? 'Update' : 'Add'}
                  </button>
                  {key.configured && (
                    <button
                      onClick={() => handleRemoveKey(key.key)}
                      className="px-3 py-2 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
                    >
                      Remove
                    </button>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </section>

      {/* LLM Providers Section */}
      <section className="bg-slate-900 rounded-xl p-6 border border-slate-800">
        <h2 className="text-xl font-semibold text-white mb-4">LLM Providers</h2>
        <p className="text-slate-400 text-sm mb-6">Available providers for AI Arena hypothesis validation.</p>

        <div className="overflow-x-auto">
          <table className="w-full text-left">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="pb-3 text-sm font-medium text-slate-400">Provider</th>
                <th className="pb-3 text-sm font-medium text-slate-400">Model</th>
                <th className="pb-3 text-sm font-medium text-slate-400">Status</th>
                <th className="pb-3 text-sm font-medium text-slate-400">Cost ($/1M tokens)</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-800">
              {providers.map((provider) => (
                <tr key={provider.alias}>
                  <td className="py-3 text-white font-medium">{provider.alias}</td>
                  <td className="py-3 text-slate-400 font-mono text-sm">{provider.model_id}</td>
                  <td className="py-3">
                    <span className={`px-2 py-1 text-xs rounded ${provider.configured ? 'bg-green-900 text-green-300' : 'bg-yellow-900 text-yellow-300'}`}>
                      {provider.configured ? 'Ready' : `Needs ${provider.api_key_required}`}
                    </span>
                  </td>
                  <td className="py-3 text-slate-400 text-sm">
                    {provider.cost_per_1m_input !== null && (
                      <>In: ${provider.cost_per_1m_input} / Out: ${provider.cost_per_1m_output}</>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>

      {/* Repository Management Section */}
      <section className="bg-slate-900 rounded-xl p-6 border border-slate-800">
        <div className="flex items-center justify-between mb-6">
          <h2 className="text-xl font-semibold text-white">Repository Management</h2>
          <button
            onClick={() => setShowForm(true)}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
          >
            Add Repository
          </button>
        </div>

        {/* Repository Form */}
        {showForm && (
          <form
            data-testid="repository-form"
            onSubmit={handleAddRepository}
            className="mb-6 p-4 bg-slate-800 rounded-lg space-y-4"
          >
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm text-slate-400 mb-1">Owner</label>
                <input
                  type="text"
                  name="owner"
                  value={formData.owner}
                  onChange={(e) => setFormData({ ...formData, owner: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                  placeholder="github-username"
                />
              </div>
              <div>
                <label className="block text-sm text-slate-400 mb-1">Repository Name</label>
                <input
                  type="text"
                  name="name"
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                  placeholder="repository-name"
                />
              </div>
            </div>
            <div>
              <label className="block text-sm text-slate-400 mb-1">Access Token (optional)</label>
              <input
                type="password"
                name="access_token"
                value={formData.access_token}
                onChange={(e) => setFormData({ ...formData, access_token: e.target.value })}
                className="w-full px-3 py-2 bg-slate-700 border border-slate-600 rounded text-white"
                placeholder="ghp_..."
              />
            </div>
            <div className="flex gap-2">
              <button
                type="submit"
                className="px-4 py-2 bg-green-600 text-white rounded hover:bg-green-700 transition-colors"
              >
                Save
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-slate-600 text-white rounded hover:bg-slate-500 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        )}

        {/* Repository List */}
        <div data-testid="repository-list" className="repository-list space-y-3">
          {repositories.length === 0 ? (
            <p className="text-slate-400 text-center py-8">No repositories configured</p>
          ) : (
            repositories.map((repo) => (
              <div
                key={repo.id}
                data-testid="repository-item"
                className="repository-item flex items-center justify-between p-4 bg-slate-800 rounded-lg"
              >
                <div>
                  <h3 className="font-medium text-white">{repo.full_name}</h3>
                  <a href={repo.url} target="_blank" rel="noopener noreferrer" className="text-sm text-slate-400 hover:text-blue-400">
                    {repo.url}
                  </a>
                </div>
                <div className="flex gap-2">
                  <button className="px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors">
                    Sync
                  </button>
                  <button
                    onClick={() => handleDelete(repo.id)}
                    className="px-3 py-1 bg-red-600 text-white text-sm rounded hover:bg-red-700 transition-colors"
                  >
                    Delete
                  </button>
                </div>
              </div>
            ))
          )}
        </div>
      </section>

      {/* System Configuration Section */}
      <section className="bg-slate-900 rounded-xl p-6 border border-slate-800">
        <h2 className="text-xl font-semibold text-white mb-4">System Configuration</h2>
        <div className="grid grid-cols-2 gap-6">
          <div>
            <label className="block text-sm text-slate-400 mb-1">API Endpoint</label>
            <input
              type="text"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
              defaultValue={API_BASE}
              disabled
            />
          </div>
          <div>
            <label className="block text-sm text-slate-400 mb-1">Environment</label>
            <input
              type="text"
              className="w-full px-3 py-2 bg-slate-800 border border-slate-700 rounded text-white"
              defaultValue="development"
              disabled
            />
          </div>
        </div>
      </section>

      {/* Database Section */}
      <section className="bg-slate-900 rounded-xl p-6 border border-slate-800">
        <h2 className="text-xl font-semibold text-white mb-4">Database</h2>
        <div className="text-slate-400">
          <p>SQLite database active</p>
          <p className="text-sm mt-2">Location: ./data/commandcenter.db</p>
        </div>
      </section>
    </main>
  );
}
