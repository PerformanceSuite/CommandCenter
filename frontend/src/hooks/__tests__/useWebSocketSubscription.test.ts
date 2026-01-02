/**
 * Tests for useWebSocketSubscription hook
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocketSubscription } from '../useWebSocketSubscription';
import { graphWebSocket } from '../../services/websocket';

// Mock the websocket service
vi.mock('../../services/websocket', () => ({
  graphWebSocket: {
    connect: vi.fn(),
    subscribe: vi.fn(() => vi.fn()), // Returns unsubscribe function
    disconnect: vi.fn(),
    isConnected: true,
  },
}));

describe('useWebSocketSubscription', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    // Reset isConnected to true for each test
    (graphWebSocket as unknown as { isConnected: boolean }).isConnected = true;
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('connects to websocket on mount', () => {
    // Set isConnected to false to trigger connect
    (graphWebSocket as unknown as { isConnected: boolean }).isConnected = false;

    renderHook(() => useWebSocketSubscription({ topic: 'entity:updated:proj123' }));
    expect(graphWebSocket.connect).toHaveBeenCalled();
  });

  it('does not reconnect if already connected', () => {
    // isConnected is true by default
    renderHook(() => useWebSocketSubscription({ topic: 'entity:updated:proj123' }));
    expect(graphWebSocket.connect).not.toHaveBeenCalled();
  });

  it('subscribes to topic when enabled', () => {
    renderHook(() => useWebSocketSubscription({ topic: 'entity:updated:proj123' }));
    expect(graphWebSocket.subscribe).toHaveBeenCalledWith(
      'entity:updated:proj123',
      expect.any(Function)
    );
  });

  it('does not subscribe when disabled', () => {
    renderHook(() => useWebSocketSubscription({
      topic: 'entity:updated:proj123',
      enabled: false
    }));
    expect(graphWebSocket.subscribe).not.toHaveBeenCalled();
  });

  it('does not subscribe when topic is empty', () => {
    renderHook(() => useWebSocketSubscription({ topic: '' }));
    expect(graphWebSocket.subscribe).not.toHaveBeenCalled();
  });

  it('calls onMessage when message received', () => {
    const onMessage = vi.fn();
    let messageHandler: (data: unknown) => void = () => {};

    (graphWebSocket.subscribe as ReturnType<typeof vi.fn>).mockImplementation(
      (_topic: string, handler: (data: unknown) => void) => {
        messageHandler = handler;
        return vi.fn();
      }
    );

    renderHook(() => useWebSocketSubscription({
      topic: 'test',
      onMessage
    }));

    act(() => {
      messageHandler({ id: 'test123' });
    });

    expect(onMessage).toHaveBeenCalledWith({ id: 'test123' });
  });

  it('updates lastMessage when message received', () => {
    let messageHandler: (data: unknown) => void = () => {};

    (graphWebSocket.subscribe as ReturnType<typeof vi.fn>).mockImplementation(
      (_topic: string, handler: (data: unknown) => void) => {
        messageHandler = handler;
        return vi.fn();
      }
    );

    const { result } = renderHook(() => useWebSocketSubscription<{ id: string }>({
      topic: 'test'
    }));

    expect(result.current.lastMessage).toBeNull();

    act(() => {
      messageHandler({ id: 'test123' });
    });

    expect(result.current.lastMessage).toEqual({ id: 'test123' });
  });

  it('unsubscribes on unmount', () => {
    const unsubscribe = vi.fn();
    (graphWebSocket.subscribe as ReturnType<typeof vi.fn>).mockReturnValue(unsubscribe);

    const { unmount } = renderHook(() =>
      useWebSocketSubscription({ topic: 'test' })
    );

    unmount();
    expect(unsubscribe).toHaveBeenCalled();
  });

  it('resubscribes when topic changes', () => {
    const unsubscribe = vi.fn();
    (graphWebSocket.subscribe as ReturnType<typeof vi.fn>).mockReturnValue(unsubscribe);

    const { rerender } = renderHook(
      ({ topic }) => useWebSocketSubscription({ topic }),
      { initialProps: { topic: 'topic1' } }
    );

    expect(graphWebSocket.subscribe).toHaveBeenCalledWith('topic1', expect.any(Function));
    expect(graphWebSocket.subscribe).toHaveBeenCalledTimes(1);

    rerender({ topic: 'topic2' });

    expect(unsubscribe).toHaveBeenCalled();
    expect(graphWebSocket.subscribe).toHaveBeenCalledWith('topic2', expect.any(Function));
    expect(graphWebSocket.subscribe).toHaveBeenCalledTimes(2);
  });

  it('returns isConnected status', () => {
    const { result } = renderHook(() =>
      useWebSocketSubscription({ topic: 'test' })
    );

    expect(result.current.isConnected).toBe(true);
  });

  it('updates isConnected status periodically', async () => {
    vi.useFakeTimers();

    const { result } = renderHook(() =>
      useWebSocketSubscription({ topic: 'test' })
    );

    expect(result.current.isConnected).toBe(true);

    // Change the mock's isConnected value
    (graphWebSocket as unknown as { isConnected: boolean }).isConnected = false;

    // Advance time past the interval
    await act(async () => {
      vi.advanceTimersByTime(1100);
    });

    expect(result.current.isConnected).toBe(false);
  });
});
