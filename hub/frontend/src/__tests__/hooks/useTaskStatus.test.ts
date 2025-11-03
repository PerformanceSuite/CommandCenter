/**
 * Tests for useTaskStatus hook
 */
import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { useTaskStatus } from '../../hooks/useTaskStatus';

describe('useTaskStatus', () => {
  beforeEach(() => {
    vi.useFakeTimers();
    global.fetch = vi.fn();
  });

  afterEach(() => {
    vi.restoreAllMocks();
    vi.useRealTimers();
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
    });

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
    });

    // Advance 2 seconds
    vi.advanceTimersByTime(2000);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(2);
    });

    // Advance another 2 seconds
    vi.advanceTimersByTime(2000);

    await waitFor(() => {
      expect(global.fetch).toHaveBeenCalledTimes(3);
    });
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
    });

    // Advance time to ensure no more polling
    vi.advanceTimersByTime(10000);

    expect(global.fetch).toHaveBeenCalledTimes(1);
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
    });
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
    });
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
    });
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
    });

    // Second poll - BUILDING
    vi.advanceTimersByTime(2000);
    await waitFor(() => {
      expect(result.current.status?.state).toBe('BUILDING');
      expect(result.current.status?.progress).toBe(50);
    });

    // Third poll - SUCCESS (should stop polling)
    vi.advanceTimersByTime(2000);
    await waitFor(() => {
      expect(result.current.status?.state).toBe('SUCCESS');
      expect(result.current.status?.progress).toBe(100);
      expect(result.current.isPolling).toBe(false);
    });
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
    });

    const callsBefore = (global.fetch as any).mock.calls.length;

    // Unmount
    unmount();

    // Advance timers - should not make more calls
    vi.advanceTimersByTime(10000);

    expect((global.fetch as any).mock.calls.length).toBe(callsBefore);
  });
});
