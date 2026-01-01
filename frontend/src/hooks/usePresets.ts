/**
 * usePresets - React hook for managing query presets
 * 
 * Provides preset management functionality:
 * - List all presets
 * - Save current query as preset
 * - Load preset into query state
 * - Delete presets
 */

import { useCallback, useEffect, useState } from 'react';
import { ComposedQuery, QueryPreset } from '../types/query';
import {
  CreatePresetRequest,
  createPreset,
  deletePreset,
  listPresets,
} from '../services/presetApi';
import { showSuccessToast, showErrorToast } from '../utils/toast';

export interface UsePresetsReturn {
  /** List of available presets */
  presets: QueryPreset[];
  /** Whether presets are being loaded */
  loading: boolean;
  /** Error message if any */
  error: string | null;
  /** Reload the presets list */
  refresh: () => Promise<void>;
  /** Save current query as a new preset */
  savePreset: (data: CreatePresetRequest) => Promise<QueryPreset | null>;
  /** Load a preset's query */
  loadPreset: (preset: QueryPreset) => void;
  /** Delete a preset */
  removePreset: (id: string) => Promise<void>;
}

export interface UsePresetsOptions {
  /** Callback when a preset is loaded */
  onLoad?: (query: ComposedQuery) => void;
  /** Auto-fetch presets on mount */
  autoFetch?: boolean;
}

export function usePresets(options: UsePresetsOptions = {}): UsePresetsReturn {
  const { onLoad, autoFetch = true } = options;
  
  const [presets, setPresets] = useState<QueryPreset[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Fetch presets from API
  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await listPresets();
      setPresets(response.presets);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to load presets';
      setError(message);
      showErrorToast(message);
    } finally {
      setLoading(false);
    }
  }, []);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch) {
      refresh();
    }
  }, [autoFetch, refresh]);

  // Save a new preset
  const savePreset = useCallback(
    async (data: CreatePresetRequest): Promise<QueryPreset | null> => {
      try {
        const preset = await createPreset(data);
        
        // Add to local state
        setPresets((prev) => [...prev, preset]);
        
        showSuccessToast(`Preset "${data.name}" saved successfully`);
        return preset;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to save preset';
        showErrorToast(message);
        return null;
      }
    },
    []
  );

  // Load a preset
  const loadPreset = useCallback(
    (preset: QueryPreset) => {
      if (onLoad) {
        onLoad(preset.query);
      }
      showSuccessToast(`Loaded preset "${preset.name}"`);
    },
    [onLoad]
  );

  // Delete a preset
  const removePreset = useCallback(
    async (id: string) => {
      try {
        await deletePreset(id);
        
        // Remove from local state
        setPresets((prev) => prev.filter((p) => p.id !== id));
        
        showSuccessToast('Preset deleted');
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to delete preset';
        showErrorToast(message);
      }
    },
    []
  );

  return {
    presets,
    loading,
    error,
    refresh,
    savePreset,
    loadPreset,
    removePreset,
  };
}
