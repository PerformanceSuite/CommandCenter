import React, { useState } from 'react';
import { X } from 'lucide-react';
import type { Technology, TechnologyCreate } from '../../types/technology';
import {
  TechnologyDomain as DomainEnum,
  TechnologyStatus as StatusEnum,
  IntegrationDifficulty,
  MaturityLevel,
  CostTier,
} from '../../types/technology';

interface TechnologyFormProps {
  technology?: Technology;
  onSubmit: (data: any) => Promise<void>;
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
    // Technology Radar v2 fields
    latency_ms: technology?.latency_ms || null,
    throughput_qps: technology?.throughput_qps || null,
    integration_difficulty: technology?.integration_difficulty || null,
    integration_time_estimate_days: technology?.integration_time_estimate_days || null,
    maturity_level: technology?.maturity_level || null,
    stability_score: technology?.stability_score || null,
    cost_tier: technology?.cost_tier || null,
    cost_monthly_usd: technology?.cost_monthly_usd || null,
    dependencies: technology?.dependencies || null,
    alternatives: technology?.alternatives || '',
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

  const handleNumberChange = (name: string, value: number | null) => {
    // Validate numeric ranges
    if (value !== null) {
      if (name === 'stability_score' && (value < 0 || value > 100)) {
        return; // Stability score must be 0-100
      }
      if (name === 'latency_ms' && value < 0) {
        return; // Latency cannot be negative
      }
      if (name === 'throughput_qps' && value < 0) {
        return; // Throughput cannot be negative
      }
      if (name === 'integration_time_estimate_days' && value < 0) {
        return; // Integration time cannot be negative
      }
      if (name === 'cost_monthly_usd' && value < 0) {
        return; // Cost cannot be negative
      }
    }
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
      <div className="bg-slate-800/50 border border-slate-700/50 rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
        <div className="sticky top-0 bg-white border-b border-gray-200 px-6 py-4 flex items-center justify-between">
          <h2 className="text-2xl font-bold">
            {technology ? 'Edit Technology' : 'Create Technology'}
          </h2>
          <button
            onClick={onCancel}
            className="text-gray-400 hover:text-slate-400 transition-colors"
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
                <label htmlFor="title" className="block text-sm font-medium text-slate-300 mb-1">
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
                <label htmlFor="vendor" className="block text-sm font-medium text-slate-300 mb-1">
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
                <label htmlFor="domain" className="block text-sm font-medium text-slate-300 mb-1">
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
                <label htmlFor="status" className="block text-sm font-medium text-slate-300 mb-1">
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
                <label htmlFor="priority" className="block text-sm font-medium text-slate-300 mb-1">
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
                  className="block text-sm font-medium text-slate-300 mb-1"
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
                <label htmlFor="description" className="block text-sm font-medium text-slate-300 mb-1">
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
                <label htmlFor="use_cases" className="block text-sm font-medium text-slate-300 mb-1">
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
                <label htmlFor="notes" className="block text-sm font-medium text-slate-300 mb-1">
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
                <label htmlFor="tags" className="block text-sm font-medium text-slate-300 mb-1">
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
                <label htmlFor="website_url" className="block text-sm font-medium text-slate-300 mb-1">
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
                  className="block text-sm font-medium text-slate-300 mb-1"
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
                  className="block text-sm font-medium text-slate-300 mb-1"
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

          {/* Technology Radar v2 - Advanced Evaluation */}
          <section>
            <h3 className="text-lg font-semibold mb-4">Advanced Evaluation (Technology Radar v2)</h3>

            {/* Performance Characteristics */}
            <div className="mb-6">
              <h4 className="text-md font-medium text-slate-300 mb-3">Performance</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="latency_ms" className="block text-sm font-medium text-slate-300 mb-1">
                    Latency (ms) - P99
                  </label>
                  <input
                    type="number"
                    id="latency_ms"
                    name="latency_ms"
                    min="0"
                    step="0.01"
                    value={formData.latency_ms || ''}
                    onChange={(e) => handleNumberChange('latency_ms', e.target.value ? parseFloat(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="P99 latency in milliseconds"
                    title="99th percentile latency in milliseconds (e.g., 50.5ms)"
                  />
                </div>

                <div>
                  <label htmlFor="throughput_qps" className="block text-sm font-medium text-slate-300 mb-1">
                    Throughput (QPS)
                  </label>
                  <input
                    type="number"
                    id="throughput_qps"
                    name="throughput_qps"
                    min="0"
                    value={formData.throughput_qps || ''}
                    onChange={(e) => handleNumberChange('throughput_qps', e.target.value ? parseInt(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="Queries per second"
                    title="Maximum queries per second the technology can handle"
                  />
                </div>
              </div>
            </div>

            {/* Integration Assessment */}
            <div className="mb-6">
              <h4 className="text-md font-medium text-slate-300 mb-3">Integration</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="integration_difficulty" className="block text-sm font-medium text-slate-300 mb-1">
                    Integration Difficulty
                  </label>
                  <select
                    id="integration_difficulty"
                    name="integration_difficulty"
                    value={formData.integration_difficulty || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    title="Estimated complexity of integrating this technology (TRIVIAL: <1 day, EASY: 1-3 days, MODERATE: 1-2 weeks, COMPLEX: 2-4 weeks, VERY_COMPLEX: >1 month)"
                  >
                    <option value="">Select difficulty</option>
                    {Object.values(IntegrationDifficulty).map((diff) => (
                      <option key={diff} value={diff}>
                        {diff.replace('_', ' ').toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="integration_time_estimate_days" className="block text-sm font-medium text-slate-300 mb-1">
                    Integration Time (days)
                  </label>
                  <input
                    type="number"
                    id="integration_time_estimate_days"
                    name="integration_time_estimate_days"
                    min="0"
                    value={formData.integration_time_estimate_days || ''}
                    onChange={(e) => handleNumberChange('integration_time_estimate_days', e.target.value ? parseInt(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="Estimated integration days"
                    title="Estimated number of days needed for full integration"
                  />
                </div>
              </div>
            </div>

            {/* Maturity and Stability */}
            <div className="mb-6">
              <h4 className="text-md font-medium text-slate-300 mb-3">Maturity & Stability</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="maturity_level" className="block text-sm font-medium text-slate-300 mb-1">
                    Maturity Level
                  </label>
                  <select
                    id="maturity_level"
                    name="maturity_level"
                    value={formData.maturity_level || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">Select maturity</option>
                    {Object.values(MaturityLevel).map((level) => (
                      <option key={level} value={level}>
                        {level.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="stability_score" className="block text-sm font-medium text-slate-300 mb-1">
                    Stability Score (0-100)
                  </label>
                  <div className="flex items-center gap-4">
                    <input
                      type="range"
                      id="stability_score"
                      name="stability_score"
                      min="0"
                      max="100"
                      value={formData.stability_score || 50}
                      onChange={(e) => handleNumberChange('stability_score', parseInt(e.target.value))}
                      className="flex-1"
                    />
                    <span className="text-lg font-semibold w-12 text-right">
                      {formData.stability_score || 50}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Cost Analysis */}
            <div className="mb-6">
              <h4 className="text-md font-medium text-slate-300 mb-3">Cost Analysis</h4>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="cost_tier" className="block text-sm font-medium text-slate-300 mb-1">
                    Cost Tier
                  </label>
                  <select
                    id="cost_tier"
                    name="cost_tier"
                    value={formData.cost_tier || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                  >
                    <option value="">Select cost tier</option>
                    {Object.values(CostTier).map((tier) => (
                      <option key={tier} value={tier}>
                        {tier.toUpperCase()}
                      </option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="cost_monthly_usd" className="block text-sm font-medium text-slate-300 mb-1">
                    Monthly Cost (USD)
                  </label>
                  <input
                    type="number"
                    id="cost_monthly_usd"
                    name="cost_monthly_usd"
                    min="0"
                    step="0.01"
                    value={formData.cost_monthly_usd || ''}
                    onChange={(e) => handleNumberChange('cost_monthly_usd', e.target.value ? parseFloat(e.target.value) : null)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="Monthly cost in USD"
                    title="Average monthly cost in USD for expected usage"
                  />
                </div>
              </div>
            </div>

            {/* Dependencies and Alternatives */}
            <div>
              <h4 className="text-md font-medium text-slate-300 mb-3">Relationships</h4>
              <div className="space-y-4">
                {/* TODO: Add UI for 'dependencies' field (JSON object: Record<string, string>)
                    This field stores technology dependencies as key-value pairs.
                    Future enhancement: Add a key-value pair editor or JSON editor component.
                    For now, dependencies can be managed via API directly. */}
                <div>
                  <label htmlFor="alternatives" className="block text-sm font-medium text-slate-300 mb-1">
                    Alternative Technologies
                  </label>
                  <input
                    type="text"
                    id="alternatives"
                    name="alternatives"
                    value={formData.alternatives || ''}
                    onChange={handleChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                    placeholder="Comma-separated technology names"
                    title="List alternative or competing technologies"
                  />
                  <p className="text-sm text-slate-500 mt-1">
                    List alternative technologies (e.g., "React, Vue, Angular")
                  </p>
                </div>
              </div>
            </div>
          </section>

          {/* Form Actions */}
          <div className="flex items-center justify-end gap-3 pt-4 border-t border-gray-200">
            <button
              type="button"
              onClick={onCancel}
              className="px-4 py-2 text-slate-300 bg-white border border-gray-300 rounded-md hover:bg-slate-900 transition-colors"
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
