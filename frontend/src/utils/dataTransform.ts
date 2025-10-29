/**
 * Data transformation utilities for normalizing API responses
 */

/**
 * Technology data from API
 */
interface TechnologyApiData {
  id: number;
  title: string;
  description?: string;
  domain?: string;
  status?: string;
  created_at: string;
  updated_at?: string;
}

/**
 * Transformed technology data for frontend
 */
interface TransformedTechnology {
  id: number;
  title: string;
  description?: string;
  domain?: string;
  status?: string;
  createdAt: Date;
  updatedAt?: Date;
}

/**
 * Transform technology data from API format to frontend format
 * @param data - Raw API data
 * @returns Transformed data with proper types
 */
export function transformTechnologyData(
  data: TechnologyApiData
): TransformedTechnology {
  return {
    id: data.id,
    title: capitalizeFirst(data.title),
    description: data.description,
    domain: data.domain,
    status: data.status,
    createdAt: new Date(data.created_at),
    updatedAt: data.updated_at ? new Date(data.updated_at) : undefined,
  };
}

/**
 * Capitalize first letter of a string
 * @param str - String to capitalize
 * @returns Capitalized string
 */
function capitalizeFirst(str: string): string {
  if (!str) return str;
  return str.charAt(0).toUpperCase() + str.slice(1);
}

/**
 * API response with pagination metadata
 */
interface ApiResponse<T> {
  data: T[];
  meta?: {
    total?: number;
    page?: number;
    per_page?: number;
  };
}

/**
 * Normalized response for frontend
 */
interface NormalizedResponse<T> {
  items: T[];
  total: number;
  page: number;
  perPage: number;
}

/**
 * Normalize API response with pagination metadata
 * @param response - Raw API response
 * @returns Normalized response with consistent structure
 */
export function normalizeApiResponse<T>(
  response: ApiResponse<T>
): NormalizedResponse<T> {
  return {
    items: response.data || [],
    total: response.meta?.total || response.data?.length || 0,
    page: response.meta?.page || 1,
    perPage: response.meta?.per_page || response.data?.length || 0,
  };
}

/**
 * Convert snake_case keys to camelCase
 * @param obj - Object with snake_case keys
 * @returns Object with camelCase keys
 */
export function snakeToCamel<T extends Record<string, unknown>>(obj: T): Record<string, unknown> {
  const result: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(obj)) {
    const camelKey = key.replace(/_([a-z])/g, (_, letter) =>
      letter.toUpperCase()
    );
    result[camelKey] = value;
  }

  return result;
}

/**
 * Filter out null and undefined values from object
 * @param obj - Object to clean
 * @returns Object without null/undefined values
 */
export function removeNullish<T extends Record<string, unknown>>(obj: T): Partial<T> {
  const result: Record<string, unknown> = {};

  for (const [key, value] of Object.entries(obj)) {
    if (value !== null && value !== undefined) {
      result[key] = value;
    }
  }

  return result as Partial<T>;
}
