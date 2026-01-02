# Wander Mind Map Implementation Plan

**Date**: 2026-01-02
**Phase**: 0 (Pre-requisite for Wander Engine)
**Estimated Effort**: 1 day
**Dependencies**: ReactFlow (installed), hub/frontend infrastructure

---

## Objective

Build the WanderMindMap visualization component using ReactFlow. This can be developed with mock data before the wander engine exists, giving us:

1. Visual playground to refine UX
2. Component ready when wander engine emits events
3. Pattern established for other real-time visualizations

---

## File Structure

```
hub/frontend/src/
├── services/
│   └── websocket.ts                    # Copy from main frontend
├── hooks/
│   ├── useWebSocketSubscription.ts     # Copy from main frontend
│   └── useWanderSession.ts             # NEW: Wander state management
├── components/
│   └── WanderMindMap/
│       ├── index.ts                    # Barrel export
│       ├── WanderMindMap.tsx           # Main ReactFlow component
│       ├── nodes/
│       │   ├── index.ts
│       │   ├── LocusNode.tsx           # Standard exploration node
│       │   ├── CrystalNode.tsx         # Hardened insight node
│       │   └── FractalNode.tsx         # Security-encoded node
│       ├── edges/
│       │   ├── index.ts
│       │   └── WanderEdge.tsx          # Animated path edge
│       ├── controls/
│       │   ├── WanderControls.tsx      # Play/Pause/Stop
│       │   └── NodeContextMenu.tsx     # Right-click menu
│       ├── panels/
│       │   ├── NodeDetailPanel.tsx     # Side panel for node info
│       │   └── SessionInfoPanel.tsx    # Session stats
│       ├── types.ts                    # TypeScript definitions
│       └── utils.ts                    # Helper functions
└── pages/
    └── WanderPage.tsx                  # Page wrapper

backend/app/websocket/
└── nats_bridge.py                      # Add wander.* subject mappings
```

---

## Implementation Tasks

### Task 1: Copy WebSocket Infrastructure (30 min)

Copy these files from `frontend/src/` to `hub/frontend/src/`:
- `services/websocket.ts`
- `hooks/useWebSocketSubscription.ts`

Adapt the WebSocket URL to hub backend.

### Task 2: Create Type Definitions (30 min)

File: `hub/frontend/src/components/WanderMindMap/types.ts`

### Task 3: Create Custom Nodes (2 hrs)

Files:
- `nodes/LocusNode.tsx`
- `nodes/CrystalNode.tsx`
- `nodes/FractalNode.tsx`

### Task 4: Create Custom Edges (45 min)

File: `edges/WanderEdge.tsx`

### Task 5: Create Main Component (2 hrs)

File: `WanderMindMap.tsx`

### Task 6: Create Controls (1 hr)

Files:
- `controls/WanderControls.tsx`
- `controls/NodeContextMenu.tsx`

### Task 7: Create Panels (1 hr)

Files:
- `panels/NodeDetailPanel.tsx`
- `panels/SessionInfoPanel.tsx`

### Task 8: Create Page Wrapper (30 min)

File: `pages/WanderPage.tsx`

### Task 9: Add NATS Mappings (30 min)

File: `backend/app/websocket/nats_bridge.py`

### Task 10: Add Route (15 min)

Add `/wander/:sessionId?` route to hub frontend router.

---

## Component Specifications

See the following sections for complete, copy-paste-ready component code.

---

## SPEC: types.ts

```typescript
// hub/frontend/src/components/WanderMindMap/types.ts

import { Node, Edge } from 'reactflow';

// Domain colors
export const DOMAIN_COLORS: Record<string, string> = {
  finance: '#3B82F6',      // Blue
  technology: '#10B981',   // Green
  health: '#EF4444',       // Red
  social: '#8B5CF6',       // Purple
  legal: '#F59E0B',        // Orange
  default: '#6B7280',      // Gray
};

// Node data types
export interface LocusData {
  type: 'locus';
  concept: string;
  domains: string[];
  abstractionLevel: number;
  visited: boolean;
  isCurrent: boolean;
  visitCount: number;
  interestingness: number;
  noveltyScore: number;
  lastVisited?: string;
}

export interface CrystalData {
  type: 'crystal';
  insight: string;
  domains: string[];
  confidence: number;
  actionability: number;
  sourceResonanceId: string;
  createdAt: string;
}

export interface FractalData {
  type: 'fractal';
  concept: string;
  domains: string[];
  fractalImageUrl?: string;
  securityLevel: 'gold' | 'silver' | 'red';
  canDecode: boolean;
  decodedContent?: string;
}

export type WanderNodeData = LocusData | CrystalData | FractalData;

// Edge data types
export interface WanderEdgeData {
  edgeType: 'path' | 'adjacency' | 'bridge' | 'resonance';
  strength: number;
  animated: boolean;
}

// ReactFlow node/edge with our data
export type WanderNode = Node<WanderNodeData>;
export type WanderEdge = Edge<WanderEdgeData>;

// Session types
export interface WanderSession {
  id: string;
  name: string;
  status: 'active' | 'paused' | 'completed' | 'abandoned';
  seedConcept: string;
  attractor?: string;
  currentLocusId?: string;
  stepCount: number;
  cloudBudgetCents: number;
  cloudSpentCents: number;
  temperature: number;
  createdAt: string;
  lastStepAt?: string;
}

// Event types from NATS
export interface WanderStepEvent {
  sessionId: string;
  stepNumber: number;
  fromLocus: {
    id: string;
    concept: string;
    domains: string[];
  };
  toLocus: {
    id: string;
    concept: string;
    domains: string[];
    interestingness: number;
    noveltyScore: number;
  };
  adjacenciesConsidered: number;
}

export interface WanderCrystalEvent {
  sessionId: string;
  crystal: {
    id: string;
    insight: string;
    confidence: number;
    actionability: number;
    domains: string[];
    sourceLocusId: string;
  };
}

export interface WanderResonanceEvent {
  sessionId: string;
  resonance: {
    id: string;
    themes: string[];
    strength: number;
    occurrences: number;
    relatedLocusIds: string[];
  };
}

// Context menu action types
export type NodeAction =
  | 'go-deeper'
  | 'fence-out'
  | 'anchor'
  | 'inject'
  | 'view-details'
  | 'force-crystallize';

// Utility to get domain color
export function getDomainColor(domain: string): string {
  return DOMAIN_COLORS[domain.toLowerCase()] || DOMAIN_COLORS.default;
}

// Utility to get mixed color for multi-domain
export function getMixedDomainColor(domains: string[]): string {
  if (domains.length === 0) return DOMAIN_COLORS.default;
  if (domains.length === 1) return getDomainColor(domains[0]);
  // For multiple domains, return first (could be gradient in future)
  return getDomainColor(domains[0]);
}
```

