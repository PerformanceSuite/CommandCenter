export interface ToolManifest {
  id: string;
  name?: string;
  version: string;
  category?: string[];
  ports?: Record<string, number>;
  health?: { url?: string };
  endpoints?: Record<string, string>;
}

export interface ToolRegistryEntry {
  id: string;
  version: string;
  categories: string[];
  ports: Record<string, number>;
  healthUrl?: string;
  endpoints: Record<string, string>;
  discoveredAt: string;
}

export interface HubState {
  registryPath: string;
  auditDir: string;
  eventsDir: string;
  rpcPort: number;
}
