export interface Provider {
  alias: string;
  model_id: string;
  api_key_required: string;
  configured: boolean;
  cost_per_1m_input: number | null;
  cost_per_1m_output: number | null;
}

export interface AgentConfig {
  role: string;
  provider_alias: string;
}