---

## SPEC: LocusNode.tsx

```tsx
// hub/frontend/src/components/WanderMindMap/nodes/LocusNode.tsx

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { LocusData, getMixedDomainColor } from '../types';

export const LocusNode = memo(({ data, selected }: NodeProps<LocusData>) => {
  // Size based on interestingness (20-50px)
  const size = 20 + data.interestingness * 30;

  // Color based on primary domain
  const bgColor = getMixedDomainColor(data.domains);

  // Opacity based on visited status and recency
  const opacity = data.visited ? (data.isCurrent ? 1 : 0.8) : 0.4;

  return (
    <div className="group relative">
      {/* Connection handles (invisible) */}
      <Handle
        type="target"
        position={Position.Top}
        className="!opacity-0 !w-2 !h-2"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!opacity-0 !w-2 !h-2"
      />

      {/* Main node circle */}
      <div
        className={`
          rounded-full flex items-center justify-center
          transition-all duration-300 ease-out
          cursor-pointer
          ${data.isCurrent ? 'ring-2 ring-yellow-400 ring-offset-2 ring-offset-slate-900' : ''}
          ${selected ? 'ring-2 ring-blue-400 ring-offset-1 ring-offset-slate-900' : ''}
          ${data.visited ? 'shadow-lg' : 'shadow-sm'}
        `}
        style={{
          width: size,
          height: size,
          backgroundColor: bgColor,
          opacity,
        }}
      >
        {/* Current indicator pulse */}
        {data.isCurrent && (
          <div
            className="absolute inset-0 rounded-full animate-ping"
            style={{ backgroundColor: bgColor, opacity: 0.3 }}
          />
        )}

        {/* Visit count badge */}
        {data.visitCount > 1 && (
          <span className="absolute -top-1 -right-1 bg-slate-700 text-white text-[10px] rounded-full w-4 h-4 flex items-center justify-center">
            {data.visitCount}
          </span>
        )}
      </div>

      {/* Tooltip on hover */}
      <div className="
        absolute bottom-full left-1/2 -translate-x-1/2 mb-2
        opacity-0 group-hover:opacity-100
        transition-opacity duration-200
        pointer-events-none
        z-50
      ">
        <div className="bg-slate-800 text-white text-xs p-2 rounded-lg shadow-xl max-w-xs whitespace-nowrap">
          <div className="font-medium truncate max-w-[200px]">{data.concept}</div>
          <div className="text-slate-400 text-[10px] mt-1">
            {data.domains.join(', ')} • {(data.interestingness * 100).toFixed(0)}% interesting
          </div>
        </div>
        {/* Tooltip arrow */}
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
      </div>
    </div>
  );
});

LocusNode.displayName = 'LocusNode';

export default LocusNode;
```

---

## SPEC: CrystalNode.tsx

```tsx
// hub/frontend/src/components/WanderMindMap/nodes/CrystalNode.tsx

import { memo } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { CrystalData, getMixedDomainColor } from '../types';
import { Gem } from 'lucide-react';

export const CrystalNode = memo(({ data, selected }: NodeProps<CrystalData>) => {
  // Size based on confidence (40-60px)
  const size = 40 + data.confidence * 20;

  // Color based on domain
  const bgColor = getMixedDomainColor(data.domains);

  return (
    <div className="group relative">
      {/* Connection handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="!opacity-0 !w-2 !h-2"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!opacity-0 !w-2 !h-2"
      />

      {/* Diamond shape using rotated square */}
      <div
        className={`
          flex items-center justify-center
          transition-all duration-300
          cursor-pointer
          rotate-45
          ${selected ? 'ring-2 ring-blue-400 ring-offset-1 ring-offset-slate-900' : ''}
        `}
        style={{
          width: size,
          height: size,
          backgroundColor: bgColor,
          boxShadow: `0 0 20px ${bgColor}66, 0 0 40px ${bgColor}33`,
        }}
      >
        {/* Inner glow effect */}
        <div
          className="absolute inset-2 rounded-sm"
          style={{
            background: `linear-gradient(135deg, rgba(255,255,255,0.3) 0%, transparent 50%)`,
          }}
        />

        {/* Icon (counter-rotate to stay upright) */}
        <Gem
          className="-rotate-45 text-white/80"
          size={size * 0.4}
        />
      </div>

      {/* Actionability indicator */}
      {data.actionability > 0.7 && (
        <div className="absolute -bottom-1 -right-1 w-3 h-3 bg-green-500 rounded-full border-2 border-slate-900" />
      )}

      {/* Tooltip */}
      <div className="
        absolute bottom-full left-1/2 -translate-x-1/2 mb-4
        opacity-0 group-hover:opacity-100
        transition-opacity duration-200
        pointer-events-none
        z-50
      ">
        <div className="bg-slate-800 text-white text-xs p-3 rounded-lg shadow-xl max-w-sm">
          <div className="font-medium text-yellow-400 mb-1">💎 Crystal</div>
          <div className="text-slate-200">{data.insight}</div>
          <div className="text-slate-400 text-[10px] mt-2 flex gap-3">
            <span>Confidence: {(data.confidence * 100).toFixed(0)}%</span>
            <span>Actionable: {(data.actionability * 100).toFixed(0)}%</span>
          </div>
        </div>
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
      </div>
    </div>
  );
});

CrystalNode.displayName = 'CrystalNode';

export default CrystalNode;
```

---

## SPEC: FractalNode.tsx

