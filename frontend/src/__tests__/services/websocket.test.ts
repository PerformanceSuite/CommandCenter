/**
 * Tests for WebSocket service
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { GraphWebSocket } from '../../services/websocket';

// Mock WebSocket class
class MockWebSocket {
  static CONNECTING = 0;
  static OPEN = 1;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  constructor(url: string) {
    this.url = url;
  }

  send = vi.fn();

  close() {
    this.readyState = MockWebSocket.CLOSED;
    this.onclose?.(new CloseEvent('close'));
  }

  // Test helpers
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    this.onopen?.(new Event('open'));
  }

  simulateMessage(data: unknown) {
    this.onmessage?.(new MessageEvent('message', {
      data: JSON.stringify(data)
    }));
  }

  simulateError() {
    this.onerror?.(new Event('error'));
  }
}

describe('GraphWebSocket', () => {
  let graphWs: GraphWebSocket;
  let mockWebSocket: MockWebSocket;
  const originalWebSocket = global.WebSocket;

  beforeEach(() => {
    graphWs = new GraphWebSocket();

    // Mock global WebSocket
    global.WebSocket = vi.fn((url: string) => {
      mockWebSocket = new MockWebSocket(url);
      return mockWebSocket;
    }) as unknown as typeof WebSocket;

    // Add static properties
    (global.WebSocket as unknown as Record<string, number>).CONNECTING = 0;
    (global.WebSocket as unknown as Record<string, number>).OPEN = 1;
    (global.WebSocket as unknown as Record<string, number>).CLOSING = 2;
    (global.WebSocket as unknown as Record<string, number>).CLOSED = 3;
  });

  afterEach(() => {
    graphWs.disconnect();
    global.WebSocket = originalWebSocket;
    vi.clearAllMocks();
    vi.useRealTimers();
  });

  describe('connect', () => {
    it('creates WebSocket connection with default URL', () => {
      graphWs.connect();
      // The URL includes window.location.host which may include a port
      expect(global.WebSocket).toHaveBeenCalledWith(
        expect.stringMatching(/^ws:\/\/localhost(:\d+)?\/ws\/graph$/)
      );
    });

    it('creates WebSocket connection with custom URL', () => {
      graphWs.connect('ws://example.com/ws');
      expect(global.WebSocket).toHaveBeenCalledWith('ws://example.com/ws');
    });

    it('does not reconnect if already connected', () => {
      graphWs.connect();
      mockWebSocket.simulateOpen();

      graphWs.connect();
      expect(global.WebSocket).toHaveBeenCalledTimes(1);
    });

    it('sets isConnected to true when connection opens', () => {
      graphWs.connect();
      expect(graphWs.isConnected).toBe(false);

      mockWebSocket.simulateOpen();
      expect(graphWs.isConnected).toBe(true);
    });
  });

  describe('session management', () => {
    it('stores session ID from connected message', () => {
      graphWs.connect();
      mockWebSocket.simulateOpen();

      mockWebSocket.simulateMessage({
        type: 'connected',
        session_id: 'test-session-123'
      });

      expect(graphWs.currentSessionId).toBe('test-session-123');
    });
  });

  describe('subscribe', () => {
    it('sends subscribe message when connected', () => {
      graphWs.connect();
      mockWebSocket.simulateOpen();

      graphWs.subscribe('entity:updated', () => {});

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ action: 'subscribe', topic: 'entity:updated' })
      );
    });

    it('queues subscriptions when not connected', () => {
      graphWs.connect();
      // Don't simulate open yet

      graphWs.subscribe('entity:updated', () => {});

      expect(mockWebSocket.send).not.toHaveBeenCalled();

      // Now connect
      mockWebSocket.simulateOpen();

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ action: 'subscribe', topic: 'entity:updated' })
      );
    });

    it('calls handler when message for topic is received', () => {
      const handler = vi.fn();
      graphWs.connect();
      mockWebSocket.simulateOpen();

      graphWs.subscribe('entity:updated', handler);

      mockWebSocket.simulateMessage({
        type: 'event',
        topic: 'entity:updated',
        data: { id: 'test123' }
      });

      expect(handler).toHaveBeenCalledWith({ id: 'test123' });
    });

    it('only calls handlers for matching topic', () => {
      const handler1 = vi.fn();
      const handler2 = vi.fn();
      graphWs.connect();
      mockWebSocket.simulateOpen();

      graphWs.subscribe('topic1', handler1);
      graphWs.subscribe('topic2', handler2);

      mockWebSocket.simulateMessage({
        type: 'event',
        topic: 'topic1',
        data: { value: 'test' }
      });

      expect(handler1).toHaveBeenCalledWith({ value: 'test' });
      expect(handler2).not.toHaveBeenCalled();
    });

    it('returns unsubscribe function', () => {
      const handler = vi.fn();
      graphWs.connect();
      mockWebSocket.simulateOpen();

      const unsubscribe = graphWs.subscribe('entity:updated', handler);

      unsubscribe();

      mockWebSocket.simulateMessage({
        type: 'event',
        topic: 'entity:updated',
        data: { id: 'test123' }
      });

      expect(handler).not.toHaveBeenCalled();
    });

    it('sends unsubscribe message when last handler removed', () => {
      graphWs.connect();
      mockWebSocket.simulateOpen();

      const unsubscribe = graphWs.subscribe('entity:updated', () => {});

      // Clear previous calls
      mockWebSocket.send.mockClear();

      unsubscribe();

      expect(mockWebSocket.send).toHaveBeenCalledWith(
        JSON.stringify({ action: 'unsubscribe', topic: 'entity:updated' })
      );
    });

    it('does not send unsubscribe if other handlers remain', () => {
      graphWs.connect();
      mockWebSocket.simulateOpen();

      const unsubscribe1 = graphWs.subscribe('entity:updated', () => {});
      graphWs.subscribe('entity:updated', () => {});

      mockWebSocket.send.mockClear();

      unsubscribe1();

      expect(mockWebSocket.send).not.toHaveBeenCalled();
    });
  });

  describe('disconnect', () => {
    it('closes WebSocket connection', () => {
      graphWs.connect();
      mockWebSocket.simulateOpen();

      const closeSpy = vi.spyOn(mockWebSocket, 'close');
      graphWs.disconnect();

      expect(closeSpy).toHaveBeenCalled();
      expect(graphWs.isConnected).toBe(false);
    });

    it('clears session ID and handlers', () => {
      graphWs.connect();
      mockWebSocket.simulateOpen();

      mockWebSocket.simulateMessage({
        type: 'connected',
        session_id: 'test-session'
      });

      graphWs.subscribe('test', () => {});
      graphWs.disconnect();

      expect(graphWs.currentSessionId).toBeNull();
    });
  });

  describe('reconnection', () => {
    it('attempts to reconnect on close with exponential backoff', () => {
      vi.useFakeTimers();

      graphWs.connect();
      mockWebSocket.simulateOpen();
      mockWebSocket.close();

      // After first close, should attempt reconnect after 1s
      expect(global.WebSocket).toHaveBeenCalledTimes(1);

      vi.advanceTimersByTime(1000);
      expect(global.WebSocket).toHaveBeenCalledTimes(2);
    });

    it('stops reconnecting after max attempts', () => {
      vi.useFakeTimers();

      graphWs.connect();

      // After max reconnect attempts, close should not trigger more reconnects
      // We need to exhaust the reconnect attempts

      // First close triggers reconnect attempt 1 (delay: 1s)
      mockWebSocket.close();
      vi.advanceTimersByTime(1000);
      // Second close triggers reconnect attempt 2 (delay: 2s)
      mockWebSocket.close();
      vi.advanceTimersByTime(2000);
      // Third close triggers reconnect attempt 3 (delay: 4s)
      mockWebSocket.close();
      vi.advanceTimersByTime(4000);
      // Fourth close triggers reconnect attempt 4 (delay: 8s)
      mockWebSocket.close();
      vi.advanceTimersByTime(8000);
      // Fifth close triggers reconnect attempt 5 (delay: 16s)
      mockWebSocket.close();
      vi.advanceTimersByTime(16000);

      const callsAfterMaxAttempts = (global.WebSocket as ReturnType<typeof vi.fn>).mock.calls.length;

      // Now close again - should NOT trigger more reconnects
      mockWebSocket.close();
      vi.advanceTimersByTime(100000);

      const finalCalls = (global.WebSocket as ReturnType<typeof vi.fn>).mock.calls.length;

      // Verify no additional reconnects after max attempts
      expect(finalCalls).toBe(callsAfterMaxAttempts);
    });

    it('resets reconnect counter on successful connection', () => {
      vi.useFakeTimers();

      graphWs.connect();
      mockWebSocket.close();

      vi.advanceTimersByTime(1000);
      mockWebSocket.simulateOpen();
      mockWebSocket.close();

      // Should start over with 1s delay
      vi.advanceTimersByTime(1000);
      expect(global.WebSocket).toHaveBeenCalledTimes(3);
    });
  });
});
