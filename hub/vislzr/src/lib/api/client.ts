/**
 * REST API Client for CommandCenter GraphService
 *
 * Fetches graph data from the backend REST endpoints.
 */

const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || 'http://localhost:8000'

export interface GraphNode {
  id: number
  entity: string
  label: string
  metadata?: Record<string, any>
}

export interface GraphEdge {
  fromId: number
  toId: number
  type: string
  weight?: number
}

export interface ProjectGraph {
  nodes: GraphNode[]
  edges: GraphEdge[]
}

export interface AuditResult {
  id: number
  status: string
  summary?: string
}

export class GraphAPIClient {
  private baseUrl: string
  private authToken?: string

  constructor(baseUrl = API_BASE) {
    this.baseUrl = baseUrl
  }

  setAuthToken(token: string) {
    this.authToken = token
  }

  private async fetch<T>(path: string, options?: RequestInit): Promise<T> {
    const headers: HeadersInit = {
      'Content-Type': 'application/json',
      ...(options?.headers || {}),
    }

    if (this.authToken) {
      headers['Authorization'] = `Bearer ${this.authToken}`
    }

    const response = await fetch(`${this.baseUrl}${path}`, {
      ...options,
      headers,
    })

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: response.statusText }))
      throw new Error(error.detail || `API error: ${response.status}`)
    }

    return response.json()
  }

  async getProjectGraph(projectId: number, depth = 2): Promise<ProjectGraph> {
    return this.fetch<ProjectGraph>(`/api/v1/graph/projects/${projectId}?depth=${depth}`)
  }

  async triggerAudit(
    targetEntity: string,
    targetId: number,
    kind: string,
    projectId: number
  ): Promise<AuditResult> {
    return this.fetch<AuditResult>('/api/v1/graph/audit/trigger', {
      method: 'POST',
      body: JSON.stringify({
        target_entity: targetEntity,
        target_id: targetId,
        kind,
        project_id: projectId,
      }),
    })
  }

  async searchGraph(
    projectId: number,
    query: string,
    entityTypes?: string[]
  ): Promise<{ results: GraphNode[] }> {
    return this.fetch('/api/v1/graph/search', {
      method: 'POST',
      body: JSON.stringify({
        project_id: projectId,
        query,
        entity_types: entityTypes,
      }),
    })
  }
}

export const graphClient = new GraphAPIClient()