```tsx
// hub/frontend/src/components/WanderMindMap/nodes/FractalNode.tsx

import { memo, useState } from 'react';
import { Handle, Position, NodeProps } from 'reactflow';
import { FractalData } from '../types';
import { Lock, Unlock, ShieldAlert, ShieldCheck } from 'lucide-react';

const SECURITY_COLORS = {
  gold: '#FFD700',
  silver: '#C0C0C0',
  red: '#EF4444',
};

export const FractalNode = memo(({ data, selected }: NodeProps<FractalData>) => {
  const [showDecoded, setShowDecoded] = useState(false);

  const size = 50;
  const borderColor = SECURITY_COLORS[data.securityLevel];

  return (
    <div className="group relative">
      {/* Connection handles */}
      <Handle
        type="target"
        position={Position.Top}
        className="!opacity-0 !w-2 !h-2"
      />
      <Handle
        type="source"
        position={Position.Bottom}
        className="!opacity-0 !w-2 !h-2"
      />

      {/* Square container */}
      <div
        className={`
          rounded-md overflow-hidden
          transition-all duration-300
          cursor-pointer
          ${selected ? 'ring-2 ring-blue-400 ring-offset-1 ring-offset-slate-900' : ''}
        `}
        style={{
          width: size,
          height: size,
          border: `3px solid ${borderColor}`,
          boxShadow: `0 0 10px ${borderColor}44`,
        }}
        onClick={() => data.canDecode && setShowDecoded(!showDecoded)}
      >
        {/* Fractal image or placeholder */}
        {data.fractalImageUrl ? (
          <img
            src={data.fractalImageUrl}
            alt="Fractal encoded data"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="w-full h-full bg-gradient-to-br from-slate-700 to-slate-800 flex items-center justify-center">
            {/* Placeholder fractal pattern */}
            <div className="text-2xl opacity-50">🌀</div>
          </div>
        )}

        {/* Lock overlay for non-decodable */}
        {!data.canDecode && (
          <div className="absolute inset-0 bg-slate-900/60 flex items-center justify-center">
            <Lock className="text-slate-400" size={20} />
          </div>
        )}
      </div>

      {/* Security level indicator */}
      <div
        className="absolute -top-1 -right-1 w-5 h-5 rounded-full flex items-center justify-center"
        style={{ backgroundColor: borderColor }}
      >
        {data.securityLevel === 'gold' && <ShieldCheck className="text-slate-900" size={12} />}
        {data.securityLevel === 'silver' && <Unlock className="text-slate-900" size={12} />}
        {data.securityLevel === 'red' && <ShieldAlert className="text-white" size={12} />}
      </div>

      {/* Tooltip */}
      <div className="
        absolute bottom-full left-1/2 -translate-x-1/2 mb-2
        opacity-0 group-hover:opacity-100
        transition-opacity duration-200
        pointer-events-none
        z-50
      ">
        <div className="bg-slate-800 text-white text-xs p-2 rounded-lg shadow-xl max-w-xs">
          <div className="font-medium flex items-center gap-2">
            <span>🔐 Fractal Encoded</span>
            <span
              className="px-1.5 py-0.5 rounded text-[10px]"
              style={{ backgroundColor: borderColor, color: data.securityLevel === 'red' ? 'white' : 'black' }}
            >
              {data.securityLevel.toUpperCase()}
            </span>
          </div>
          <div className="text-slate-400 text-[10px] mt-1">
            {data.canDecode ? 'Click to decode' : 'Access denied - decoder not available'}
          </div>
        </div>
        <div className="absolute top-full left-1/2 -translate-x-1/2 border-4 border-transparent border-t-slate-800" />
      </div>

      {/* Decoded content popup */}
      {showDecoded && data.decodedContent && (
        <div className="
          absolute top-full left-1/2 -translate-x-1/2 mt-2
          bg-slate-800 text-white text-xs p-3 rounded-lg shadow-xl
          max-w-sm z-50 border border-yellow-500/50
        ">
          <div className="font-medium text-yellow-400 mb-1">Decoded Content</div>
          <div className="text-slate-200">{data.decodedContent}</div>
        </div>
      )}
    </div>
  );
});

FractalNode.displayName = 'FractalNode';

export default FractalNode;
```

---

## SPEC: WanderEdge.tsx

```tsx
// hub/frontend/src/components/WanderMindMap/edges/WanderEdge.tsx

import { memo } from 'react';
import { EdgeProps, getBezierPath, EdgeLabelRenderer } from 'reactflow';
import { WanderEdgeData, DOMAIN_COLORS } from '../types';

const EDGE_STYLES = {
  path: {
    strokeWidth: 2,
    strokeDasharray: 'none',
    color: '#64748b', // slate-500
  },
  adjacency: {
    strokeWidth: 1,
    strokeDasharray: '5,5',
    color: '#475569', // slate-600
  },
  bridge: {
    strokeWidth: 3,
    strokeDasharray: 'none',
    color: '#8B5CF6', // purple-500
  },
  resonance: {
    strokeWidth: 2,
    strokeDasharray: '10,5',
    color: '#F59E0B', // amber-500
  },
};

export const WanderEdge = memo(({
  id,
  sourceX,
  sourceY,
  targetX,
  targetY,
  sourcePosition,
  targetPosition,
  data,
  selected,
}: EdgeProps<WanderEdgeData>) => {
  const style = EDGE_STYLES[data?.edgeType || 'path'];

  const [edgePath, labelX, labelY] = getBezierPath({
    sourceX,
    sourceY,
    sourcePosition,
    targetX,
    targetY,
    targetPosition,
  });

  return (
    <>
      {/* Base edge */}
      <path
        id={id}
        className="react-flow__edge-path"
        d={edgePath}
        strokeWidth={style.strokeWidth}
        stroke={selected ? '#3B82F6' : style.color}
        strokeDasharray={style.strokeDasharray}
        fill="none"
        style={{
          opacity: data?.strength || 0.8,
        }}
      />

      {/* Animated flow for active edges */}
      {data?.animated && (
        <path
          d={edgePath}
          strokeWidth={style.strokeWidth + 2}
          stroke={style.color}
          strokeDasharray="10,10"
          fill="none"
          opacity={0.5}
          style={{
            animation: 'flowAnimation 1s linear infinite',
          }}
        />
      )}

      {/* Bridge indicator */}
      {data?.edgeType === 'bridge' && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
              pointerEvents: 'all',
            }}
            className="bg-purple-500 text-white text-[10px] px-1.5 py-0.5 rounded font-medium"
          >
            BRIDGE
          </div>
        </EdgeLabelRenderer>
      )}

      {/* Resonance pulse indicator */}
      {data?.edgeType === 'resonance' && (
        <EdgeLabelRenderer>
          <div
            style={{
              position: 'absolute',
              transform: `translate(-50%, -50%) translate(${labelX}px, ${labelY}px)`,
            }}
            className="w-3 h-3 bg-amber-500 rounded-full animate-ping"
          />
        </EdgeLabelRenderer>
      )}
    </>
  );
});

WanderEdge.displayName = 'WanderEdge';

export default WanderEdge;
```

