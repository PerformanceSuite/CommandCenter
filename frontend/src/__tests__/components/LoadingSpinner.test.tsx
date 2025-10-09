import { describe, it, expect } from 'vitest';
import { render } from '../../tests/utils';
import { LoadingSpinner } from '../../components/common/LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with default size', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector('div[class*="animate-spin"]');

    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveClass('h-8', 'w-8');
  });

  it('renders with small size', () => {
    const { container } = render(<LoadingSpinner size="sm" />);
    const spinner = container.querySelector('div[class*="animate-spin"]');

    expect(spinner).toHaveClass('h-4', 'w-4');
  });

  it('renders with large size', () => {
    const { container } = render(<LoadingSpinner size="lg" />);
    const spinner = container.querySelector('div[class*="animate-spin"]');

    expect(spinner).toHaveClass('h-12', 'w-12');
  });

  it('applies custom className', () => {
    const { container } = render(<LoadingSpinner className="my-custom-class" />);
    const wrapper = container.firstChild;

    expect(wrapper).toHaveClass('my-custom-class');
  });

  it('has spinner animation class', () => {
    const { container } = render(<LoadingSpinner />);
    const spinner = container.querySelector('div[class*="animate-spin"]');

    expect(spinner).toHaveClass('animate-spin');
  });
});
