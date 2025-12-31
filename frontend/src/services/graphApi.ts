/**
 * Graph API service for VISLZR visualization
 *
 * Provides methods for fetching graph data and managing cross-project links.
 */

import axios from 'axios';
import {
  ProjectGraphResponse,
  FederationQueryRequest,
  FederationQueryResponse,
  GraphNode,
  GraphEdge,
} from '../types/graph';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// ============================================================================
// API Client
// ============================================================================

const graphClient = axios.create({
  baseURL: `${BASE_URL}/api/v1/graph`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Graph Query Interfaces
// ============================================================================

export interface GraphQueryParams {
  depth?: number;
  languages?: string[];
  filePaths?: string[];
  symbolKinds?: string[];
  serviceTypes?: string[];
}

export interface SearchParams {
  query: string;
  scope?: ('symbols' | 'files' | 'tasks')[];
}

export interface SearchResults {
  symbols: GraphNode[];
  files: GraphNode[];
  tasks: GraphNode[];
  total: number;
}

// ============================================================================
// API Methods
// ============================================================================

export const graphApi = {
  /**
   * Get complete project graph
   */
  async getProjectGraph(
    projectId: number,
    params: GraphQueryParams = {}
  ): Promise<ProjectGraphResponse> {
    const queryParams = new URLSearchParams();

    if (params.depth) queryParams.set('depth', String(params.depth));
    if (params.languages?.length) queryParams.set('languages', params.languages.join(','));
    if (params.filePaths?.length) queryParams.set('file_paths', params.filePaths.join(','));
    if (params.symbolKinds?.length) queryParams.set('symbol_kinds', params.symbolKinds.join(','));
    if (params.serviceTypes?.length) queryParams.set('service_types', params.serviceTypes.join(','));

    const response = await graphClient.get<ProjectGraphResponse>(
      `/projects/${projectId}?${queryParams.toString()}`
    );
    return response.data;
  },

  /**
   * Get symbol dependencies
   */
  async getSymbolDependencies(
    symbolId: number,
    direction: 'inbound' | 'outbound' | 'both' = 'both',
    depth: number = 3
  ): Promise<{ nodes: GraphNode[]; edges: GraphEdge[]; depth_reached: number }> {
    const response = await graphClient.get(
      `/dependencies/${symbolId}?direction=${direction}&depth=${depth}`
    );
    return response.data;
  },

  /**
   * Search across code, specs, and tasks
   */
  async search(params: SearchParams): Promise<SearchResults> {
    const response = await graphClient.post<SearchResults>('/search', {
      query: params.query,
      scope: params.scope || ['symbols', 'files', 'tasks'],
    });
    return response.data;
  },

  /**
   * Query cross-project federation links
   */
  async queryFederation(request: FederationQueryRequest): Promise<FederationQueryResponse> {
    const response = await graphClient.post<FederationQueryResponse>(
      '/federation/query',
      request
    );
    return response.data;
  },

  /**
   * Create a cross-project link
   */
  async createCrossProjectLink(params: {
    sourceProjectId: number;
    targetProjectId: number;
    fromEntity: string;
    fromId: number;
    toEntity: string;
    toId: number;
    linkType: string;
    weight?: number;
  }): Promise<void> {
    const queryParams = new URLSearchParams({
      source_project_id: String(params.sourceProjectId),
      target_project_id: String(params.targetProjectId),
      from_entity: params.fromEntity,
      from_id: String(params.fromId),
      to_entity: params.toEntity,
      to_id: String(params.toId),
      link_type: params.linkType,
      weight: String(params.weight || 1.0),
    });

    await graphClient.post(`/federation/links?${queryParams.toString()}`);
  },

  /**
   * Health check
   */
  async healthCheck(): Promise<{ status: string; service: string }> {
    const response = await graphClient.get('/health');
    return response.data;
  },
};

export default graphApi;