---

## SPEC: WanderControls.tsx

```tsx
// hub/frontend/src/components/WanderMindMap/controls/WanderControls.tsx

import { Play, Pause, Square, SkipForward, Settings, ZoomIn, ZoomOut, Maximize2 } from 'lucide-react';
import { useReactFlow } from 'reactflow';

interface WanderControlsProps {
  sessionId: string;
  status: 'active' | 'paused' | 'completed' | 'abandoned';
  stepCount: number;
  onPlay: () => void;
  onPause: () => void;
  onStop: () => void;
  onStep: () => void;
  onSettingsClick: () => void;
}

export function WanderControls({
  sessionId,
  status,
  stepCount,
  onPlay,
  onPause,
  onStop,
  onStep,
  onSettingsClick,
}: WanderControlsProps) {
  const { zoomIn, zoomOut, fitView } = useReactFlow();

  const isActive = status === 'active';
  const isPaused = status === 'paused';
  const isEnded = status === 'completed' || status === 'abandoned';

  return (
    <div className="absolute bottom-4 left-1/2 -translate-x-1/2 z-10">
      <div className="bg-slate-800/90 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700 p-2 flex items-center gap-2">
        {/* Playback controls */}
        <div className="flex items-center gap-1 pr-2 border-r border-slate-600">
          {/* Play/Pause toggle */}
          {isActive ? (
            <button
              onClick={onPause}
              className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-yellow-400"
              title="Pause"
            >
              <Pause size={20} />
            </button>
          ) : (
            <button
              onClick={onPlay}
              disabled={isEnded}
              className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-green-400 disabled:opacity-50 disabled:cursor-not-allowed"
              title="Resume"
            >
              <Play size={20} />
            </button>
          )}

          {/* Stop */}
          <button
            onClick={onStop}
            disabled={isEnded}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-red-400 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Stop"
          >
            <Square size={20} />
          </button>

          {/* Single step */}
          <button
            onClick={onStep}
            disabled={isActive || isEnded}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-blue-400 disabled:opacity-50 disabled:cursor-not-allowed"
            title="Single step"
          >
            <SkipForward size={20} />
          </button>
        </div>

        {/* Status indicator */}
        <div className="px-3 flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${
            isActive ? 'bg-green-500 animate-pulse' :
            isPaused ? 'bg-yellow-500' :
            'bg-slate-500'
          }`} />
          <span className="text-slate-300 text-sm font-medium">
            Step {stepCount}
          </span>
        </div>

        {/* Zoom controls */}
        <div className="flex items-center gap-1 pl-2 border-l border-slate-600">
          <button
            onClick={() => zoomIn()}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-slate-400"
            title="Zoom in"
          >
            <ZoomIn size={18} />
          </button>
          <button
            onClick={() => zoomOut()}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-slate-400"
            title="Zoom out"
          >
            <ZoomOut size={18} />
          </button>
          <button
            onClick={() => fitView({ padding: 0.2 })}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-slate-400"
            title="Fit view"
          >
            <Maximize2 size={18} />
          </button>
        </div>

        {/* Settings */}
        <div className="pl-2 border-l border-slate-600">
          <button
            onClick={onSettingsClick}
            className="p-2 hover:bg-slate-700 rounded-lg transition-colors text-slate-400"
            title="Session settings"
          >
            <Settings size={18} />
          </button>
        </div>
      </div>
    </div>
  );
}

export default WanderControls;
```

---

## SPEC: NodeContextMenu.tsx

```tsx
// hub/frontend/src/components/WanderMindMap/controls/NodeContextMenu.tsx

import { useCallback } from 'react';
import {
  ArrowDownToLine,
  Ban,
  Anchor,
  Syringe,
  Eye,
  Gem,
  X
} from 'lucide-react';
import { NodeAction, WanderNodeData } from '../types';

interface NodeContextMenuProps {
  nodeId: string;
  nodeData: WanderNodeData;
  position: { x: number; y: number };
  onAction: (action: NodeAction, nodeId: string) => void;
  onClose: () => void;
}

interface MenuAction {
  id: NodeAction;
  label: string;
  icon: React.ReactNode;
  description: string;
  available: (data: WanderNodeData) => boolean;
  dangerous?: boolean;
}

const ACTIONS: MenuAction[] = [
  {
    id: 'view-details',
    label: 'View Details',
    icon: <Eye size={16} />,
    description: 'Open detail panel',
    available: () => true,
  },
  {
    id: 'go-deeper',
    label: 'Go Deeper',
    icon: <ArrowDownToLine size={16} />,
    description: 'Spawn focused sub-wander from this point',
    available: (data) => data.type === 'locus',
  },
  {
    id: 'inject',
    label: 'Inject Here',
    icon: <Syringe size={16} />,
    description: 'Force wander to visit this area',
    available: (data) => data.type === 'locus' && !(data as any).isCurrent,
  },
  {
    id: 'anchor',
    label: 'Add as Anchor',
    icon: <Anchor size={16} />,
    description: 'Add to seed concepts',
    available: (data) => data.type === 'locus',
  },
  {
    id: 'fence-out',
    label: 'Fence Out',
    icon: <Ban size={16} />,
    description: 'Add to forbidden zone',
    available: (data) => data.type === 'locus',
    dangerous: true,
  },
  {
    id: 'force-crystallize',
    label: 'Force Crystallize',
    icon: <Gem size={16} />,
    description: 'Attempt crystallization now',
    available: (data) => data.type === 'locus' && (data as any).interestingness > 0.6,
  },
];

