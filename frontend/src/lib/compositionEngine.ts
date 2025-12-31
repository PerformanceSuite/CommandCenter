/**
 * Composition Engine - Decides how to render query results
 *
 * Based on the data shape and query hints, determines whether to use
 * graph, list, detail, or dashboard layout.
 */

import { ComposedQuery, LayoutType, Affordance } from '../types/query';
import { GraphNode, GraphEdge, EntityType } from '../types/graph';

// ============================================================================
// Composition Context
// ============================================================================

export interface CompositionContext {
  nodeCount: number;
  edgeCount: number;
  hasRelationships: boolean;
  entityTypes: EntityType[];
}

export function buildContext(nodes: GraphNode[], edges: GraphEdge[]): CompositionContext {
  const entityTypes = [...new Set(nodes.map((n) => n.entity_type))] as EntityType[];
  return {
    nodeCount: nodes.length,
    edgeCount: edges.length,
    hasRelationships: edges.length > 0,
    entityTypes,
  };
}

// ============================================================================
// Layout Determination
// ============================================================================

const GRAPH_THRESHOLD = 100; // Switch to list above this node count
const DASHBOARD_ENTITY_TYPES = 4; // Switch to dashboard with this many entity types

export function determineLayout(query: ComposedQuery, context: CompositionContext): LayoutType {
  // Respect explicit layout hint
  if (query.presentation.layout !== 'auto') {
    return query.presentation.layout;
  }

  // Single entity → detail
  if (context.nodeCount === 1) {
    return 'detail';
  }

  // Many heterogeneous entity types → dashboard
  if (context.entityTypes.length >= DASHBOARD_ENTITY_TYPES) {
    return 'dashboard';
  }

  // Few entities with relationships → graph
  if (context.nodeCount < GRAPH_THRESHOLD && context.hasRelationships) {
    return 'graph';
  }

  // Many entities or no relationships → list
  if (context.nodeCount >= GRAPH_THRESHOLD || !context.hasRelationships) {
    return 'list';
  }

  // Default to graph
  return 'graph';
}

// ============================================================================
// Affordance Generation
// ============================================================================

export function generateAffordances(
  nodes: GraphNode[],
  resolvedLayout: LayoutType
): Affordance[] {
  const affordances: Affordance[] = [];

  // If showing a graph, offer zoom controls
  if (resolvedLayout === 'graph' && nodes.length > 0) {
    affordances.push({
      action: 'zoom_out',
      target: { type: nodes[0].entity_type as EntityType, id: nodes[0].entity_id },
      description: 'Zoom out to parent context',
    });
  }

  // For each node, generate contextual affordances
  for (const node of nodes.slice(0, 10)) { // Limit to first 10
    const nodeType = node.entity_type as EntityType;

    // Drill down for container types
    if (['project', 'repo', 'file', 'service'].includes(nodeType)) {
      affordances.push({
        action: 'drill_down',
        target: { type: nodeType, id: node.entity_id },
        description: `Explore ${node.label}`,
      });
    }

    // View dependencies for symbols
    if (nodeType === 'symbol') {
      affordances.push({
        action: 'view_dependencies',
        target: { type: nodeType, id: node.entity_id },
        description: `View dependencies of ${node.label}`,
      });
      affordances.push({
        action: 'view_dependents',
        target: { type: nodeType, id: node.entity_id },
        description: `View what depends on ${node.label}`,
      });
    }

    // Trigger audit for files/symbols
    if (['file', 'symbol'].includes(nodeType)) {
      affordances.push({
        action: 'trigger_audit',
        target: { type: nodeType, id: node.entity_id },
        description: `Run audit on ${node.label}`,
      });
    }

    // Create task for any entity
    affordances.push({
      action: 'create_task',
      target: { type: nodeType, id: node.entity_id },
      description: `Create task related to ${node.label}`,
    });
  }

  return affordances;
}

// ============================================================================
// Summary Generation
// ============================================================================

export function generateSummary(
  context: CompositionContext,
  resolvedLayout: LayoutType
): string {
  const { nodeCount, edgeCount, entityTypes } = context;

  if (nodeCount === 0) {
    return 'No entities match the query.';
  }

  if (nodeCount === 1) {
    return `Showing details for 1 ${entityTypes[0]}.`;
  }

  const typeList = entityTypes.join(', ');
  const layoutDesc = {
    graph: 'graph view',
    list: 'list view',
    detail: 'detail view',
    dashboard: 'dashboard',
    auto: 'auto view',
  }[resolvedLayout];

  let summary = `Showing ${nodeCount} entities (${typeList}) in ${layoutDesc}`;
  if (edgeCount > 0) {
    summary += ` with ${edgeCount} relationships`;
  }
  summary += '.';

  return summary;
}
