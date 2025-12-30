import { Provider, AgentConfig, ModelsResponse } from '../types/settings';

const API_BASE = '/api/v1';

async function fetchJSON<T>(url: string, options?: RequestInit): Promise<T> {
  const response = await fetch(url, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const settingsApi = {
  getProviders: async (): Promise<Provider[]> => {
    const response = await fetchJSON<{ providers: Provider[] }>(`${API_BASE}/settings/providers`);
    return response.providers;
  },

  getModels: async (): Promise<ModelsResponse> => {
    const response = await fetchJSON<{ models: ModelsResponse }>(`${API_BASE}/settings/models`);
    return response.models;
  },

  getAgents: async (): Promise<AgentConfig[]> => {
    const response = await fetchJSON<{ agents: AgentConfig[] }>(`${API_BASE}/settings/agents`);
    return response.agents;
  },

  setAgentModel: async (role: string, provider: string, modelId: string): Promise<AgentConfig> => {
    return fetchJSON<AgentConfig>(`${API_BASE}/settings/agents/${role}`, {
      method: 'PUT',
      body: JSON.stringify({ provider, model_id: modelId }),
    });
  },

  seedDefaults: async (): Promise<void> => {
    await fetchJSON<void>(`${API_BASE}/settings/seed`, { method: 'POST' });
  },
};
