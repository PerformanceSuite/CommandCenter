import React, { useState } from 'react';
import type { ResearchTaskCreate } from '../../types/researchTask';
import { TaskStatus } from '../../types/researchTask';

interface ResearchTaskFormProps {
  onSubmit: (data: ResearchTaskCreate) => void;
  onCancel: () => void;
  initialData?: Partial<ResearchTaskCreate>;
  isLoading?: boolean;
}

export const ResearchTaskForm: React.FC<ResearchTaskFormProps> = ({
  onSubmit,
  onCancel,
  initialData,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<ResearchTaskCreate>({
    title: initialData?.title || '',
    description: initialData?.description || '',
    status: initialData?.status || TaskStatus.PENDING,
    technology_id: initialData?.technology_id,
    repository_id: initialData?.repository_id,
    assigned_to: initialData?.assigned_to || '',
    due_date: initialData?.due_date || '',
    estimated_hours: initialData?.estimated_hours,
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title.trim()) {
      newErrors.title = 'Title is required';
    }

    if (formData.estimated_hours && formData.estimated_hours < 0) {
      newErrors.estimated_hours = 'Estimated hours must be positive';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    // Clean up empty fields
    const cleanedData: ResearchTaskCreate = {
      title: formData.title.trim(),
      description: formData.description?.trim() || undefined,
      status: formData.status,
      technology_id: formData.technology_id || undefined,
      repository_id: formData.repository_id || undefined,
      assigned_to: formData.assigned_to?.trim() || undefined,
      due_date: formData.due_date || undefined,
      estimated_hours: formData.estimated_hours || undefined,
    };

    onSubmit(cleanedData);
  };

  const handleChange = (
    field: keyof ResearchTaskCreate,
    value: string | number | undefined
  ) => {
    setFormData((prev) => ({
      ...prev,
      [field]: value,
    }));

    // Clear error for this field
    if (errors[field]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[field];
        return newErrors;
      });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-4">
      {/* Title */}
      <div>
        <label
          htmlFor="title"
          className="block text-sm font-medium text-slate-300 mb-1"
        >
          Title <span className="text-red-500">*</span>
        </label>
        <input
          id="title"
          type="text"
          value={formData.title}
          onChange={(e) => handleChange('title', e.target.value)}
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
            errors.title ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="Enter task title"
          disabled={isLoading}
        />
        {errors.title && (
          <p className="mt-1 text-sm text-red-500">{errors.title}</p>
        )}
      </div>

      {/* Description */}
      <div>
        <label
          htmlFor="description"
          className="block text-sm font-medium text-slate-300 mb-1"
        >
          Description
        </label>
        <textarea
          id="description"
          value={formData.description}
          onChange={(e) => handleChange('description', e.target.value)}
          rows={4}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Enter task description"
          disabled={isLoading}
        />
      </div>

      {/* Status */}
      <div>
        <label
          htmlFor="status"
          className="block text-sm font-medium text-slate-300 mb-1"
        >
          Status
        </label>
        <select
          id="status"
          value={formData.status}
          onChange={(e) =>
            handleChange('status', e.target.value as TaskStatus)
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          disabled={isLoading}
        >
          <option value="pending">Pending</option>
          <option value="in_progress">In Progress</option>
          <option value="blocked">Blocked</option>
          <option value="completed">Completed</option>
          <option value="cancelled">Cancelled</option>
        </select>
      </div>

      {/* Technology ID (simple input for now) */}
      <div>
        <label
          htmlFor="technology_id"
          className="block text-sm font-medium text-slate-300 mb-1"
        >
          Technology ID (Optional)
        </label>
        <input
          id="technology_id"
          type="number"
          value={formData.technology_id || ''}
          onChange={(e) =>
            handleChange(
              'technology_id',
              e.target.value ? parseInt(e.target.value) : undefined
            )
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Enter technology ID"
          disabled={isLoading}
        />
        <p className="mt-1 text-xs text-slate-500">
          Link this task to a specific technology
        </p>
      </div>

      {/* Repository ID (simple input for now) */}
      <div>
        <label
          htmlFor="repository_id"
          className="block text-sm font-medium text-slate-300 mb-1"
        >
          Repository ID (Optional)
        </label>
        <input
          id="repository_id"
          type="number"
          value={formData.repository_id || ''}
          onChange={(e) =>
            handleChange(
              'repository_id',
              e.target.value ? parseInt(e.target.value) : undefined
            )
          }
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Enter repository ID"
          disabled={isLoading}
        />
        <p className="mt-1 text-xs text-slate-500">
          Link this task to a specific repository
        </p>
      </div>

      {/* Assignee */}
      <div>
        <label
          htmlFor="assigned_to"
          className="block text-sm font-medium text-slate-300 mb-1"
        >
          Assign To
        </label>
        <input
          id="assigned_to"
          type="text"
          value={formData.assigned_to}
          onChange={(e) => handleChange('assigned_to', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          placeholder="Enter assignee name"
          disabled={isLoading}
        />
      </div>

      {/* Due Date */}
      <div>
        <label
          htmlFor="due_date"
          className="block text-sm font-medium text-slate-300 mb-1"
        >
          Due Date
        </label>
        <input
          id="due_date"
          type="date"
          value={formData.due_date}
          onChange={(e) => handleChange('due_date', e.target.value)}
          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500"
          disabled={isLoading}
        />
      </div>

      {/* Estimated Hours */}
      <div>
        <label
          htmlFor="estimated_hours"
          className="block text-sm font-medium text-slate-300 mb-1"
        >
          Estimated Hours
        </label>
        <input
          id="estimated_hours"
          type="number"
          min="0"
          value={formData.estimated_hours || ''}
          onChange={(e) =>
            handleChange(
              'estimated_hours',
              e.target.value ? parseInt(e.target.value) : undefined
            )
          }
          className={`w-full px-3 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 ${
            errors.estimated_hours ? 'border-red-500' : 'border-gray-300'
          }`}
          placeholder="Enter estimated hours"
          disabled={isLoading}
        />
        {errors.estimated_hours && (
          <p className="mt-1 text-sm text-red-500">{errors.estimated_hours}</p>
        )}
      </div>

      {/* Actions */}
      <div className="flex gap-3 pt-4 border-t">
        <button
          type="submit"
          disabled={isLoading}
          className="flex-1 px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          {isLoading ? 'Saving...' : 'Save Task'}
        </button>
        <button
          type="button"
          onClick={onCancel}
          disabled={isLoading}
          className="flex-1 px-4 py-2 bg-slate-800 text-slate-300 rounded-lg hover:bg-slate-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          Cancel
        </button>
      </div>
    </form>
  );
};
