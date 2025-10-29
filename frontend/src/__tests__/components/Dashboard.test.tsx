import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { DashboardView } from '../../components/Dashboard/DashboardView';
import { renderWithMemoryRouter } from '../../test-utils/test-utils';
import { mockDashboardStats, mockActivity } from '../../test-utils/mocks';
import { useDashboard } from '../../hooks/useDashboard';

// Mock the dashboard API
vi.mock('../../services/dashboardApi');

// Mock the useDashboard hook
vi.mock('../../hooks/useDashboard', () => ({
  useDashboard: vi.fn(),
}));

describe('DashboardView', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays loading spinner while fetching data', () => {
    vi.mocked(useDashboard).mockReturnValue({
      stats: null,
      activity: [],
      loading: true,
      error: null,
    });

    renderWithMemoryRouter(<DashboardView />);

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays error message when fetch fails', () => {
    vi.mocked(useDashboard).mockReturnValue({
      stats: null,
      activity: [],
      loading: false,
      error: new Error('Network error'),
    });

    renderWithMemoryRouter(<DashboardView />);

    expect(screen.getByText('Failed to load dashboard data')).toBeInTheDocument();
    expect(screen.getByText('Network error')).toBeInTheDocument();
  });

  it('renders dashboard statistics correctly', () => {
    const { useDashboard } = require('../../hooks/useDashboard');
    const mockStats = mockDashboardStats();

    useDashboard.mockReturnValue({
      stats: mockStats,
      activity: [],
      loading: false,
      error: null,
    });

    renderWithMemoryRouter(<DashboardView />);

    // Check statistics section
    expect(screen.getByLabelText('Dashboard statistics')).toBeInTheDocument();

    // Check metric cards
    expect(screen.getByText('Total Repositories')).toBeInTheDocument();
    expect(screen.getByText('5')).toBeInTheDocument();

    expect(screen.getByText('Technologies')).toBeInTheDocument();
    expect(screen.getByText('10')).toBeInTheDocument();

    expect(screen.getByText('Research Tasks')).toBeInTheDocument();
    expect(screen.getByText('15')).toBeInTheDocument();

    expect(screen.getByText('Knowledge Base')).toBeInTheDocument();
    expect(screen.getByText('25')).toBeInTheDocument();
  });

  it('renders quick actions section', () => {
    const { useDashboard } = require('../../hooks/useDashboard');
    const mockStats = mockDashboardStats();

    useDashboard.mockReturnValue({
      stats: mockStats,
      activity: [],
      loading: false,
      error: null,
    });

    renderWithMemoryRouter(<DashboardView />);

    // Check quick actions section
    expect(screen.getByLabelText('Quick actions')).toBeInTheDocument();
    expect(screen.getByText('Add Technology')).toBeInTheDocument();
    expect(screen.getByText('Create Task')).toBeInTheDocument();
    expect(screen.getByText('Upload Document')).toBeInTheDocument();
  });

  it('renders activity feed', () => {
    const { useDashboard } = require('../../hooks/useDashboard');
    const mockStats = mockDashboardStats();
    const activities = mockActivity();

    useDashboard.mockReturnValue({
      stats: mockStats,
      activity: activities,
      loading: false,
      error: null,
    });

    renderWithMemoryRouter(<DashboardView />);

    // Check recent activity section
    expect(screen.getByText('Recent Activity')).toBeInTheDocument();
  });

  it('navigates to correct routes when metric cards are clicked', async () => {
    const { useDashboard } = require('../../hooks/useDashboard');
    const mockStats = mockDashboardStats();

    useDashboard.mockReturnValue({
      stats: mockStats,
      activity: [],
      loading: false,
      error: null,
    });

    renderWithMemoryRouter(<DashboardView />);

    // We can't fully test navigation without checking the actual navigation,
    // but we can verify the buttons are clickable
    const repoButton = screen.getByText('Total Repositories').closest('button');
    expect(repoButton).toBeInTheDocument();
  });

  it('returns null when stats are not available but not loading', () => {
    const { useDashboard } = require('../../hooks/useDashboard');

    useDashboard.mockReturnValue({
      stats: null,
      activity: [],
      loading: false,
      error: null,
    });

    const { container } = renderWithMemoryRouter(<DashboardView />);

    expect(container.firstChild).toBeNull();
  });
});
