import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../../hooks/useWebSocket';

// Mock WebSocket
class MockWebSocket {
  static OPEN = 1;
  static CONNECTING = 0;
  static CLOSING = 2;
  static CLOSED = 3;

  url: string;
  readyState: number = MockWebSocket.CONNECTING;
  onopen: ((event: Event) => void) | null = null;
  onclose: ((event: CloseEvent) => void) | null = null;
  onmessage: ((event: MessageEvent) => void) | null = null;
  onerror: ((event: Event) => void) | null = null;

  private listeners: Map<string, Set<EventListener>> = new Map();

  constructor(url: string) {
    this.url = url;
  }

  addEventListener(event: string, handler: EventListener) {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set());
    }
    this.listeners.get(event)!.add(handler);
  }

  removeEventListener(event: string, handler: EventListener) {
    this.listeners.get(event)?.delete(handler);
  }

  send(data: string) {
    if (this.readyState !== MockWebSocket.OPEN) {
      throw new Error('WebSocket is not open');
    }
  }

  close() {
    this.readyState = MockWebSocket.CLOSED;
    const closeEvent = new Event('close') as CloseEvent;
    this.listeners.get('close')?.forEach((handler) => handler(closeEvent));
  }

  // Helper method to simulate opening connection
  simulateOpen() {
    this.readyState = MockWebSocket.OPEN;
    const openEvent = new Event('open');
    this.listeners.get('open')?.forEach((handler) => handler(openEvent));
  }

  // Helper method to simulate message
  simulateMessage(data: any) {
    const messageEvent = new MessageEvent('message', {
      data: JSON.stringify(data),
    });
    this.listeners.get('message')?.forEach((handler) => handler(messageEvent));
  }

  // Helper method to simulate error
  simulateError() {
    const errorEvent = new Event('error');
    this.listeners.get('error')?.forEach((handler) => handler(errorEvent));
  }
}

describe('useWebSocket', () => {
  let mockWebSocket: MockWebSocket;
  const originalWebSocket = global.WebSocket;

  beforeEach(() => {
    // @ts-ignore
    global.WebSocket = vi.fn((url: string) => {
      mockWebSocket = new MockWebSocket(url);
      return mockWebSocket;
    });
  });

  afterEach(() => {
    global.WebSocket = originalWebSocket;
    vi.clearAllMocks();
  });

  it('handles connection lifecycle correctly', () => {
    const { result, unmount } = renderHook(() =>
      useWebSocket('ws://localhost:8000')
    );

    // Should start disconnected (CONNECTING state)
    expect(result.current.isConnected).toBe(false);
    expect(result.current.error).toBeNull();

    // Simulate connection opening
    act(() => {
      mockWebSocket.simulateOpen();
    });

    // Should now be connected
    expect(result.current.isConnected).toBe(true);
    expect(result.current.error).toBeNull();

    // Test sending message
    act(() => {
      result.current.sendMessage({ type: 'test', data: 'hello' });
    });

    // Test receiving message
    act(() => {
      mockWebSocket.simulateMessage({ type: 'response', data: 'world' });
    });

    expect(result.current.lastMessage).toEqual({
      type: 'response',
      data: 'world',
    });

    // Cleanup - should close connection
    unmount();
    expect(mockWebSocket.readyState).toBe(MockWebSocket.CLOSED);
  });
});
