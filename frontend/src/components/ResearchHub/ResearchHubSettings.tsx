import { useState, useEffect } from 'react';
import { Key, Cpu, Bot, CheckCircle, XCircle, RefreshCw, Save } from 'lucide-react';

interface ApiKeyInfo {
  key: string;
  name: string;
  configured: boolean;
  masked_value?: string;
}

interface ModelInfo {
  id: string;
  name: string;
  cost_per_1m_input: number | null;
  cost_per_1m_output: number | null;
  configured: boolean;
}

interface AgentConfig {
  role: string;
  provider: string;
  model_id: string;
}

const API_BASE = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

export function ResearchHubSettings() {
  const [apiKeys, setApiKeys] = useState<ApiKeyInfo[]>([]);
  const [models, setModels] = useState<Record<string, ModelInfo[]>>({});
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const [editingKey, setEditingKey] = useState<string | null>(null);
  const [keyValue, setKeyValue] = useState('');
  const [pendingAgentChanges, setPendingAgentChanges] = useState<Record<string, { provider: string; model_id: string }>>({});

  // Fetch all settings data
  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    try {
      setLoading(true);
      setError(null);

      const [keysRes, modelsRes, agentsRes] = await Promise.all([
        fetch(`${API_BASE}/api/v1/settings/api-keys`),
        fetch(`${API_BASE}/api/v1/settings/models`),
        fetch(`${API_BASE}/api/v1/settings/agents`),
      ]);

      if (!keysRes.ok || !modelsRes.ok || !agentsRes.ok) {
        throw new Error('Failed to fetch settings');
      }

      const keysData = await keysRes.json();
      const modelsData = await modelsRes.json();
      const agentsData = await agentsRes.json();

      setApiKeys(keysData.keys || []);
      setModels(modelsData.models || {});
      setAgents(agentsData.agents || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveApiKey = async (keyName: string) => {
    if (!keyValue.trim()) {
      setEditingKey(null);
      setKeyValue('');
      return;
    }

    try {
      setSaving(true);
      const res = await fetch(`${API_BASE}/api/v1/settings/api-keys`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          updates: [{ key: keyName, value: keyValue }],
        }),
      });

      if (!res.ok) throw new Error('Failed to save API key');

      setEditingKey(null);
      setKeyValue('');
      await fetchSettings();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save API key');
    } finally {
      setSaving(false);
    }
  };

  const handleAgentChange = (role: string, provider: string, model_id: string) => {
    setPendingAgentChanges((prev) => ({
      ...prev,
      [role]: { provider, model_id },
    }));
  };

  const handleSaveAgentConfig = async (role: string) => {
    const change = pendingAgentChanges[role];
    if (!change) return;

    try {
      setSaving(true);
      const res = await fetch(`${API_BASE}/api/v1/settings/agents/${role}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(change),
      });

      if (!res.ok) throw new Error('Failed to save agent config');

      setPendingAgentChanges((prev) => {
        const next = { ...prev };
        delete next[role];
        return next;
      });
      await fetchSettings();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save agent config');
    } finally {
      setSaving(false);
    }
  };

  const refreshModels = async () => {
    try {
      setSaving(true);
      await fetch(`${API_BASE}/api/v1/settings/models/refresh`, { method: 'POST' });
      await fetchSettings();
    } catch (err) {
      setError('Failed to refresh models');
    } finally {
      setSaving(false);
    }
  };

  if (loading) {
    return (
      <div className="py-8 text-center">
        <div className="text-slate-400 animate-pulse">Loading settings...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="py-8 text-center">
        <div className="text-red-400 mb-4">{error}</div>
        <button onClick={fetchSettings} className="text-blue-400 hover:text-blue-300">
          Retry
        </button>
      </div>
    );
  }

  const providers = Object.keys(models);

  return (
    <div className="space-y-8">
      {/* API Keys Section */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Key className="text-blue-500" size={24} />
          <h3 className="text-xl font-semibold text-white">API Keys</h3>
        </div>
        <p className="text-sm text-slate-400 mb-4">
          Configure API keys for LLM providers used by research agents.
        </p>

        <div className="space-y-3">
          {apiKeys.map((apiKey) => (
            <div
              key={apiKey.key}
              className="flex items-center justify-between p-4 bg-slate-800/50 border border-slate-700 rounded-lg"
            >
              <div className="flex items-center gap-3">
                {apiKey.configured ? (
                  <CheckCircle className="text-green-500" size={20} />
                ) : (
                  <XCircle className="text-red-500" size={20} />
                )}
                <div>
                  <div className="font-medium text-white">{apiKey.name}</div>
                  <div className="text-xs text-slate-500 font-mono">{apiKey.key}</div>
                </div>
              </div>

              <div className="flex items-center gap-3">
                {editingKey === apiKey.key ? (
                  <>
                    <input
                      type="password"
                      value={keyValue}
                      onChange={(e) => setKeyValue(e.target.value)}
                      placeholder="Enter API key..."
                      className="px-3 py-1.5 bg-slate-900 border border-slate-600 rounded text-sm text-white w-64"
                      autoFocus
                    />
                    <button
                      onClick={() => handleSaveApiKey(apiKey.key)}
                      disabled={saving}
                      className="px-3 py-1.5 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-50"
                    >
                      <Save size={16} />
                    </button>
                    <button
                      onClick={() => {
                        setEditingKey(null);
                        setKeyValue('');
                      }}
                      className="px-3 py-1.5 bg-slate-600 text-white rounded text-sm hover:bg-slate-500"
                    >
                      Cancel
                    </button>
                  </>
                ) : (
                  <>
                    {apiKey.configured && (
                      <span className="text-xs text-slate-500 font-mono">{apiKey.masked_value}</span>
                    )}
                    <button
                      onClick={() => setEditingKey(apiKey.key)}
                      className="px-3 py-1.5 bg-blue-600 text-white rounded text-sm hover:bg-blue-700"
                    >
                      {apiKey.configured ? 'Update' : 'Configure'}
                    </button>
                  </>
                )}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Model Selection Section */}
      <section>
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <Cpu className="text-purple-500" size={24} />
            <h3 className="text-xl font-semibold text-white">Available Models</h3>
          </div>
          <button
            onClick={refreshModels}
            disabled={saving}
            className="flex items-center gap-2 px-3 py-1.5 bg-slate-700 text-slate-300 rounded text-sm hover:bg-slate-600 disabled:opacity-50"
          >
            <RefreshCw size={14} className={saving ? 'animate-spin' : ''} />
            Refresh
          </button>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {providers.map((provider) => (
            <div key={provider} className="bg-slate-800/50 border border-slate-700 rounded-lg p-4">
              <h4 className="font-medium text-white capitalize mb-3">{provider}</h4>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {models[provider].map((model) => (
                  <div
                    key={model.id}
                    className={`text-sm p-2 rounded ${
                      model.configured
                        ? 'bg-slate-700/50 text-slate-300'
                        : 'bg-slate-900/50 text-slate-500'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="truncate">{model.name}</span>
                      {model.configured ? (
                        <CheckCircle size={14} className="text-green-500 flex-shrink-0" />
                      ) : (
                        <XCircle size={14} className="text-slate-600 flex-shrink-0" />
                      )}
                    </div>
                    {model.cost_per_1m_input !== null && (
                      <div className="text-xs text-slate-500 mt-1">
                        ${model.cost_per_1m_input}/1M in · ${model.cost_per_1m_output}/1M out
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Agent Configuration Section */}
      <section>
        <div className="flex items-center gap-2 mb-4">
          <Bot className="text-amber-500" size={24} />
          <h3 className="text-xl font-semibold text-white">Agent Configuration</h3>
        </div>
        <p className="text-sm text-slate-400 mb-4">
          Configure which LLM provider and model each research agent role uses.
        </p>

        <div className="space-y-3">
          {agents.map((agent) => {
            const pending = pendingAgentChanges[agent.role];
            const currentProvider = pending?.provider || agent.provider;
            const currentModel = pending?.model_id || agent.model_id;
            const hasChanges = !!pending;

            return (
              <div
                key={agent.role}
                className="p-4 bg-slate-800/50 border border-slate-700 rounded-lg"
              >
                <div className="flex items-center justify-between mb-3">
                  <h4 className="font-medium text-white capitalize">{agent.role}</h4>
                  {hasChanges && (
                    <button
                      onClick={() => handleSaveAgentConfig(agent.role)}
                      disabled={saving}
                      className="flex items-center gap-1 px-3 py-1 bg-green-600 text-white rounded text-sm hover:bg-green-700 disabled:opacity-50"
                    >
                      <Save size={14} />
                      Save
                    </button>
                  )}
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Provider</label>
                    <select
                      value={currentProvider}
                      onChange={(e) => {
                        const newProvider = e.target.value;
                        const providerModels = models[newProvider] || [];
                        const firstModel = providerModels[0]?.id || '';
                        handleAgentChange(agent.role, newProvider, firstModel);
                      }}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white text-sm"
                    >
                      {providers.map((p) => (
                        <option key={p} value={p}>
                          {p}
                        </option>
                      ))}
                    </select>
                  </div>

                  <div>
                    <label className="block text-xs text-slate-400 mb-1">Model</label>
                    <select
                      value={currentModel}
                      onChange={(e) => handleAgentChange(agent.role, currentProvider, e.target.value)}
                      className="w-full px-3 py-2 bg-slate-900 border border-slate-600 rounded text-white text-sm"
                    >
                      {(models[currentProvider] || []).map((m) => (
                        <option key={m.id} value={m.id} disabled={!m.configured}>
                          {m.name} {!m.configured && '(not configured)'}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>
              </div>
            );
          })}

          {agents.length === 0 && (
            <div className="text-center py-8 text-slate-500">
              No agent configurations found. Run seed to create defaults.
            </div>
          )}
        </div>
      </section>
    </div>
  );
}

export default ResearchHubSettings;
