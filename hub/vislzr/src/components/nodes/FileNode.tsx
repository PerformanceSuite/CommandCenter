/**
 * FileNode - Custom node for file entities
 */

'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

export const FileNode = memo(({ data }: NodeProps) => {
  return (
    <div className="rounded-lg border-2 border-blue-500 bg-white px-4 py-2 shadow-md">
      <Handle type="target" position={Position.Top} />
      <div className="flex items-center gap-2">
        <svg
          className="h-5 w-5 text-blue-500"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M7 21h10a2 2 0 002-2V9.414a1 1 0 00-.293-.707l-5.414-5.414A1 1 0 0012.586 3H7a2 2 0 00-2 2v14a2 2 0 002 2z"
          />
        </svg>
        <div className="text-sm font-medium">{data.label}</div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
})

FileNode.displayName = 'FileNode'
