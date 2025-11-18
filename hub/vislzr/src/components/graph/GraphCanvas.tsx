/**
 * GraphCanvas - Main Graph Visualization Component
 *
 * Uses ReactFlow for interactive graph rendering with real-time updates.
 */

'use client'

import { useEffect, useState, useCallback } from 'react'
import ReactFlow, {
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  NodeTypes,
} from 'reactflow'
import 'reactflow/dist/style.css'
import { graphClient } from '@/lib/api/client'
import { useProjectEvents } from '@/lib/websocket/events'
import { FileNode } from '@/components/nodes/FileNode'
import { SymbolNode } from '@/components/nodes/SymbolNode'
import { ServiceNode } from '@/components/nodes/ServiceNode'
import { TaskNode } from '@/components/nodes/TaskNode'
import { NodeDetailPanel } from '@/components/panels/NodeDetailPanel'

const nodeTypes: NodeTypes = {
  file: FileNode,
  graph_file: FileNode, // Alias for database entity name
  symbol: SymbolNode,
  graph_symbol: SymbolNode,
  service: ServiceNode,
  task: TaskNode,
  graph_task: TaskNode,
}

interface GraphCanvasProps {
  projectId: number
}

export function GraphCanvas({ projectId }: GraphCanvasProps) {
  const [nodes, setNodes, onNodesChange] = useNodesState([])
  const [edges, setEdges, onEdgesChange] = useEdgesState([])
  const [selectedNode, setSelectedNode] = useState<Node | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Fetch graph data from REST API
  useEffect(() => {
    const fetchGraph = async () => {
      try {
        setLoading(true)
        setError(null)
        const data = await graphClient.getProjectGraph(projectId, 2)

        const graphNodes: Node[] = data.nodes.map((n, idx) => ({
          id: String(n.id),
          type: n.entity.toLowerCase(),
          position: {
            x: (idx % 10) * 200,
            y: Math.floor(idx / 10) * 150,
          },
          data: {
            label: n.label,
            metadata: n.metadata,
            entity: n.entity,
          },
        }))

        const graphEdges: Edge[] = data.edges.map((e, idx) => ({
          id: `${e.fromId}-${e.toId}-${idx}`,
          source: String(e.fromId),
          target: String(e.toId),
          label: e.type,
          animated: e.type === 'call' || e.type === 'import',
          type: 'smoothstep',
        }))

        setNodes(graphNodes)
        setEdges(graphEdges)
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load graph')
      } finally {
        setLoading(false)
      }
    }

    fetchGraph()
  }, [projectId, setNodes, setEdges])

  // Real-time updates from SSE
  useProjectEvents(projectId, (event) => {
    if (event.subject.includes('task.created')) {
      // Add new task node
      const newNode: Node = {
        id: String(event.payload.task_id),
        type: 'task',
        position: {
          x: Math.random() * 500 + 100,
          y: Math.random() * 400 + 100,
        },
        data: {
          label: event.payload.title,
          metadata: event.payload,
          entity: 'task',
        },
      }
      setNodes((nodes) => [...nodes, newNode])
    } else if (event.subject.includes('symbol.added')) {
      // Add new symbol node
      const newNode: Node = {
        id: String(event.payload.symbol_id),
        type: 'symbol',
        position: {
          x: Math.random() * 500 + 100,
          y: Math.random() * 400 + 100,
        },
        data: {
          label: event.payload.qualified_name,
          metadata: event.payload,
          entity: 'symbol',
        },
      }
      setNodes((nodes) => [...nodes, newNode])
    }
  })

  const onNodeClick = useCallback((event: React.MouseEvent, node: Node) => {
    setSelectedNode(node)
  }, [])

  if (loading) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="text-xl">Loading graph...</div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="flex h-screen w-full items-center justify-center">
        <div className="text-xl text-red-600">Error loading graph: {error}</div>
      </div>
    )
  }

  return (
    <div className="relative h-screen w-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        onNodesChange={onNodesChange}
        onEdgesChange={onEdgesChange}
        onNodeClick={onNodeClick}
        nodeTypes={nodeTypes}
        fitView
        attributionPosition="bottom-left"
      >
        <Controls />
        <MiniMap />
        <Background variant={BackgroundVariant.Dots} gap={12} size={1} />
      </ReactFlow>

      {selectedNode && (
        <div className="absolute right-0 top-0 h-full w-96">
          <NodeDetailPanel
            node={selectedNode}
            projectId={projectId}
            onClose={() => setSelectedNode(null)}
          />
        </div>
      )}
    </div>
  )
}
