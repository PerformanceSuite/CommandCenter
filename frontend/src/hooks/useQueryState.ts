/**
 * useQueryState - React hook for query-driven navigation
 *
 * Syncs ComposedQuery with URL search params, providing:
 * - Current query state from URL
 * - Functions to update query (merges into URL)
 * - Query execution via API
 */

import { useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { parseQueryFromParams, serializeQueryToParams } from '../lib/queryParser';
import {
  ComposedQuery,
  EntitySelector,
  Filter,
  PresentationHint,
} from '../types/query';

export interface UseQueryStateReturn {
  /** Current parsed query from URL */
  query: ComposedQuery;
  /** Update the entire query (replaces URL params) */
  setQuery: (query: ComposedQuery) => void;
  /** Merge partial query into current (updates URL params) */
  updateQuery: (partial: Partial<ComposedQuery>) => void;
  /** Add an entity selector */
  addEntity: (entity: EntitySelector) => void;
  /** Remove an entity selector by index */
  removeEntity: (index: number) => void;
  /** Add a filter */
  addFilter: (filter: Filter) => void;
  /** Remove a filter by field name */
  removeFilter: (field: string) => void;
  /** Update presentation hints */
  setPresentation: (hints: Partial<PresentationHint>) => void;
  /** Clear all query params */
  clearQuery: () => void;
  /** Check if query has any constraints */
  hasQuery: boolean;
}

export function useQueryState(): UseQueryStateReturn {
  const [searchParams, setSearchParams] = useSearchParams();

  // Parse current query from URL
  const query = useMemo(() => {
    return parseQueryFromParams(searchParams);
  }, [searchParams]);

  // Check if query has any constraints
  const hasQuery = useMemo(() => {
    return query.entities.length > 0 || query.filters.length > 0;
  }, [query]);

  // Set entire query
  const setQuery = useCallback(
    (newQuery: ComposedQuery) => {
      const params = serializeQueryToParams(newQuery);
      setSearchParams(params);
    },
    [setSearchParams]
  );

  // Merge partial query
  const updateQuery = useCallback(
    (partial: Partial<ComposedQuery>) => {
      const merged: ComposedQuery = {
        ...query,
        ...partial,
        presentation: {
          ...query.presentation,
          ...(partial.presentation || {}),
        },
      };
      setQuery(merged);
    },
    [query, setQuery]
  );

  // Entity helpers
  const addEntity = useCallback(
    (entity: EntitySelector) => {
      updateQuery({ entities: [...query.entities, entity] });
    },
    [query.entities, updateQuery]
  );

  const removeEntity = useCallback(
    (index: number) => {
      updateQuery({
        entities: query.entities.filter((_, i) => i !== index),
      });
    },
    [query.entities, updateQuery]
  );

  // Filter helpers
  const addFilter = useCallback(
    (filter: Filter) => {
      updateQuery({ filters: [...query.filters, filter] });
    },
    [query.filters, updateQuery]
  );

  const removeFilter = useCallback(
    (field: string) => {
      updateQuery({
        filters: query.filters.filter((f) => f.field !== field),
      });
    },
    [query.filters, updateQuery]
  );

  // Presentation helper
  const setPresentation = useCallback(
    (hints: Partial<PresentationHint>) => {
      updateQuery({
        presentation: { ...query.presentation, ...hints },
      });
    },
    [query.presentation, updateQuery]
  );

  // Clear query
  const clearQuery = useCallback(() => {
    setSearchParams(new URLSearchParams());
  }, [setSearchParams]);

  return {
    query,
    setQuery,
    updateQuery,
    addEntity,
    removeEntity,
    addFilter,
    removeFilter,
    setPresentation,
    clearQuery,
    hasQuery,
  };
}
