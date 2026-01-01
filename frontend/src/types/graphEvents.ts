/**
 * Graph Event Types for Sprint 4: Real-time Subscriptions
 *
 * These types mirror the backend graph_events.py schemas
 * and are used by the useGraphSubscription hook.
 */

// ============================================================================
// Event Type Literals
// ============================================================================

export type GraphNodeEventType = 'node.created' | 'node.updated' | 'node.deleted';
export type GraphEdgeEventType = 'edge.created' | 'edge.deleted';
export type GraphEventType = GraphNodeEventType | GraphEdgeEventType | 'invalidated';

// ============================================================================
// Event Payloads
// ============================================================================

export interface GraphNodeEvent {
  event_type: 'created' | 'updated' | 'deleted';
  project_id: number;
  node_type: string;
  node_id: string; // Format: "type:id" (e.g., "task:123")
  label?: string;
  changes?: Record<string, unknown>;
  timestamp: string;
}

export interface GraphEdgeEvent {
  event_type: 'created' | 'deleted';
  project_id: number;
  from_node: string; // Format: "type:id"
  to_node: string; // Format: "type:id"
  edge_type: string;
  weight?: number;
  timestamp: string;
}

export interface GraphInvalidatedEvent {
  project_id: number;
  reason: string;
  affected_types?: string[];
  timestamp: string;
}

// ============================================================================
// Unified Event Type
// ============================================================================

export type GraphEvent =
  | { type: 'node.created'; data: GraphNodeEvent }
  | { type: 'node.updated'; data: GraphNodeEvent }
  | { type: 'node.deleted'; data: GraphNodeEvent }
  | { type: 'edge.created'; data: GraphEdgeEvent }
  | { type: 'edge.deleted'; data: GraphEdgeEvent }
  | { type: 'invalidated'; data: GraphInvalidatedEvent };

// ============================================================================
// SSE Connection Events
// ============================================================================

export interface SSEConnectedEvent {
  project_id: number;
  subjects: string[];
  warning?: string;
}

export interface SSEErrorEvent {
  error: string;
}

// ============================================================================
// Hook Options & Return Types
// ============================================================================

export interface UseGraphSubscriptionOptions {
  /** Callback when a graph event is received */
  onEvent: (event: GraphEvent) => void;
  /** Callback when an error occurs */
  onError?: (error: Error) => void;
  /** Callback when connection is established */
  onConnected?: (info: SSEConnectedEvent) => void;
  /** NATS subject patterns to subscribe (default: graph.*) */
  subjects?: string[];
  /** Whether to automatically reconnect (default: true) */
  autoReconnect?: boolean;
}

export interface UseGraphSubscriptionReturn {
  /** Whether the SSE connection is established */
  isConnected: boolean;
  /** The most recent event received */
  lastEvent: GraphEvent | null;
  /** Any connection error */
  error: Error | null;
  /** Manually trigger reconnection */
  reconnect: () => void;
  /** Disconnect from SSE */
  disconnect: () => void;
}
