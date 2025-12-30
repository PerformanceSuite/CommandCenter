import { useEffect, useState } from 'react';
import { settingsApi } from '../services/settingsApi';
import { AgentConfig, ModelsResponse, ModelOption } from '../types/settings';

// Provider display names
const PROVIDER_NAMES: Record<string, string> = {
  anthropic: 'Anthropic',
  openai: 'OpenAI',
  google: 'Google',
  zai: 'Z.AI',
};

export function SettingsDashboard() {
  const [models, setModels] = useState<ModelsResponse>({});
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
      const [modelsData, agentsData] = await Promise.all([
        settingsApi.getModels(),
        settingsApi.getAgents(),
      ]);
      setModels(modelsData);
      setAgents(agentsData);
    } catch (err) {
      setError('Failed to load settings data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleProviderChange = async (role: string, newProvider: string) => {
    // When provider changes, select the first model from that provider
    const providerModels = models[newProvider];
    if (providerModels && providerModels.length > 0) {
      await handleModelChange(role, newProvider, providerModels[0].id);
    }
  };

  const handleModelChange = async (role: string, provider: string, modelId: string) => {
    try {
      setError(null);
      setSuccessMessage(null);
      await settingsApi.setAgentModel(role, provider, modelId);

      // Find model name for success message
      const model = models[provider]?.find(m => m.id === modelId);
      const modelName = model?.name || modelId;
      setSuccessMessage(`Updated ${role} to use ${PROVIDER_NAMES[provider] || provider} / ${modelName}`);

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

  const getModelName = (provider: string, modelId: string): string => {
    const model = models[provider]?.find(m => m.id === modelId);
    return model?.name || modelId.split('/').pop() || modelId;
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="text-slate-400">Loading settings...</div>
      </div>
    );
  }

  const providers = Object.keys(models);

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

      {/* Available Models Panel */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Available Models</h3>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {providers.map((provider) => (
            <div key={provider} className="bg-slate-800/50 rounded-lg border border-slate-700 p-4">
              <h4 className="text-md font-medium text-white mb-3">
                {PROVIDER_NAMES[provider] || provider}
              </h4>
              <div className="space-y-2">
                {models[provider].map((model) => (
                  <div
                    key={model.id}
                    className="flex items-center justify-between text-sm py-1.5 px-2 rounded bg-slate-700/30"
                  >
                    <div className="flex items-center gap-2">
                      <span className={model.configured ? 'text-white' : 'text-slate-500'}>
                        {model.name}
                      </span>
                      {!model.configured && (
                        <span className="text-xs text-amber-500">(no API key)</span>
                      )}
                    </div>
                    <span className="text-slate-500 text-xs">
                      ${model.cost_per_1m_input?.toFixed(2)} / ${model.cost_per_1m_output?.toFixed(2)}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Agent Configuration Panel */}
      <div>
        <h3 className="text-lg font-semibold text-white mb-4">Agent Configuration</h3>
        <div className="bg-slate-800/50 rounded-lg border border-slate-700 overflow-hidden">
          <table className="w-full">
            <thead>
              <tr className="border-b border-slate-700">
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Agent Role</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Provider</th>
                <th className="text-left px-4 py-3 text-sm font-medium text-slate-400">Model</th>
              </tr>
            </thead>
            <tbody>
              {agents.map((agent) => (
                <tr key={agent.role} className="border-b border-slate-700/50 last:border-0">
                  <td className="px-4 py-3">
                    <div className="text-sm font-medium text-white capitalize">{agent.role}</div>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={agent.provider}
                      onChange={(e) => handleProviderChange(agent.role, e.target.value)}
                      className="px-3 py-1.5 bg-slate-700 border border-slate-600 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      {providers.map((provider) => (
                        <option key={provider} value={provider}>
                          {PROVIDER_NAMES[provider] || provider}
                        </option>
                      ))}
                    </select>
                  </td>
                  <td className="px-4 py-3">
                    <select
                      value={agent.model_id}
                      onChange={(e) => handleModelChange(agent.role, agent.provider, e.target.value)}
                      className="px-3 py-1.5 bg-slate-700 border border-slate-600 rounded text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500 min-w-[200px]"
                    >
                      {models[agent.provider]?.map((model) => (
                        <option key={model.id} value={model.id}>
                          {model.name} (${model.cost_per_1m_input}/{model.cost_per_1m_output})
                        </option>
                      ))}
                    </select>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        {agents.length === 0 && (
          <div className="text-center py-8 text-slate-500">
            No agent configurations found. Click seed to create defaults.
          </div>
        )}
      </div>
    </div>
  );
}
