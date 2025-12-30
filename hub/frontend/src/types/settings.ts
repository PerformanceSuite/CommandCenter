export interface Provider {
  alias: string;
  model_id: string;
  api_key_required: string;
  configured: boolean;
  cost_per_1m_input: number | null;
  cost_per_1m_output: number | null;
}

export interface ModelOption {
  id: string;
  name: string;
  cost_per_1m_input: number;
  cost_per_1m_output: number;
  configured: boolean;
}

export interface ModelsResponse {
  [provider: string]: ModelOption[];
}

export interface AgentConfig {
  role: string;
  provider: string;
  model_id: string;
}
