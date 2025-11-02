import React, { useState, useRef } from 'react';
import { X, Upload, Download, FileText } from 'lucide-react';
import type { ResearchTask, ResearchTaskUpdate } from '../../types/researchTask';
import { TaskStatus } from '../../types/researchTask';
import { useUpdateResearchTask, useUploadDocument } from '../../hooks/useResearchTasks';

interface ResearchTaskModalProps {
  task: ResearchTask;
  isOpen: boolean;
  onClose: () => void;
}

type TabType = 'overview' | 'documents' | 'notes' | 'findings' | 'activity';

export const ResearchTaskModal: React.FC<ResearchTaskModalProps> = ({
  task,
  isOpen,
  onClose,
}) => {
  const [activeTab, setActiveTab] = useState<TabType>('overview');
  const [editData, setEditData] = useState<ResearchTaskUpdate>({});
  const fileInputRef = useRef<HTMLInputElement>(null);

  const updateMutation = useUpdateResearchTask();
  const uploadMutation = useUploadDocument();

  if (!isOpen) return null;

  const handleUpdate = (field: keyof ResearchTaskUpdate, value: string | number | TaskStatus | undefined) => {
    setEditData((prev) => ({ ...prev, [field]: value }));
  };

  const handleSave = async () => {
    if (Object.keys(editData).length === 0) return;

    try {
      await updateMutation.mutateAsync({
        taskId: task.id,
        data: editData,
      });
      setEditData({});
    } catch (error) {
      console.error('Failed to update task:', error);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      await uploadMutation.mutateAsync({
        taskId: task.id,
        file,
      });
      // Reset file input
      if (fileInputRef.current) {
        fileInputRef.current.value = '';
      }
    } catch (error) {
      console.error('Failed to upload document:', error);
    }
  };

  const tabs: { id: TabType; label: string }[] = [
    { id: 'overview', label: 'Overview' },
    { id: 'documents', label: 'Documents' },
    { id: 'notes', label: 'Notes' },
    { id: 'findings', label: 'Findings' },
    { id: 'activity', label: 'Activity' },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black bg-opacity-50">
      <div className="bg-slate-800 border border-slate-700 rounded-lg shadow-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b">
          <h2 className="text-2xl font-bold text-white">{task.title}</h2>
          <button
            onClick={onClose}
            className="p-2 hover:bg-slate-800 rounded-full transition-colors"
          >
            <X size={24} />
          </button>
        </div>

        {/* Tabs */}
        <div className="border-b">
          <div className="flex gap-4 px-6">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`py-3 px-2 border-b-2 font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'border-primary-600 text-primary-600'
                    : 'border-transparent text-slate-500 hover:text-slate-300'
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Overview Tab */}
          {activeTab === 'overview' && (
            <div className="space-y-4">
              {/* Description */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Description
                </label>
                <textarea
                  value={editData.description ?? task.description ?? ''}
                  onChange={(e) => handleUpdate('description', e.target.value)}
                  rows={4}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Enter task description"
                />
              </div>

              {/* Status */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Status
                </label>
                <select
                  value={editData.status ?? task.status}
                  onChange={(e) => handleUpdate('status', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                >
                  <option value="pending">Pending</option>
                  <option value="in_progress">In Progress</option>
                  <option value="blocked">Blocked</option>
                  <option value="completed">Completed</option>
                  <option value="cancelled">Cancelled</option>
                </select>
              </div>

              {/* Progress */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Progress: {editData.progress_percentage ?? task.progress_percentage}%
                </label>
                <input
                  type="range"
                  min="0"
                  max="100"
                  value={editData.progress_percentage ?? task.progress_percentage}
                  onChange={(e) =>
                    handleUpdate('progress_percentage', parseInt(e.target.value))
                  }
                  className="w-full"
                />
              </div>

              {/* Assignee */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Assigned To
                </label>
                <input
                  type="text"
                  value={editData.assigned_to ?? task.assigned_to ?? ''}
                  onChange={(e) => handleUpdate('assigned_to', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Enter assignee name"
                />
              </div>

              {/* Due Date */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Due Date
                </label>
                <input
                  type="date"
                  value={
                    editData.due_date ??
                    (task.due_date ? task.due_date.split('T')[0] : '')
                  }
                  onChange={(e) => handleUpdate('due_date', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                />
              </div>

              {/* Actual Hours */}
              <div>
                <label className="block text-sm font-medium text-slate-300 mb-2">
                  Actual Hours
                </label>
                <input
                  type="number"
                  min="0"
                  value={editData.actual_hours ?? task.actual_hours ?? ''}
                  onChange={(e) =>
                    handleUpdate(
                      'actual_hours',
                      e.target.value ? parseInt(e.target.value) : undefined
                    )
                  }
                  className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
                  placeholder="Enter actual hours spent"
                />
              </div>

              {/* Metadata Display */}
              <div className="grid grid-cols-2 gap-4 pt-4 border-t">
                <div>
                  <span className="text-sm text-slate-500">Estimated Hours:</span>
                  <p className="font-medium">{task.estimated_hours ?? 'N/A'}</p>
                </div>
                <div>
                  <span className="text-sm text-slate-500">Created:</span>
                  <p className="font-medium">
                    {new Date(task.created_at).toLocaleDateString()}
                  </p>
                </div>
                <div>
                  <span className="text-sm text-slate-500">Technology ID:</span>
                  <p className="font-medium">{task.technology_id ?? 'N/A'}</p>
                </div>
                <div>
                  <span className="text-sm text-slate-500">Repository ID:</span>
                  <p className="font-medium">{task.repository_id ?? 'N/A'}</p>
                </div>
              </div>
            </div>
          )}

          {/* Documents Tab */}
          {activeTab === 'documents' && (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-semibold">Uploaded Documents</h3>
                <button
                  onClick={() => fileInputRef.current?.click()}
                  disabled={uploadMutation.isPending}
                  className="flex items-center gap-2 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
                >
                  <Upload size={18} />
                  {uploadMutation.isPending ? 'Uploading...' : 'Upload Document'}
                </button>
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={handleFileUpload}
                  className="hidden"
                />
              </div>

              {task.uploaded_documents && task.uploaded_documents.length > 0 ? (
                <div className="space-y-2">
                  {task.uploaded_documents.map((doc, index) => (
                    <div
                      key={index}
                      className="flex items-center justify-between p-3 border border-gray-200 rounded-lg hover:bg-slate-900"
                    >
                      <div className="flex items-center gap-3">
                        <FileText size={20} className="text-gray-400" />
                        <div>
                          <p className="font-medium">{doc.filename}</p>
                          <p className="text-sm text-slate-500">
                            {(doc.size / 1024).toFixed(2)} KB •{' '}
                            {new Date(doc.uploaded_at).toLocaleDateString()}
                          </p>
                        </div>
                      </div>
                      <button
                        className="p-2 text-gray-400 hover:text-primary-600 transition-colors"
                        title="Download"
                      >
                        <Download size={18} />
                      </button>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-500">
                  <FileText size={48} className="mx-auto mb-3 opacity-30" />
                  <p>No documents uploaded yet</p>
                </div>
              )}
            </div>
          )}

          {/* Notes Tab */}
          {activeTab === 'notes' && (
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                User Notes
              </label>
              <textarea
                value={editData.user_notes ?? task.user_notes ?? ''}
                onChange={(e) => handleUpdate('user_notes', e.target.value)}
                rows={12}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
                placeholder="Enter your notes here..."
              />
            </div>
          )}

          {/* Findings Tab */}
          {activeTab === 'findings' && (
            <div>
              <label className="block text-sm font-medium text-slate-300 mb-2">
                Research Findings
              </label>
              <textarea
                value={editData.findings ?? task.findings ?? ''}
                onChange={(e) => handleUpdate('findings', e.target.value)}
                rows={12}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 font-mono text-sm"
                placeholder="Document your research findings..."
              />
            </div>
          )}

          {/* Activity Tab */}
          {activeTab === 'activity' && (
            <div className="space-y-4">
              <div className="border-l-2 border-gray-200 pl-4 space-y-6">
                <div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium">Created</span>
                    <span className="text-slate-500">
                      {new Date(task.created_at).toLocaleString()}
                    </span>
                  </div>
                </div>
                <div>
                  <div className="flex items-center gap-2 text-sm">
                    <span className="font-medium">Last Updated</span>
                    <span className="text-slate-500">
                      {new Date(task.updated_at).toLocaleString()}
                    </span>
                  </div>
                </div>
                {task.completed_at && (
                  <div>
                    <div className="flex items-center gap-2 text-sm">
                      <span className="font-medium">Completed</span>
                      <span className="text-slate-500">
                        {new Date(task.completed_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="flex items-center justify-end gap-3 p-6 border-t bg-slate-900">
          <button
            onClick={onClose}
            className="px-4 py-2 text-slate-300 hover:bg-slate-700 rounded-lg transition-colors"
          >
            Close
          </button>
          {Object.keys(editData).length > 0 && (
            <button
              onClick={handleSave}
              disabled={updateMutation.isPending}
              className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              {updateMutation.isPending ? 'Saving...' : 'Save Changes'}
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
