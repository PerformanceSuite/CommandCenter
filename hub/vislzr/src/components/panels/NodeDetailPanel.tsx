/**
 * NodeDetailPanel - Side panel showing node details and actions
 */

'use client'

import { useState } from 'react'
import { Node } from 'reactflow'
import { graphClient } from '@/lib/api/client'

interface NodeDetailPanelProps {
  node: Node
  projectId: number
  onClose: () => void
}

export function NodeDetailPanel({ node, projectId, onClose }: NodeDetailPanelProps) {
  const [activeTab, setActiveTab] = useState<'overview' | 'code' | 'audits' | 'links'>('overview')
  const [auditLoading, setAuditLoading] = useState(false)

  const handleCodeReview = async () => {
    try {
      setAuditLoading(true)
      await graphClient.triggerAudit(
        node.data.entity,
        parseInt(node.id),
        'codeReview',
        projectId
      )
      alert('Code review triggered successfully!')
    } catch (error) {
      console.error('Failed to trigger code review:', error)
      alert('Failed to trigger code review')
    } finally {
      setAuditLoading(false)
    }
  }

  const handleSecurityScan = async () => {
    try {
      setAuditLoading(true)
      await graphClient.triggerAudit(
        node.data.entity,
        parseInt(node.id),
        'security',
        projectId
      )
      alert('Security scan triggered successfully!')
    } catch (error) {
      console.error('Failed to trigger security scan:', error)
      alert('Failed to trigger security scan')
    } finally {
      setAuditLoading(false)
    }
  }

  const handleCompleteness = async () => {
    try {
      setAuditLoading(true)
      await graphClient.triggerAudit(
        node.data.entity,
        parseInt(node.id),
        'completeness',
        projectId
      )
      alert('Completeness audit triggered successfully!')
    } catch (error) {
      console.error('Failed to trigger completeness audit:', error)
      alert('Failed to trigger completeness audit')
    } finally {
      setAuditLoading(false)
    }
  }

  return (
    <div className="flex h-full flex-col bg-white shadow-2xl">
      {/* Header */}
      <div className="flex items-start justify-between border-b p-6">
        <div>
          <h2 className="text-xl font-bold">{node.data.label}</h2>
          <p className="mt-1 text-sm text-gray-500">
            {node.data.entity} • ID: {node.id}
          </p>
        </div>
        <button
          onClick={onClose}
          className="rounded-lg p-2 hover:bg-gray-100"
          aria-label="Close panel"
        >
          <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {/* Tabs */}
      <div className="flex border-b">
        {(['overview', 'code', 'audits', 'links'] as const).map((tab) => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            className={`px-4 py-2 text-sm font-medium ${
              activeTab === tab
                ? 'border-b-2 border-blue-500 text-blue-600'
                : 'text-gray-500 hover:text-gray-700'
            }`}
          >
            {tab.charAt(0).toUpperCase() + tab.slice(1)}
          </button>
        ))}
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto p-6">
        {activeTab === 'overview' && (
          <div className="space-y-4">
            <div>
              <h3 className="mb-2 font-semibold">Metadata</h3>
              <pre className="rounded bg-gray-50 p-3 text-xs">
                {JSON.stringify(node.data.metadata, null, 2)}
              </pre>
            </div>
          </div>
        )}

        {activeTab === 'audits' && (
          <div className="space-y-4">
            <h3 className="font-semibold">Trigger Audit</h3>
            <div className="space-y-2">
              <button
                onClick={handleCodeReview}
                disabled={auditLoading}
                className="w-full rounded-lg border border-blue-500 bg-blue-50 px-4 py-2 text-left text-sm font-medium text-blue-700 hover:bg-blue-100 disabled:opacity-50"
              >
                🔍 Run Code Review
              </button>
              <button
                onClick={handleSecurityScan}
                disabled={auditLoading}
                className="w-full rounded-lg border border-red-500 bg-red-50 px-4 py-2 text-left text-sm font-medium text-red-700 hover:bg-red-100 disabled:opacity-50"
              >
                🔒 Run Security Scan
              </button>
              <button
                onClick={handleCompleteness}
                disabled={auditLoading}
                className="w-full rounded-lg border border-green-500 bg-green-50 px-4 py-2 text-left text-sm font-medium text-green-700 hover:bg-green-100 disabled:opacity-50"
              >
                ✅ Run Completeness Check
              </button>
            </div>
          </div>
        )}

        {activeTab === 'code' && (
          <div>
            <p className="text-sm text-gray-500">Code viewer coming soon...</p>
          </div>
        )}

        {activeTab === 'links' && (
          <div>
            <p className="text-sm text-gray-500">Linked entities coming soon...</p>
          </div>
        )}
      </div>
    </div>
  )
}
