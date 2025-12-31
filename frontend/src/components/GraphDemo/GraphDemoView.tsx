/**
 * GraphDemoView - Demo page for the GraphCanvas component
 *
 * Demonstrates the VISLZR GraphCanvas capabilities including:
 * - Project graph visualization
 * - Cross-project federation links
 * - Interactive controls and filtering
 */

import React, { useState, useMemo } from 'react';
import { Network, Layers, GitBranch, RefreshCw, Info } from 'lucide-react';
import { GraphCanvas } from '../Graph/GraphCanvas';
import { useProjectGraph } from '../../hooks/useGraph';
import { LoadingSpinner } from '../common/LoadingSpinner';
import { GraphNode, GraphEdge, EntityType } from '../../types/graph';

// Demo data for when no backend data is available
const DEMO_NODES: GraphNode[] = [
  { id: 'project:1', entity_type: 'project', entity_id: 1, label: 'CommandCenter', metadata: { description: 'Main project' } },
  { id: 'repo:1', entity_type: 'repo', entity_id: 1, label: 'backend', metadata: { language: 'Python' } },
  { id: 'repo:2', entity_type: 'repo', entity_id: 2, label: 'frontend', metadata: { language: 'TypeScript' } },
  { id: 'file:1', entity_type: 'file', entity_id: 1, label: 'main.py', metadata: { lines: 250 } },
  { id: 'file:2', entity_type: 'file', entity_id: 2, label: 'graph_service.py', metadata: { lines: 400 } },
  { id: 'file:3', entity_type: 'file', entity_id: 3, label: 'App.tsx', metadata: { lines: 140 } },
  { id: 'symbol:1', entity_type: 'symbol', entity_id: 1, label: 'GraphService', metadata: { kind: 'class' } },
  { id: 'symbol:2', entity_type: 'symbol', entity_id: 2, label: 'get_project_graph', metadata: { kind: 'function' } },
  { id: 'symbol:3', entity_type: 'symbol', entity_id: 3, label: 'GraphCanvas', metadata: { kind: 'component' } },
  { id: 'service:1', entity_type: 'service', entity_id: 1, label: 'Graph API', metadata: { type: 'REST' } },
  { id: 'task:1', entity_type: 'task', entity_id: 1, label: 'Add federation query', metadata: { status: 'done' } },
  { id: 'spec:1', entity_type: 'spec', entity_id: 1, label: 'VISLZR Phase 1', metadata: { status: 'in_progress' } },
];

const DEMO_EDGES: GraphEdge[] = [
  { from_node: 'project:1', to_node: 'repo:1', type: 'contains' },
  { from_node: 'project:1', to_node: 'repo:2', type: 'contains' },
  { from_node: 'repo:1', to_node: 'file:1', type: 'contains' },
  { from_node: 'repo:1', to_node: 'file:2', type: 'contains' },
  { from_node: 'repo:2', to_node: 'file:3', type: 'contains' },
  { from_node: 'file:2', to_node: 'symbol:1', type: 'contains' },
  { from_node: 'file:2', to_node: 'symbol:2', type: 'contains' },
  { from_node: 'file:3', to_node: 'symbol:3', type: 'contains' },
  { from_node: 'symbol:1', to_node: 'symbol:2', type: 'contains' },
  { from_node: 'symbol:3', to_node: 'service:1', type: 'uses' },
  { from_node: 'service:1', to_node: 'symbol:1', type: 'implements' },
  { from_node: 'task:1', to_node: 'spec:1', type: 'implements' },
  { from_node: 'spec:1', to_node: 'symbol:1', type: 'references' },
];

type LayoutDirection = 'TB' | 'LR' | 'BT' | 'RL';

