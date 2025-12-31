/**
 * Hook for fetching and managing graph data
 *
 * Provides methods for fetching project graphs, searching, and
 * querying cross-project federation links.
 */

import { useState, useEffect, useCallback } from 'react';
import { graphApi, GraphQueryParams, SearchParams, SearchResults } from '../services/graphApi';
import {
  ProjectGraphResponse,
  FederationQueryRequest,
  FederationQueryResponse,
  GraphNode,
  GraphEdge,
} from '../types/graph';

// ============================================================================
// useProjectGraph - Fetch a project's graph
// ============================================================================

export interface UseProjectGraphResult {
  nodes: GraphNode[];
  edges: GraphEdge[];
  metadata: ProjectGraphResponse['metadata'] | null;
  loading: boolean;
  error: Error | null;
  refresh: () => Promise<void>;
}

export function useProjectGraph(
  projectId: number | null,
  params: GraphQueryParams = {}
): UseProjectGraphResult {
  const [data, setData] = useState<ProjectGraphResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(async () => {
    if (!projectId) return;

    try {
      setLoading(true);
      setError(null);
      const result = await graphApi.getProjectGraph(projectId, params);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Failed to fetch graph'));
    } finally {
      setLoading(false);
    }
  }, [projectId, JSON.stringify(params)]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return {
    nodes: data?.nodes || [],
    edges: data?.edges || [],
    metadata: data?.metadata || null,
    loading,
    error,
    refresh: fetch,
  };
}

// ============================================================================
// useGraphSearch - Search across the graph
// ============================================================================

export interface UseGraphSearchResult {
  results: SearchResults | null;
  loading: boolean;
  error: Error | null;
  search: (query: string, scope?: SearchParams['scope']) => Promise<void>;
  clear: () => void;
}

export function useGraphSearch(): UseGraphSearchResult {
  const [results, setResults] = useState<SearchResults | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const search = useCallback(async (query: string, scope?: SearchParams['scope']) => {
    if (!query.trim()) {
      setResults(null);
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const data = await graphApi.search({ query, scope });
      setResults(data);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Search failed'));
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setResults(null);
    setError(null);
  }, []);

  return {
    results,
    loading,
    error,
    search,
    clear,
  };
}

// ============================================================================
// useFederationQuery - Query cross-project links
// ============================================================================

export interface UseFederationQueryResult {
  data: FederationQueryResponse | null;
  loading: boolean;
  error: Error | null;
  query: (request: FederationQueryRequest) => Promise<void>;
  refresh: () => Promise<void>;
}

export function useFederationQuery(
  initialRequest?: FederationQueryRequest
): UseFederationQueryResult {
  const [data, setData] = useState<FederationQueryResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);
  const [lastRequest, setLastRequest] = useState<FederationQueryRequest | null>(
    initialRequest || null
  );

  const query = useCallback(async (request: FederationQueryRequest) => {
    try {
      setLoading(true);
      setError(null);
      setLastRequest(request);
      const result = await graphApi.queryFederation(request);
      setData(result);
    } catch (err) {
      setError(err instanceof Error ? err : new Error('Federation query failed'));
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(async () => {
    if (lastRequest) {
      await query(lastRequest);
    }
  }, [lastRequest, query]);

  // Initial fetch if request provided
  useEffect(() => {
    if (initialRequest) {
      query(initialRequest);
    }
  }, []);

  return {
    data,
    loading,
    error,
    query,
    refresh,
  };
}

// ============================================================================
// useSymbolDependencies - Fetch symbol dependency graph
// ============================================================================

export interface UseSymbolDependenciesResult {
  nodes: GraphNode[];
  edges: GraphEdge[];
  depthReached: number;
  loading: boolean;
  error: Error | null;
  fetch: (
    symbolId: number,
    direction?: 'inbound' | 'outbound' | 'both',
    depth?: number
  ) => Promise<void>;
}

export function useSymbolDependencies(): UseSymbolDependenciesResult {
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [depthReached, setDepthReached] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<Error | null>(null);

  const fetch = useCallback(
    async (
      symbolId: number,
      direction: 'inbound' | 'outbound' | 'both' = 'both',
      depth: number = 3
    ) => {
      try {
        setLoading(true);
        setError(null);
        const result = await graphApi.getSymbolDependencies(symbolId, direction, depth);
        setNodes(result.nodes);
        setEdges(result.edges);
        setDepthReached(result.depth_reached);
      } catch (err) {
        setError(err instanceof Error ? err : new Error('Failed to fetch dependencies'));
      } finally {
        setLoading(false);
      }
    },
    []
  );

  return {
    nodes,
    edges,
    depthReached,
    loading,
    error,
    fetch,
  };
}
