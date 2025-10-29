/**
 * Date formatting utilities for the application
 */

interface FormatDateOptions {
  timeZone?: string;
  includeTime?: boolean;
}

/**
 * Format a date into a readable string
 * @param date - The date to format
 * @param options - Formatting options
 * @returns Formatted date string
 */
export function formatDate(date: Date, options: FormatDateOptions = {}): string {
  const { timeZone, includeTime = false } = options;

  const formatOptions: Intl.DateTimeFormatOptions = {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    ...(timeZone && { timeZone }),
    ...(includeTime && {
      hour: '2-digit',
      minute: '2-digit',
    }),
  };

  return new Intl.DateTimeFormat('en-US', formatOptions).format(date);
}

/**
 * Format a date as relative time (e.g., "2 hours ago")
 * @param date - The date to format
 * @returns Relative time string
 */
export function formatRelativeTime(date: Date): string {
  const now = new Date();
  const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);

  if (diffInSeconds < 60) {
    return 'just now';
  }

  const diffInMinutes = Math.floor(diffInSeconds / 60);
  if (diffInMinutes < 60) {
    return `${diffInMinutes} minute${diffInMinutes === 1 ? '' : 's'} ago`;
  }

  const diffInHours = Math.floor(diffInMinutes / 60);
  if (diffInHours < 24) {
    return `${diffInHours} hour${diffInHours === 1 ? '' : 's'} ago`;
  }

  const diffInDays = Math.floor(diffInHours / 24);
  if (diffInDays < 30) {
    return `${diffInDays} day${diffInDays === 1 ? '' : 's'} ago`;
  }

  const diffInMonths = Math.floor(diffInDays / 30);
  if (diffInMonths < 12) {
    return `${diffInMonths} month${diffInMonths === 1 ? '' : 's'} ago`;
  }

  const diffInYears = Math.floor(diffInMonths / 12);
  return `${diffInYears} year${diffInYears === 1 ? '' : 's'} ago`;
}

/**
 * Parse ISO date string to Date object
 * @param dateString - ISO date string
 * @returns Date object
 */
export function parseISODate(dateString: string): Date {
  return new Date(dateString);
}

/**
 * Format date for API requests (ISO 8601)
 * @param date - The date to format
 * @returns ISO 8601 formatted string
 */
export function formatForAPI(date: Date): string {
  return date.toISOString();
}
