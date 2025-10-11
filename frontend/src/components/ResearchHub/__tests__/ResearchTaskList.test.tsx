import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import ResearchTaskList from '../ResearchTaskList';
import { researchApi } from '../../../services/researchApi';

// Mock the research API
vi.mock('../../../services/researchApi', () => ({
  researchApi: {
    getResearchTaskStatus: vi.fn(),
  },
}));

describe('ResearchTaskList', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should render empty state when no tasks are tracked', () => {
    render(<ResearchTaskList />);

    expect(screen.getByText('No tasks tracked yet.')).toBeInTheDocument();
    expect(screen.getByText(/Launch a research task from Deep Dive/)).toBeInTheDocument();
  });

  it('should allow adding a task by ID', async () => {
    const mockTask = {
      task_id: 'test-uuid-123',
      status: 'pending' as const,
      technology: 'React',
      created_at: '2025-10-10T12:00:00Z',
      completed_at: null,
      results: null,
      summary: null,
      error: null,
    };

    (researchApi.getResearchTaskStatus as any).mockResolvedValue(mockTask);

    render(<ResearchTaskList />);

    const input = screen.getByPlaceholderText('Enter task ID to track...');
    const addButton = screen.getByText('Add Task');

    fireEvent.change(input, { target: { value: 'test-uuid-123' } });
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(researchApi.getResearchTaskStatus).toHaveBeenCalledWith('test-uuid-123');
    });

    await waitFor(() => {
      expect(screen.getByText(/test-uuid-123/)).toBeInTheDocument();
      expect(screen.getByText('pending')).toBeInTheDocument();
    });
  });

  it('should display error message when task not found', async () => {
    (researchApi.getResearchTaskStatus as any).mockRejectedValue({
      response: { data: { detail: 'Task not found' } },
    });

    render(<ResearchTaskList />);

    const input = screen.getByPlaceholderText('Enter task ID to track...');
    const addButton = screen.getByText('Add Task');

    fireEvent.change(input, { target: { value: 'invalid-id' } });
    fireEvent.click(addButton);

    await waitFor(() => {
      expect(screen.getByText(/Task not found/)).toBeInTheDocument();
    });
  });

  it('should auto-refresh tasks every 3 seconds', async () => {
    const mockTask = {
      task_id: 'test-uuid-123',
      status: 'running' as const,
      technology: 'React',
      created_at: '2025-10-10T12:00:00Z',
      completed_at: null,
      results: null,
      summary: null,
      error: null,
    };

    (researchApi.getResearchTaskStatus as any).mockResolvedValue(mockTask);

    render(<ResearchTaskList />);

    // Add a task first
    const input = screen.getByPlaceholderText('Enter task ID to track...');
    fireEvent.change(input, { target: { value: 'test-uuid-123' } });
    fireEvent.click(screen.getByText('Add Task'));

    await waitFor(() => {
      expect(researchApi.getResearchTaskStatus).toHaveBeenCalledTimes(1);
    });

    // Fast-forward 3 seconds
    vi.advanceTimersByTime(3000);

    await waitFor(() => {
      expect(researchApi.getResearchTaskStatus).toHaveBeenCalledTimes(2);
    });

    // Fast-forward another 3 seconds
    vi.advanceTimersByTime(3000);

    await waitFor(() => {
      expect(researchApi.getResearchTaskStatus).toHaveBeenCalledTimes(3);
    });
  });

  it('should expand task details when task card is clicked', async () => {
    const mockTask = {
      task_id: 'test-uuid-123',
      status: 'completed' as const,
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

    (researchApi.getResearchTaskStatus as any).mockResolvedValue(mockTask);

    render(<ResearchTaskList />);

    // Add task
    const input = screen.getByPlaceholderText('Enter task ID to track...');
    fireEvent.change(input, { target: { value: 'test-uuid-123' } });
    fireEvent.click(screen.getByText('Add Task'));

    await waitFor(() => {
      expect(screen.getByText(/test-uuid-123/)).toBeInTheDocument();
    });

    // Click task card to expand
    const taskCard = screen.getByText('completed').closest('.task-header');
    fireEvent.click(taskCard!);

    // Check expanded content
    await waitFor(() => {
      expect(screen.getByText('Research completed successfully')).toBeInTheDocument();
      expect(screen.getByText('deep_researcher')).toBeInTheDocument();
      expect(screen.getByText(/5.2s/)).toBeInTheDocument();
    });
  });

  it('should display status badges with correct styling', async () => {
    const statuses = ['pending', 'running', 'completed', 'failed'] as const;

    for (const status of statuses) {
      const mockTask = {
        task_id: `test-${status}`,
        status,
        technology: 'React',
        created_at: '2025-10-10T12:00:00Z',
        completed_at: null,
        results: null,
        summary: null,
        error: null,
      };

      (researchApi.getResearchTaskStatus as any).mockResolvedValue(mockTask);

      const { unmount } = render(<ResearchTaskList />);

      const input = screen.getByPlaceholderText('Enter task ID to track...');
      fireEvent.change(input, { target: { value: `test-${status}` } });
      fireEvent.click(screen.getByText('Add Task'));

      await waitFor(() => {
        const badge = screen.getByText(status);
        expect(badge).toHaveClass(`status-${status}`);
      });

      unmount();
    }
  });

  it('should handle manual refresh', async () => {
    const mockTask = {
      task_id: 'test-uuid-123',
      status: 'running' as const,
      technology: 'React',
      created_at: '2025-10-10T12:00:00Z',
      completed_at: null,
      results: null,
      summary: null,
      error: null,
    };

    (researchApi.getResearchTaskStatus as any).mockResolvedValue(mockTask);

    render(<ResearchTaskList />);

    // Add a task
    const input = screen.getByPlaceholderText('Enter task ID to track...');
    fireEvent.change(input, { target: { value: 'test-uuid-123' } });
    fireEvent.click(screen.getByText('Add Task'));

    await waitFor(() => {
      expect(researchApi.getResearchTaskStatus).toHaveBeenCalledTimes(1);
    });

    // Click refresh button
    const refreshButton = screen.getByText('Refresh All');
    fireEvent.click(refreshButton);

    await waitFor(() => {
      expect(researchApi.getResearchTaskStatus).toHaveBeenCalledTimes(2);
    });
  });
});
