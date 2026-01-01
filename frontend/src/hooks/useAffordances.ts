/**
 * useAffordances - React hook for executing affordance actions
 *
 * Provides a function to execute affordances with automatic handling of:
 * - Navigation actions (updates URL search params)
 * - Created/triggered actions (logs messages)
 * - Data actions (returns data)
 * - Error handling
 */

import { useCallback } from 'react';
import { useSearchParams } from 'react-router-dom';
import type { Affordance } from '../types/query';
import { executeAffordance, ExecuteActionResponse } from '../services/actionApi';

export interface UseAffordancesReturn {
  /** Execute an affordance action */
  execute: (affordance: Affordance) => Promise<ExecuteActionResponse>;
  /** Check if an action is currently executing */
  isExecuting: boolean;
}

/**
 * Hook for executing affordance actions
 *
 * @returns Object with execute function and loading state
 */
export function useAffordances(): UseAffordancesReturn {
  const [, setSearchParams] = useSearchParams();

  const execute = useCallback(
    async (affordance: Affordance): Promise<ExecuteActionResponse> => {
      try {
        // Execute the affordance via API
        const result = await executeAffordance(affordance);

        // Handle different result types
        switch (result.result_type) {
          case 'navigate': {
            // Update URL search params with the new query
            if (result.query) {
              const newParams = new URLSearchParams();
              
              // Merge query parameters into URL
              Object.entries(result.query).forEach(([key, value]) => {
                if (value !== null && value !== undefined) {
                  // Convert arrays and objects to JSON strings
                  const stringValue = 
                    typeof value === 'object' 
                      ? JSON.stringify(value) 
                      : String(value);
                  newParams.set(key, stringValue);
                }
              });
              
              setSearchParams(newParams);
            }
            break;
          }

          case 'created':
          case 'triggered': {
            // Log the message (toast can be added later)
            console.log(`[Affordance] ${result.result_type}: ${result.message}`);
            break;
          }

          case 'data': {
            // Data is returned in the result, caller can use it
            console.log(`[Affordance] Data result: ${result.message}`);
            break;
          }

          default: {
            console.warn(`[Affordance] Unknown result type: ${result.result_type}`);
          }
        }

        return result;
      } catch (error) {
        console.error('[Affordance] Execution failed:', error);
        throw error;
      }
    },
    [setSearchParams]
  );

  // For now, we don't track execution state
  // This can be enhanced with useState if needed
  const isExecuting = false;

  return {
    execute,
    isExecuting,
  };
}