export function NodeContextMenu({
  nodeId,
  nodeData,
  position,
  onAction,
  onClose,
}: NodeContextMenuProps) {
  const handleAction = useCallback((action: NodeAction) => {
    onAction(action, nodeId);
    onClose();
  }, [nodeId, onAction, onClose]);

  const availableActions = ACTIONS.filter(a => a.available(nodeData));

  return (
    <div
      className="fixed z-50 bg-slate-800 rounded-lg shadow-xl border border-slate-700 py-1 min-w-[200px]"
      style={{
        left: position.x,
        top: position.y,
        transform: 'translate(0, 0)',
      }}
    >
      {/* Header */}
      <div className="px-3 py-2 border-b border-slate-700 flex items-center justify-between">
        <span className="text-slate-300 text-sm font-medium truncate max-w-[150px]">
          {nodeData.type === 'crystal'
            ? (nodeData as any).insight?.slice(0, 30) + '...'
            : (nodeData as any).concept?.slice(0, 30) + '...'
          }
        </span>
        <button
          onClick={onClose}
          className="p-1 hover:bg-slate-700 rounded"
        >
          <X size={14} className="text-slate-400" />
        </button>
      </div>

      {/* Actions */}
      <div className="py-1">
        {availableActions.map((action) => (
          <button
            key={action.id}
            onClick={() => handleAction(action.id)}
            className={`
              w-full px-3 py-2 text-left flex items-center gap-3
              hover:bg-slate-700 transition-colors
              ${action.dangerous ? 'text-red-400 hover:text-red-300' : 'text-slate-300'}
            `}
          >
            <span className="text-slate-400">{action.icon}</span>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-medium">{action.label}</div>
              <div className="text-[10px] text-slate-500 truncate">
                {action.description}
              </div>
            </div>
          </button>
        ))}
      </div>

      {availableActions.length === 0 && (
        <div className="px-3 py-4 text-center text-slate-500 text-sm">
          No actions available
        </div>
      )}
    </div>
  );
}

export default NodeContextMenu;
```

---

## SPEC: WanderMindMap.tsx (Main Component)

```tsx
// hub/frontend/src/components/WanderMindMap/WanderMindMap.tsx

import { useCallback, useState, useEffect, useRef } from 'react';
import ReactFlow, {
  Controls,
  Background,
  BackgroundVariant,
  useNodesState,
  useEdgesState,
  useReactFlow,
  ReactFlowProvider,
  NodeMouseHandler,
  OnNodesChange,
  OnEdgesChange,
} from 'reactflow';
import 'reactflow/dist/style.css';

import { LocusNode } from './nodes/LocusNode';
import { CrystalNode } from './nodes/CrystalNode';
import { FractalNode } from './nodes/FractalNode';
import { WanderEdge } from './edges/WanderEdge';
import { WanderControls } from './controls/WanderControls';
import { NodeContextMenu } from './controls/NodeContextMenu';
import { NodeDetailPanel } from './panels/NodeDetailPanel';
import {
  WanderNode,
  WanderEdge as WanderEdgeType,
  WanderSession,
  WanderStepEvent,
  WanderCrystalEvent,
  NodeAction,
  WanderNodeData,
} from './types';

// Register custom node types
const nodeTypes = {
  locus: LocusNode,
  crystal: CrystalNode,
  fractal: FractalNode,
};

// Register custom edge types
const edgeTypes = {
  wander: WanderEdge,
};

interface WanderMindMapProps {
  sessionId: string;
  session?: WanderSession;
  onSessionAction?: (action: 'play' | 'pause' | 'stop' | 'step') => void;
  onNodeAction?: (action: NodeAction, nodeId: string) => void;
}

// Inner component that uses ReactFlow hooks
function WanderMindMapInner({
  sessionId,
  session,
  onSessionAction,
  onNodeAction,
}: WanderMindMapProps) {
  const reactFlowInstance = useReactFlow();
  const [nodes, setNodes, onNodesChange] = useNodesState<WanderNodeData>([]);
  const [edges, setEdges, onEdgesChange] = useEdgesState([]);

  // Context menu state
  const [contextMenu, setContextMenu] = useState<{
    nodeId: string;
    nodeData: WanderNodeData;
    position: { x: number; y: number };
  } | null>(null);

  // Selected node for detail panel
  const [selectedNodeId, setSelectedNodeId] = useState<string | null>(null);

  // Track current node for highlighting
  const [currentNodeId, setCurrentNodeId] = useState<string | null>(null);

  // Handle step event - add new node and edge
  const handleStepEvent = useCallback((event: WanderStepEvent) => {
    const { fromLocus, toLocus, stepNumber } = event;

    // Check if toLocus already exists
    const existingNode = nodes.find(n => n.id === toLocus.id);

    if (!existingNode) {
      // Add new node
      const newNode: WanderNode = {
        id: toLocus.id,
        type: 'locus',
        position: calculatePosition(nodes.length, stepNumber),
        data: {
          type: 'locus',
          concept: toLocus.concept,
          domains: toLocus.domains,
          abstractionLevel: 0.5,
          visited: true,
          isCurrent: true,
          visitCount: 1,
          interestingness: toLocus.interestingness,
          noveltyScore: toLocus.noveltyScore,
        },
      };

      setNodes(nds => {
        // Update previous current to not current
        const updated = nds.map(n => ({
          ...n,
          data: { ...n.data, isCurrent: false },
        }));
        return [...updated, newNode];
      });
    } else {
      // Update existing node
      setNodes(nds => nds.map(n => ({
        ...n,
        data: {
          ...n.data,
          isCurrent: n.id === toLocus.id,
          visitCount: n.id === toLocus.id ? (n.data as any).visitCount + 1 : (n.data as any).visitCount,
        },
      })));
    }

    // Add edge from previous to new
    if (fromLocus) {
      const newEdge: WanderEdgeType = {
        id: `${fromLocus.id}-${toLocus.id}`,
        source: fromLocus.id,
        target: toLocus.id,
        type: 'wander',
        data: {
          edgeType: 'path',
          strength: 1,
          animated: true,
        },
      };

      setEdges(eds => {
        // Check if edge already exists
        if (eds.find(e => e.id === newEdge.id)) {
          return eds;
        }
        // Remove animation from previous edges
        const updated = eds.map(e => ({
          ...e,
          data: { ...e.data, animated: false },
        }));
        return [...updated, newEdge];
      });
    }

    setCurrentNodeId(toLocus.id);

    // Fit view to include new node
    setTimeout(() => {
      reactFlowInstance.fitView({ padding: 0.2, duration: 500 });
    }, 100);
  }, [nodes, setNodes, setEdges, reactFlowInstance]);

  // Handle crystal event - transform node to crystal
  const handleCrystalEvent = useCallback((event: WanderCrystalEvent) => {
    const { crystal } = event;

    setNodes(nds => nds.map(n => {
      if (n.id === crystal.sourceLocusId) {
        return {
          ...n,
          type: 'crystal',
          data: {
            type: 'crystal',
            insight: crystal.insight,
            domains: crystal.domains,
            confidence: crystal.confidence,
            actionability: crystal.actionability,
            sourceResonanceId: '',
            createdAt: new Date().toISOString(),
          },
        };
      }
      return n;
    }));
  }, [setNodes]);

  // Context menu handlers
  const onNodeContextMenu: NodeMouseHandler = useCallback((event, node) => {
    event.preventDefault();
    setContextMenu({
      nodeId: node.id,
      nodeData: node.data,
      position: { x: event.clientX, y: event.clientY },
    });
  }, []);

  const onNodeClick: NodeMouseHandler = useCallback((_, node) => {
    setSelectedNodeId(node.id);
    setContextMenu(null);
  }, []);

  const onPaneClick = useCallback(() => {
    setContextMenu(null);
    setSelectedNodeId(null);
  }, []);

  const handleNodeAction = useCallback((action: NodeAction, nodeId: string) => {
    onNodeAction?.(action, nodeId);

    // Handle view-details locally
    if (action === 'view-details') {
      setSelectedNodeId(nodeId);
    }
  }, [onNodeAction]);

  // TODO: Replace with actual WebSocket subscription
  // useWebSocketSubscription({
  //   topic: `wander:step:${sessionId}`,
  //   onMessage: handleStepEvent,
  // });

  // Load mock data for development
  useEffect(() => {
    if (nodes.length === 0) {
      loadMockData(setNodes, setEdges);
    }
  }, []);

  const selectedNode = nodes.find(n => n.id === selectedNodeId);

  return (
    <div className="w-full h-full relative">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        nodeTypes={nodeTypes}
        edgeTypes={edgeTypes}
        onNodeContextMenu={onNodeContextMenu}
        onNodeClick={onNodeClick}
        onPaneClick={onPaneClick}
        fitView
        minZoom={0.1}
        maxZoom={2}
        defaultViewport={{ x: 0, y: 0, zoom: 1 }}
        proOptions={{ hideAttribution: true }}
      >
        <Background
          variant={BackgroundVariant.Dots}
          gap={20}
          size={1}
          color="#334155"
        />
        <Controls
          className="!bg-slate-800 !border-slate-700 !rounded-lg [&>button]:!bg-slate-800 [&>button]:!border-slate-700 [&>button]:!text-slate-400 [&>button:hover]:!bg-slate-700"
          showInteractive={false}
        />
      </ReactFlow>

      {/* Wander Controls */}
      <WanderControls
        sessionId={sessionId}
        status={session?.status || 'paused'}
        stepCount={session?.stepCount || nodes.filter(n => n.data.type === 'locus' && (n.data as any).visited).length}
        onPlay={() => onSessionAction?.('play')}
        onPause={() => onSessionAction?.('pause')}
        onStop={() => onSessionAction?.('stop')}
        onStep={() => onSessionAction?.('step')}
        onSettingsClick={() => {}}
      />

      {/* Context Menu */}
      {contextMenu && (
        <NodeContextMenu
          nodeId={contextMenu.nodeId}
          nodeData={contextMenu.nodeData}
          position={contextMenu.position}
          onAction={handleNodeAction}
          onClose={() => setContextMenu(null)}
        />
      )}

      {/* Detail Panel */}
      {selectedNode && (
        <NodeDetailPanel
          node={selectedNode}
          onClose={() => setSelectedNodeId(null)}
        />
      )}
    </div>
  );
}

