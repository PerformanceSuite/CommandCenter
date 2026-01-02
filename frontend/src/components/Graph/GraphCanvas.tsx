/**
 * GraphCanvas - Core visualization primitive for VISLZR
 *
 * A React Flow-based graph visualization component that renders
 * nodes and edges with automatic layout using dagre.
 *
 * Features:
 * - Automatic hierarchical layout (dagre)
 * - Pan and zoom navigation
 * - Node hover tooltips
 * - Minimap for large graphs
 * - Entity-type-based styling
 */

import React, { useMemo, useCallback, useState } from 'react';
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  Node,
  Edge,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  NodeMouseHandler,
} from '@xyflow/react';
import dagre from 'dagre';
import '@xyflow/react/dist/style.css';

import {
  GraphCanvasProps,
  GraphNode,
  GraphEdge,
  EntityType,
  EdgeType,
  NODE_STYLES,
  EDGE_STYLES,
} from '../../types/graph';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { GraphNodeTooltip } from './GraphNodeTooltip';
import { useWebSocketSubscription } from '../../hooks';

// ============================================================================
// Real-Time Update Types
// ============================================================================

interface EntityUpdateMessage {
  entity_id: string;
  entity_type: string;
  change_type: 'created' | 'updated' | 'deleted';
  data?: unknown;
}

// ============================================================================
// Layout Configuration
// ============================================================================

const DAGRE_CONFIG = {
  rankdir: 'TB' as const,
  nodesep: 80,
  ranksep: 100,
  edgesep: 30,
};

const NODE_WIDTH = 180;
const NODE_HEIGHT = 60;

// ============================================================================
// Layout Helper
// ============================================================================

function getLayoutedElements(
  nodes: Node[],
  edges: Edge[],
  direction: 'TB' | 'LR' | 'BT' | 'RL' = 'TB'
): { nodes: Node[]; edges: Edge[] } {
  const dagreGraph = new dagre.graphlib.Graph();
  dagreGraph.setDefaultEdgeLabel(() => ({}));
  dagreGraph.setGraph({ ...DAGRE_CONFIG, rankdir: direction });

  // Add nodes to dagre
  nodes.forEach((node) => {
    dagreGraph.setNode(node.id, { width: NODE_WIDTH, height: NODE_HEIGHT });
  });

  // Add edges to dagre
  edges.forEach((edge) => {
    dagreGraph.setEdge(edge.source, edge.target);
  });

  // Calculate layout
  dagre.layout(dagreGraph);

  // Apply calculated positions to nodes
  const layoutedNodes = nodes.map((node) => {
    const nodeWithPosition = dagreGraph.node(node.id);
    return {
      ...node,
      position: {
        x: nodeWithPosition.x - NODE_WIDTH / 2,
        y: nodeWithPosition.y - NODE_HEIGHT / 2,
      },
    };
  });

  return { nodes: layoutedNodes, edges };
}

// ============================================================================
// Node Styling
// ============================================================================

function getNodeStyle(entityType: EntityType): React.CSSProperties {
  const config = NODE_STYLES[entityType] || NODE_STYLES.spec;
  return {
    background: config.background,
    border: `2px solid ${config.border}`,
    color: config.color,
    borderRadius: '8px',
    padding: '10px 16px',
    fontSize: '13px',
    fontWeight: 500,
    width: NODE_WIDTH,
    minHeight: NODE_HEIGHT,
    display: 'flex',
    flexDirection: 'column',
    justifyContent: 'center',
    boxShadow: '0 4px 6px -1px rgb(0 0 0 / 0.1)',
  };
}

function getEdgeStyle(edgeType: EdgeType): { stroke: string; strokeWidth: number; animated?: boolean } {
  const config = EDGE_STYLES[edgeType] || EDGE_STYLES.references;
  return {
    stroke: config.stroke,
    strokeWidth: 2,
    animated: config.animated,
  };
}

// ============================================================================
// Transform Functions
// ============================================================================

