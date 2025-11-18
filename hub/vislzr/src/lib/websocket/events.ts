/**
 * WebSocket Event Stream for Real-Time Updates
 *
 * Subscribes to Server-Sent Events (SSE) from CommandCenter for graph updates.
 */

import { useEffect, useState } from 'react'

export interface GraphEvent {
  subject: string
  payload: {
    project_id?: number
    task_id?: number
    title?: string
    entity_type?: string
    entity_id?: number
    operation?: string
    [key: string]: any
  }
  timestamp: string
}

/**
 * Hook to subscribe to SSE events matching a pattern
 *
 * @param pattern - Event subject pattern (e.g., "hub.*.1.*" for project 1 events)
 * @param handler - Callback when event received
 */
export function useEventStream(pattern: string, handler: (event: GraphEvent) => void) {
  const [connected, setConnected] = useState(false)

  useEffect(() => {
    const baseUrl = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'
    const eventSource = new EventSource(`${baseUrl}/api/events/stream?filter=${pattern}`)

    eventSource.onopen = () => {
      setConnected(true)
      console.log('[VISLZR] SSE connected:', pattern)
    }

    eventSource.onmessage = (event) => {
      try {
        const data: GraphEvent = JSON.parse(event.data)
        handler(data)
      } catch (error) {
        console.error('[VISLZR] Failed to parse SSE event:', error)
      }
    }

    eventSource.onerror = (error) => {
      console.error('[VISLZR] SSE error:', error)
      setConnected(false)
      eventSource.close()
    }

    return () => {
      eventSource.close()
      setConnected(false)
    }
  }, [pattern, handler])

  return { connected }
}

/**
 * Hook to subscribe to graph update events for a project
 *
 * @param projectId - Project ID to monitor
 * @param handler - Callback when event received
 */
export function useProjectEvents(projectId: number, handler: (event: GraphEvent) => void) {
  return useEventStream(`graph.*.${projectId}`, handler)
}

/**
 * Hook to subscribe to audit result events
 *
 * @param handler - Callback when audit completes
 */
export function useAuditResults(handler: (event: GraphEvent) => void) {
  return useEventStream('audit.result.*', handler)
}
