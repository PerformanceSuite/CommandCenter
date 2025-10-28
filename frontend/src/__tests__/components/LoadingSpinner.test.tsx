import { describe, it, expect } from 'vitest';
import { screen, render } from '@testing-library/react';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with default props', () => {
    render(<LoadingSpinner />);

    const status = screen.getByRole('status');
    expect(status).toBeInTheDocument();
    expect(status).toHaveAttribute('aria-live', 'polite');
    expect(status).toHaveAttribute('aria-busy', 'true');

    expect(screen.getByText('Loading...')).toBeInTheDocument();
  });

  it('renders with custom label', () => {
    render(<LoadingSpinner label="Please wait..." />);

    expect(screen.getByText('Please wait...')).toBeInTheDocument();
  });

  it('applies small size classes', () => {
    render(<LoadingSpinner size="sm" />);

    const status = screen.getByRole('status');
    const spinner = status.querySelector('div[aria-hidden="true"]');
    expect(spinner).toHaveClass('h-4', 'w-4', 'border-2');
  });

  it('applies medium size classes (default)', () => {
    render(<LoadingSpinner size="md" />);

    const status = screen.getByRole('status');
    const spinner = status.querySelector('div[aria-hidden="true"]');
    expect(spinner).toHaveClass('h-8', 'w-8', 'border-3');
  });

  it('applies large size classes', () => {
    render(<LoadingSpinner size="lg" />);

    const status = screen.getByRole('status');
    const spinner = status.querySelector('div[aria-hidden="true"]');
    expect(spinner).toHaveClass('h-12', 'w-12', 'border-4');
  });

  it('applies custom className', () => {
    render(<LoadingSpinner className="mt-20 custom-class" />);

    const status = screen.getByRole('status');
    expect(status).toHaveClass('mt-20', 'custom-class');
  });

  it('screen reader text is visually hidden but accessible', () => {
    render(<LoadingSpinner />);

    const srText = screen.getByText('Loading...');
    expect(srText).toHaveClass('sr-only');
  });
});
