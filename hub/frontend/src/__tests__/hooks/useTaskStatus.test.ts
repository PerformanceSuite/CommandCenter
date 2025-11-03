/**
 * Tests for useTaskStatus hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useTaskStatus } from '../../hooks/useTaskStatus';

describe('useTaskStatus', () => {
  beforeEach(() => {
    global.fetch = vi.fn();
    vi.clearAllTimers();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.clearAllTimers();
  });

  it('should return null status when taskId is null', () => {
    const { result } = renderHook(() => useTaskStatus(null));

    expect(result.current.status).toBeNull();
    expect(result.current.isPolling).toBe(false);
    expect(result.current.error).toBeNull();
  });

  it('should start polling when taskId is provided', async () => {
    const taskId = 'test-task-123';
    const mockResponse = {
      task_id: taskId,
      state: 'PENDING',
      ready: false,
      status: 'Task is queued',
      progress: 0,
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const { result } = renderHook(() => useTaskStatus(taskId));

    await waitFor(() => {
      expect(result.current.isPolling).toBe(true);
    }, { timeout: 100 });

    expect(global.fetch).toHaveBeenCalledWith('/api/task-status/test-task-123');
  });

  it('should poll every 2 seconds', async () => {
    const taskId = 'test-task-456';
    const mockResponse = {
      task_id: taskId,
      state: 'BUILDING',
      ready: false,
      status: 'Building containers...',
      progress: 50,
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    renderHook(() => useTaskStatus(taskId));

    // Initial call
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(1);
    }, { timeout: 100 });

    // Wait for second poll (2 seconds + buffer)
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    }, { timeout: 2200 });

    // Wait for third poll
    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(3);
    }, { timeout: 2200 });
  });

  it('should stop polling when task is SUCCESS', async () => {
    const taskId = 'test-task-success';
    const mockResponse = {
      task_id: taskId,
      state: 'SUCCESS',
      ready: true,
      status: 'Completed successfully',
      progress: 100,
      result: { status: 'running' },
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const { result } = renderHook(() => useTaskStatus(taskId));

    await waitFor(() => {
      expect(result.current.status?.state).toBe('SUCCESS');
      expect(result.current.isPolling).toBe(false);
    }, { timeout: 100 });

    // Get the initial call count (should be 1)
    const initialCallCount = (global.fetch as any).mock.calls.length;
    expect(initialCallCount).toBeGreaterThanOrEqual(1);

    // Wait to ensure no more polling happens
    await new Promise(resolve => setTimeout(resolve, 2500));

    // Should not have made more calls (or at most one more if interval fired before clearing)
    const finalCallCount = (global.fetch as any).mock.calls.length;
    expect(finalCallCount).toBeLessThanOrEqual(initialCallCount + 1);
  });

  it('should stop polling when task is FAILURE', async () => {
    const taskId = 'test-task-fail';
    const mockResponse = {
      task_id: taskId,
      state: 'FAILURE',
      ready: true,
      status: 'Task failed',
      progress: 0,
      error: 'Dagger build failed',
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const { result } = renderHook(() => useTaskStatus(taskId));

    await waitFor(() => {
      expect(result.current.status?.state).toBe('FAILURE');
      expect(result.current.isPolling).toBe(false);
    }, { timeout: 100 });
  });

  it('should stop polling when task is REVOKED', async () => {
    const taskId = 'test-task-revoked';
    const mockResponse = {
      task_id: taskId,
      state: 'REVOKED',
      ready: true,
      status: 'Task was cancelled',
      progress: 0,
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const { result } = renderHook(() => useTaskStatus(taskId));

    await waitFor(() => {
      expect(result.current.status?.state).toBe('REVOKED');
      expect(result.current.isPolling).toBe(false);
    }, { timeout: 100 });
  });

  it('should handle fetch errors', async () => {
    const taskId = 'test-task-error';

    (global.fetch as any).mockResolvedValue({
      ok: false,
      status: 500,
    });

    const { result } = renderHook(() => useTaskStatus(taskId));

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
      expect(result.current.isPolling).toBe(false);
    }, { timeout: 100 });
  });

  it('should update status as task progresses', async () => {
    const taskId = 'test-task-progress';
    let callCount = 0;

    (global.fetch as any).mockImplementation(async () => {
      callCount++;
      if (callCount === 1) {
        return {
          ok: true,
          json: async () => ({
            task_id: taskId,
            state: 'PENDING',
            ready: false,
            status: 'Queued',
            progress: 0,
          }),
        };
      } else if (callCount === 2) {
        return {
          ok: true,
          json: async () => ({
            task_id: taskId,
            state: 'BUILDING',
            ready: false,
            status: 'Building containers...',
            progress: 50,
          }),
        };
      } else {
        return {
          ok: true,
          json: async () => ({
            task_id: taskId,
            state: 'SUCCESS',
            ready: true,
            status: 'Complete',
            progress: 100,
          }),
        };
      }
    });

    const { result } = renderHook(() => useTaskStatus(taskId));

    // First poll - PENDING
    await waitFor(() => {
      expect(result.current.status?.state).toBe('PENDING');
      expect(result.current.status?.progress).toBe(0);
    }, { timeout: 100 });

    // Second poll - BUILDING (wait for 2 second interval)
    await waitFor(() => {
      expect(result.current.status?.state).toBe('BUILDING');
      expect(result.current.status?.progress).toBe(50);
    }, { timeout: 2200 });

    // Third poll - SUCCESS (should stop polling)
    await waitFor(() => {
      expect(result.current.status?.state).toBe('SUCCESS');
      expect(result.current.status?.progress).toBe(100);
      expect(result.current.isPolling).toBe(false);
    }, { timeout: 2200 });
  });

  it('should cleanup interval on unmount', async () => {
    const taskId = 'test-task-cleanup';
    const mockResponse = {
      task_id: taskId,
      state: 'BUILDING',
      ready: false,
      status: 'Building...',
      progress: 30,
    };

    (global.fetch as any).mockResolvedValue({
      ok: true,
      json: async () => mockResponse,
    });

    const { unmount } = renderHook(() => useTaskStatus(taskId));

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalled();
    }, { timeout: 100 });

    const callsBefore = (global.fetch as any).mock.calls.length;

    // Unmount
    unmount();

    // Wait to ensure no more calls after unmount
    await new Promise(resolve => setTimeout(resolve, 2500));

    expect((global.fetch as any).mock.calls.length).toBe(callsBefore);
  });
});
