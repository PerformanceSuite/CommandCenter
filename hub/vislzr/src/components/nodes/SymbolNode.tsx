/**
 * SymbolNode - Custom node for symbol entities (functions, classes, etc.)
 */

'use client'

import { memo } from 'react'
import { Handle, Position, NodeProps } from 'reactflow'

export const SymbolNode = memo(({ data }: NodeProps) => {
  const kindIcons: Record<string, string> = {
    function: '𝑓',
    class: 'C',
    module: 'M',
    variable: 'V',
    type: 'T',
  }

  const kind = data.metadata?.kind?.toLowerCase() || 'function'
  const icon = kindIcons[kind] || '•'

  return (
    <div className="rounded-lg border-2 border-purple-500 bg-white px-3 py-2 shadow-md">
      <Handle type="target" position={Position.Top} />
      <div className="flex items-center gap-2">
        <div className="flex h-6 w-6 items-center justify-center rounded bg-purple-100 text-sm font-bold text-purple-700">
          {icon}
        </div>
        <div className="text-xs font-medium">{data.label}</div>
      </div>
      <Handle type="source" position={Position.Bottom} />
    </div>
  )
})

SymbolNode.displayName = 'SymbolNode'
