/**
 * Tests for Dashboard component (Project List Display)
 *
 * Tests project list rendering, loading states, and empty states.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import Dashboard from '../../pages/Dashboard';
import { mockProjects, mockStats } from '../../test-utils/mocks';

// Mock react-hot-toast
vi.mock('react-hot-toast', () => ({
  default: {
    loading: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
    dismiss: vi.fn(),
  },
}));

// Mock API (must be defined inline to avoid hoisting issues)
vi.mock('../../services/api', () => ({
  projectsApi: {
    list: vi.fn(),
    stats: vi.fn(),
    create: vi.fn(),
  },
  api: {
    orchestration: {
      start: vi.fn(),
      stop: vi.fn(),
      status: vi.fn(),
    },
  },
  deleteProject: vi.fn(),
}));

describe('Dashboard - Project List Display', () => {
  beforeEach(async () => {
    vi.clearAllMocks();
    const { projectsApi } = await import('../../services/api');
    (projectsApi.list as any).mockReset();
    (projectsApi.stats as any).mockReset();
  });

  it('displays loading state initially', async () => {
    const { projectsApi } = await import('../../services/api');
    (projectsApi.list as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );
    (projectsApi.stats as any).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    render(<Dashboard />);

    expect(screen.getByText(/loading projects/i)).toBeInTheDocument();
  });

  it('renders project list after loading', async () => {
    const { projectsApi } = await import('../../services/api');
    (projectsApi.list as any).mockResolvedValue(mockProjects);
    (projectsApi.stats as any).mockResolvedValue(mockStats);

    render(<Dashboard />);

    await waitFor(() => {
      expect(screen.getByText('TestProject1')).toBeInTheDocument();
      expect(screen.getByText('TestProject2')).toBeInTheDocument();
      expect(screen.getByText('ErrorProject')).toBeInTheDocument();
    });
  });

  it('displays empty state when no projects', async () => {
    const { projectsApi } = await import('../../services/api');
    (projectsApi.list as any).mockResolvedValue([]);
    (projectsApi.stats as any).mockResolvedValue({
      total_projects: 0,
      running: 0,
      stopped: 0,
      errors: 0,
    });

    render(<Dashboard />);

    await waitFor(() => {
      expect(
        screen.getByText(/no projects yet/i)
      ).toBeInTheDocument();
    });
  });

  it('calls API to load projects and stats', async () => {
    const { projectsApi } = await import('../../services/api');
    (projectsApi.list as any).mockResolvedValue(mockProjects);
    (projectsApi.stats as any).mockResolvedValue(mockStats);

    render(<Dashboard />);

    // Wait for API calls
    await waitFor(() => {
      expect(projectsApi.list).toHaveBeenCalled();
      expect(projectsApi.stats).toHaveBeenCalled();
    });
  });
});
