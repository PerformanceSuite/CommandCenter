import { describe, it, expect } from 'vitest';
import { formatDate, formatRelativeTime } from '../../utils/dateFormatting';

describe('dateFormatting', () => {
  it('formats dates correctly', () => {
    const date = new Date('2025-10-29T12:00:00Z');
    const formatted = formatDate(date);

    // Should format as "Oct 29, 2025" or similar
    expect(formatted).toMatch(/Oct 29, 2025/);
  });

  it('handles timezone conversions', () => {
    const date = new Date('2025-10-29T00:00:00Z');
    const formatted = formatDate(date, { timeZone: 'America/New_York' });

    // Should show previous day in EST (Oct 28)
    // EST is UTC-5, so midnight UTC is 7 PM previous day in EST
    expect(formatted).toMatch(/Oct 28, 2025/);
  });
});

describe('formatRelativeTime', () => {
  it('formats recent dates correctly', () => {
    const now = new Date();
    const oneMinuteAgo = new Date(now.getTime() - 60 * 1000);
    const oneHourAgo = new Date(now.getTime() - 60 * 60 * 1000);
    const oneDayAgo = new Date(now.getTime() - 24 * 60 * 60 * 1000);

    expect(formatRelativeTime(new Date(now.getTime() - 30 * 1000))).toBe('just now');
    expect(formatRelativeTime(oneMinuteAgo)).toBe('1 minute ago');
    expect(formatRelativeTime(oneHourAgo)).toBe('1 hour ago');
    expect(formatRelativeTime(oneDayAgo)).toBe('1 day ago');
  });
});
