/**
 * GraphNodeTooltip - Hover tooltip for graph nodes
 *
 * Displays detailed information about a node when hovered.
 */

import React from 'react';
import { GraphNode, EntityType, NODE_STYLES } from '../../types/graph';
import {
  GitBranch,
  File,
  Code,
  Server,
  CheckSquare,
  FileText,
  Folder,
} from 'lucide-react';

// ============================================================================
// Icon Mapping
// ============================================================================

const ENTITY_ICONS: Record<EntityType, React.ElementType> = {
  project: Folder,
  repo: GitBranch,
  file: File,
  symbol: Code,
  service: Server,
  task: CheckSquare,
  spec: FileText,
};

// ============================================================================
// Props
// ============================================================================

interface GraphNodeTooltipProps {
  node: GraphNode;
  position: { x: number; y: number };
}

// ============================================================================
// Component
// ============================================================================

export const GraphNodeTooltip: React.FC<GraphNodeTooltipProps> = ({
  node,
  position,
}) => {
  const Icon = ENTITY_ICONS[node.entity_type] || FileText;
  const style = NODE_STYLES[node.entity_type] || NODE_STYLES.spec;

  // Format metadata for display
  const metadataEntries = Object.entries(node.metadata || {}).filter(
    ([key, value]) => value !== null && value !== undefined && key !== 'metadata'
  );

  return (
    <div
      className="fixed z-50 pointer-events-none"
      style={{
        left: position.x + 15,
        top: position.y + 15,
        maxWidth: 320,
      }}
    >
      <div className="bg-slate-800 border border-slate-600 rounded-lg shadow-xl p-3">
        {/* Header */}
        <div className="flex items-center gap-2 mb-2">
          <div
            className="p-1.5 rounded"
            style={{ background: style.background }}
          >
            <Icon size={14} className="text-white" />
          </div>
          <div>
            <div className="text-white font-medium text-sm truncate max-w-[250px]">
              {node.label}
            </div>
            <div className="text-slate-400 text-xs capitalize">
              {node.entity_type} #{node.entity_id}
            </div>
          </div>
        </div>

        {/* Metadata */}
        {metadataEntries.length > 0 && (
          <div className="border-t border-slate-700 pt-2 mt-2">
            <div className="grid gap-1">
              {metadataEntries.slice(0, 5).map(([key, value]) => (
                <div key={key} className="flex justify-between text-xs">
                  <span className="text-slate-400 capitalize">
                    {key.replace(/_/g, ' ')}
                  </span>
                  <span className="text-slate-300 ml-2 truncate max-w-[150px]">
                    {formatValue(value)}
                  </span>
                </div>
              ))}
              {metadataEntries.length > 5 && (
                <div className="text-xs text-slate-500 italic">
                  +{metadataEntries.length - 5} more fields
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// Helpers
// ============================================================================

function formatValue(value: unknown): string {
  if (typeof value === 'boolean') {
    return value ? 'Yes' : 'No';
  }
  if (typeof value === 'number') {
    return value.toLocaleString();
  }
  if (typeof value === 'string') {
    return value;
  }
  if (Array.isArray(value)) {
    return value.length > 0 ? value.join(', ') : '(empty)';
  }
  if (value === null || value === undefined) {
    return '-';
  }
  return String(value);
}

export default GraphNodeTooltip;
