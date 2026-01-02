/**
 * WebSocket service for real-time graph updates
 *
 * Sprint 4: WebSocket Infrastructure
 *
 * Provides a singleton WebSocket connection to the graph endpoint
 * with automatic reconnection and topic-based subscriptions.
 */

type MessageHandler = (data: unknown) => void;

interface WebSocketMessage {
  type: string;
  session_id?: string;
  topic?: string;
  data?: unknown;
}

/**
 * GraphWebSocket - Singleton WebSocket manager for graph updates
 *
 * Features:
 * - Automatic reconnection with exponential backoff
 * - Topic-based subscriptions
 * - Pending subscription queue for pre-connection subscribes
 */
class GraphWebSocket {
  private ws: WebSocket | null = null;
  private sessionId: string | null = null;
  private handlers: Map<string, Set<MessageHandler>> = new Map();
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private pendingSubscriptions: string[] = [];
  private url: string | null = null;

  /**
   * Connect to the WebSocket server
   * @param url - WebSocket URL (defaults to ws://${window.location.host}/ws/graph)
   */
  connect(url?: string): void {
    const wsUrl = url || `ws://${window.location.host}/ws/graph`;
    this.url = wsUrl;

    // Don't reconnect if already connected
    if (this.ws?.readyState === WebSocket.OPEN) {
      return;
    }

    // Close existing connection if any
    if (this.ws) {
      this.ws.close();
    }

    this.ws = new WebSocket(wsUrl);

    this.ws.onopen = () => {
      this.reconnectAttempts = 0;
      // Subscribe to pending topics
      this.pendingSubscriptions.forEach(topic => {
        this.sendSubscribe(topic);
      });
      this.pendingSubscriptions = [];
    };

    this.ws.onmessage = (event) => {
      try {
        const message: WebSocketMessage = JSON.parse(event.data);

        if (message.type === 'connected') {
          this.sessionId = message.session_id || null;
        } else if (message.type === 'event' && message.topic) {
          const handlers = this.handlers.get(message.topic);
          handlers?.forEach(handler => handler(message.data));
        }
        // Handle 'subscribed' and 'unsubscribed' confirmations silently
      } catch (err) {
        console.error('Failed to parse WebSocket message:', err);
      }
    };

    this.ws.onclose = () => {
      if (this.reconnectAttempts < this.maxReconnectAttempts && this.url) {
        const delay = 1000 * Math.pow(2, this.reconnectAttempts);
        setTimeout(() => {
          this.reconnectAttempts++;
          this.connect(this.url!);
        }, delay);
      }
    };

    this.ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };
  }

  /**
   * Send subscribe message to server
   */
  private sendSubscribe(topic: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({ action: 'subscribe', topic }));
    }
  }

  /**
   * Subscribe to a topic
   * @param topic - Topic pattern to subscribe to
   * @param handler - Callback for messages on this topic
   * @returns Unsubscribe function
   */
  subscribe(topic: string, handler: MessageHandler): () => void {
    if (!this.handlers.has(topic)) {
      this.handlers.set(topic, new Set());
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.sendSubscribe(topic);
      } else {
        this.pendingSubscriptions.push(topic);
      }
    }
    this.handlers.get(topic)!.add(handler);

    // Return unsubscribe function
    return () => {
      this.handlers.get(topic)?.delete(handler);
      if (this.handlers.get(topic)?.size === 0) {
        this.handlers.delete(topic);
        if (this.ws?.readyState === WebSocket.OPEN) {
          this.ws.send(JSON.stringify({ action: 'unsubscribe', topic }));
        }
      }
    };
  }

  /**
   * Disconnect from the WebSocket server
   */
  disconnect(): void {
    this.ws?.close();
    this.ws = null;
    this.sessionId = null;
    this.handlers.clear();
    this.pendingSubscriptions = [];
    this.reconnectAttempts = this.maxReconnectAttempts; // Prevent auto-reconnect
  }

  /**
   * Check if WebSocket is currently connected
   */
  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }

  /**
   * Get the current session ID
   */
  get currentSessionId(): string | null {
    return this.sessionId;
  }
}

// Export singleton instance
export const graphWebSocket = new GraphWebSocket();

// Export types and class for testing
export { GraphWebSocket };
export type { MessageHandler, WebSocketMessage };
