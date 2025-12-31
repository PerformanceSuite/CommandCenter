/**
 * Query Layer Types for VISLZR Composable Surface
 *
 * These types define the structured query interface for the composable
 * operating surface. Queries can come from URL params, structured navigation,
 * or saved recipes.
 */

import { EntityType, EdgeType } from './graph';

// ============================================================================
// Entity Selection
// ============================================================================

export type ScopeType = 'ecosystem' | 'project' | 'service' | 'file' | 'symbol';

export interface EntitySelector {
  /** Entity type to select */
  type: EntityType;
  /** Specific entity ID (if targeting one entity) */
  id?: number;
  /** Project scope */
  projectId?: number;
  /** Additional constraints */
  constraints?: Record<string, unknown>;
}

// ============================================================================
// Filters
// ============================================================================

export type FilterOperator = 'eq' | 'neq' | 'in' | 'contains' | 'gt' | 'lt' | 'between';

export interface Filter {
  /** Field to filter on */
  field: string;
  /** Filter operator */
  operator: FilterOperator;
  /** Filter value(s) */
  value: unknown;
}

// ============================================================================
// Relationships
// ============================================================================

export interface RelationshipSpec {
  /** Relationship type to include */
  type: EdgeType;
  /** Direction: from selected entity, to it, or both */
  direction: 'outbound' | 'inbound' | 'both';
  /** Traversal depth (default 1) */
  depth?: number;
}

// ============================================================================
// Presentation Hints
// ============================================================================

export type LayoutType = 'graph' | 'list' | 'detail' | 'dashboard' | 'auto';
export type SortOrder = 'asc' | 'desc';

export interface PresentationHint {
  /** Preferred layout (auto = let composition engine decide) */
  layout: LayoutType;
  /** Graph layout direction (if layout is graph) */
  graphDirection?: 'TB' | 'LR' | 'BT' | 'RL';
  /** Sort field */
  sortBy?: string;
  /** Sort order */
  sortOrder?: SortOrder;
  /** Group by field */
  groupBy?: string;
  /** Show minimap (for graph) */
  showMinimap?: boolean;
  /** Compact mode */
  compact?: boolean;
}

// ============================================================================
// Time Range
// ============================================================================

export interface TimeRange {
  /** Start timestamp (ISO string or relative like '-7d') */
  from?: string;
  /** End timestamp (ISO string or 'now') */
  to?: string;
}

// ============================================================================
// Composed Query
// ============================================================================

export interface ComposedQuery {
  /** What entities to fetch */
  entities: EntitySelector[];
  /** How to filter them */
  filters: Filter[];
  /** What relationships to include */
  relationships: RelationshipSpec[];
  /** How to present them */
  presentation: PresentationHint;
  /** Temporal scope */
  timeRange?: TimeRange;
  /** Pagination */
  limit?: number;
  offset?: number;
}

// ============================================================================
// Query Presets (Saved Recipes)
// ============================================================================

export interface QueryPreset {
  id: string;
  name: string;
  description?: string;
  query: ComposedQuery;
  icon?: string;
}

// ============================================================================
// Affordances (Agent Actions)
// ============================================================================

export type AffordanceAction =
  | 'drill_down'
  | 'zoom_out'
  | 'filter'
  | 'trigger_audit'
  | 'create_task'
  | 'open_in_editor'
  | 'view_dependencies'
  | 'view_dependents'
  | 'search_related';

export interface Affordance {
  /** Action type */
  action: AffordanceAction;
  /** Target entity reference */
  target: {
    type: EntityType;
    id: number;
  };
  /** Human-readable description */
  description: string;
  /** Parameters for the action */
  parameters?: Record<string, unknown>;
}

// ============================================================================
// Query Result
// ============================================================================

export interface QueryResult {
  /** The queried entities as graph nodes */
  nodes: import('./graph').GraphNode[];
  /** Relationships as edges */
  edges: import('./graph').GraphEdge[];
  /** What the agent/user can do next */
  affordances: Affordance[];
  /** Natural language summary */
  summary: string;
  /** If clarification needed */
  clarifications?: ClarificationRequest[];
  /** Total count (for pagination) */
  total: number;
  /** Resolved query (after defaults/normalization) */
  resolvedQuery: ComposedQuery;
}

export interface ClarificationRequest {
  /** Field needing clarification */
  field: string;
  /** Question to ask */
  question: string;
  /** Suggested options */
  options?: string[];
}

// ============================================================================
// Default Query
// ============================================================================

export const DEFAULT_PRESENTATION: PresentationHint = {
  layout: 'auto',
  graphDirection: 'TB',
  sortOrder: 'desc',
  showMinimap: true,
  compact: false,
};

export const EMPTY_QUERY: ComposedQuery = {
  entities: [],
  filters: [],
  relationships: [],
  presentation: DEFAULT_PRESENTATION,
};