export const GraphDemoView: React.FC = () => {
  const [projectId] = useState<number>(1);
  const [useDemo, setUseDemo] = useState(true);
  const [layoutDirection, setLayoutDirection] = useState<LayoutDirection>('TB');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [filterEntityType, setFilterEntityType] = useState<EntityType | 'all'>('all');

  // Fetch real project graph data
  const { nodes: apiNodes, edges: apiEdges, loading, error, refresh } = useProjectGraph(
    useDemo ? null : projectId,
    { depth: 2 }
  );

  // Use demo data or API data
  const rawNodes = useDemo ? DEMO_NODES : apiNodes;
  const rawEdges = useDemo ? DEMO_EDGES : apiEdges;

  // Filter nodes and edges based on selected entity type
  const { nodes, edges } = useMemo(() => {
    if (filterEntityType === 'all') {
      return { nodes: rawNodes, edges: rawEdges };
    }

    const filteredNodes = rawNodes.filter(n => n.entity_type === filterEntityType);
    const nodeIds = new Set(filteredNodes.map(n => n.id));
    const filteredEdges = rawEdges.filter(
      e => nodeIds.has(e.from_node) && nodeIds.has(e.to_node)
    );

    return { nodes: filteredNodes, edges: filteredEdges };
  }, [rawNodes, rawEdges, filterEntityType]);

  const handleNodeClick = (node: GraphNode) => {
    setSelectedNode(node);
  };

  const entityTypes: (EntityType | 'all')[] = ['all', 'project', 'repo', 'file', 'symbol', 'service', 'task', 'spec'];

  return (
    <div className="h-full flex flex-col gap-4">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <Network className="w-8 h-8 text-blue-400" />
          <div>
            <h1 className="text-2xl font-bold text-white">GraphCanvas Demo</h1>
            <p className="text-sm text-gray-400">VISLZR visualization primitive</p>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* Data source toggle */}
          <label className="flex items-center gap-2 text-sm text-gray-300">
            <input
              type="checkbox"
              checked={useDemo}
              onChange={(e) => setUseDemo(e.target.checked)}
              className="rounded border-gray-600 bg-gray-700 text-blue-500 focus:ring-blue-500"
            />
            Use demo data
          </label>

          {!useDemo && (
            <button
              onClick={refresh}
              disabled={loading}
              className="flex items-center gap-2 px-3 py-2 bg-gray-700 hover:bg-gray-600 rounded-lg text-sm text-gray-200 transition-colors disabled:opacity-50"
            >
              <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
              Refresh
            </button>
          )}
        </div>
      </div>

      {/* Controls */}
      <div className="flex items-center gap-4 p-4 bg-gray-800/50 rounded-lg">
        {/* Layout direction */}
        <div className="flex items-center gap-2">
          <Layers className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-400">Layout:</span>
          <select
            value={layoutDirection}
            onChange={(e) => setLayoutDirection(e.target.value as LayoutDirection)}
            className="bg-gray-700 border-gray-600 rounded px-2 py-1 text-sm text-gray-200"
          >
            <option value="TB">Top to Bottom</option>
            <option value="LR">Left to Right</option>
            <option value="BT">Bottom to Top</option>
            <option value="RL">Right to Left</option>
          </select>
        </div>

        {/* Entity type filter */}
        <div className="flex items-center gap-2">
          <GitBranch className="w-4 h-4 text-gray-400" />
          <span className="text-sm text-gray-400">Filter:</span>
          <select
            value={filterEntityType}
            onChange={(e) => setFilterEntityType(e.target.value as EntityType | 'all')}
            className="bg-gray-700 border-gray-600 rounded px-2 py-1 text-sm text-gray-200"
          >
            {entityTypes.map(type => (
              <option key={type} value={type}>
                {type === 'all' ? 'All Types' : type.charAt(0).toUpperCase() + type.slice(1) + 's'}
              </option>
            ))}
          </select>
        </div>

        {/* Stats */}
        <div className="flex-1" />
        <div className="flex items-center gap-4 text-sm text-gray-400">
          <span>{nodes.length} nodes</span>
          <span>{edges.length} edges</span>
        </div>
      </div>

      {/* Graph Container */}
      <div className="flex-1 bg-gray-800/30 rounded-lg overflow-hidden relative">
        {loading ? (
          <div className="flex items-center justify-center h-full">
            <LoadingSpinner size="lg" />
          </div>
        ) : error ? (
          <div className="flex flex-col items-center justify-center h-full text-red-400">
            <Info className="w-12 h-12 mb-4" />
            <p className="text-lg">Failed to load graph</p>
            <p className="text-sm text-gray-500 mt-2">{error.message}</p>
          </div>
        ) : nodes.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-gray-400">
            <Network className="w-12 h-12 mb-4" />
            <p className="text-lg">No graph data</p>
            <p className="text-sm text-gray-500 mt-2">Enable demo data or fetch from a project</p>
          </div>
        ) : (
          <GraphCanvas
            nodes={nodes}
            edges={edges}
            layoutDirection={layoutDirection}
            onNodeClick={handleNodeClick}
            showMinimap={true}
            showControls={true}
          />
        )}

        {/* Selected node info panel */}
        {selectedNode && (
          <div className="absolute bottom-4 left-4 bg-gray-900/95 rounded-lg p-4 max-w-sm border border-gray-700 shadow-xl">
            <div className="flex items-center justify-between mb-2">
              <span className="text-xs font-medium px-2 py-1 rounded bg-blue-500/20 text-blue-300">
                {selectedNode.entity_type}
              </span>
              <button
                onClick={() => setSelectedNode(null)}
                className="text-gray-500 hover:text-gray-300"
              >
                &times;
              </button>
            </div>
            <h3 className="text-lg font-semibold text-white">{selectedNode.label}</h3>
            <p className="text-xs text-gray-500 mt-1">ID: {selectedNode.id}</p>
            {Object.keys(selectedNode.metadata).length > 0 && (
              <div className="mt-3 pt-3 border-t border-gray-700">
                <p className="text-xs text-gray-400 mb-2">Metadata:</p>
                <pre className="text-xs text-gray-300 bg-gray-800 rounded p-2 overflow-auto max-h-32">
                  {JSON.stringify(selectedNode.metadata, null, 2)}
                </pre>
              </div>
            )}
          </div>
        )}
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 p-3 bg-gray-800/30 rounded-lg text-xs">
        <span className="text-gray-400">Node types:</span>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-purple-500" />
          <span className="text-gray-300">Project</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-green-500" />
          <span className="text-gray-300">Repo</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-yellow-500" />
          <span className="text-gray-300">File</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-blue-500" />
          <span className="text-gray-300">Symbol</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-cyan-500" />
          <span className="text-gray-300">Service</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-orange-500" />
          <span className="text-gray-300">Task</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="w-3 h-3 rounded-full bg-pink-500" />
          <span className="text-gray-300">Spec</span>
        </div>
      </div>
    </div>
  );
};

export default GraphDemoView;
