import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { render, screen, waitFor } from '@testing-library/react';
import ResearchSummary from '../ResearchSummary';
import { researchApi } from '../../../services/researchApi';

vi.mock('../../../services/researchApi', () => ({
  researchApi: {
    getResearchSummary: vi.fn(),
  },
}));

const mockGetResearchSummary = researchApi.getResearchSummary as ReturnType<typeof vi.fn>;

describe('ResearchSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    vi.useFakeTimers();
  });

  afterEach(() => {
    vi.useRealTimers();
  });

  it('should display loading state initially', () => {
    mockGetResearchSummary.mockReturnValue(new Promise(() => {}));

    render(<ResearchSummary />);

    expect(screen.getByText('Loading summary...')).toBeInTheDocument();
  });

  it('should display summary metrics when loaded', async () => {
    const mockSummary = {
      total_tasks: 10,
      completed_tasks: 7,
      failed_tasks: 2,
      agents_deployed: 25,
      total_cost_usd: 1.23,
      avg_execution_time_seconds: 5.5,
    };

    mockGetResearchSummary.mockResolvedValue(mockSummary);

    render(<ResearchSummary />);

    // Run pending timers to allow useEffect and promises to resolve
    await vi.advanceTimersByTimeAsync(0);

    await waitFor(() => {
      expect(screen.getByText('10')).toBeInTheDocument(); // total tasks
      expect(screen.getByText('7')).toBeInTheDocument(); // completed
      expect(screen.getByText('2')).toBeInTheDocument(); // failed
      expect(screen.getByText('25')).toBeInTheDocument(); // agents
      expect(screen.getByText('$1.23')).toBeInTheDocument(); // cost
      expect(screen.getByText('5.5s')).toBeInTheDocument(); // avg time
    });
  });

  it('should calculate completion rate correctly', async () => {
    const mockSummary = {
      total_tasks: 10,
      completed_tasks: 7,
      failed_tasks: 2,
      agents_deployed: 25,
      total_cost_usd: 0,
      avg_execution_time_seconds: 0,
    };

    mockGetResearchSummary.mockResolvedValue(mockSummary);

    render(<ResearchSummary />);

    await vi.advanceTimersByTimeAsync(0);

    await waitFor(() => {
      // 7/10 = 70%
      expect(screen.getByText('70.0%')).toBeInTheDocument();
    });
  });

  it('should display error state on API failure', async () => {
    mockGetResearchSummary.mockRejectedValue(
      new Error('Network error')
    );

    render(<ResearchSummary />);

    await vi.advanceTimersByTimeAsync(0);

    await waitFor(() => {
      expect(screen.getByText(/Network error/)).toBeInTheDocument();
      expect(screen.getByText('Retry')).toBeInTheDocument();
    });
  });

  it('should display empty state when no tasks exist', async () => {
    const mockSummary = {
      total_tasks: 0,
      completed_tasks: 0,
      failed_tasks: 0,
      agents_deployed: 0,
      total_cost_usd: 0,
      avg_execution_time_seconds: 0,
    };

    mockGetResearchSummary.mockResolvedValue(mockSummary);

    render(<ResearchSummary />);

    await vi.advanceTimersByTimeAsync(0);

    await waitFor(() => {
      expect(screen.getByText(/No research tasks have been launched yet/)).toBeInTheDocument();
    });
  });

  it('should auto-refresh every 10 seconds', async () => {
    const mockSummary = {
      total_tasks: 5,
      completed_tasks: 3,
      failed_tasks: 1,
      agents_deployed: 10,
      total_cost_usd: 0,
      avg_execution_time_seconds: 0,
    };

    mockGetResearchSummary.mockResolvedValue(mockSummary);

    render(<ResearchSummary />);

    // Initial load
    await vi.advanceTimersByTimeAsync(0);
    await waitFor(() => {
      expect(researchApi.getResearchSummary).toHaveBeenCalledTimes(1);
    });

    // Fast-forward 10 seconds
    await vi.advanceTimersByTimeAsync(10000);

    await waitFor(() => {
      expect(researchApi.getResearchSummary).toHaveBeenCalledTimes(2);
    });

    // Fast-forward another 10 seconds
    await vi.advanceTimersByTimeAsync(10000);

    await waitFor(() => {
      expect(researchApi.getResearchSummary).toHaveBeenCalledTimes(3);
    });
  });

  it('should cleanup on unmount to prevent memory leaks', async () => {
    const mockSummary = {
      total_tasks: 5,
      completed_tasks: 3,
      failed_tasks: 1,
      agents_deployed: 10,
      total_cost_usd: 0,
      avg_execution_time_seconds: 0,
    };

    mockGetResearchSummary.mockResolvedValue(mockSummary);

    const { unmount } = render(<ResearchSummary />);

    await vi.advanceTimersByTimeAsync(0);
    await waitFor(() => {
      expect(researchApi.getResearchSummary).toHaveBeenCalledTimes(1);
    });

    // Unmount component
    unmount();

    // Fast-forward 10 seconds after unmount
    await vi.advanceTimersByTimeAsync(10000);

    // Should NOT call API again after unmount
    expect(researchApi.getResearchSummary).toHaveBeenCalledTimes(1);
  });

  it('should display progress bar visualization', async () => {
    const mockSummary = {
      total_tasks: 10,
      completed_tasks: 6,
      failed_tasks: 2,
      agents_deployed: 20,
      total_cost_usd: 0,
      avg_execution_time_seconds: 0,
    };

    mockGetResearchSummary.mockResolvedValue(mockSummary);

    render(<ResearchSummary />);

    await vi.advanceTimersByTimeAsync(0);

    await waitFor(() => {
      const progressSection = screen.getByText('Task Completion Progress');
      expect(progressSection).toBeInTheDocument();
    });
  });
});
