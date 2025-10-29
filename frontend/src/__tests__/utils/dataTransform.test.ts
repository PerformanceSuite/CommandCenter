import { describe, it, expect } from 'vitest';
import { transformTechnologyData, normalizeApiResponse } from '../../utils/dataTransform';

describe('dataTransform', () => {
  it('transforms data correctly', () => {
    const input = {
      id: 1,
      title: 'python',
      description: 'A programming language',
      domain: 'backend',
      status: 'adopt',
      created_at: '2025-10-29T12:00:00Z',
      updated_at: '2025-10-29T14:00:00Z',
    };

    const result = transformTechnologyData(input);

    // Title should be capitalized
    expect(result.title).toBe('Python');

    // Dates should be converted to Date objects
    expect(result.createdAt).toBeInstanceOf(Date);
    expect(result.updatedAt).toBeInstanceOf(Date);

    // Other fields should be preserved
    expect(result.id).toBe(1);
    expect(result.description).toBe('A programming language');
    expect(result.domain).toBe('backend');
    expect(result.status).toBe('adopt');
  });

  it('normalizes API responses', () => {
    const apiResponse = {
      data: [
        { id: 1, name: 'Item 1' },
        { id: 2, name: 'Item 2' },
      ],
      meta: {
        total: 2,
        page: 1,
        per_page: 10,
      },
    };

    const normalized = normalizeApiResponse(apiResponse);

    expect(normalized.items).toHaveLength(2);
    expect(normalized.total).toBe(2);
    expect(normalized.page).toBe(1);
    expect(normalized.perPage).toBe(10);
  });
});

describe('normalizeApiResponse edge cases', () => {
  it('handles missing meta data', () => {
    const apiResponse = {
      data: [{ id: 1 }, { id: 2 }, { id: 3 }],
    };

    const normalized = normalizeApiResponse(apiResponse);

    // Should infer from data length
    expect(normalized.items).toHaveLength(3);
    expect(normalized.total).toBe(3);
    expect(normalized.page).toBe(1);
    expect(normalized.perPage).toBe(3);
  });

  it('handles empty data', () => {
    const apiResponse = {
      data: [],
      meta: {
        total: 0,
      },
    };

    const normalized = normalizeApiResponse(apiResponse);

    expect(normalized.items).toHaveLength(0);
    expect(normalized.total).toBe(0);
  });
});
