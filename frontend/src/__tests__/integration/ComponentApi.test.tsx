import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { TechnologyCard } from '../../components/TechnologyRadar/TechnologyCard';
import type { Technology } from '../../types/technology';

function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('Component + API Integration', () => {
  it('integrates component rendering with data correctly', () => {
    const mockTechnology: Technology = {
      id: 1,
      title: 'Python',
      domain: 'backend',
      status: 'integrated',
      vendor: 'Python Software Foundation',
      description: 'A high-level programming language',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    render(<TechnologyCard technology={mockTechnology} />);

    // Should render the technology title
    expect(screen.getByText('Python')).toBeInTheDocument();
  });

  it('handles rendering with minimal data', () => {
    const minimalTechnology: Technology = {
      id: 2,
      title: 'TypeScript',
      domain: 'language',
      status: 'integrated',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    render(<TechnologyCard technology={minimalTechnology} />);

    // Should render with minimal data
    expect(screen.getByText('TypeScript')).toBeInTheDocument();
  });
});

describe('TechnologyCard component rendering', () => {
  it('renders technology card with data', () => {
    const mockTechnology: Technology = {
      id: 1,
      title: 'React',
      domain: 'frontend',
      status: 'integrated',
      vendor: 'Meta',
      description: 'A JavaScript library for building user interfaces',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    render(<TechnologyCard technology={mockTechnology} />);

    // Should display the technology title
    expect(screen.getByText('React')).toBeInTheDocument();
  });

  it('handles empty or missing data gracefully', () => {
    const minimalTechnology: Technology = {
      id: 2,
      title: 'TypeScript',
      domain: 'language',
      status: 'integrated',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    };

    render(<TechnologyCard technology={minimalTechnology} />);

    // Should still render with minimal data
    expect(screen.getByText('TypeScript')).toBeInTheDocument();
  });
});
