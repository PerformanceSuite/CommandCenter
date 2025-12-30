import { useEffect, useState } from 'react';
import { settingsApi } from '../services/settingsApi';
import { Provider, AgentConfig } from '../types/settings';

export function SettingsDashboard() {
  const [providers, setProviders] = useState<Provider[]>([]);
  const [agents, setAgents] = useState<AgentConfig[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const [providersData, agentsData] = await Promise.all([
        settingsApi.getProviders(),
        settingsApi.getAgents(),
      ]);
      setProviders(providersData);
      setAgents(agentsData);
    } catch (err) {
      setError('Failed to load settings data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAgentProviderChange = async (role: string, providerAlias: string) => {
    try {
      setError(null);
      setSuccessMessage(null);
      await settingsApi.setAgentProvider(role, providerAlias);
      setSuccessMessage(`Successfully updated ${role} to use ${providerAlias}`);
      // Reload agents to reflect the change
      const agentsData = await settingsApi.getAgents();
      setAgents(agentsData);
      // Clear success message after 3 seconds
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(`Failed to update ${role}`);
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-slate-400">Loading settings...</div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Toast messages */}
      {error && (
        <div className="bg-red-500/10 border border-red-500/50 rounded-lg p-4 text-red-400">
          {error}
        </div>
      )}
      {successMessage && (
        <div className="bg-green-500/10 border border-green-500/50 rounded-lg p-4 text-green-400">
          {successMessage}
        </div>
      )}

      {/* Providers Panel */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Providers</h3>
        <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-slate-700">
                  <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Alias</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Model</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Cost (Input)</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Cost (Output)</th>
                  <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Status</th>
                </tr>
              </thead>
              <tbody>
                {providers.map((provider) => (
                  <tr key={provider.alias} className="border-b border-slate-700/50 last:border-0">
                    <td className="px-4 py-3 text-sm text-white font-medium">{provider.alias}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">{provider.model_id}</td>
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {provider.cost_per_1m_input !== null
                        ? `$${provider.cost_per_1m_input.toFixed(2)}`
                        : 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm text-slate-300">
                      {provider.cost_per_1m_output !== null
                        ? `$${provider.cost_per_1m_output.toFixed(2)}`
                        : 'N/A'}
                    </td>
                    <td className="px-4 py-3 text-sm">
                      {provider.configured ? (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-green-500/10 text-green-400 text-xs font-medium">
                          <span className="w-1.5 h-1.5 rounded-full bg-green-400"></span>
                          Configured
                        </span>
                      ) : (
                        <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-500/10 text-slate-400 text-xs font-medium">
                          <span className="w-1.5 h-1.5 rounded-full bg-slate-400"></span>
                          Not Configured
                        </span>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* Agents Panel */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Agent Configuration</h3>
        <div className="bg-slate-800/50 rounded-lg border border-slate-700 p-6">
          <div className="space-y-4">
            {agents.map((agent) => (
              <div key={agent.role} className="flex items-center justify-between py-3 border-b border-slate-700/50 last:border-0">
                <div>
                  <div className="text-sm font-medium text-white">{agent.role}</div>
                  <div className="text-xs text-slate-400 mt-0.5">
                    Current provider: <span className="text-slate-300">{agent.provider_alias}</span>
                  </div>
                </div>
                <div className="flex items-center gap-3">
                  <select
                    value={agent.provider_alias}
                    onChange={(e) => handleAgentProviderChange(agent.role, e.target.value)}
                    className="px-3 py-2 bg-slate-700 border border-slate-600 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  >
                    {providers.map((provider) => (
                      <option key={provider.alias} value={provider.alias}>
                        {provider.alias}
                      </option>
                    ))}
                  </select>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
