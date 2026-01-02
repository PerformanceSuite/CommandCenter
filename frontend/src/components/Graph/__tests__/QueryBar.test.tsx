/**
 * Tests for QueryBar component with composed query support.
 *
 * Phase 2, Task 2.5: Frontend QueryBar Component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryBar } from '../QueryBar';

// Mock the hooks
vi.mock('../../../hooks/useQueryState', () => ({
  useQueryState: () => ({
    query: { entities: [], filters: [], relationships: [], presentation: { layout: 'auto' } },
    setQuery: vi.fn(),
    clearQuery: vi.fn(),
    hasQuery: false,
  }),
}));

vi.mock('../../../hooks/usePresets', () => ({
  usePresets: () => ({
    presets: [],
    loading: false,
    savePreset: vi.fn(),
    loadPreset: vi.fn(),
    removePreset: vi.fn(),
  }),
}));

// Mock the queryApi
vi.mock('../../../services/queryApi', () => ({
  queryApi: {
    parseAndExecute: vi.fn().mockResolvedValue({
      entities: [],
      relationships: [],
      total: 0,
      metadata: { execution_time_ms: 10 },
    }),
    executeQuery: vi.fn().mockResolvedValue({
      entities: [],
      relationships: [],
      total: 0,
      metadata: { execution_time_ms: 10 },
    }),
    createEntityQuery: vi.fn().mockReturnValue({
      entities: [{ type: 'symbol' }],
    }),
    createSearchQuery: vi.fn().mockReturnValue({
      entities: [{ type: 'any' }],
      filters: [{ field: 'name', operator: 'contains', value: 'test' }],
    }),
  },
}));

describe('QueryBar', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('renders search input', () => {
    render(<QueryBar />);

    const searchInput = screen.getByPlaceholderText(/search symbols/i);
    expect(searchInput).toBeInTheDocument();
  });

  it('renders presets button', () => {
    render(<QueryBar />);

    const presetsButton = screen.getByText('Presets');
    expect(presetsButton).toBeInTheDocument();
  });

  it('renders save button', () => {
    render(<QueryBar />);

    const saveButton = screen.getByText('Save');
    expect(saveButton).toBeInTheDocument();
  });

  it('allows typing in search input', async () => {
    const user = userEvent.setup();
    render(<QueryBar />);

    const searchInput = screen.getByPlaceholderText(/search symbols/i);
    await user.type(searchInput, 'test query');

    expect(searchInput).toHaveValue('test query');
  });

  it('calls onQueryResult when search is submitted', async () => {
    const mockOnQueryResult = vi.fn();
    const user = userEvent.setup();

    render(<QueryBar onQueryResult={mockOnQueryResult} />);

    const searchInput = screen.getByPlaceholderText(/search symbols/i);
    await user.type(searchInput, 'test search');
    await user.keyboard('{Enter}');

    await waitFor(() => {
      expect(mockOnQueryResult).toHaveBeenCalled();
    });
  });

  it('accepts custom placeholder', () => {
    render(<QueryBar placeholder="Custom placeholder text" />);

    const searchInput = screen.getByPlaceholderText('Custom placeholder text');
    expect(searchInput).toBeInTheDocument();
  });

  it('accepts projectId prop', async () => {
    const { queryApi } = await import('../../../services/queryApi');
    render(<QueryBar projectId={123} />);

    // The projectId is used for scoping queries
    expect(screen.getByPlaceholderText(/search symbols/i)).toBeInTheDocument();
  });

  it('shows presets dropdown when clicked', async () => {
    const user = userEvent.setup();
    render(<QueryBar />);

    const presetsButton = screen.getByText('Presets');
    await user.click(presetsButton);

    // Should show "No saved presets" since presets array is empty
    expect(screen.getByText('No saved presets')).toBeInTheDocument();
  });
});

describe('QueryBar search behavior', () => {
  it('does not submit empty search', async () => {
    const mockOnQueryResult = vi.fn();
    const user = userEvent.setup();

    render(<QueryBar onQueryResult={mockOnQueryResult} />);

    const searchInput = screen.getByPlaceholderText(/search symbols/i);
    await user.click(searchInput);
    await user.keyboard('{Enter}');

    expect(mockOnQueryResult).not.toHaveBeenCalled();
  });

  it('trims whitespace from search', async () => {
    const mockOnQueryResult = vi.fn();
    const user = userEvent.setup();

    render(<QueryBar onQueryResult={mockOnQueryResult} />);

    const searchInput = screen.getByPlaceholderText(/search symbols/i);
    await user.type(searchInput, '   ');
    await user.keyboard('{Enter}');

    // Whitespace-only search should not trigger
    expect(mockOnQueryResult).not.toHaveBeenCalled();
  });
});
