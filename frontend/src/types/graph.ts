/**
 * Graph types for VISLZR visualization primitives
 *
 * These types mirror the backend graph schemas and provide
 * type-safe interfaces for the GraphCanvas component.
 */

// ============================================================================
// Core Graph Types
// ============================================================================

export type EntityType =
  | 'repo'
  | 'file'
  | 'symbol'
  | 'service'
  | 'task'
  | 'spec'
  | 'project';
  | 'persona'
  | 'workflow'
  | 'execution';

export type EdgeType =
  | 'contains'
  | 'import'
  | 'call'
  | 'extends'
  | 'implements'
  | 'uses'
  | 'references'
  | 'dependsOn'
  | 'tests'
  | 'documents'
  | 'produces'
  | 'consumes';

export interface GraphNode {
  id: string; // Format: "entity_type:entity_id"
  entity_type: EntityType;
  entity_id: number;
  label: string;
  metadata: Record<string, unknown>;
}

export interface GraphEdge {
  from_node: string; // Node ID
  to_node: string; // Node ID
  type: EdgeType;
  weight?: number;
  metadata?: Record<string, unknown>;
}

export interface ProjectGraphResponse {
  nodes: GraphNode[];
  edges: GraphEdge[];
  metadata: {
    node_count: number;
    edge_count: number;
    depth: number;
    repos?: number;
    files?: number;
    symbols?: number;
    services?: number;
    tasks?: number;
    specs?: number;
  };
}

// ============================================================================
// Federation Types
// ============================================================================

export type FederationScopeType = 'ecosystem' | 'projects';

export interface FederationScope {
  type: FederationScopeType;
  project_ids?: number[];
}

export type LinkType =
  | 'references'
  | 'dependsOn'
  | 'implements'
  | 'tests'
  | 'documents'
  | 'produces'
  | 'consumes'
  | 'contains';

export interface CrossProjectLink {
  id: number;
  source_project_id: number;
  target_project_id: number;
  from_entity: string;
  from_id: number;
  to_entity: string;
  to_id: number;
  type: LinkType;
  weight: number;
  metadata?: Record<string, unknown>;
  created_at: string;
}

export interface FederationQueryRequest {
  scope: FederationScope;
  link_types?: LinkType[];
  entity_types?: string[];
  limit?: number;
  offset?: number;
}

export interface FederationQueryResponse {
  links: CrossProjectLink[];
  total: number;
  metadata: {
    projects_involved: number[];
    scope_type: FederationScopeType;
    filters_applied: {
      link_types?: string[];
      entity_types?: string[];
    };
  };
}

// ============================================================================
// GraphCanvas Props Types
// ============================================================================

export interface GraphCanvasNode extends GraphNode {
  position?: { x: number; y: number };
  style?: React.CSSProperties;
}

export interface GraphCanvasProps {
  /** Nodes to render in the graph */
  nodes: GraphNode[];
  /** Edges connecting the nodes */
  edges: GraphEdge[];
  /** Optional callback when a node is hovered */
  onNodeHover?: (node: GraphNode | null) => void;
  /** Optional callback when a node is clicked */
  onNodeClick?: (node: GraphNode) => void;
  /** Layout direction: 'TB' (top-bottom), 'LR' (left-right) */
  layoutDirection?: 'TB' | 'LR' | 'BT' | 'RL';
  /** Whether to show the minimap */
  showMinimap?: boolean;
  /** Whether to show the controls */
  showControls?: boolean;
  /** Custom class name for the container */
  className?: string;
  /** Loading state */
  loading?: boolean;
  /** Height of the canvas (default: 600px) */
  height?: number | string;
}

// ============================================================================
// Node Styling Types
// ============================================================================

export interface NodeStyleConfig {
  background: string;
  border: string;
  color: string;
  icon?: string;
}

export const NODE_STYLES: Record<EntityType, NodeStyleConfig> = {
  project: {
    background: '#1e40af',
    border: '#3b82f6',
    color: '#ffffff',
  },
  repo: {
    background: '#166534',
    border: '#22c55e',
    color: '#ffffff',
  },
  file: {
    background: '#854d0e',
    border: '#eab308',
    color: '#ffffff',
  },
  symbol: {
    background: '#7c3aed',
    border: '#a78bfa',
    color: '#ffffff',
  },
  service: {
    background: '#0891b2',
    border: '#22d3ee',
    color: '#ffffff',
  },
  task: {
    background: '#be185d',
    border: '#f472b6',
    color: '#ffffff',
  },
  spec: {
    background: '#475569',
    border: '#94a3b8',
    color: '#ffffff',
  },
  persona: {
    background: '#7c2d12',
    border: '#c2410c',
    color: '#ffffff',
  },
  workflow: {
    background: '#0e7490',
    border: '#06b6d4',
    color: '#ffffff',
  },
  execution: {
    background: '#047857',
    border: '#10b981',
    color: '#ffffff',
  },
};

export const EDGE_STYLES: Record<EdgeType, { stroke: string; animated?: boolean }> = {
  contains: { stroke: '#64748b' },
  import: { stroke: '#3b82f6' },
  call: { stroke: '#22c55e' },
  extends: { stroke: '#a855f7', animated: true },
  implements: { stroke: '#8b5cf6', animated: true },
  uses: { stroke: '#6366f1' },
  references: { stroke: '#94a3b8' },
  dependsOn: { stroke: '#f59e0b', animated: true },
  tests: { stroke: '#10b981' },
  documents: { stroke: '#6b7280' },
  produces: { stroke: '#14b8a6' },
  consumes: { stroke: '#f97316' },
};