function transformToReactFlowNodes(graphNodes: GraphNode[]): Node[] {
  return graphNodes.map((node) => ({
    id: node.id,
    data: {
      label: node.label,
      entityType: node.entity_type,
      entityId: node.entity_id,
      metadata: node.metadata,
    },
    position: { x: 0, y: 0 }, // Will be set by layout
    style: getNodeStyle(node.entity_type),
    type: 'default',
  }));
}

function transformToReactFlowEdges(graphEdges: GraphEdge[]): Edge[] {
  return graphEdges.map((edge, index) => {
    const edgeStyle = getEdgeStyle(edge.type as EdgeType);
    return {
      id: `edge-${index}-${edge.from_node}-${edge.to_node}`,
      source: edge.from_node,
      target: edge.to_node,
      label: edge.type,
      labelStyle: { fontSize: 10, fill: '#64748b' },
      labelBgStyle: { fill: '#f8fafc', fillOpacity: 0.9 },
      style: {
        stroke: edgeStyle.stroke,
        strokeWidth: edgeStyle.strokeWidth,
      },
      animated: edgeStyle.animated,
      data: {
        type: edge.type,
        weight: edge.weight,
        metadata: edge.metadata,
      },
    };
  });
}

// ============================================================================
// GraphCanvas Component
// ============================================================================

