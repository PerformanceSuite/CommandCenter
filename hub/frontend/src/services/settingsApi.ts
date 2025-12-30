import axios from 'axios';
import { Provider, AgentConfig } from '../types/settings';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const settingsApi = {
  getProviders: async (): Promise<Provider[]> => {
    const response = await axios.get(`${API_BASE}/api/v1/settings/providers`);
    return response.data.providers;
  },

  getAgents: async (): Promise<AgentConfig[]> => {
    const response = await axios.get(`${API_BASE}/api/v1/settings/agents`);
    return response.data.agents;
  },

  setAgentProvider: async (role: string, providerAlias: string): Promise<AgentConfig> => {
    const response = await axios.put(
      `${API_BASE}/api/v1/settings/agents/${role}`,
      { provider_alias: providerAlias }
    );
    return response.data;
  },

  seedDefaults: async (): Promise<void> => {
    await axios.post(`${API_BASE}/api/v1/settings/seed`);
  },
};
