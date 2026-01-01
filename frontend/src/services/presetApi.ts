/**
 * Preset API Service
 * 
 * Provides CRUD operations for query presets (saved recipes).
 * Presets allow users to save and load composed queries.
 */

import { ComposedQuery, QueryPreset } from '../types/query';
import { api } from './api';

export interface CreatePresetRequest {
  name: string;
  description?: string;
  query: ComposedQuery;
  icon?: string;
}

export interface UpdatePresetRequest {
  name?: string;
  description?: string;
  query?: ComposedQuery;
  icon?: string;
}

export interface ListPresetsResponse {
  presets: QueryPreset[];
  total: number;
}

/**
 * List all query presets for the current user/project
 */
export async function listPresets(): Promise<ListPresetsResponse> {
  const response = await api.get<ListPresetsResponse>('/api/v1/graph/presets');
  return response.data;
}

/**
 * Get a specific preset by ID
 */
export async function getPreset(id: string): Promise<QueryPreset> {
  const response = await api.get<QueryPreset>(`/api/v1/graph/presets/${id}`);
  return response.data;
}

/**
 * Create a new query preset
 */
export async function createPreset(data: CreatePresetRequest): Promise<QueryPreset> {
  const response = await api.post<QueryPreset>('/api/v1/graph/presets', data);
  return response.data;
}

/**
 * Update an existing preset
 */
export async function updatePreset(
  id: string,
  data: UpdatePresetRequest
): Promise<QueryPreset> {
  const response = await api.put<QueryPreset>(`/api/v1/graph/presets/${id}`, data);
  return response.data;
}

/**
 * Delete a preset
 */
export async function deletePreset(id: string): Promise<void> {
  await api.delete(`/api/v1/graph/presets/${id}`);
}
