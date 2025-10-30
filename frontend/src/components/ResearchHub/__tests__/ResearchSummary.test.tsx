import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent } from '@testing-library/react';
import ResearchSummary from '../ResearchSummary';
import { useResearchSummary } from '../../../hooks/useResearchSummary';

vi.mock('../../../hooks/useResearchSummary', () => ({
  useResearchSummary: vi.fn(),
}));

describe('ResearchSummary', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should display loading state initially', () => {
    vi.mocked(useResearchSummary).mockReturnValue({
      summary: null,
      loading: true,
      error: null,
      refetch: vi.fn(),
    });

    render(<ResearchSummary />);

    expect(screen.getByText('Loading summary...')).toBeInTheDocument();
  });

  it('should display summary metrics when loaded', () => {
    const mockSummary = {
      total_tasks: 10,
      completed_tasks: 7,
      failed_tasks: 2,
      agents_deployed: 25,
      total_cost_usd: 1.23,
      avg_execution_time_seconds: 5.5,
    };

    vi.mocked(useResearchSummary).mockReturnValue({
      summary: mockSummary,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<ResearchSummary />);

    expect(screen.getByText('10')).toBeInTheDocument(); // total tasks
    expect(screen.getByText('7')).toBeInTheDocument(); // completed
    expect(screen.getByText('2')).toBeInTheDocument(); // failed
    expect(screen.getByText('25')).toBeInTheDocument(); // agents
    expect(screen.getByText('$1.23')).toBeInTheDocument(); // cost
    expect(screen.getByText('5.5s')).toBeInTheDocument(); // avg time
  });

  it('should calculate completion rate correctly', () => {
    const mockSummary = {
      total_tasks: 10,
      completed_tasks: 7,
      failed_tasks: 2,
      agents_deployed: 25,
      total_cost_usd: 0,
      avg_execution_time_seconds: 0,
    };

    vi.mocked(useResearchSummary).mockReturnValue({
      summary: mockSummary,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<ResearchSummary />);

    // 7/10 = 70%
    expect(screen.getByText('70.0%')).toBeInTheDocument();
  });

  it('should display error state on API failure', () => {
    const mockRefetch = vi.fn();

    vi.mocked(useResearchSummary).mockReturnValue({
      summary: null,
      loading: false,
      error: 'Network error',
      refetch: mockRefetch,
    });

    render(<ResearchSummary />);

    expect(screen.getByText(/Network error/)).toBeInTheDocument();

    const retryButton = screen.getByText('Retry');
    expect(retryButton).toBeInTheDocument();

    fireEvent.click(retryButton);
    expect(mockRefetch).toHaveBeenCalledTimes(1);
  });

  it('should display empty state when no tasks exist', () => {
    const mockSummary = {
      total_tasks: 0,
      completed_tasks: 0,
      failed_tasks: 0,
      agents_deployed: 0,
      total_cost_usd: 0,
      avg_execution_time_seconds: 0,
    };

    vi.mocked(useResearchSummary).mockReturnValue({
      summary: mockSummary,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<ResearchSummary />);

    expect(screen.getByText(/No research tasks have been launched yet/)).toBeInTheDocument();
  });

  it('should display progress bar visualization', () => {
    const mockSummary = {
      total_tasks: 10,
      completed_tasks: 6,
      failed_tasks: 2,
      agents_deployed: 20,
      total_cost_usd: 0,
      avg_execution_time_seconds: 0,
    };

    vi.mocked(useResearchSummary).mockReturnValue({
      summary: mockSummary,
      loading: false,
      error: null,
      refetch: vi.fn(),
    });

    render(<ResearchSummary />);

    const progressSection = screen.getByText('Task Completion Progress');
    expect(progressSection).toBeInTheDocument();
  });
});
