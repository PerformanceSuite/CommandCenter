import React, { useState } from 'react';
import { X } from 'lucide-react';
import type { Technology, TechnologyCreate } from '../../types/technology';
import { TechnologyDomain as DomainEnum, TechnologyStatus as StatusEnum } from '../../types/technology';

interface TechnologyFormProps {
  technology?: Technology;
  onSubmit: (data: TechnologyCreate) => Promise<void>;
  onCancel: () => void;
  isLoading?: boolean;
}

export const TechnologyForm: React.FC<TechnologyFormProps> = ({
  technology,
  onSubmit,
  onCancel,
  isLoading = false,
}) => {
  const [formData, setFormData] = useState<TechnologyCreate>({
    title: technology?.title || '',
    vendor: technology?.vendor || '',
    domain: technology?.domain || DomainEnum.OTHER,
    status: technology?.status || StatusEnum.DISCOVERY,
    relevance_score: technology?.relevance_score || 50,
    priority: technology?.priority || 3,
    description: technology?.description || '',
    notes: technology?.notes || '',
    use_cases: technology?.use_cases || '',
    documentation_url: technology?.documentation_url || '',
    repository_url: technology?.repository_url || '',
    website_url: technology?.website_url || '',
    tags: technology?.tags || '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement | HTMLSelectElement>
  ) => {
    const { name, value } = e.target;
    setFormData((prev) => ({ ...prev, [name]: value }));
    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  const handleNumberChange = (name: string, value: number) => {
    setFormData((prev) => ({ ...prev, [name]: value }));
  };

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.title?.trim()) {
      newErrors.title = 'Title is required';
    }

    if (formData.relevance_score !== undefined && (formData.relevance_score < 0 || formData.relevance_score > 100)) {
      newErrors.relevance_score = 'Relevance score must be between 0 and 100';
    }

    if (formData.priority !== undefined && (formData.priority < 1 || formData.priority > 5)) {
      newErrors.priority = 'Priority must be between 1 and 5';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!validate()) return;

    try {
      await onSubmit(formData);
    } catch (error) {
      console.error('Failed to submit form:', error);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold">
            {technology ? 'Edit Technology' : 'Create Technology'}
          </h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-gray-600 transition-colors"
            aria-label="Close"
          >
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="p-6 space-y-6">
          {/* Basic Information */}
          <section>
            <h3 className="text-lg font-semibold mb-4">Basic Information</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-1">
                  Title <span className="text-red-500">*</span>
                </label>
                <input
                  type="text"
                  id="title"
                  name="title"
                  value={formData.title}
                  onChange={handleChange}
                  className={`w-full px-3 py-2 border rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent ${
                    errors.title ? 'border-red-500' : 'border-gray-300'
                  }`}
                  required
                />
                {errors.title && <p className="text-red-500 text-sm mt-1">{errors.title}</p>}
              </div>

              <div>
                <label htmlFor="vendor" className="block text-sm font-medium text-gray-700 mb-1">
                  Vendor
                </label>
                <input
                  type="text"
                  id="vendor"
                  name="vendor"
                  value={formData.vendor || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                />
              </div>

              <div>
                <label htmlFor="domain" className="block text-sm font-medium text-gray-700 mb-1">
                  Domain
                </label>
                <select
                  id="domain"
                  name="domain"
                  value={formData.domain}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {Object.values(DomainEnum).map((domain) => (
                    <option key={domain} value={domain}>
                      {domain.replace(/-/g, ' ').toUpperCase()}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label htmlFor="status" className="block text-sm font-medium text-gray-700 mb-1">
                  Status
                </label>
                <select
                  id="status"
                  name="status"
                  value={formData.status}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                >
                  {Object.values(StatusEnum).map((status) => (
                    <option key={status} value={status}>
                      {status.charAt(0).toUpperCase() + status.slice(1)}
                    </option>
                  ))}
                </select>
              </div>
            </div>
          </section>

          {/* Priority and Relevance */}
          <section>
            <h3 className="text-lg font-semibold mb-4">Priority & Relevance</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label htmlFor="priority" className="block text-sm font-medium text-gray-700 mb-1">
                  Priority (1-5)
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    id="priority"
                    name="priority"
                    min="1"
                    max="5"
                    value={formData.priority}
                    onChange={(e) => handleNumberChange('priority', parseInt(e.target.value))}
                    className="flex-1"
                  />
                  <div className="flex gap-1">
                    {[1, 2, 3, 4, 5].map((star) => (
                      <span
                        key={star}
                        className={`text-2xl ${
                          star <= (formData.priority || 3) ? 'text-yellow-500' : 'text-gray-300'
                        }`}
                      >
                        ★
                      </span>
                    ))}
                  </div>
                </div>
              </div>

              <div>
                <label
                  htmlFor="relevance_score"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Relevance Score (0-100)
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    id="relevance_score"
                    name="relevance_score"
                    min="0"
                    max="100"
                    value={formData.relevance_score}
                    onChange={(e) => handleNumberChange('relevance_score', parseInt(e.target.value))}
                    className="flex-1"
                  />
                  <span className="text-lg font-semibold w-12 text-right">
                    {formData.relevance_score}
                  </span>
                </div>
              </div>
            </div>
          </section>

          {/* Description and Notes */}
          <section>
            <h3 className="text-lg font-semibold mb-4">Details</h3>
            <div className="space-y-4">
              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-1">
                  Description
                </label>
                <textarea
                  id="description"
                  name="description"
                  value={formData.description || ''}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Brief description of the technology..."
                />
              </div>

              <div>
                <label htmlFor="use_cases" className="block text-sm font-medium text-gray-700 mb-1">
                  Use Cases
                </label>
                <textarea
                  id="use_cases"
                  name="use_cases"
                  value={formData.use_cases || ''}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Potential use cases for this technology..."
                />
              </div>

              <div>
                <label htmlFor="notes" className="block text-sm font-medium text-gray-700 mb-1">
                  Notes
                </label>
                <textarea
                  id="notes"
                  name="notes"
                  value={formData.notes || ''}
                  onChange={handleChange}
                  rows={3}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Additional notes..."
                />
              </div>

              <div>
                <label htmlFor="tags" className="block text-sm font-medium text-gray-700 mb-1">
                  Tags
                </label>
                <input
                  type="text"
                  id="tags"
                  name="tags"
                  value={formData.tags || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="Comma-separated tags..."
                />
              </div>
            </div>
          </section>

          {/* URLs */}
          <section>
            <h3 className="text-lg font-semibold mb-4">External Links</h3>
            <div className="space-y-4">
              <div>
                <label htmlFor="website_url" className="block text-sm font-medium text-gray-700 mb-1">
                  Website URL
                </label>
                <input
                  type="url"
                  id="website_url"
                  name="website_url"
                  value={formData.website_url || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="https://example.com"
                />
              </div>

              <div>
                <label
                  htmlFor="documentation_url"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Documentation URL
                </label>
                <input
                  type="url"
                  id="documentation_url"
                  name="documentation_url"
                  value={formData.documentation_url || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="https://docs.example.com"
                />
              </div>

              <div>
                <label
                  htmlFor="repository_url"
                  className="block text-sm font-medium text-gray-700 mb-1"
                >
                  Repository URL
                </label>
                <input
                  type="url"
                  id="repository_url"
                  name="repository_url"
                  value={formData.repository_url || ''}
                  onChange={handleChange}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  placeholder="https://github.com/example/repo"
                />
              </div>
            </div>
          </section>

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 transition-colors"
              disabled={isLoading}
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-4 py-2 text-white bg-primary-600 rounded-md hover:bg-primary-700 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              disabled={isLoading}
            >
              {isLoading ? 'Saving...' : technology ? 'Update' : 'Create'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};
