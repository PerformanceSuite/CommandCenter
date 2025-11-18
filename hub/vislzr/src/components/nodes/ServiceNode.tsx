/**
 * ServiceNode - Custom node for service entities
 */

'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

export const ServiceNode = memo(({ data }: NodeProps) => {
  const healthStatus = data.metadata?.health_status || 'unknown'
  const statusColors: Record<string, string> = {
    up: 'border-green-500 bg-green-50',
    down: 'border-red-500 bg-red-50',
    degraded: 'border-yellow-500 bg-yellow-50',
    unknown: 'border-gray-500 bg-gray-50',
  }

  return (
    <div className={`rounded-lg border-2 ${statusColors[healthStatus]} px-4 py-3 shadow-md`}>
      <Handle type="target" position={Position.Top} />
      <div className="space-y-1">
        <div className="flex items-center gap-2">
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01"
            />
          </svg>
          <div className="text-sm font-bold">{data.label}</div>
        </div>
        <div className="text-xs text-gray-600">{data.metadata?.type || 'service'}</div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
})

ServiceNode.displayName = 'ServiceNode'