// Wrapper component that provides ReactFlow context
export function WanderMindMap(props: WanderMindMapProps) {
  return (
    <ReactFlowProvider>
      <WanderMindMapInner {...props} />
    </ReactFlowProvider>
  );
}

// Helper: Calculate position for new node (simple spiral layout)
function calculatePosition(index: number, step: number): { x: number; y: number } {
  const angle = step * 0.5;
  const radius = 100 + step * 30;
  return {
    x: Math.cos(angle) * radius,
    y: Math.sin(angle) * radius,
  };
}

// Helper: Load mock data for development
function loadMockData(
  setNodes: (nodes: WanderNode[]) => void,
  setEdges: (edges: WanderEdgeType[]) => void
) {
  const mockNodes: WanderNode[] = [
    {
      id: 'seed',
      type: 'locus',
      position: { x: 0, y: 0 },
      data: {
        type: 'locus',
        concept: 'Financial intelligence tooling for autonomous agents',
        domains: ['finance', 'technology'],
        abstractionLevel: 0.7,
        visited: true,
        isCurrent: false,
        visitCount: 1,
        interestingness: 0.8,
        noveltyScore: 0.5,
      },
    },
    {
      id: 'node-1',
      type: 'locus',
      position: { x: 150, y: 100 },
      data: {
        type: 'locus',
        concept: 'Real-time market data aggregation',
        domains: ['finance'],
        abstractionLevel: 0.4,
        visited: true,
        isCurrent: false,
        visitCount: 2,
        interestingness: 0.7,
        noveltyScore: 0.6,
      },
    },
    {
      id: 'node-2',
      type: 'locus',
      position: { x: -100, y: 150 },
      data: {
        type: 'locus',
        concept: 'Natural language processing for SEC filings',
        domains: ['technology', 'legal'],
        abstractionLevel: 0.5,
        visited: true,
        isCurrent: false,
        visitCount: 1,
        interestingness: 0.85,
        noveltyScore: 0.7,
      },
    },
    {
      id: 'node-3',
      type: 'locus',
      position: { x: 200, y: -50 },
      data: {
        type: 'locus',
        concept: 'Sentiment analysis from social media',
        domains: ['technology', 'social'],
        abstractionLevel: 0.4,
        visited: true,
        isCurrent: true,
        visitCount: 1,
        interestingness: 0.6,
        noveltyScore: 0.8,
      },
    },
    {
      id: 'crystal-1',
      type: 'crystal',
      position: { x: -150, y: -100 },
      data: {
        type: 'crystal',
        insight: 'Combining SEC filing analysis with social sentiment creates alpha signal unavailable from either source alone',
        domains: ['finance', 'technology'],
        confidence: 0.82,
        actionability: 0.75,
        sourceResonanceId: 'res-1',
        createdAt: new Date().toISOString(),
      },
    },
    {
      id: 'unvisited-1',
      type: 'locus',
      position: { x: 300, y: 150 },
      data: {
        type: 'locus',
        concept: 'Blockchain transaction flow analysis',
        domains: ['technology', 'finance'],
        abstractionLevel: 0.5,
        visited: false,
        isCurrent: false,
        visitCount: 0,
        interestingness: 0.5,
        noveltyScore: 0.9,
      },
    },
  ];

  const mockEdges: WanderEdgeType[] = [
    {
      id: 'seed-node-1',
      source: 'seed',
      target: 'node-1',
      type: 'wander',
      data: { edgeType: 'path', strength: 1, animated: false },
    },
    {
      id: 'seed-node-2',
      source: 'seed',
      target: 'node-2',
      type: 'wander',
      data: { edgeType: 'path', strength: 1, animated: false },
    },
    {
      id: 'node-1-node-3',
      source: 'node-1',
      target: 'node-3',
      type: 'wander',
      data: { edgeType: 'path', strength: 1, animated: true },
    },
    {
      id: 'node-2-crystal-1',
      source: 'node-2',
      target: 'crystal-1',
      type: 'wander',
      data: { edgeType: 'resonance', strength: 0.8, animated: false },
    },
    {
      id: 'node-3-unvisited-1',
      source: 'node-3',
      target: 'unvisited-1',
      type: 'wander',
      data: { edgeType: 'adjacency', strength: 0.5, animated: false },
    },
  ];

  setNodes(mockNodes);
  setEdges(mockEdges);
}

