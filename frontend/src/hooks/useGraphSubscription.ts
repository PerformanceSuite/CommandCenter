/**
 * useGraphSubscription - SSE hook for real-time graph updates
 *
 * Sprint 4: Real-time Subscriptions
 *
 * Connects to the SSE endpoint and delivers typed graph events
 * for real-time UI updates.
 *
 * @example
 * ```tsx
 * const { isConnected, lastEvent } = useGraphSubscription(projectId, {
 *   onEvent: (event) => {
 *     if (event.type === 'node.created') {
 *       console.log('New node:', event.data.label);
 *     }
 *   }
 * });
 * ```
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  GraphEvent,
  GraphNodeEvent,
  GraphEdgeEvent,
  GraphInvalidatedEvent,
  SSEConnectedEvent,
  UseGraphSubscriptionOptions,
  UseGraphSubscriptionReturn,
} from '../types/graphEvents';

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

/**
 * Parse SSE event into typed GraphEvent
 */
function parseSSEEvent(eventType: string, data: string): GraphEvent | null {
  try {
    const parsed = JSON.parse(data);

    // Map SSE event types to our union types
    if (eventType.startsWith('graph.node.')) {
      const nodeEventType = eventType.replace('graph.node.', '') as 'created' | 'updated' | 'deleted';
      return {
        type: `node.${nodeEventType}` as const,
        data: parsed as GraphNodeEvent,
      };
    }

    if (eventType.startsWith('graph.edge.')) {
      const edgeEventType = eventType.replace('graph.edge.', '') as 'created' | 'deleted';
      return {
        type: `edge.${edgeEventType}` as const,
        data: parsed as GraphEdgeEvent,
      };
    }

    if (eventType === 'graph.invalidated') {
      return {
        type: 'invalidated',
        data: parsed as GraphInvalidatedEvent,
      };
    }

    // Unknown event type
    console.warn('Unknown SSE event type:', eventType);
    return null;
  } catch (err) {
    console.error('Failed to parse SSE event data:', err);
    return null;
  }
}

export function useGraphSubscription(
  projectId: number | null,
  options: UseGraphSubscriptionOptions
): UseGraphSubscriptionReturn {
  const [isConnected, setIsConnected] = useState(false);
  const [lastEvent, setLastEvent] = useState<GraphEvent | null>(null);
  const [error, setError] = useState<Error | null>(null);

  const eventSourceRef = useRef<EventSource | null>(null);
  const reconnectTimeoutRef = useRef<ReturnType<typeof setTimeout>>();

  const {
    onEvent,
    onError,
    onConnected,
    subjects = ['graph.*'],
    autoReconnect = true,
  } = options;

  // Store callbacks in refs to avoid reconnecting on callback changes
  const onEventRef = useRef(onEvent);
  const onErrorRef = useRef(onError);
  const onConnectedRef = useRef(onConnected);

  useEffect(() => {
    onEventRef.current = onEvent;
    onErrorRef.current = onError;
    onConnectedRef.current = onConnected;
  }, [onEvent, onError, onConnected]);

  const connect = useCallback(() => {
    if (!projectId) return;

    // Clean up existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    try {
      // Build SSE URL
      const params = new URLSearchParams({
        project_id: String(projectId),
        subjects: subjects.join(','),
      });
      const url = `${API_BASE_URL}/api/v1/events/stream?${params}`;

      const eventSource = new EventSource(url);
      eventSourceRef.current = eventSource;

      // Connection opened
      eventSource.addEventListener('connected', (event) => {
        setIsConnected(true);
        setError(null);

        try {
          const info: SSEConnectedEvent = JSON.parse(event.data);
          onConnectedRef.current?.(info);

          if (info.warning) {
            console.warn('SSE connection warning:', info.warning);
          }
        } catch (err) {
          console.error('Failed to parse connected event:', err);
        }
      });

      // Graph node events
      eventSource.addEventListener('graph.node.created', (event) => {
        const graphEvent = parseSSEEvent('graph.node.created', event.data);
        if (graphEvent) {
          setLastEvent(graphEvent);
          onEventRef.current(graphEvent);
        }
      });

      eventSource.addEventListener('graph.node.updated', (event) => {
        const graphEvent = parseSSEEvent('graph.node.updated', event.data);
        if (graphEvent) {
          setLastEvent(graphEvent);
          onEventRef.current(graphEvent);
        }
      });

      eventSource.addEventListener('graph.node.deleted', (event) => {
        const graphEvent = parseSSEEvent('graph.node.deleted', event.data);
        if (graphEvent) {
          setLastEvent(graphEvent);
          onEventRef.current(graphEvent);
        }
      });

      // Graph edge events
      eventSource.addEventListener('graph.edge.created', (event) => {
        const graphEvent = parseSSEEvent('graph.edge.created', event.data);
        if (graphEvent) {
          setLastEvent(graphEvent);
          onEventRef.current(graphEvent);
        }
      });

      eventSource.addEventListener('graph.edge.deleted', (event) => {
        const graphEvent = parseSSEEvent('graph.edge.deleted', event.data);
        if (graphEvent) {
          setLastEvent(graphEvent);
          onEventRef.current(graphEvent);
        }
      });

      // Graph invalidation
      eventSource.addEventListener('graph.invalidated', (event) => {
        const graphEvent = parseSSEEvent('graph.invalidated', event.data);
        if (graphEvent) {
          setLastEvent(graphEvent);
          onEventRef.current(graphEvent);
        }
      });

      // Error event
      eventSource.addEventListener('error', (event) => {
        try {
          const data = JSON.parse((event as MessageEvent).data || '{}');
          const err = new Error(data.error || 'SSE error occurred');
          setError(err);
          onErrorRef.current?.(err);
        } catch {
          // Generic error (connection issue)
          const err = new Error('SSE connection error');
          setError(err);
          onErrorRef.current?.(err);
        }
      });

      // Connection error/close - try to reconnect
      eventSource.onerror = () => {
        setIsConnected(false);

        if (autoReconnect && eventSourceRef.current === eventSource) {
          // Clear any pending reconnect
          if (reconnectTimeoutRef.current) {
            clearTimeout(reconnectTimeoutRef.current);
          }

          // Reconnect after delay
          reconnectTimeoutRef.current = setTimeout(() => {
            if (eventSourceRef.current === eventSource) {
              console.log('SSE reconnecting...');
              connect();
            }
          }, 3000);
        }
      };
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to connect to SSE');
      setError(error);
      onErrorRef.current?.(error);
    }
  }, [projectId, subjects, autoReconnect]);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsConnected(false);
  }, []);

  const reconnect = useCallback(() => {
    disconnect();
    connect();
  }, [disconnect, connect]);

  // Connect on mount and when projectId changes
  useEffect(() => {
    if (projectId) {
      connect();
    }

    return () => {
      disconnect();
    };
  }, [projectId, connect, disconnect]);

  return {
    isConnected,
    lastEvent,
    error,
    reconnect,
    disconnect,
  };
}
