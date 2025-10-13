import type { AxiosError } from 'axios';

/**
 * FastAPI error response structure
 */
export interface ApiErrorResponse {
  detail?: string | ValidationError[];
  message?: string;
}

/**
 * FastAPI validation error structure
 */
export interface ValidationError {
  loc: (string | number)[];
  msg: string;
  type: string;
}

/**
 * Extended Axios error with typed response data
 */
export type ApiError = AxiosError<ApiErrorResponse>;

/**
 * Type guard to check if error is an API error
 */
export function isApiError(error: unknown): error is ApiError {
  return (
    error !== null &&
    typeof error === 'object' &&
    'response' in error &&
    'isAxiosError' in error
  );
}

/**
 * Extract error message from various error types
 */
export function extractErrorMessage(error: unknown): string {
  if (isApiError(error)) {
    const data = error.response?.data;

    // Handle FastAPI detail field
    if (data?.detail) {
      if (typeof data.detail === 'string') {
        return data.detail;
      }
      if (Array.isArray(data.detail)) {
        return data.detail.map(err => err.msg).join(', ');
      }
    }

    // Handle generic message field
    if (data?.message) {
      return data.message;
    }

    // Fall back to status text
    if (error.response?.statusText) {
      return `${error.response.status}: ${error.response.statusText}`;
    }
  }

  // Handle standard errors
  if (error instanceof Error) {
    return error.message;
  }

  // Handle string errors
  if (typeof error === 'string') {
    return error;
  }

  return 'An unexpected error occurred';
}