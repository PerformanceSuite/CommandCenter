/**
 * useRealtimeGraph - Real-time graph state manager
 *
 * Sprint 4: Real-time Subscriptions (Task 4)
 *
 * Combines useProjectGraph with useGraphSubscription to provide
 * live-updating graph state. Initial data is fetched from the API,
 * then SSE events apply incremental updates.
 *
 * @example
 * ```tsx
 * const { nodes, edges, isConnected, isStale } = useRealtimeGraph(projectId);
 * ```
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { useProjectGraph, UseProjectGraphResult } from './useGraph';
import { useGraphSubscription } from './useGraphSubscription';
import type { GraphNode, GraphEdge, EntityType, EdgeType } from '../types/graph';
import type {
  GraphEvent,
  GraphNodeEvent,
  GraphEdgeEvent,
} from '../types/graphEvents';

// ============================================================================
// Types
// ============================================================================

export interface UseRealtimeGraphOptions {
  /** Whether to enable real-time updates (default: true) */
  enableRealtime?: boolean;
  /** NATS subjects to subscribe to (default: graph.*) */
  subjects?: string[];
}

export interface UseRealtimeGraphReturn extends Omit<UseProjectGraphResult, 'refresh'> {
  /** Whether the SSE connection is established */
  isConnected: boolean;
  /** Whether the graph data may be stale (invalidation received) */
  isStale: boolean;
  /** Count of updates received since initial load */
  updateCount: number;
  /** Refresh graph data from API and clear stale state */
  refresh: () => Promise<void>;
  /** Reconnect to SSE stream */
  reconnect: () => void;
}

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Convert a node event to a GraphNode
 */
function eventToNode(event: GraphNodeEvent): GraphNode {
  return {
    id: event.node_id,
    entity_type: event.node_type as EntityType,
    entity_id: parseInt(event.node_id.split(':')[1], 10) || 0,
    label: event.label || event.node_id,
    metadata: event.changes || {},
  };
}

/**
 * Convert an edge event to a GraphEdge
 */
function eventToEdge(event: GraphEdgeEvent): GraphEdge {
  return {
    from_node: event.from_node,
    to_node: event.to_node,
    type: event.edge_type as EdgeType,
    weight: event.weight,
  };
}

/**
 * Apply partial changes to a node
 */
function applyNodeChanges(node: GraphNode, changes: Record<string, unknown>): GraphNode {
  const updated = { ...node };

  // Update label if provided
  if (typeof changes.label === 'string') {
    updated.label = changes.label;
  }

  // Merge metadata changes
  if (changes.metadata && typeof changes.metadata === 'object') {
    updated.metadata = { ...updated.metadata, ...(changes.metadata as Record<string, unknown>) };
  }

  // Handle other standard fields
  if (typeof changes.entity_type === 'string') {
    updated.entity_type = changes.entity_type as EntityType;
  }

  return updated;
}

// ============================================================================
// Hook
// ============================================================================

export function useRealtimeGraph(
  projectId: number | null,
  options: UseRealtimeGraphOptions = {}
): UseRealtimeGraphReturn {
  const { enableRealtime = true, subjects = ['graph.*'] } = options;

  // Fetch initial graph data
  const {
    nodes: initialNodes,
    edges: initialEdges,
    metadata,
    loading,
    error,
    refresh: refetch,
  } = useProjectGraph(projectId);

  // Local state for live updates
  const [nodes, setNodes] = useState<GraphNode[]>([]);
  const [edges, setEdges] = useState<GraphEdge[]>([]);
  const [isStale, setIsStale] = useState(false);
  const [updateCount, setUpdateCount] = useState(0);

  // Track whether we've initialized from API data
  const initializedRef = useRef(false);

  // Sync initial data from API
  useEffect(() => {
    if (initialNodes.length > 0 || initialEdges.length > 0) {
      setNodes(initialNodes);
      setEdges(initialEdges);
      setIsStale(false);
      initializedRef.current = true;
    }
  }, [initialNodes, initialEdges]);

  // Handle graph events from SSE
  const handleEvent = useCallback((event: GraphEvent) => {
    setUpdateCount((prev) => prev + 1);

    switch (event.type) {
      case 'node.created': {
        const newNode = eventToNode(event.data);
        setNodes((prev) => {
          // Don't add if already exists
          if (prev.some((n) => n.id === newNode.id)) {
            return prev;
          }
          return [...prev, newNode];
        });
        break;
      }

      case 'node.updated': {
        setNodes((prev) =>
          prev.map((node) =>
            node.id === event.data.node_id
              ? applyNodeChanges(node, event.data.changes || {})
              : node
          )
        );
        break;
      }

      case 'node.deleted': {
        const deletedNodeId = event.data.node_id;
        setNodes((prev) => prev.filter((n) => n.id !== deletedNodeId));
        // Also remove any edges connected to this node
        setEdges((prev) =>
          prev.filter(
            (e) => e.from_node !== deletedNodeId && e.to_node !== deletedNodeId
          )
        );
        break;
      }

      case 'edge.created': {
        const newEdge = eventToEdge(event.data);
        setEdges((prev) => {
          // Don't add if already exists
          if (
            prev.some(
              (e) =>
                e.from_node === newEdge.from_node &&
                e.to_node === newEdge.to_node &&
                e.type === newEdge.type
            )
          ) {
            return prev;
          }
          return [...prev, newEdge];
        });
        break;
      }

      case 'edge.deleted': {
        setEdges((prev) =>
          prev.filter(
            (e) =>
              !(
                e.from_node === event.data.from_node &&
                e.to_node === event.data.to_node &&
                e.type === (event.data.edge_type as EdgeType)
              )
          )
        );
        break;
      }

      case 'invalidated': {
        // Mark as stale - user should refresh
        setIsStale(true);
        break;
      }
    }
  }, []);

  // Connect to SSE if enabled
  const { isConnected, reconnect } = useGraphSubscription(
    enableRealtime ? projectId : null,
    {
      onEvent: handleEvent,
      subjects,
      onError: (err) => {
        console.error('SSE error:', err);
      },
    }
  );

  // Refresh: re-fetch from API and clear stale state
  const refresh = useCallback(async () => {
    await refetch();
    setIsStale(false);
    setUpdateCount(0);
  }, [refetch]);

  return {
    nodes,
    edges,
    metadata,
    loading,
    error,
    isConnected,
    isStale,
    updateCount,
    refresh,
    reconnect,
  };
}