export default WanderMindMap;
```

---

## SPEC: NodeDetailPanel.tsx

```tsx
// hub/frontend/src/components/WanderMindMap/panels/NodeDetailPanel.tsx

import { X, ExternalLink, Clock, Sparkles, Target, Brain } from 'lucide-react';
import { WanderNode, WanderNodeData, getDomainColor } from '../types';

interface NodeDetailPanelProps {
  node: WanderNode;
  onClose: () => void;
}

export function NodeDetailPanel({ node, onClose }: NodeDetailPanelProps) {
  const data = node.data;

  return (
    <div className="absolute top-4 right-4 w-80 bg-slate-800/95 backdrop-blur-sm rounded-lg shadow-xl border border-slate-700 z-20">
      {/* Header */}
      <div className="px-4 py-3 border-b border-slate-700 flex items-center justify-between">
        <div className="flex items-center gap-2">
          {data.type === 'locus' && <Brain className="text-blue-400" size={18} />}
          {data.type === 'crystal' && <Sparkles className="text-yellow-400" size={18} />}
          {data.type === 'fractal' && <Target className="text-purple-400" size={18} />}
          <span className="font-medium text-white capitalize">{data.type}</span>
        </div>
        <button
          onClick={onClose}
          className="p-1 hover:bg-slate-700 rounded transition-colors"
        >
          <X size={18} className="text-slate-400" />
        </button>
      </div>

      {/* Content */}
      <div className="p-4 space-y-4">
        {/* Main text */}
        <div>
          <label className="text-xs text-slate-500 uppercase tracking-wide">
            {data.type === 'crystal' ? 'Insight' : 'Concept'}
          </label>
          <p className="text-slate-200 mt-1">
            {data.type === 'crystal'
              ? (data as any).insight
              : (data as any).concept
            }
          </p>
        </div>

        {/* Domains */}
        <div>
          <label className="text-xs text-slate-500 uppercase tracking-wide">Domains</label>
          <div className="flex flex-wrap gap-1.5 mt-1">
            {data.domains.map((domain) => (
              <span
                key={domain}
                className="px-2 py-0.5 rounded text-xs font-medium"
                style={{
                  backgroundColor: getDomainColor(domain) + '33',
                  color: getDomainColor(domain),
                }}
              >
                {domain}
              </span>
            ))}
          </div>
        </div>

        {/* Locus-specific fields */}
        {data.type === 'locus' && (
          <>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wide">Interestingness</label>
                <div className="mt-1">
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-blue-500 rounded-full"
                      style={{ width: `${(data as any).interestingness * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-400">
                    {((data as any).interestingness * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wide">Novelty</label>
                <div className="mt-1">
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 rounded-full"
                      style={{ width: `${(data as any).noveltyScore * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-400">
                    {((data as any).noveltyScore * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center justify-between text-sm">
              <span className="text-slate-400">Visit count</span>
              <span className="text-white font-medium">{(data as any).visitCount}</span>
            </div>

            {(data as any).isCurrent && (
              <div className="flex items-center gap-2 text-yellow-400 text-sm">
                <div className="w-2 h-2 bg-yellow-400 rounded-full animate-pulse" />
                Currently exploring
              </div>
            )}
          </>
        )}

        {/* Crystal-specific fields */}
        {data.type === 'crystal' && (
          <>
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wide">Confidence</label>
                <div className="mt-1">
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-yellow-500 rounded-full"
                      style={{ width: `${(data as any).confidence * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-400">
                    {((data as any).confidence * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
              <div>
                <label className="text-xs text-slate-500 uppercase tracking-wide">Actionability</label>
                <div className="mt-1">
                  <div className="h-2 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 rounded-full"
                      style={{ width: `${(data as any).actionability * 100}%` }}
                    />
                  </div>
                  <span className="text-xs text-slate-400">
                    {((data as any).actionability * 100).toFixed(0)}%
                  </span>
                </div>
              </div>
            </div>

            <div className="flex items-center gap-2 text-xs text-slate-500">
              <Clock size={12} />
              Crystallized {new Date((data as any).createdAt).toLocaleDateString()}
            </div>
          </>
        )}
      </div>

      {/* Footer actions */}
      <div className="px-4 py-3 border-t border-slate-700 flex gap-2">
        {data.type === 'locus' && (
          <button className="flex-1 py-2 px-3 bg-blue-600 hover:bg-blue-700 text-white text-sm rounded-lg transition-colors">
            Go Deeper
          </button>
        )}
        {data.type === 'crystal' && (
          <button className="flex-1 py-2 px-3 bg-green-600 hover:bg-green-700 text-white text-sm rounded-lg transition-colors flex items-center justify-center gap-2">
            <ExternalLink size={14} />
            Export
          </button>
        )}
      </div>
    </div>
  );
}

export default NodeDetailPanel;
```

---

## SPEC: index.ts (Barrel Exports)

```typescript
// hub/frontend/src/components/WanderMindMap/index.ts

export { WanderMindMap } from './WanderMindMap';
export { LocusNode } from './nodes/LocusNode';
export { CrystalNode } from './nodes/CrystalNode';
export { FractalNode } from './nodes/FractalNode';
export { WanderEdge } from './edges/WanderEdge';
export { WanderControls } from './controls/WanderControls';
export { NodeContextMenu } from './controls/NodeContextMenu';
export { NodeDetailPanel } from './panels/NodeDetailPanel';
export * from './types';
```

```typescript
// hub/frontend/src/components/WanderMindMap/nodes/index.ts

export { LocusNode } from './LocusNode';
export { CrystalNode } from './CrystalNode';
export { FractalNode } from './FractalNode';
```

```typescript
// hub/frontend/src/components/WanderMindMap/edges/index.ts

export { WanderEdge } from './WanderEdge';
```

---

## SPEC: WanderPage.tsx

```tsx
// hub/frontend/src/pages/WanderPage.tsx

import { useState } from 'react';
import { useParams } from 'react-router-dom';
import { WanderMindMap } from '../components/WanderMindMap';
import { WanderSession, NodeAction } from '../components/WanderMindMap/types';
import { Brain, Plus, List } from 'lucide-react';

export function WanderPage() {
  const { sessionId } = useParams<{ sessionId?: string }>();
  const [currentSessionId, setCurrentSessionId] = useState(sessionId || 'demo-session');

  // Mock session data - replace with API call
  const [session, setSession] = useState<WanderSession>({
    id: currentSessionId,
    name: 'Veria Business Model Exploration',
    status: 'paused',
    seedConcept: 'Financial intelligence tooling for autonomous agents',
    attractor: 'Economic opportunity with tractable solutions',
    stepCount: 5,
    cloudBudgetCents: 500,
    cloudSpentCents: 45,
    temperature: 0.7,
    createdAt: new Date().toISOString(),
  });

  const handleSessionAction = (action: 'play' | 'pause' | 'stop' | 'step') => {
    console.log('Session action:', action);

    // Update local state for demo
    if (action === 'play') {
      setSession(s => ({ ...s, status: 'active' }));
    } else if (action === 'pause') {
      setSession(s => ({ ...s, status: 'paused' }));
    } else if (action === 'stop') {
      setSession(s => ({ ...s, status: 'completed' }));
    }

    // TODO: Call backend API
  };

  const handleNodeAction = (action: NodeAction, nodeId: string) => {
    console.log('Node action:', action, nodeId);
    // TODO: Implement actions
  };

  return (
    <div className="h-screen flex flex-col bg-slate-900">
      {/* Header */}
      <header className="bg-slate-800 border-b border-slate-700 px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="flex items-center gap-2">
              <Brain className="text-purple-500" size={28} />
              <h1 className="text-xl font-bold text-white">Wander</h1>
            </div>
            <div className="h-6 w-px bg-slate-700" />
            <div>
              <h2 className="text-white font-medium">{session.name}</h2>
              <p className="text-slate-400 text-sm">{session.attractor}</p>
            </div>
          </div>

          <div className="flex items-center gap-3">
            {/* Budget indicator */}
            <div className="text-sm">
              <span className="text-slate-400">Budget: </span>
              <span className="text-white font-medium">
                ${(session.cloudSpentCents / 100).toFixed(2)} / ${(session.cloudBudgetCents / 100).toFixed(2)}
              </span>
            </div>

            {/* Session selector */}
            <button className="flex items-center gap-2 px-3 py-2 bg-slate-700 hover:bg-slate-600 rounded-lg text-slate-300 text-sm transition-colors">
              <List size={16} />
              Sessions
            </button>

            {/* New session */}
            <button className="flex items-center gap-2 px-3 py-2 bg-purple-600 hover:bg-purple-700 rounded-lg text-white text-sm transition-colors">
              <Plus size={16} />
              New Wander
            </button>
          </div>
        </div>
      </header>

      {/* Mind Map */}
      <main className="flex-1 relative">
        <WanderMindMap
          sessionId={currentSessionId}
          session={session}
          onSessionAction={handleSessionAction}
          onNodeAction={handleNodeAction}
        />
      </main>
    </div>
  );
}

export default WanderPage;
```

---

## SPEC: NATS Bridge Extension

Add these mappings to `backend/app/websocket/nats_bridge.py`:

```python
# Add to NATS_TO_WS_TOPIC_MAP

NATS_TO_WS_TOPIC_MAP: Dict[str, str] = {
    # Existing graph events
    "graph.node.created": "entity:created",
    "graph.node.updated": "entity:updated",
    "graph.node.deleted": "entity:deleted",
    "graph.edge.created": "edge:created",
    "graph.edge.deleted": "edge:deleted",
    "graph.invalidated": "graph:invalidated",

    # Wander events
    "wander.step.started": "wander:step:started",
    "wander.step.completed": "wander:step",
    "wander.adjacencies.found": "wander:adjacencies",
    "wander.resonance.detected": "wander:resonance",
    "wander.resonance.strengthened": "wander:resonance:strengthened",
    "wander.crystal.formed": "wander:crystal",
    "wander.session.paused": "wander:paused",
    "wander.session.resumed": "wander:resumed",
    "wander.fence.approached": "wander:fence",
    "wander.circuit.tripped": "wander:breaker",
}
```

---

## SPEC: CSS Animation (add to index.css)

```css
/* Add to hub/frontend/src/index.css */

@keyframes flowAnimation {
  0% {
    stroke-dashoffset: 0;
  }
  100% {
    stroke-dashoffset: 20;
  }
}

/* ReactFlow customizations */
.react-flow__node {
  cursor: pointer;
}

.react-flow__node:focus {
  outline: none;
}

.react-flow__edge-path {
  stroke-linecap: round;
}
```

---

## Verification Checklist

After implementation, verify:

- [ ] ReactFlow renders with mock nodes
- [ ] Custom nodes display correctly (Locus, Crystal, Fractal)
- [ ] Edges animate properly
- [ ] Controls work (zoom, pan, fit view)
- [ ] Play/Pause/Stop buttons update UI state
- [ ] Context menu appears on right-click
- [ ] Detail panel shows on node click
- [ ] Tooltips display on hover
- [ ] Current node has pulse animation
- [ ] Crystal nodes glow
- [ ] Fractal nodes show security indicators

---

## Next Steps After Phase 0

Once this component works with mock data:

1. **Phase 1-5**: Build wander engine (backend)
2. **Phase 6**: Wire WebSocket subscriptions to real NATS events
3. **Phase 7**: Add session persistence and archival
4. **Phase 8**: Implement fractal security layer

---

*This implementation plan provides copy-paste-ready components for autonomous agent implementation.*
