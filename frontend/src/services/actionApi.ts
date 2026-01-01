/**
 * Action API Client for VISLZR Affordances
 *
 * Handles execution of affordance actions via the backend API.
 */

import api from './api';
import type { Affordance } from '../types/query';

/**
 * Response from executing an affordance action
 */
export interface ExecuteActionResponse {
  /** Type of result */
  result_type: 'navigate' | 'created' | 'triggered' | 'data';
  /** Human-readable message about what happened */
  message: string;
  /** Navigation query (if result_type is 'navigate') */
  query?: Record<string, unknown>;
  /** Created entity data (if result_type is 'created') */
  data?: unknown;
}

/**
 * Execute an affordance action via the backend API
 *
 * @param affordance - The affordance to execute
 * @returns Promise resolving to the action execution result
 */
export async function executeAffordance(
  affordance: Affordance
): Promise<ExecuteActionResponse> {
  const response = await api.post<ExecuteActionResponse>(
    '/api/v1/graph/actions',
    {
      action: affordance.action,
      target: affordance.target,
      parameters: affordance.parameters || {},
    }
  );

  return response.data;
}
