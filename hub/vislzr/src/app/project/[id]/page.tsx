/**
 * Project Graph View Page
 *
 * Displays interactive graph visualization for a specific project.
 */

'use client'

import { GraphCanvas } from '@/components/graph/GraphCanvas'

interface PageProps {
  params: { id: string }
}

export default function ProjectPage({ params }: PageProps) {
  const projectId = parseInt(params.id, 10)

  if (isNaN(projectId)) {
    return (
      <div className="flex h-screen items-center justify-center">
        <div className="text-xl text-red-600">Invalid project ID</div>
      </div>
    )
  }

  return (
    <main className="h-screen w-full">
      <GraphCanvas projectId={projectId} />
    </main>
  )
}
