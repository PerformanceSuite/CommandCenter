/**
 * Tests for ProgressBar component
 */
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProgressBar } from '../../components/common/ProgressBar';

describe('ProgressBar', () => {
  it('should render with basic progress value', () => {
    render(<ProgressBar value={50} />);

    const progressBar = screen.getByText('50%');
    expect(progressBar).toBeTruthy();
  });

  it('should render with label', () => {
    render(<ProgressBar value={30} label="Building containers..." />);

    expect(screen.getByText('Building containers...')).toBeTruthy();
    expect(screen.getByText('30%')).toBeTruthy();
  });

  it('should clamp values below 0 to 0', () => {
    render(<ProgressBar value={-10} />);

    expect(screen.getByText('0%')).toBeTruthy();
  });

  it('should clamp values above 100 to 100', () => {
    render(<ProgressBar value={150} />);

    expect(screen.getByText('100%')).toBeTruthy();
  });

  it('should apply running status color (blue)', () => {
    const { container } = render(<ProgressBar value={50} status="running" />);

    const progressFill = container.querySelector('.bg-blue-500');
    expect(progressFill).toBeTruthy();
  });

  it('should apply success status color (green)', () => {
    const { container } = render(<ProgressBar value={100} status="success" />);

    const progressFill = container.querySelector('.bg-green-500');
    expect(progressFill).toBeTruthy();
  });

  it('should apply error status color (red)', () => {
    const { container } = render(<ProgressBar value={50} status="error" />);

    const progressFill = container.querySelector('.bg-red-500');
    expect(progressFill).toBeTruthy();
  });

  it('should default to running status when not specified', () => {
    const { container } = render(<ProgressBar value={50} />);

    const progressFill = container.querySelector('.bg-blue-500');
    expect(progressFill).toBeTruthy();
  });

  it('should render progress bar with correct width', () => {
    const { container } = render(<ProgressBar value={75} />);

    const progressFill = container.querySelector('.bg-blue-500');
    expect(progressFill).toBeTruthy();

    // Check style attribute for width
    const style = progressFill?.getAttribute('style');
    expect(style).toContain('width: 75%');
  });

  it('should render all elements: bar, label, and percentage', () => {
    const { container } = render(
      <ProgressBar value={60} label="Processing..." status="running" />
    );

    // Progress bar container
    expect(container.querySelector('.bg-gray-700')).toBeTruthy();

    // Progress fill
    expect(container.querySelector('.bg-blue-500')).toBeTruthy();

    // Label
    expect(screen.getByText('Processing...')).toBeTruthy();

    // Percentage
    expect(screen.getByText('60%')).toBeTruthy();
  });

  it('should handle 0% progress', () => {
    const { container } = render(<ProgressBar value={0} label="Starting..." />);

    expect(screen.getByText('0%')).toBeTruthy();
    expect(screen.getByText('Starting...')).toBeTruthy();

    const progressFill = container.querySelector('.bg-blue-500');
    const style = progressFill?.getAttribute('style');
    expect(style).toContain('width: 0%');
  });

  it('should handle 100% progress', () => {
    const { container } = render(
      <ProgressBar value={100} label="Complete!" status="success" />
    );

    expect(screen.getByText('100%')).toBeTruthy();
    expect(screen.getByText('Complete!')).toBeTruthy();

    const progressFill = container.querySelector('.bg-green-500');
    const style = progressFill?.getAttribute('style');
    expect(style).toContain('width: 100%');
  });

  it('should render without label when not provided', () => {
    const { container } = render(<ProgressBar value={45} />);

    expect(screen.getByText('45%')).toBeTruthy();

    // Should not have label text
    expect(container.querySelector('.text-sm.text-gray-300')).toBeFalsy();
  });
});
