/**
 * Query API service for Composable Query Layer (Phase 2)
 *
 * Provides methods for executing composed queries and parsing natural language.
 */

import axios from 'axios';

const BASE_URL = import.meta.env.VITE_API_BASE_URL || '';

// ============================================================================
// API Client
// ============================================================================

const queryClient = axios.create({
  baseURL: `${BASE_URL}/api/v1/graph`,
  headers: {
    'Content-Type': 'application/json',
  },
});

// ============================================================================
// Query Types (mirroring backend schemas)
// ============================================================================

export interface EntitySelector {
  type: string;
  scope?: string;
  id?: string;
  constraints?: Record<string, unknown>;
}

export interface Filter {
  field: string;
  operator: 'eq' | 'ne' | 'lt' | 'gt' | 'lte' | 'gte' | 'in' | 'contains';
  value: unknown;
}

export interface RelationshipSpec {
  type: string;
  direction: 'inbound' | 'outbound' | 'both';
  depth: number;
  filters?: Record<string, unknown>;
}

export interface TimeRange {
  start?: string;
  end?: string;
}

export interface Aggregation {
  type: 'count' | 'sum' | 'avg' | 'min' | 'max' | 'group';
  field?: string;
  group_by?: string[];
}

export interface ComposedQuery {
  entities: EntitySelector[];
  filters?: Filter[];
  relationships?: RelationshipSpec[];
  presentation?: Record<string, unknown>;
  time_range?: TimeRange;
  aggregations?: Aggregation[];
  limit?: number;
  offset?: number;
}

export interface QueryResultEntity {
  id: number | string;
  type: string;
  label: string;
  kind?: string;
  status?: string;
  metadata?: Record<string, unknown>;
  [key: string]: unknown;
}

export interface QueryResultRelationship {
  id: number | string;
  source: number | string;
  target: number | string;
  type: string;
  weight?: number;
}

export interface QueryResult {
  entities: QueryResultEntity[];
  relationships: QueryResultRelationship[];
  aggregations?: Record<string, unknown>;
  total: number;
  metadata: {
    execution_time_ms: number;
    entity_types_queried: string[];
    filters_applied: number;
    relationships_traversed: number;
  };
}

export interface ParseQueryRequest {
  query: string | Record<string, unknown>;
}

// ============================================================================
// API Methods
// ============================================================================

export const queryApi = {
  /**
   * Execute a composed query against the graph database.
   */
  async executeQuery(query: ComposedQuery): Promise<QueryResult> {
    const response = await queryClient.post<QueryResult>('/query', query);
    return response.data;
  },

  /**
   * Parse and execute a natural language or structured query.
   */
  async parseAndExecute(query: string | Record<string, unknown>): Promise<QueryResult> {
    const response = await queryClient.post<QueryResult>('/query/parse', { query });
    return response.data;
  },

  /**
   * Create a simple entity query.
   */
  createEntityQuery(
    entityType: string,
    options: {
      scope?: string;
      id?: string;
      filters?: Filter[];
      limit?: number;
    } = {}
  ): ComposedQuery {
    return {
      entities: [
        {
          type: entityType,
          scope: options.scope,
          id: options.id,
        },
      ],
      filters: options.filters,
      limit: options.limit || 50,
    };
  },

  /**
   * Create a query with relationship traversal.
   */
  createRelationshipQuery(
    entityType: string,
    entityId: string,
    relationship: {
      type: string;
      direction: 'inbound' | 'outbound' | 'both';
      depth?: number;
    }
  ): ComposedQuery {
    return {
      entities: [
        {
          type: entityType,
          id: entityId,
        },
      ],
      relationships: [
        {
          type: relationship.type,
          direction: relationship.direction,
          depth: relationship.depth || 1,
        },
      ],
      limit: 100,
    };
  },

  /**
   * Create a search query with name filter.
   */
  createSearchQuery(
    searchTerm: string,
    entityType: string = 'any',
    limit: number = 50
  ): ComposedQuery {
    return {
      entities: [{ type: entityType }],
      filters: searchTerm
        ? [{ field: 'name', operator: 'contains', value: searchTerm }]
        : undefined,
      limit,
    };
  },
};

export default queryApi;
