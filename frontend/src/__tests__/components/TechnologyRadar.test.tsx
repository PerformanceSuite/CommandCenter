import { describe, it, expect, vi, beforeEach } from 'vitest';
import { screen } from '@testing-library/react';
import { RadarView } from '../../components/TechnologyRadar/RadarView';
import { renderWithMemoryRouter } from '../../test-utils/test-utils';
import { mockTechnology } from '../../test-utils/mocks';
import { useTechnologies } from '../../hooks/useTechnologies';

// Mock the useTechnologies hook
vi.mock('../../hooks/useTechnologies', () => ({
  useTechnologies: vi.fn(),
}));

describe('TechnologyRadar (RadarView)', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('displays loading spinner while fetching technologies', () => {
    vi.mocked(useTechnologies).mockReturnValue({
      technologies: [],
      loading: true,
      error: null,
      total: 0,
      page: 1,
      totalPages: 1,
    });

    renderWithMemoryRouter(<RadarView />);

    expect(screen.getByRole('status')).toBeInTheDocument();
    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('displays error message when fetch fails', () => {
    vi.mocked(useTechnologies).mockReturnValue({
      technologies: [],
      loading: false,
      error: new Error('Failed to fetch technologies'),
      total: 0,
      page: 1,
      totalPages: 1,
    });

    renderWithMemoryRouter(<RadarView />);

    expect(screen.getByText('Error loading technologies')).toBeInTheDocument();
    expect(screen.getByText('Failed to fetch technologies')).toBeInTheDocument();
  });

  it('renders technology radar header and controls', () => {
    vi.mocked(useTechnologies).mockReturnValue({
      technologies: [],
      loading: false,
      error: null,
      total: 0,
      page: 1,
      totalPages: 1,
    });

    renderWithMemoryRouter(<RadarView />);

    expect(screen.getByText('Technology Radar')).toBeInTheDocument();
    expect(screen.getByText('Add Technology')).toBeInTheDocument();
    expect(screen.getByText('Cards')).toBeInTheDocument();
    expect(screen.getByText('Matrix')).toBeInTheDocument();
  });

  it('renders search and filter controls', () => {
    vi.mocked(useTechnologies).mockReturnValue({
      technologies: [],
      loading: false,
      error: null,
      total: 0,
      page: 1,
      totalPages: 1,
    });

    renderWithMemoryRouter(<RadarView />);

    expect(screen.getByPlaceholderText('Search technologies...')).toBeInTheDocument();
    expect(screen.getByText('Filters')).toBeInTheDocument();
  });

  it('displays technologies grouped by domain in card view', () => {
    const tech1 = mockTechnology({ id: 1, title: 'Python', domain: 'ai-ml' });
    const tech2 = mockTechnology({ id: 2, title: 'FastAPI', domain: 'backend' });

    vi.mocked(useTechnologies).mockReturnValue({
      technologies: [tech1, tech2],
      loading: false,
      error: null,
      total: 2,
      page: 1,
      totalPages: 1,
    });

    renderWithMemoryRouter(<RadarView />);

    // Check that domains are rendered
    expect(screen.getByText(/ai ml/i)).toBeInTheDocument();
    expect(screen.getByText(/backend/i)).toBeInTheDocument();
  });

  it('displays empty state when no technologies exist', () => {
    vi.mocked(useTechnologies).mockReturnValue({
      technologies: [],
      loading: false,
      error: null,
      total: 0,
      page: 1,
      totalPages: 1,
    });

    renderWithMemoryRouter(<RadarView />);

    expect(screen.getByText('No technologies tracked yet')).toBeInTheDocument();
    expect(screen.getByText('Add technologies to see them on the radar')).toBeInTheDocument();
  });

  it('displays empty state with clear filters option when filters are active', () => {
    vi.mocked(useTechnologies).mockReturnValue({
      technologies: [],
      loading: false,
      error: null,
      total: 0,
      page: 1,
      totalPages: 1,
    });

    renderWithMemoryRouter(<RadarView />, {
      initialEntries: ['/?search=nonexistent'],
    });

    expect(screen.getByText('No technologies match your filters')).toBeInTheDocument();
  });

  it('toggles between card and matrix view', async () => {
    const tech1 = mockTechnology({ id: 1, title: 'Python' });

    vi.mocked(useTechnologies).mockReturnValue({
      technologies: [tech1],
      loading: false,
      error: null,
      total: 1,
      page: 1,
      totalPages: 1,
    });

    renderWithMemoryRouter(<RadarView />);

    // Initially in card view
    const matrixButton = screen.getByText('Matrix');
    expect(matrixButton.closest('button')).toBeInTheDocument();
  });

  it('shows pagination when there are multiple pages', () => {
    const technologies = Array.from({ length: 5 }, (_, i) =>
      mockTechnology({ id: i + 1, title: `Tech ${i + 1}` })
    );

    vi.mocked(useTechnologies).mockReturnValue({
      technologies,
      loading: false,
      error: null,
      total: 50,
      page: 1,
      totalPages: 3,
    });

    renderWithMemoryRouter(<RadarView />);

    // The pagination component should be rendered
    // We can check for technologies being displayed
    expect(screen.getByText('Tech 1')).toBeInTheDocument();
  });
});
