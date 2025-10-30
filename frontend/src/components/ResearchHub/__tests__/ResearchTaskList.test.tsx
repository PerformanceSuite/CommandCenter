import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ResearchTaskList from '../ResearchTaskList';
import { useResearchTaskList } from '../../../hooks/useResearchTaskList';
import type { ResearchTask } from '../../../types/research';

vi.mock('../../../hooks/useResearchTaskList', () => ({
  useResearchTaskList: vi.fn(),
}));

describe('ResearchTaskList', () => {
  const mockAddTask = vi.fn();
  const mockRemoveTask = vi.fn();
  const mockRefreshTasks = vi.fn();
  const mockToggleExpand = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should render empty state when no tasks are tracked', () => {
    vi.mocked(useResearchTaskList).mockReturnValue({
      tasks: new Map(),
      expandedTaskId: null,
      refreshing: false,
      error: null,
      addTask: mockAddTask,
      removeTask: mockRemoveTask,
      refreshTasks: mockRefreshTasks,
      toggleExpand: mockToggleExpand,
    });

    render(<ResearchTaskList />);

    expect(screen.getByText('No tasks tracked yet.')).toBeInTheDocument();
    expect(screen.getByText(/Launch a research task from Deep Dive/)).toBeInTheDocument();
  });

  it('should allow adding a task by ID', async () => {
    const mockTask: ResearchTask = {
      task_id: 'test-uuid-123',
      status: 'pending',
      technology: 'React',
      created_at: '2025-10-10T12:00:00Z',
      completed_at: null,
      results: null,
      summary: null,
      error: null,
    };

    const tasksMap = new Map();
    tasksMap.set('test-uuid-123', mockTask);

    vi.mocked(useResearchTaskList).mockReturnValue({
      tasks: tasksMap,
      expandedTaskId: null,
      refreshing: false,
      error: null,
      addTask: mockAddTask,
      removeTask: mockRemoveTask,
      refreshTasks: mockRefreshTasks,
      toggleExpand: mockToggleExpand,
    });

    render(<ResearchTaskList />);

    // Task ID is truncated to 8 chars + "..."
    expect(screen.getByText(/test-uui\.\.\./)).toBeInTheDocument();
    // Status badge contains emoji + text
    expect(screen.getByText(/pending/)).toBeInTheDocument();
    expect(screen.getByText('React')).toBeInTheDocument();
  });

  it('should display error message when task not found', () => {
    vi.mocked(useResearchTaskList).mockReturnValue({
      tasks: new Map(),
      expandedTaskId: null,
      refreshing: false,
      error: 'Failed to add task: Task not found',
      addTask: mockAddTask,
      removeTask: mockRemoveTask,
      refreshTasks: mockRefreshTasks,
      toggleExpand: mockToggleExpand,
    });

    render(<ResearchTaskList />);

    expect(screen.getByText(/Task not found/)).toBeInTheDocument();
  });

  it('should expand task details when task card is clicked', () => {
    const mockTask: ResearchTask = {
      task_id: 'test-uuid-123',
      status: 'completed',
      technology: 'React',
      created_at: '2025-10-10T12:00:00Z',
      completed_at: '2025-10-10T12:05:00Z',
      results: [
        {
          data: { analysis: 'React is great' },
          metadata: {
            agent_role: 'deep_researcher',
            model_used: 'claude-3.5-sonnet',
            provider: 'anthropic',
            execution_time_seconds: 5.2,
            tokens_used: { prompt: 100, completion: 200, total: 300 },
            cost_usd: 0.0045,
          },
          error: null,
        },
      ],
      summary: 'Research completed successfully',
      error: null,
    };

    const tasksMap = new Map();
    tasksMap.set('test-uuid-123', mockTask);

    // First render - not expanded
    vi.mocked(useResearchTaskList).mockReturnValue({
      tasks: tasksMap,
      expandedTaskId: null,
      refreshing: false,
      error: null,
      addTask: mockAddTask,
      removeTask: mockRemoveTask,
      refreshTasks: mockRefreshTasks,
      toggleExpand: mockToggleExpand,
    });

    const { rerender } = render(<ResearchTaskList />);

    // Verify task is displayed (truncated ID)
    expect(screen.getByText(/test-uui\.\.\./)).toBeInTheDocument();
    expect(screen.getByText(/completed/)).toBeInTheDocument();

    // Click task card to expand
    const taskCard = screen.getByText(/completed/).closest('.task-header');
    fireEvent.click(taskCard!);

    expect(mockToggleExpand).toHaveBeenCalledWith('test-uuid-123');

    // Re-render with expanded state
    vi.mocked(useResearchTaskList).mockReturnValue({
      tasks: tasksMap,
      expandedTaskId: 'test-uuid-123',
      refreshing: false,
      error: null,
      addTask: mockAddTask,
      removeTask: mockRemoveTask,
      refreshTasks: mockRefreshTasks,
      toggleExpand: mockToggleExpand,
    });

    rerender(<ResearchTaskList />);

    // Check expanded content
    expect(screen.getByText('Research completed successfully')).toBeInTheDocument();
    expect(screen.getByText('deep_researcher')).toBeInTheDocument();
    // Execution time displayed as "5.20s" with timer emoji
    expect(screen.getByText(/5\.20s/)).toBeInTheDocument();
  });

  it('should display status badges with correct styling', () => {
    const statuses = ['pending', 'running', 'completed', 'failed'] as const;

    for (const status of statuses) {
      const mockTask: ResearchTask = {
        task_id: `test-${status}`,
        status,
        technology: 'React',
        created_at: '2025-10-10T12:00:00Z',
        completed_at: null,
        results: null,
        summary: null,
        error: null,
      };

      const tasksMap = new Map();
      tasksMap.set(`test-${status}`, mockTask);

      vi.mocked(useResearchTaskList).mockReturnValue({
        tasks: tasksMap,
        expandedTaskId: null,
        refreshing: false,
        error: null,
        addTask: mockAddTask,
        removeTask: mockRemoveTask,
        refreshTasks: mockRefreshTasks,
        toggleExpand: mockToggleExpand,
      });

      const { unmount } = render(<ResearchTaskList />);

      // Status text is inside badge with emoji, use regex and check class
      const badge = screen.getByText(new RegExp(status)).closest('.status-badge');
      expect(badge).toHaveClass(`status-${status}`);

      unmount();
    }
  });

  it('should handle manual refresh', () => {
    const mockTask: ResearchTask = {
      task_id: 'test-uuid-123',
      status: 'running',
      technology: 'React',
      created_at: '2025-10-10T12:00:00Z',
      completed_at: null,
      results: null,
      summary: null,
      error: null,
    };

    const tasksMap = new Map();
    tasksMap.set('test-uuid-123', mockTask);

    vi.mocked(useResearchTaskList).mockReturnValue({
      tasks: tasksMap,
      expandedTaskId: null,
      refreshing: false,
      error: null,
      addTask: mockAddTask,
      removeTask: mockRemoveTask,
      refreshTasks: mockRefreshTasks,
      toggleExpand: mockToggleExpand,
    });

    render(<ResearchTaskList />);

    // Click refresh button
    const refreshButton = screen.getByText('Refresh All');
    fireEvent.click(refreshButton);

    expect(mockRefreshTasks).toHaveBeenCalledTimes(1);
  });
});
