/**
 * Tests for ProjectCard component
 *
 * Tests project card rendering, status display, and user interactions.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import ProjectCard from '../../components/ProjectCard';
import { createMockProject } from '../../test-utils/mocks';
import type { Project } from '../../types';

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    loading: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  },
}));

// Mock API
vi.mock('../../services/api', () => ({
  deleteProject: vi.fn(),
  api: {
    orchestration: {
      start: vi.fn().mockResolvedValue({ success: true }),
      stop: vi.fn().mockResolvedValue({ success: true }),
    },
    tasks: {
      start: vi.fn().mockResolvedValue({
        task_id: 'test-task-123',
        status: 'pending',
        message: 'Task started',
      }),
      stop: vi.fn().mockResolvedValue({
        task_id: 'test-task-456',
        status: 'pending',
        message: 'Task started',
      }),
    },
  },
}));

// Mock useTaskStatus hook
vi.mock('../../hooks/useTaskStatus', () => ({
  useTaskStatus: vi.fn().mockReturnValue({
    status: null,
    isPolling: false,
    error: null,
  }),
}));

describe('ProjectCard', () => {
  const mockOnDelete = vi.fn();

  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders project information correctly', () => {
    const project = createMockProject({
      name: 'TestProject',
      path: '/tmp/test',
      frontend_port: 3010,
      backend_port: 8010,
      status: 'stopped',
    });

    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    expect(screen.getByText('TestProject')).toBeInTheDocument();
    expect(screen.getByText('/tmp/test')).toBeInTheDocument();
    expect(screen.getByText('3010')).toBeInTheDocument();
    expect(screen.getByText('8010')).toBeInTheDocument();
  });

  it('displays correct status for stopped project', () => {
    const project = createMockProject({ status: 'stopped' });

    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    expect(screen.getByText('Stopped')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /start/i })).toBeInTheDocument();
  });

  it('displays correct status for running project', () => {
    const project = createMockProject({
      status: 'running',
      health: 'healthy',
    });

    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    expect(screen.getByText('Running')).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /open/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /stop/i })).toBeInTheDocument();
  });

  it('displays correct status for error project', () => {
    const project = createMockProject({ status: 'error' });

    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    expect(screen.getByText('Error')).toBeInTheDocument();
  });

  it('displays starting status correctly', () => {
    const project = createMockProject({
      status: 'running',
      health: 'unhealthy', // Starting but not healthy yet
    });

    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    expect(screen.getByText('Starting...')).toBeInTheDocument();
  });

  it('start button triggers start action', async () => {
    const { api } = await import('../../services/api');
    const project = createMockProject({ status: 'stopped', id: 1 });

    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    const startButton = screen.getByRole('button', { name: /start/i });
    await userEvent.click(startButton);

    await waitFor(() => {
      expect(api.tasks.start).toHaveBeenCalledWith(1);
    });
  });

  it('stop button triggers stop action', async () => {
    const { api } = await import('../../services/api');
    const project = createMockProject({
      status: 'running',
      health: 'healthy',
      id: 2,
    });

    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    const stopButton = screen.getByRole('button', { name: /stop/i });
    await userEvent.click(stopButton);

    await waitFor(() => {
      expect(api.tasks.stop).toHaveBeenCalledWith(2);
    });
  });

  it('open button opens project in new window', async () => {
    const project = createMockProject({
      status: 'running',
      health: 'healthy',
      frontend_port: 3010,
    });

    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    const openButton = screen.getByRole('button', { name: /open/i });
    await userEvent.click(openButton);

    expect(window.open).toHaveBeenCalled();
    const callArgs = (window.open as any).mock.calls[0];
    expect(callArgs[0]).toContain('localhost:3010');
  });

  it('delete button shows confirmation dialog', async () => {
    const project = createMockProject({ status: 'stopped' });

    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    const deleteButton = screen.getByRole('button', { name: /delete/i });
    await userEvent.click(deleteButton);

    expect(screen.getByText(/delete files too/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /yes/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /no/i })).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /cancel/i })).toBeInTheDocument();
  });

  it('delete without files calls deleteProject correctly', async () => {
    const { deleteProject } = await import('../../services/api');
    const project = createMockProject({ id: 1 });

    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    // Open delete confirmation
    const deleteButton = screen.getByRole('button', { name: /delete/i });
    await userEvent.click(deleteButton);

    // Click "No" to delete without files
    const noButton = screen.getByRole('button', { name: /no/i });
    await userEvent.click(noButton);

    await waitFor(() => {
      expect(deleteProject).toHaveBeenCalledWith(1, false);
      expect(mockOnDelete).toHaveBeenCalled();
    });
  });

  it('delete with files calls deleteProject correctly', async () => {
    const { deleteProject } = await import('../../services/api');
    const project = createMockProject({ id: 2 });

    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    // Open delete confirmation
    const deleteButton = screen.getByRole('button', { name: /delete/i });
    await userEvent.click(deleteButton);

    // Click "Yes" to delete with files
    const yesButton = screen.getByRole('button', { name: /yes/i });
    await userEvent.click(yesButton);

    await waitFor(() => {
      expect(deleteProject).toHaveBeenCalledWith(2, true);
      expect(mockOnDelete).toHaveBeenCalled();
    });
  });

  it('cancel delete closes confirmation dialog', async () => {
    const project = createMockProject();

    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    // Open delete confirmation
    const deleteButton = screen.getByRole('button', { name: /delete/i });
    await userEvent.click(deleteButton);

    // Click cancel
    const cancelButton = screen.getByRole('button', { name: /cancel/i });
    await userEvent.click(cancelButton);

    // Confirmation should be hidden
    expect(screen.queryByText(/delete files too/i)).not.toBeInTheDocument();
  });

  it('displays status color indicator correctly', () => {
    const { container: stoppedContainer } = render(
      <ProjectCard
        project={createMockProject({ status: 'stopped' })}
        onDelete={mockOnDelete}
      />
    );

    // Check for gray indicator (stopped)
    expect(stoppedContainer.querySelector('.bg-gray-500')).toBeInTheDocument();
  });

  it('disables start button while task is polling', () => {
    const { useTaskStatus } = require('../../hooks/useTaskStatus');
    useTaskStatus.mockReturnValue({
      status: { state: 'BUILDING', progress: 50, status: 'Building...' },
      isPolling: true,
      error: null,
    });

    const project = createMockProject({ status: 'stopped' });
    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    const startButton = screen.getByRole('button', { name: /starting/i });
    expect(startButton).toBeDisabled();
  });

  it('shows progress bar when task is running', () => {
    const { useTaskStatus } = require('../../hooks/useTaskStatus');
    useTaskStatus.mockReturnValue({
      status: {
        state: 'BUILDING',
        progress: 60,
        status: 'Building containers...',
        ready: false,
      },
      isPolling: true,
      error: null,
    });

    const project = createMockProject({ status: 'stopped' });
    const { container } = render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    // Check for progress bar
    expect(screen.getByText('60%')).toBeInTheDocument();
    expect(screen.getByText('Building containers...')).toBeInTheDocument();

    // Check for progress bar element
    expect(container.querySelector('.bg-blue-500')).toBeInTheDocument();
  });

  it('does not show progress bar when no task is running', () => {
    const { useTaskStatus } = require('../../hooks/useTaskStatus');
    useTaskStatus.mockReturnValue({
      status: null,
      isPolling: false,
      error: null,
    });

    const project = createMockProject({ status: 'stopped' });
    render(<ProjectCard project={project} onDelete={mockOnDelete} />);

    // Should not have progress percentage
    expect(screen.queryByText(/%$/)).not.toBeInTheDocument();
  });
});