export const GraphCanvas: React.FC<GraphCanvasProps> = ({
  nodes: inputNodes,
  edges: inputEdges,
  onNodeHover,
  onNodeClick,
  layoutDirection = 'TB',
  showMinimap = true,
  showControls = true,
  className = '',
  loading = false,
  height = 600,
  enableRealTime = false,
  projectId,
  onNodeUpdate,
  onNodeCreate,
  onNodeDelete,
}) => {
  // Real-time WebSocket subscription
  const { isConnected } = useWebSocketSubscription<EntityUpdateMessage>({
    topic: enableRealTime && projectId ? `entity:updated:${projectId}` : '',
    enabled: enableRealTime && !!projectId,
    onMessage: (message) => {
      if (message.change_type === 'updated') {
        onNodeUpdate?.(message.entity_id, message.data);
      } else if (message.change_type === 'created') {
        onNodeCreate?.(message.data);
      } else if (message.change_type === 'deleted') {
        onNodeDelete?.(message.entity_id);
      }
    },
  });

  // Transform and layout nodes/edges
  const { layoutedNodes, layoutedEdges } = useMemo(() => {
    const rfNodes = transformToReactFlowNodes(inputNodes);
    const rfEdges = transformToReactFlowEdges(inputEdges);
    const { nodes: laidOutNodes, edges: laidOutEdges } = getLayoutedElements(
      rfNodes,
      rfEdges,
      layoutDirection
    );
    return { layoutedNodes: laidOutNodes, layoutedEdges: laidOutEdges };
  }, [inputNodes, inputEdges, layoutDirection]);

  // React Flow state
  const [nodes, setNodes, onNodesChange] = useNodesState(layoutedNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(layoutedEdges);

  // Tooltip state
  const [hoveredNode, setHoveredNode] = useState<GraphNode | null>(null);
  const [tooltipPosition, setTooltipPosition] = useState({ x: 0, y: 0 });

  // Update nodes/edges when input changes
  React.useEffect(() => {
    setNodes(layoutedNodes);
    setEdges(layoutedEdges);
  }, [layoutedNodes, layoutedEdges, setNodes, setEdges]);

  // Handle node hover
  const handleNodeMouseEnter: NodeMouseHandler = useCallback(
    (event, node) => {
      const graphNode: GraphNode = {
        id: node.id,
        entity_type: node.data.entityType as EntityType,
        entity_id: node.data.entityId as number,
        label: node.data.label as string,
        metadata: node.data.metadata as Record<string, unknown>,
      };
      setHoveredNode(graphNode);
      setTooltipPosition({ x: event.clientX, y: event.clientY });
      onNodeHover?.(graphNode);
    },
    [onNodeHover]
  );

  const handleNodeMouseLeave: NodeMouseHandler = useCallback(() => {
    setHoveredNode(null);
    onNodeHover?.(null);
  }, [onNodeHover]);

  // Handle node click
  const handleNodeClick: NodeMouseHandler = useCallback(
    (_event, node) => {
      if (onNodeClick) {
        const graphNode: GraphNode = {
          id: node.id,
          entity_type: node.data.entityType as EntityType,
          entity_id: node.data.entityId as number,
          label: node.data.label as string,
          metadata: node.data.metadata as Record<string, unknown>,
        };
        onNodeClick(graphNode);
      }
    },
    [onNodeClick]
  );

  // Minimap node color function
  const minimapNodeColor = useCallback((node: Node) => {
    const entityType = node.data?.entityType as EntityType;
    return NODE_STYLES[entityType]?.background || '#475569';
  }, []);

  // Loading state
  if (loading) {
    return (
      <div
        className={`flex items-center justify-center bg-slate-900 rounded-lg ${className}`}
        style={{ height }}
      >
        <LoadingSpinner />
      </div>
    );
  }

  // Empty state
  if (inputNodes.length === 0) {
    return (
      <div
        className={`flex items-center justify-center bg-slate-900 rounded-lg text-slate-400 ${className}`}
        style={{ height }}
      >
        <div className="text-center">
          <p className="text-lg font-medium">No graph data</p>
          <p className="text-sm mt-1">Add nodes to visualize the graph</p>
        </div>
      </div>
    );
  }

  return (
    <div
      className={`relative bg-slate-900 rounded-lg overflow-hidden ${className}`}
      style={{ height }}
    >
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeMouseEnter={handleNodeMouseEnter}
        onNodeMouseLeave={handleNodeMouseLeave}
        onNodeClick={handleNodeClick}
        fitView
        fitViewOptions={{ padding: 0.2 }}
        minZoom={0.1}
        maxZoom={2}
        nodesDraggable={false}
        nodesConnectable={false}
        elementsSelectable={true}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#334155"
        />
        {showControls && (
          <Controls
            showInteractive={false}
            className="!bg-slate-800 !border-slate-700 !rounded-lg !shadow-lg"
          />
        )}
        {showMinimap && (
          <MiniMap
            nodeColor={minimapNodeColor}
            maskColor="rgba(15, 23, 42, 0.8)"
            className="!bg-slate-800 !border-slate-700 !rounded-lg"
            pannable
            zoomable
          />
        )}
      </ReactFlow>

      {/* Tooltip */}
      {hoveredNode && (
        <GraphNodeTooltip
          node={hoveredNode}
          position={tooltipPosition}
        />
      )}

      {/* Real-time connection indicator */}
      {enableRealTime && (
        <div
          className="realtime-indicator"
          style={{
            position: 'absolute',
            top: 8,
            right: 8,
            display: 'flex',
            alignItems: 'center',
            gap: 4,
            fontSize: 12,
            color: isConnected ? '#22c55e' : '#ef4444',
            backgroundColor: 'rgba(30, 41, 59, 0.9)',
            padding: '4px 8px',
            borderRadius: 6,
          }}
        >
          <span
            style={{
              width: 8,
              height: 8,
              borderRadius: '50%',
              backgroundColor: isConnected ? '#22c55e' : '#ef4444',
            }}
          />
          {isConnected ? 'Live' : 'Connecting...'}
        </div>
      )}

      {/* Legend */}
      <div className="absolute bottom-4 left-4 bg-slate-800/90 rounded-lg p-3 text-xs">
        <div className="text-slate-400 font-medium mb-2">Entity Types</div>
        <div className="grid grid-cols-2 gap-x-4 gap-y-1">
          {Object.entries(NODE_STYLES).slice(0, 6).map(([type, config]) => (
            <div key={type} className="flex items-center gap-2">
              <div
                className="w-3 h-3 rounded"
                style={{ background: config.background }}
              />
              <span className="text-slate-300 capitalize">{type}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default GraphCanvas;
