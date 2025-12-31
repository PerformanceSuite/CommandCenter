/**
 * QueryResult Builder - Assembles full query result with affordances
 *
 * Takes raw API response (nodes + edges) and enriches with:
 * - Layout determination
 * - Affordances for agents
 * - Natural language summary
 */

import { GraphNode, GraphEdge } from '../types/graph';
import { ComposedQuery, QueryResult, Affordance } from '../types/query';
import {
  buildContext,
  determineLayout,
  generateAffordances,
  generateSummary,
} from './compositionEngine';

export interface BuildQueryResultOptions {
  nodes: GraphNode[];
  edges: GraphEdge[];
  query: ComposedQuery;
  total?: number;
}

export function buildQueryResult(options: BuildQueryResultOptions): QueryResult {
  const { nodes, edges, query, total } = options;

  // Build context for composition decisions
  const context = buildContext(nodes, edges);

  // Determine layout
  const resolvedLayout = determineLayout(query, context);

  // Generate affordances
  const affordances = generateAffordances(nodes, resolvedLayout);

  // Generate summary
  const summary = generateSummary(context, resolvedLayout);

  // Build resolved query (with defaults filled in)
  const resolvedQuery: ComposedQuery = {
    ...query,
    presentation: {
      ...query.presentation,
      layout: resolvedLayout,
    },
  };

  return {
    nodes,
    edges,
    affordances,
    summary,
    total: total ?? nodes.length,
    resolvedQuery,
  };
}

/**
 * Execute an affordance action
 * Returns the URL params for navigation or action data for API call
 */
export function executeAffordance(
  affordance: Affordance,
  _currentQuery: ComposedQuery
): { type: 'navigate'; params: URLSearchParams } | { type: 'api'; endpoint: string; body: unknown } {
  switch (affordance.action) {
    case 'drill_down':
      return {
        type: 'navigate',
        params: new URLSearchParams({
          entity: `${affordance.target.type}:${affordance.target.id}`,
          depth: '2',
        }),
      };

    case 'zoom_out':
      // Remove the current entity, show parent
      return {
        type: 'navigate',
        params: new URLSearchParams({
          layout: 'graph',
          depth: '1',
        }),
      };

    case 'view_dependencies':
      return {
        type: 'navigate',
        params: new URLSearchParams({
          entity: `${affordance.target.type}:${affordance.target.id}`,
          rel_direction: 'outbound',
          depth: '3',
        }),
      };

    case 'view_dependents':
      return {
        type: 'navigate',
        params: new URLSearchParams({
          entity: `${affordance.target.type}:${affordance.target.id}`,
          rel_direction: 'inbound',
          depth: '3',
        }),
      };

    case 'trigger_audit':
      return {
        type: 'api',
        endpoint: '/api/v1/graph/audits',
        body: {
          target_entity: `graph_${affordance.target.type}s`,
          target_id: affordance.target.id,
          kind: 'security',
        },
      };

    case 'create_task':
      return {
        type: 'api',
        endpoint: '/api/v1/graph/tasks',
        body: {
          title: `Task for ${affordance.target.type}:${affordance.target.id}`,
          kind: 'feature',
          description: affordance.description,
        },
      };

    default:
      return {
        type: 'navigate',
        params: new URLSearchParams(),
      };
  }
}
