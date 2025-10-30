import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useResearchTaskList } from '../../hooks/useResearchTaskList';
import { researchApi } from '../../services/researchApi';
import type { ResearchTask } from '../../types/research';

vi.mock('../../services/researchApi', () => ({
  researchApi: {
    getResearchTaskStatus: vi.fn(),
  },
}));

describe('useResearchTaskList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should start with empty task list', () => {
    const { result } = renderHook(() => useResearchTaskList());

    expect(result.current.tasks.size).toBe(0);
    expect(result.current.error).toBeNull();
    expect(result.current.refreshing).toBe(false);
  });

  it('should add task and fetch its status', async () => {
    const mockTask: ResearchTask = {
      task_id: 'test-123',
      status: 'running',
      technology: 'React',
      created_at: '2025-10-29T12:00:00Z',
      completed_at: null,
      results: null,
      summary: null,
      error: null,
    };

    vi.mocked(researchApi.getResearchTaskStatus).mockResolvedValue(mockTask);

    const { result } = renderHook(() => useResearchTaskList());

    await act(async () => {
      await result.current.addTask('test-123');
    });

    expect(result.current.tasks.size).toBe(1);
    expect(result.current.tasks.get('test-123')).toEqual(mockTask);
  });

  it('should handle API errors when adding task', async () => {
    vi.mocked(researchApi.getResearchTaskStatus).mockRejectedValue(
      new Error('Task not found')
    );

    const { result } = renderHook(() => useResearchTaskList());

    await act(async () => {
      await result.current.addTask('invalid-id');
    });

    expect(result.current.tasks.size).toBe(0);
    expect(result.current.error).toBe('Failed to add task: Task not found');
  });

  it('should remove task', async () => {
    const mockTask: ResearchTask = {
      task_id: 'test-123',
      status: 'completed',
      technology: 'React',
      created_at: '2025-10-29T12:00:00Z',
      completed_at: '2025-10-29T12:05:00Z',
      results: { success: true },
      summary: 'Test completed',
      error: null,
    };

    vi.mocked(researchApi.getResearchTaskStatus).mockResolvedValue(mockTask);

    const { result } = renderHook(() => useResearchTaskList());

    await act(async () => {
      await result.current.addTask('test-123');
    });

    expect(result.current.tasks.size).toBe(1);

    act(() => {
      result.current.removeTask('test-123');
    });

    expect(result.current.tasks.size).toBe(0);
  });

  it('should refresh all tasks', async () => {
    const mockTask1: ResearchTask = {
      task_id: 'test-1',
      status: 'running',
      technology: 'React',
      created_at: '2025-10-29T12:00:00Z',
      completed_at: null,
      results: null,
      summary: null,
      error: null,
    };

    const mockTask2: ResearchTask = {
      task_id: 'test-2',
      status: 'completed',
      technology: 'Vue',
      created_at: '2025-10-29T12:00:00Z',
      completed_at: '2025-10-29T12:03:00Z',
      results: { success: true },
      summary: 'Done',
      error: null,
    };

    vi.mocked(researchApi.getResearchTaskStatus)
      .mockResolvedValueOnce(mockTask1)
      .mockResolvedValueOnce(mockTask2)
      .mockResolvedValueOnce({ ...mockTask1, status: 'completed' })
      .mockResolvedValueOnce(mockTask2);

    const { result } = renderHook(() => useResearchTaskList());

    // Add two tasks
    await act(async () => {
      await result.current.addTask('test-1');
      await result.current.addTask('test-2');
    });

    expect(result.current.tasks.get('test-1')?.status).toBe('running');

    // Refresh to get updated status
    await act(async () => {
      await result.current.refreshTasks();
    });

    expect(result.current.tasks.get('test-1')?.status).toBe('completed');
    expect(researchApi.getResearchTaskStatus).toHaveBeenCalledTimes(4); // 2 adds + 2 refresh
  });

  it('should toggle task expansion', () => {
    const { result } = renderHook(() => useResearchTaskList());

    expect(result.current.expandedTaskId).toBeNull();

    act(() => {
      result.current.toggleExpand('test-123');
    });

    expect(result.current.expandedTaskId).toBe('test-123');

    act(() => {
      result.current.toggleExpand('test-123');
    });

    expect(result.current.expandedTaskId).toBeNull();
  });
});
