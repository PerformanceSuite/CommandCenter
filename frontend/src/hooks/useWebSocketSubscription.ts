/**
 * useWebSocketSubscription - React hook for WebSocket-based graph subscriptions
 *
 * Sprint 4: Real-time Subscriptions via WebSocket
 *
 * Provides a React hook interface to the GraphWebSocket service for
 * real-time graph updates.
 *
 * @example
 * ```tsx
 * const { lastMessage, isConnected } = useWebSocketSubscription({
 *   topic: 'entity:updated:proj123',
 *   onMessage: (data) => {
 *     console.log('Entity updated:', data);
 *   }
 * });
 * ```
 */

import { useEffect, useState, useRef } from 'react';
import { graphWebSocket } from '../services/websocket';

interface UseWebSocketSubscriptionOptions<T> {
  /** Topic pattern to subscribe to */
  topic: string;
  /** Callback for incoming messages */
  onMessage?: (data: T) => void;
  /** Whether subscription is enabled (default: true) */
  enabled?: boolean;
}

interface UseWebSocketSubscriptionResult<T> {
  /** Last received message data */
  lastMessage: T | null;
  /** Whether WebSocket is currently connected */
  isConnected: boolean;
}

/**
 * Hook for subscribing to WebSocket topics
 */
export function useWebSocketSubscription<T = unknown>({
  topic,
  onMessage,
  enabled = true,
}: UseWebSocketSubscriptionOptions<T>): UseWebSocketSubscriptionResult<T> {
  const [lastMessage, setLastMessage] = useState<T | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const onMessageRef = useRef(onMessage);

  // Keep onMessage ref current to avoid subscription churn
  useEffect(() => {
    onMessageRef.current = onMessage;
  }, [onMessage]);

  // Connect on mount
  useEffect(() => {
    if (!graphWebSocket.isConnected) {
      graphWebSocket.connect();
    }
    setIsConnected(graphWebSocket.isConnected);

    // Check connection status periodically
    const interval = setInterval(() => {
      setIsConnected(graphWebSocket.isConnected);
    }, 1000);

    return () => clearInterval(interval);
  }, []);

  // Subscribe to topic
  useEffect(() => {
    if (!enabled || !topic) return;

    const handler = (data: unknown) => {
      setLastMessage(data as T);
      onMessageRef.current?.(data as T);
    };

    const unsubscribe = graphWebSocket.subscribe(topic, handler);
    return unsubscribe;
  }, [topic, enabled]);

  return { lastMessage, isConnected };
}

export default useWebSocketSubscription;
export type { UseWebSocketSubscriptionOptions, UseWebSocketSubscriptionResult };
