/**
 * QueryBar - Query control bar with search and preset management
 *
 * Provides UI for:
 * - Executing composed queries via search input
 * - Loading saved presets via dropdown
 * - Saving current query as preset
 * - Clearing current query
 *
 * Phase 2: Enhanced with composed query execution support
 */

import { useState, useCallback } from 'react';
import { Save, ChevronDown, Trash2, BookmarkPlus, Search, Loader2 } from 'lucide-react';
import { useQueryState } from '../../hooks/useQueryState';
import { usePresets } from '../../hooks/usePresets';
import { QueryPreset } from '../../types/query';
import { queryApi, QueryResult } from '../../services/queryApi';

interface QueryBarProps {
  /** Callback when query results are received */
  onQueryResult?: (result: QueryResult) => void;
  /** Current project ID for scoping queries */
  projectId?: number;
  /** Placeholder text for search input */
  placeholder?: string;
}

export function QueryBar({ onQueryResult, projectId: _projectId, placeholder }: QueryBarProps) {
  // Note: projectId is kept for future scoped query support
  const { query, setQuery, clearQuery, hasQuery } = useQueryState();
  const { presets, loading, savePreset, loadPreset, removePreset } = usePresets({
    onLoad: (loadedQuery) => {
      setQuery(loadedQuery);
    },
  });

  const [showPresetMenu, setShowPresetMenu] = useState(false);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  const [presetName, setPresetName] = useState('');
  const [presetDescription, setPresetDescription] = useState('');
  const [isSaving, setIsSaving] = useState(false);

  // Search state
  const [searchText, setSearchText] = useState('');
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState<string | null>(null);

  // Execute search query
  const handleSearch = useCallback(async (e?: React.FormEvent) => {
    e?.preventDefault();

    if (!searchText.trim()) {
      return;
    }

    setIsSearching(true);
    setSearchError(null);

    try {
      // Use natural language parsing endpoint
      const result = await queryApi.parseAndExecute(searchText);
      onQueryResult?.(result);
    } catch (error) {
      console.error('Search error:', error);
      setSearchError(error instanceof Error ? error.message : 'Search failed');
    } finally {
      setIsSearching(false);
    }
  }, [searchText, onQueryResult]);

  // Handle save preset
  const handleSavePreset = async () => {
    if (!presetName.trim()) {
      return;
    }

    setIsSaving(true);
    const result = await savePreset({
      name: presetName,
      description: presetDescription || undefined,
      query,
    });

    if (result) {
      setShowSaveDialog(false);
      setPresetName('');
      setPresetDescription('');
    }
    setIsSaving(false);
  };

  // Handle load preset
  const handleLoadPreset = (preset: QueryPreset) => {
    loadPreset(preset);
    setShowPresetMenu(false);
  };

  // Handle delete preset
  const handleDeletePreset = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (confirm('Are you sure you want to delete this preset?')) {
      await removePreset(id);
    }
  };

  return (
    <div className="bg-white border-b border-gray-200 px-4 py-3">
      <div className="flex items-center justify-between gap-4">
        {/* Left side: Search input */}
        <form onSubmit={handleSearch} className="flex-1 max-w-xl">
          <div className="relative">
            <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
              {isSearching ? (
                <Loader2 className="w-4 h-4 text-gray-400 animate-spin" />
              ) : (
                <Search className="w-4 h-4 text-gray-400" />
              )}
            </div>
            <input
              type="text"
              value={searchText}
              onChange={(e) => setSearchText(e.target.value)}
              placeholder={placeholder || 'Search symbols, files, services... (e.g., "functions with auth")'}
              className="w-full pl-10 pr-4 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-100"
              disabled={isSearching}
            />
            {searchError && (
              <div className="absolute inset-y-0 right-0 flex items-center pr-3">
                <span className="text-xs text-red-500" title={searchError}>Error</span>
              </div>
            )}
          </div>
        </form>

        {/* Query status */}
        <div className="flex items-center gap-2 text-sm text-gray-500">
          {hasQuery && (
            <span>
              {query.entities.length} {query.entities.length === 1 ? 'entity' : 'entities'}
              {query.filters.length > 0 && `, ${query.filters.length} ${query.filters.length === 1 ? 'filter' : 'filters'}`}
            </span>
          )}
        </div>

        {/* Right side: Controls */}
        <div className="flex items-center gap-2">
          {/* Preset dropdown */}
          <div className="relative">
            <button
              onClick={() => setShowPresetMenu(!showPresetMenu)}
              className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={loading}
            >
              <BookmarkPlus size={16} />
              Presets
              <ChevronDown size={14} />
            </button>

            {/* Preset menu */}
            {showPresetMenu && (
              <div className="absolute right-0 mt-2 w-64 bg-white border border-gray-200 rounded-md shadow-lg z-10">
                <div className="py-1 max-h-64 overflow-y-auto">
                  {loading ? (
                    <div className="px-4 py-2 text-sm text-gray-500">Loading...</div>
                  ) : presets.length === 0 ? (
                    <div className="px-4 py-2 text-sm text-gray-500">No saved presets</div>
                  ) : (
                    presets.map((preset) => (
                      <div
                        key={preset.id}
                        className="group flex items-center justify-between px-4 py-2 hover:bg-gray-50 cursor-pointer"
                        onClick={() => handleLoadPreset(preset)}
                      >
                        <div className="flex-1 min-w-0">
                          <div className="text-sm font-medium text-gray-900 truncate">
                            {preset.icon && <span className="mr-1">{preset.icon}</span>}
                            {preset.name}
                          </div>
                          {preset.description && (
                            <div className="text-xs text-gray-500 truncate">
                              {preset.description}
                            </div>
                          )}
                        </div>
                        <button
                          onClick={(e) => handleDeletePreset(preset.id, e)}
                          className="ml-2 p-1 text-gray-400 hover:text-red-600 opacity-0 group-hover:opacity-100 transition-opacity"
                          title="Delete preset"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    ))
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Save current query */}
          <button
            onClick={() => setShowSaveDialog(true)}
            disabled={!hasQuery}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-300 disabled:cursor-not-allowed"
          >
            <Save size={16} />
            Save
          </button>

          {/* Clear query */}
          {hasQuery && (
            <button
              onClick={clearQuery}
              className="px-3 py-1.5 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              Clear
            </button>
          )}
        </div>
      </div>

      {/* Save preset dialog */}
      {showSaveDialog && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div className="bg-white rounded-lg shadow-xl p-6 w-full max-w-md">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Save Query Preset</h3>

            <div className="space-y-4">
              <div>
                <label htmlFor="preset-name" className="block text-sm font-medium text-gray-700 mb-1">
                  Name *
                </label>
                <input
                  id="preset-name"
                  type="text"
                  value={presetName}
                  onChange={(e) => setPresetName(e.target.value)}
                  placeholder="e.g., Python Dependencies"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  autoFocus
                />
              </div>

              <div>
                <label htmlFor="preset-description" className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  id="preset-description"
                  value={presetDescription}
                  onChange={(e) => setPresetDescription(e.target.value)}
                  placeholder="Optional description..."
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>
            </div>

            <div className="flex justify-end gap-2 mt-6">
              <button
                onClick={() => {
                  setShowSaveDialog(false);
                  setPresetName('');
                  setPresetDescription('');
                }}
                className="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50"
                disabled={isSaving}
              >
                Cancel
              </button>
              <button
                onClick={handleSavePreset}
                disabled={!presetName.trim() || isSaving}
                className="px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-md hover:bg-blue-700 disabled:bg-gray-300 disabled:cursor-not-allowed"
              >
                {isSaving ? 'Saving...' : 'Save Preset'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Click outside to close menu */}
      {showPresetMenu && (
        <div
          className="fixed inset-0 z-0"
          onClick={() => setShowPresetMenu(false)}
        />
      )}
    </div>
  );
}
