/**
 * TaskNode - Custom node for task entities
 */

'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

export const TaskNode = memo(({ data }: NodeProps) => {
  const status = data.metadata?.status || 'pending'
  const kind = data.metadata?.kind || 'feature'

  const statusColors: Record<string, string> = {
    pending: 'border-gray-400 bg-gray-50',
    in_progress: 'border-blue-500 bg-blue-50',
    completed: 'border-green-500 bg-green-50',
    blocked: 'border-red-500 bg-red-50',
  }

  const kindIcons: Record<string, string> = {
    feature: '✨',
    bug: '🐛',
    chore: '🔧',
    review: '👁️',
    security: '🔒',
  }

  return (
    <div className={`rounded-lg border-2 ${statusColors[status]} px-3 py-2 shadow-md`}>
      <Handle type="target" position={Position.Top} />
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <span className="text-lg">{kindIcons[kind] || '📝'}</span>
          <div className="text-xs font-medium">{data.label}</div>
        </div>
        <div className="text-xs text-gray-500">{kind}</div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
})

TaskNode.displayName = 'TaskNode'
